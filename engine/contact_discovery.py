import json
import os
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
from engine.llm_provider import generate
from engine.utils import get_data_dir

def _get_github_pat() -> str:
    from engine.auth import get_system_credential
    return get_system_credential("github", "token") or ""

def _infer_email_pattern(first: str, last: str, known_email: str) -> str:
    """
    Given a known employee's name and email, infers the pattern.
    E.g. (John, Doe, john.doe@company.com) -> '{first}.{last}@{domain}'
    """
    first = first.lower()
    last = last.lower()
    known_email = known_email.lower()
    
    if "@" not in known_email:
        return ""
        
    username, domain = known_email.split("@", 1)
    
    # Check common patterns
    if username == f"{first}.{last}":
        return f"{{first}}.{{last}}@{domain}"
    elif username == f"{first}{last}":
        return f"{{first}}{{last}}@{domain}"
    elif username == f"{first[0]}{last}":
        return f"{{f}}{{last}}@{domain}"
    elif username == f"{first}_{last}":
        return f"{{first}}_{{last}}@{domain}"
    elif username == first:
        return f"{{first}}@{domain}"
    
    return ""

def _generate_email(first: str, last: str, pattern: str) -> str:
    if not pattern: return ""
    return pattern.format(
        first=first.lower(),
        last=last.lower(),
        f=first[0].lower() if first else ""
    )

def fetch_github_org_members(company_name: str) -> list[dict]:
    """Uses GitHub Search API to find users working at the company."""
    pat = _get_github_pat()
    headers = {"Accept": "application/vnd.github.v3+json"}
    if pat:
        headers["Authorization"] = f"token {pat}"
        
    # Search for users where company:company_name
    safe_company = urllib.parse.quote(f"company:{company_name}")
    url = f"https://api.github.com/search/users?q={safe_company}&per_page=10"
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return []
            
        data = resp.json()
        users = []
        for item in data.get("items", []):
            # We need to fetch the full user profile to get the name and email
            user_resp = requests.get(item["url"], headers=headers, timeout=5)
            if user_resp.status_code == 200:
                u = user_resp.json()
                if u.get("name"):
                    users.append({
                        "name": u.get("name"),
                        "title": "Software Engineer (Inferred via GitHub)",
                        "email": u.get("email"),
                        "source": "GitHub",
                        "tier": "employee" # hard to infer if HM from github alone
                    })
        return users
    except Exception as e:
        print(f"[Contact Discovery] GitHub fetch error: {e}")
        return []

