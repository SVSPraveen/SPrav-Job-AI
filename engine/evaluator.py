import json
import os
from datetime import datetime
from engine.llm_provider import generate

KB_PATH = "knowledge_base/me.json"
MASTER_IDENTITY_PATH = "knowledge_base/master_identity.txt"

class KnowledgeDistiller:
    def __init__(self):
        # Approx 1 token = 4 chars. We want chunks of ~4000 tokens.
        self.chunk_size_chars = 16000 
        
    def _load_all_user_data(self) -> str:
        """Loads the entirety of the user's uploaded knowledge base."""
        kb_text = ""
        if os.path.exists(KB_PATH):
            with open(KB_PATH, "r") as f:
                data = json.load(f)
            kb_text += json.dumps(data) + "\n\n"
            
        proof_path = "knowledge_base/proof_points.md"
        if os.path.exists(proof_path):
            with open(proof_path, "r", encoding="utf-8") as f:
                kb_text += "PORTFOLIO & PROOF POINTS:\n" + f.read()
                
        return kb_text
        
    def _chunk_text(self, text: str) -> list:
        """Splits massive text into safe chunk sizes."""
        chunks = []
        for i in range(0, len(text), self.chunk_size_chars):
            chunks.append(text[i : i + self.chunk_size_chars])
        return chunks

    def _calculate_yoe(self) -> float:
        """Calculates YoE strictly from employment-type roles in the KB."""
        if not os.path.exists(KB_PATH):
            return 0.0
            
        try:
            with open(KB_PATH, "r", encoding="utf-8") as f:
                kb = json.load(f)
        except Exception:
            return 0.0
            
        total_days = 0
        valid_types = {"full-time", "part-time", "internship", "contract"}
        
        for job in kb.get("work_history", []):
            emp_type = job.get("employment_type", "full-time").lower()
            if emp_type not in valid_types:
                continue
                
            start_str = job.get("start_date")
            end_str = job.get("end_date")
            if not start_str:
                continue
                
            try:
                # Handle YYYY-MM or YYYY-MM-DD
                start_fmt = "%Y-%m-%d" if len(start_str) > 7 else "%Y-%m"
                start_date = datetime.strptime(start_str, start_fmt)
                
                if not end_str or end_str.lower() == "present":
                    end_date = datetime.now()
                else:
                    end_fmt = "%Y-%m-%d" if len(end_str) > 7 else "%Y-%m"
                    end_date = datetime.strptime(end_str, end_fmt)
                    
                days = (end_date - start_date).days
                if days > 0:
                    total_days += days
            except Exception as e:
                print(f"[Knowledge Distiller] Error parsing dates for YoE: {e}")
                
        return round(total_days / 365.25, 1)

    def get_master_identity(self) -> str:
        """
        Executes the One-Time Knowledge Distillation pipeline if the Master Identity doesn't exist.
        Otherwise, returns the cached Master Identity instantly.
        """
        if os.path.exists(MASTER_IDENTITY_PATH):
            kb_mtime = os.path.getmtime(KB_PATH) if os.path.exists(KB_PATH) else 0
            if os.path.getmtime(MASTER_IDENTITY_PATH) >= kb_mtime:
                print("[Knowledge Distiller] Master Identity Core found and up-to-date. Loading from cache (0 LLM calls).")
                with open(MASTER_IDENTITY_PATH, "r") as f:
                    return f.read()
            else:
                print("[Knowledge Distiller] KB was updated. Invalidating stale Master Identity.")
                
        print("[Knowledge Distiller] No Master Identity found. Initiating One-Time Distillation Loop...")
        full_text = self._load_all_user_data()
        chunks = self._chunk_text(full_text)
        
        print(f"[Knowledge Distiller] Size: {len(full_text)} chars. Splitting into {len(chunks)} chunks...")
        
        extracted_evidence = []
        
        # --- MAP: Extract holistic narrative per chunk ---
        for idx, chunk in enumerate(chunks):
            print(f"[Knowledge Distiller] Distilling Chunk {idx+1}/{len(chunks)}...")
            
            map_prompt = f"""You are an elite Knowledge Distiller.
Read the following Chunk of the User's Profile and extract their holistic narrative, leadership history, and all critical bullet points (technologies, metrics, achievements).
Ignore irrelevant noise. Output a dense summary.

User Profile Chunk:
{chunk}
"""
            # Use the extraction model (Qwen2.5) for fast structured fact mapping
            evidence = generate(map_prompt, use_case="extraction")
            extracted_evidence.append(evidence)
                
        # Aggregate all evidence
        master_identity = "\n\n".join(extracted_evidence)
        if not master_identity.strip():
            master_identity = "User profile is empty."
            
        print(f"[Knowledge Distiller] Distillation Complete. Writing 3000-token Core to disk.")
        
        os.makedirs(os.path.dirname(MASTER_IDENTITY_PATH), exist_ok=True)
        with open(MASTER_IDENTITY_PATH, "w") as f:
            f.write(master_identity)
            
        return master_identity

    def evaluate_job(self, master_identity: str, job_requirements: dict, dynamic_rubric: str, threshold: float, company_name: str = "Unknown") -> dict:
        """
        Runs the final A-F evaluation using the pre-compiled Master Identity.
        Executes exactly 1 LLM call.
        """
        print(f"[Knowledge Distiller] Executing Single-Call DeepSeek-R1 Hard Filter for {company_name}...")
        
        yoe = self._calculate_yoe()
        print(f"[Knowledge Distiller] Pre-calculated YoE: {yoe} years (excluding freelance/personal)")
        
        filter_prompt = dynamic_rubric.replace("{threshold}", str(threshold)) + f"""
Company Name: {company_name}
Job Requirements: {job_requirements}
Aggregated User Context (Master Identity): {master_identity}
Pre-Calculated Verified Experience: {yoe} years (Use this exact number for YoE requirements)"""
        
        filter_response = generate(filter_prompt, use_case="hard_filter")
        
        is_match = False
        parsed_data = {}
        try:
            cleaned = filter_response.split("<think>")[-1].split("</think>")[-1].strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
            data = json.loads(cleaned)
            is_match = data.get("match", False)
            parsed_data = data
        except Exception as e:
            print(f"[Knowledge Distiller Error] Failed to parse DeepSeek JSON: {e}")
            parsed_data = {"score": 0.0, "match": False, "rubric": {}}
            is_match = False
            
        parsed_data["match"] = is_match
        return parsed_data
