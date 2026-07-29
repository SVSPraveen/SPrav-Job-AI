import json
from engine.llm_provider import generate

def extract_star_stories(master_identity: str, job_requirements: dict, active_behavioral_gaps: list = None) -> list:
    """
    Generates 2-3 STAR (Situation, Task, Action, Result) interview stories
    based on the user's Master Identity and the specific job requirements.
    """
    gaps_instruction = ""
    if active_behavioral_gaps:
        gaps_list = ", ".join(active_behavioral_gaps)
        gaps_instruction = f"\n\nCRITICAL DIRECTIVE: The candidate has known behavioral gaps in: {gaps_list}. Ensure that at least one of the stories specifically targets these weaknesses and demonstrates competence in these areas."

    prompt = f"""You are an expert interview coach.
Read the candidate's Master Identity and the target Job Requirements.

Master Identity:
{master_identity}

Job Requirements:
{json.dumps(job_requirements)}{gaps_instruction}

Extract and formulate 2-3 highly relevant behavioral stories using the STAR method (Situation, Task, Action, Result) that the candidate can use in their interview. 
The stories must be based ONLY on the actual experiences listed in the Master Identity. Do not invent facts.

Format as a JSON array of objects:
[
    {{
        "theme": "e.g., Overcoming technical debt",
        "situation": "...",
        "task": "...",
        "action": "...",
        "result": "..."
    }}
]

Output ONLY the JSON array inside <think> tags. Wait, no, use <think> tags for reasoning, then output the JSON array.
"""
    
    print("[STAR Bank] Generating behavioral interview stories...")
    response = generate(prompt, use_case="extraction")
    
    stories = []
    try:
        cleaned = response.split("<think>")[-1].split("</think>")[-1].strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        stories = json.loads(cleaned)
        
        # Validation
        from engine.fact_checker import extract_metric_claims
        allowed_metrics = extract_metric_claims(master_identity)
        
        for story in stories:
            story_text = json.dumps(story)
            story_metrics = extract_metric_claims(story_text)
            invented = story_metrics - allowed_metrics
            if invented:
                print(f"[STAR Bank FactChecker] Invented metrics {invented} in story. Appending warning.")
                story["theme"] = f"[⚠️ WARNING: LLM hallucinated metric {invented} - verify before using] " + story.get("theme", "")
                
    except Exception as e:
        print(f"[STAR Bank Error] Failed to parse stories: {e}")
        
    return stories
