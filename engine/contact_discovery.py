import json
from engine.llm_provider import generate

def generate_contact_message(master_identity: str, job_requirements: dict) -> str:
    """
    Generates a personalized, 3-sentence cold email directed at the 
    Founders or Hiring Manager for the specific startup/job.
    """
    prompt = f"""You are an expert at B2B networking and cold outreach.
Read the candidate's Master Identity and the target Job Requirements.

Master Identity:
{master_identity}

Job Requirements:
{json.dumps(job_requirements)}

Draft a highly personalized, 3-sentence cold email for the founders or hiring manager.
The message should briefly state why the candidate is a perfect fit based on their past experience.
Do not use placeholders like [Hiring Manager Name] -- instead use "Hi there" or a similar natural greeting.

Output ONLY the email text. No quotes, no markdown, no preamble, and absolutely no "Subject:" lines.
"""
    
    print("[Contact Discovery] Drafting Cold Email...")
    response = generate(prompt, use_case="resume_tailoring").strip()
    
    # Strip quotes if they were added
    if response.startswith('"') and response.endswith('"'):
        response = response[1:-1]
        
    return response
