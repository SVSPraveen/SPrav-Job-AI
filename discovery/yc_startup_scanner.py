import requests
from bs4 import BeautifulSoup
import uuid
import sqlite3
from datetime import datetime
from engine.scope_enforcer import load_scope
from engine.llm_provider import generate
from engine.tailor import load_kb

DB_PATH = "jobs.db"
YC_URL = "https://www.ycombinator.com/companies?isHiring=true&regions=Remote"

def run_yc_scanner() -> list:
    """
    Scrapes 'Work at a Startup' (Y Combinator) public directories.
    Filters for Remote jobs.
    Pushes to the Action Required queue with a tailored Cover Letter.
    """
    scope = load_scope()
    roles = [r['keyword'].lower() for r in scope.get('roles', []) if r.get('preference') != 'exclude']
    
    print(f"[YC Scanner] Scanning YC Companies for Remote roles matching {roles}...")
    
    created_ids = []
    kb = load_kb()

    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = requests.get(YC_URL, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # YC companies are listed in anchor tags with class '_company_...'
        company_links = soup.find_all('a', href=lambda href: href and href.startswith("/companies/"))
        
        # Deduplicate and limit to top 10 for performance
        seen = set()
        targets = []
        for a in company_links:
            href = "https://www.ycombinator.com" + a['href']
            if href not in seen:
                seen.add(href)
                name = a.text.strip().split('\n')[0]
                targets.append((name, href))
                if len(targets) >= 10:
                    break

        for company_name, url in targets:
            job_id = f"yc_{uuid.uuid4().hex[:8]}"
            # Since we just have the company profile, we draft a general cover letter for the roles
            desc = f"YC Startup hiring remotely. Profile: {url}"
            _log_to_db(job_id, f"Software Role at {company_name}", company_name, url, desc, "Remote", kb)
            created_ids.append(job_id)
            
    except Exception as e:
        print(f"[YC Scanner] Error fetching YC directory: {e}")
        
    print(f"[YC Scanner] Found {len(created_ids)} remote hiring startups on YC.")
    return created_ids

def _log_to_db(job_id, title, company, url, desc, loc, kb):
    prompt = f"Draft a short, punchy cold email (3 sentences) from {kb.get('personal', {}).get('name', 'Applicant')} to the founders of {company}, a YC startup, expressing interest in remote engineering roles."
    email_draft = generate(prompt, use_case="resume_tailoring")

    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    cursor.execute("""
        INSERT INTO jobs
            (id, title, company, url, description, location, source,
             fit_score, scam_flags, status, updated_at, strategy_report)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO NOTHING
    """, (
        job_id, title, company, url, desc, loc, 'ycombinator', 
        0.0, '', 'manual_review', now, f'## YC Application Strategy\n\n[Cold Email Draft]\n\n{email_draft}'
    ))
    conn.commit()
    conn.close()
