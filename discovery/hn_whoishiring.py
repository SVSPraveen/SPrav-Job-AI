import requests
import re
import uuid
import sqlite3
from datetime import datetime
from engine.scope_enforcer import load_scope
from engine.email_extractor import get_best_email
from engine.llm_provider import generate
from engine.tailor import load_kb

DB_PATH = "jobs.db"
from discovery.scraper import load_targeting

HN_API_BASE = "https://hacker-news.firebaseio.com/v0"

def get_latest_who_is_hiring_post():
    # Fetch the user 'whoishiring' submissions
    try:
        res = requests.get(f"{HN_API_BASE}/user/whoishiring.json").json()
        for post_id in res.get("submitted", [])[:10]:
            post = requests.get(f"{HN_API_BASE}/item/{post_id}.json").json()
            if post and "Ask HN: Who is hiring?" in post.get("title", ""):
                return post
    except Exception as e:
        print(f"[HN Scanner] Error fetching whoishiring: {e}")
    return None

def run_hn_scanner() -> list:
    """
    Scrapes the monthly Hacker News 'Who is Hiring' thread.
    Parses comments for remote/India friendly roles, extracts emails, 
    and drafts cold emails for the Action Required queue.
    """
    scope = load_scope()
    roles = [r['keyword'].lower() for r in scope.get('roles', []) if r.get('preference') != 'exclude']
    
    print(f"[HN Scanner] Scanning 'Ask HN: Who is hiring?' for {roles}...")
    
    post = get_latest_who_is_hiring_post()
    if not post:
        print("[HN Scanner] No recent 'Who is hiring' post found.")
        return []

    created_ids = []
    kids = post.get("kids", [])[:20] # Scan top 20 comments for speed
    
    kb = load_kb()

    for comment_id in kids:
        try:
            comment = requests.get(f"{HN_API_BASE}/item/{comment_id}.json").json()
            if not comment or comment.get("deleted") or comment.get("dead"):
                continue
            
            text = comment.get("text", "").lower()
            
            # Check if post mentions remote or any target locations
            targeting = load_targeting()
            target_locs = [loc.lower() for loc in targeting.get("target_locations", ["remote"])]
            
            if "remote" in text or any(loc in text for loc in target_locs):
                role_match = any(r in text for r in roles) if roles else True
                if role_match:
                    email = get_best_email(comment.get("text", ""), comment.get("by", ""), "")
                    if email:
                        job_id = f"hn_{comment_id}"
                        company_hint = comment.get("text", "")[:30].split("|")[0].strip() or "HN Startup"
                        _log_hn_application(job_id, company_hint, "Startup Role", f"https://news.ycombinator.com/item?id={comment_id}", comment.get("text", ""), email, kb)
                        created_ids.append(job_id)
        except Exception as e:
            pass

    print(f"[HN Scanner] Found {len(created_ids)} matching roles on HN.")
    return created_ids

def _log_hn_application(job_id, company, title, url, post_text, email_to, kb):
    prompt = f"""Draft a 3-sentence cold email for {kb.get('personal', {}).get('name', 'Applicant')} to send to {email_to} at {company} for a role matching their profile based on this HN post: {post_text[:500]}"""
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
        job_id, title, company, url, post_text, 'Remote', 'hacker_news', 
        0.0, '', 'manual_review', now, f"## Direct Application Email Draft\n\n**To:** {email_to}\n\n---\n\n{email_draft}"
    ))
    conn.commit()
    conn.close()