def scrape_about_team_page(company_url: str) -> list[dict]:
    """Scrapes /about or /team for basic names."""
    if not company_url: return []
    
    # Make sure it has http
    if not company_url.startswith("http"):
        company_url = "https://" + company_url
        
    base = company_url.rstrip('/')
    urls_to_try = [f"{base}/about", f"{base}/team", f"{base}/about-us", base]
    
    contacts = []
    
    for url in urls_to_try:
        try:
            resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                # Look for typical team member structures (this is heuristic)
                # LLM can extract this better from text dump
                text = soup.get_text(separator="\n", strip=True)
                
                # We use a tiny fast LLM prompt to extract names/titles from the text dump
                # Limit text to first 5000 chars to avoid blowing context
                text = text[:5000]
                
                prompt = f"""Extract a JSON list of team members (name, title) from this About page text.
If none found, return [].
Output EXACT JSON array format: [{{"name": "...", "title": "..."}}]

Text:
{text}
"""
                result = generate(prompt, use_case="extraction")
                match = re.search(r"\[.*\]", result, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                    for p in parsed:
                        if p.get("name") and p.get("title"):
                            contacts.append({
                                "name": p["name"],
                                "title": p["title"],
                                "email": None,
                                "source": "Company Website",
                                "tier": "hiring_manager" if any(x in p["title"].lower() for x in ["director", "head", "vp", "manager", "lead", "founder", "cto"]) else "employee"
                            })
                if contacts:
                    break # if we found contacts on one of the URLs, stop trying
        except Exception:
            pass
            
    return contacts

def generate_linkedin_search_url(company: str, role: str, college: str = "") -> str:
    """Generates a pre-filled LinkedIn people search URL."""
    # If a college is provided, prioritize alumni: "[College]" "[Company]" [Role]
    if college:
        query = f'"{college}" "{company}" {role}'.strip()
    else:
        query = f"{company} {role}".strip()
    encoded = urllib.parse.quote(query)
    return f"https://www.linkedin.com/search/results/people/?keywords={encoded}"

def run_discovery_pipeline(company: str, company_url: str = "", job_title: str = "") -> dict:
    """
    Master pipeline for finding contacts at a company.
    """
    print(f"\n[Contact Discovery] Sourcing contacts for {company}...")
    
    # 0. Load user's college for LinkedIn search prioritization
    college = ""
    try:
        me_path = os.path.join(get_data_dir(), "knowledge_base", "me.json")
        if os.path.exists(me_path):
            with open(me_path, "r", encoding="utf-8") as f:
                kb = json.load(f)
                edus = kb.get("education", [])
                if edus and isinstance(edus, list) and edus[0].get("institution"):
                    college = edus[0].get("institution")
    except Exception as e:
        print(f"[Contact Discovery] Failed to load education for LinkedIn search: {e}")
    
    contacts = []
    
    # 1. GitHub Org search
    gh_contacts = fetch_github_org_members(company)
    contacts.extend(gh_contacts)
    
    # 2. Company About/Team Page
    web_contacts = scrape_about_team_page(company_url)
    contacts.extend(web_contacts)
    
    # 3. Email Pattern Inference
    known_email = None
    known_first = None
    known_last = None
    
    for c in contacts:
        if c.get("email") and " " in c.get("name", ""):
            parts = c["name"].split()
            known_first = parts[0]
            known_last = parts[-1]
            known_email = c["email"]
            break
            
    if known_email:
        pattern = _infer_email_pattern(known_first, known_last, known_email)
        if pattern:
            print(f"[Contact Discovery] Inferred email pattern: {pattern}")
            for c in contacts:
                if not c.get("email") and " " in c.get("name", ""):
                    parts = c["name"].split()
                    c["email"] = _generate_email(parts[0], parts[-1], pattern)
    
    # 4. Rank & Tier (Hiring managers first)
    def tier_score(c):
        t = c.get("title", "").lower()
        if "founder" in t or "cto" in t or "ceo" in t: return 3
        if "director" in t or "vp" in t or "head" in t: return 2
        if "manager" in t or "lead" in t: return 1
        return 0
        
    for c in contacts:
        c["score"] = tier_score(c)
        
    contacts.sort(key=lambda x: x["score"], reverse=True)
    
    # Limit to top 3
    top_contacts = contacts[:3]
    
    return {
        "contacts": top_contacts,
        "linkedin_search_url": generate_linkedin_search_url(company, job_title, college),
        "warm_path": len(contacts) > 0
    }

def generate_contact_message(master_identity: str, job_requirements: dict, contact_name: str = "", contact_title: str = "", intent: str = "referral") -> str:
    """
    Generates a personalized cold email/InMail draft.
    intent can be 'referral' or 'informational'.
    """
    if intent == "agency_outreach":
        agency_name = job_requirements.get("Target Company/Agency", "the agency")
        prompt = f"""You are an expert at B2B networking and cold outreach.
Read the candidate's Master Identity.

Master Identity:
{master_identity}

You are reaching out to {agency_name}, a staffing/recruiting agency that places candidates across many different companies and roles — it is not itself the employer. Do not assume anything about what the agency's business does.

Contact Name: {contact_name or "there"}
Contact Title: {contact_title or "Tech Recruiter"}

Draft a highly personalized cold note. You must follow this exact sentence structure:
1. Open immediately by asking if they are currently recruiting for roles matching your background, and offer to share your resume or have a quick call.
2. Only after making the ask, state your name and briefly highlight your technical background as supporting context.

Write entirely in first person, as the candidate speaking. Never write as if the agency or recruiter is the one reaching out to the candidate.

Do not use email conventions — no greeting line like 'Hi [title] at [company]', and no sign-off like 'Best, [name]'. 
Do NOT use placeholders like [Your Name]. Use the actual name from Master Identity.
Output ONLY the message text. No quotes, no markdown, no preamble, and no "Subject:" lines.

Maximum 200 characters. Count strictly. If your draft exceeds 200 characters, shorten it before responding.
"""
    else:
        prompt = f"""You are an expert at B2B networking and cold outreach.
Read the candidate's Master Identity and the target Job Requirements.

Master Identity:
{master_identity}

Job Requirements:
{json.dumps(job_requirements)}

Contact Name: {contact_name or "there"}
Contact Title: {contact_title or "Team Member"}

Draft a highly personalized, 3-sentence cold note.
If intent is 'referral': ask if they would be open to referring you for the role, citing 1 specific overlap between your background and the requirements.
If intent is 'informational': ask for a brief 10-15 minute chat to hear about their experience at the company, without directly asking for a job yet.

Intent: {intent}

Do NOT use placeholders like [Your Name]. Use the actual name from Master Identity.
Output ONLY the message text. No quotes, no markdown, no preamble, and no "Subject:" lines.
"""
    
    print(f"[Contact Discovery] Drafting '{intent}' note for {contact_name or 'contact'}...")
    response = generate(prompt, use_case="general").strip()
    
    if response.startswith('"') and response.endswith('"'):
        response = response[1:-1]
        
    return response
