import re
from engine.llm_provider import generate

def classify_archetype(job_title: str, requirements: str) -> str:
    """
    Classifies a job into a strict Archetype to determine its scoring rubric.
    Uses a fast, low-temp extraction call.
    """
    prompt = f"""Analyze the Job Title and Requirements and classify the role into EXACTLY ONE of these archetypes:
- Backend
- Frontend
- DevOps
- Data/ML
- Product
- General (if none apply)

Job Title: {job_title}
Requirements: {requirements}

Output ONLY the Archetype name (e.g. "DevOps"). Do not output any other text."""

    archetype_raw = generate(prompt, use_case="extraction").strip()
    
    # Clean output just in case
    archetype_raw = archetype_raw.lower()
    if "devops" in archetype_raw or "llmops" in archetype_raw:
        return "DevOps"
    elif "frontend" in archetype_raw or "ui" in archetype_raw or "ux" in archetype_raw:
        return "Frontend"
    elif "data" in archetype_raw or "ml" in archetype_raw or "machine learning" in archetype_raw or "ai" in archetype_raw:
        return "Data/ML"
    elif "product" in archetype_raw or "manager" in archetype_raw:
        return "Product"
    elif "backend" in archetype_raw:
        return "Backend"
    else:
        return "General"

def get_rubric_for_archetype(archetype: str, threshold: float, scoring_caps: list = None) -> str:
    """
    Returns the specific DeepSeek scoring rubric for the given archetype.
    """
    if scoring_caps is None:
        scoring_caps = []
        
    rubrics = {
        "DevOps": f"ARCHETYPE: DevOps/Infrastructure.\nSPECIAL FOCUS: Penalize lack of Kubernetes, Docker, CI/CD pipelines, or cloud (AWS/GCP) experience.",
        "Frontend": f"ARCHETYPE: Frontend/UI.\nSPECIAL FOCUS: Penalize lack of React, Vue, CSS architecture, or State Management.",
        "Data/ML": f"ARCHETYPE: Data/Machine Learning.\nSPECIAL FOCUS: Penalize lack of Python, PyTorch/TensorFlow, SQL, or data pipelines.",
        "Backend": f"ARCHETYPE: Backend Systems.\nSPECIAL FOCUS: Penalize lack of API design, DB scaling, Postgres/SQL, or caching (Redis).",
        "Product": f"ARCHETYPE: Product Management.\nSPECIAL FOCUS: Penalize lack of Agile, Stakeholder Management, PRDs, or cross-functional leadership.",
        "General": f"ARCHETYPE: General Software Engineering.\nSPECIAL FOCUS: Evaluate general software lifecycle and problem-solving skills."
    }
    
    base_prompt = """You are an elite Tech Recruiter evaluating a candidate against a job description.
Read the Job Requirements and the User Context (Master Identity).

Evaluate the candidate on the following 5 dimensions using an A-F grading scale (A=5, B=4, C=3, D=2, F=1):
1. Role Fit: Do they have the core technical skills and tools required?
2. Level Match: Do their Years of Experience (YoE) and scope of past roles align with the job's seniority? (F if Job YoE > User YoE).
3. Value/Comp: Does the candidate's track record show high-impact results justifying a premium salary?
4. Culture: Does their background show evidence of soft skills, leadership, or autonomy matching the role?
5. Personalization: Does the candidate possess a unique angle or domain expertise that makes them stand out?

Additionally, you must output a Block C for Level & Positioning Strategy:
1. Identify if the role is a downlevel, uplevel, or lateral move based on the user's YoE and the JD.
2. Provide a 1-sentence strategy on how to sell their seniority without sounding overqualified (if downlevel) or underqualified (if uplevel).
3. Provide a 1-sentence response strategy if the company tries to downlevel the candidate during the interview.

Additionally, you must output a Block D for Compensation Intelligence:
1. Classify the Company Type (Public Big Tech, VC Startup, Enterprise, SMB, Agency, Unknown).
2. Estimate the Compensation Reliability (High, Medium, Low, Unknown).
3. Estimate Expected Stable Cash if not stated.

"""
    caps_prompt = ""
    if scoring_caps:
        caps_prompt = "\nUSER-DEFINED SCORING CAPS (CRITICAL):\n"
        for cap in scoring_caps:
            caps_prompt += f"- If {cap.get('condition', '')}, then cap the final holistic score at {cap.get('cap', 5.0)}/5.0 max.\n"

    rubric = rubrics.get(archetype, rubrics["General"])
    end_prompt = f"""
{caps_prompt}
Calculate the final holistic score as a float from 1.0 to 5.0 (average of the 5 grades).
If the final score is >= {threshold}, set "match" to true, else false.

Use <think> tags to reason, then output a final JSON strictly matching this schema:
{{
  "rubric": {{
    "role_fit": "A|B|C|D|F",
    "level_match": "A|B|C|D|F",
    "value": "A|B|C|D|F",
    "culture": "A|B|C|D|F",
    "personalization": "A|B|C|D|F"
  }},
  "block_c": {{
    "level_delta": "Downlevel|Lateral|Uplevel",
    "positioning_strategy": "...",
    "downlevel_response": "..."
  }},
  "block_d": {{
    "company_type": "...",
    "comp_reliability": "...",
    "expected_stable_cash": "..."
  }},
  "score": 4.2,
  "match": true|false
}}"""
    
    return base_prompt + rubric + end_prompt
