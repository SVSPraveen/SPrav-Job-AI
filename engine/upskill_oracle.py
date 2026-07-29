import os
import json
import chromadb
from engine.llm_provider import generate

CHROMA_PATH = "sprav_memory"

def get_upskill_directive() -> str:
    if not os.path.exists(CHROMA_PATH):
        return "Memory Palace is empty. Get rejected from some jobs first before I can help you."
        
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(name="lessons_engineering")
    
    if collection.count() == 0:
        return "Memory Palace is empty. No lessons learned yet."
        
    results = collection.get()
    metadatas = results.get("metadatas", [])
    
    all_lessons = [meta.get("lesson", "") for meta in metadatas if "lesson" in meta]
    
    if not all_lessons:
        return "No actionable lessons found."
        
    lessons_text = "\n".join([f"- {l}" for l in all_lessons])
    
    from engine.conversion_stats import get_conversion_stats
    try:
        stats = get_conversion_stats()
        stats_text = json.dumps(stats.get("by_skill", {}), indent=2)
    except Exception:
        stats_text = "No structured conversion data available yet."

    prompt = f"""You are the Upskill Oracle, a brutal and hyper-analytical career coach.
You are reviewing the exact reasons why this candidate was rejected from their recent job applications, alongside their exact conversion rates per skill keyword.

REJECTION LESSONS (From Memory Palace):
{lessons_text}

EXACT SKILL CONVERSION STATS (Ghost/Reject/Interview rates per keyword):
{stats_text}

Analyze the patterns across all of these rejections and the conversion data.
Identify the specific gaps causing the candidate to lose jobs.

Output EXACTLY a JSON array of objects. Do not include markdown formatting or any other text.
Each object must have:
- "gap_name": (string) The specific skill or area (e.g. "System Design", "Docker", "Behavioral").
- "category": (string) MUST BE exactly one of: "tech_skill", "dsa_coding_round", "aptitude_test", "interview_behavioral".
- "reason": (string) A brutal, data-driven reason drawn from the stats/lessons (e.g., "3 of 5 apps requiring X ghosted").

If there are no actionable gaps, return an empty array: []
"""
    return generate(prompt, use_case="extraction")

def run_upskill_oracle():
    """
    Scans every single rejection lesson in the ChromaDB Memory Palace,
    analyzes the patterns, and outputs specific directives.
    Persists these to prep_gaps.json.
    """
    print("\n[Upskill Oracle] Waking up. Scanning Memory Palace for rejection patterns...")
    directive_json = get_upskill_directive()
    
    try:
        import re
        match = re.search(r"\[.*\]", directive_json, re.DOTALL)
        if match:
            directive_json = match.group(0)
        new_gaps = json.loads(directive_json)
    except Exception as e:
        print(f"[Upskill Oracle] Failed to parse Oracle JSON: {e}")
        return

    from engine.utils import get_data_dir
    import uuid
    import time
    
    prep_file = os.path.join(get_data_dir(), "prep_gaps.json")
    existing_gaps = []
    if os.path.exists(prep_file):
        with open(prep_file, "r", encoding="utf-8") as f:
            existing_gaps = json.load(f)
            
    # Merge new gaps
    for ng in new_gaps:
        # Check if a gap with same name/category already exists
        exists = any(eg.get("gap_name", "").lower() == ng.get("gap_name", "").lower() for eg in existing_gaps)
        if not exists:
            ng["id"] = f"gap_{uuid.uuid4().hex[:8]}"
            ng["prep_status"] = "not_started"
            ng["detected_at"] = time.time()
            existing_gaps.append(ng)
            
    with open(prep_file, "w", encoding="utf-8") as f:
        json.dump(existing_gaps, f, indent=2)
        
    print(f"\n================== THE ORACLE HAS SPOKEN ==================")
    print(f"Detected {len(new_gaps)} actionable gaps. Prep Center updated.")
    print("===========================================================\n")

if __name__ == "__main__":
    run_upskill_oracle()
