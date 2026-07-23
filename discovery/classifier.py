import json
from engine.llm_provider import generate
from engine.tailor import load_kb

def score_job(job: dict, mode: str = "free") -> dict:
    """
    Uses the LLM to analyze the job description and output a fit score (0-100) 
    and any scam flags.
    """
    kb = load_kb()
    kb_str = json.dumps(kb.get("personal", {})) + "\n" + json.dumps(kb.get("skills", {}))
    
    from engine.config import CLASSIFIER_PROMPT
    prompt = CLASSIFIER_PROMPT.format(kb_context=kb_str, jd_text=job['description'][:2000])
    try:
        raw_response = generate(prompt, use_case="job_scoring")
        raw_response = raw_response.strip()
        
        import re
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_response, re.DOTALL)
        if json_match:
            raw_response = json_match.group(1)
            
        parsed = json.loads(raw_response)
        
        # Ensure correct types
        job["fit_score"] = int(parsed.get("fit_score", 0))
        flags = parsed.get("scam_flags", [])
        job["scam_flags"] = ", ".join(flags) if flags else ""
        
    except Exception as e:
        print(f"Failed to score job {job['id']}: {e}")
        job["fit_score"] = 0
        job["scam_flags"] = "Error during LLM classification"
        
    return job
