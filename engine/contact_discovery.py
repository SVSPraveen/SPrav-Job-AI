import json
from engine.llm_provider import generate

def generate_contact_message(master_identity: str, job_requirements: dict) -> str:
    """
    Generates a personalized, <=300 character LinkedIn connection request message
    directed at the Hiring Manager or Recruiter for the specific job.
    """
    prompt = f"""You are an expert at B2B networking and cold outreach.
Read the candidate's Master Identity and the target Job Requirements.

Master Identity:
{master_identity}

Job Requirements:
{json.dumps(job_requirements)}

Draft a highly personalized LinkedIn connection request message (maximum 300 characters, strict limit) for the hiring manager or recruiter.
The message should briefly state why the candidate is a perfect fit based on their past experience.
Do not use placeholders like [Hiring Manager Name] -- instead use "Hi there" or similar natural greetings.

Output ONLY the message text. No quotes, no markdown, no preamble.
"""
    
    print("[Contact Discovery] Drafting LinkedIn outreach message...")
    response = generate(prompt, use_case="extraction").strip()
    
    # Strip quotes if they were added
    if response.startswith('"') and response.endswith('"'):
        response = response[1:-1]
        
    return response[:300]
