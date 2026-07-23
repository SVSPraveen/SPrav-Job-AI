"""
discovery/linkedin_scanner.py
==============================
LinkedIn HR/CEO Post Scanner Pipeline Orchestrator.

Calls the Node.js headless LinkedIn scraper, filters results through the
ghost detector, generates a personalized cold email per post, and sends it
via Gmail with the tailored resume PDF attached.

Each sent application is also logged to jobs.db so it appears in the dashboard.
"""

import os
import uuid
import json
import sqlite3
import subprocess
from datetime import datetime

from engine.llm_provider import generate
from engine.email_extractor import get_best_email
from engine.ghost_detector import detect_ghost_job
from tracking.gmail_tracker import send_email
from engine.tailor import load_kb

DB_PATH = "jobs.db"
SCANNER_JS = os.path.join("scraper_service", "linkedin_post_scanner.js")


def _log_linkedin_application(post: dict, email_sent_to: str, email_draft: str) -> str:
    """Saves the LinkedIn outreach as a job entry in the DB."""
    job_id = f"linkedin_{uuid.uuid4().hex[:10]}"
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()

    cursor.execute("""
        INSERT INTO jobs
            (id, title, company, url, description, location, source,
             fit_score, scam_flags, status, updated_at, strategy_report)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO NOTHING
    """, (
        job_id,
        f"LinkedIn Post — {post.get('poster_title', 'Unknown Role')}",
        post.get('company', 'Unknown'),
        post.get('post_url', ''),
        post.get('post_text', ''),
        'India',
        'linkedin_post',
        0.0,
        '',
        'applied',
        now,
        f"## LinkedIn Outreach Email\n\n**Sent to:** {email_sent_to}\n\n---\n\n{email_draft}"
    ))
    conn.commit()
    conn.close()
    return job_id


def _draft_cold_email(post: dict, kb: dict) -> tuple[str, str]:
    """
    Uses the LLM to draft a concise, personalized cold email for this LinkedIn post.
    Returns (subject, body).
    """
    personal = kb.get("personal", {})
    name = personal.get("name", "the applicant")
    role_hint = post.get('poster_title', 'a role')
    company = post.get('company', 'your company')
    poster = post.get('poster_name', 'there')

    prompt = f"""You are an elite job-application strategist.

Draft a short, highly personalized cold email for {name} to send to {poster} at {company},
responding to this LinkedIn hiring post:

"{post.get('post_text', '')}"

User Background:
{json.dumps(personal, indent=2)}

Requirements:
1. Subject line: direct and specific, mention the role if inferable.
2. Body: max 3 short paragraphs. No filler phrases like "I hope this finds you well."
3. Open with one concrete achievement that directly maps to their need.
4. End with a clear, single call to action.
5. Sign off with the user's name.
6. Output ONLY the email. Format:
SUBJECT: <subject line>
BODY:
<body text>
"""

    raw = generate(prompt, use_case="resume_tailoring")
    
    # Parse subject and body from the response
    subject = f"Re: {company} Opportunity — {name}"
    body = raw
    
    if "SUBJECT:" in raw:
        parts = raw.split("BODY:", 1)
        subject_line = parts[0].replace("SUBJECT:", "").strip()
        if subject_line:
            subject = subject_line
        body = parts[1].strip() if len(parts) > 1 else raw
    
    return subject, body


def _find_resume_pdf(company: str) -> str | None:
    """Find the most recently generated PDF for a given company."""
    resumes_dir = "resumes"
    if not os.path.exists(resumes_dir):
        return None
    
    candidates = [
        f for f in os.listdir(resumes_dir)
        if f.endswith('.pdf') and company.lower().split()[0] in f.lower()
    ]
    
    if not candidates:
        # Fall back to any available resume
        all_pdfs = [f for f in os.listdir(resumes_dir) if f.endswith('.pdf')]
        if all_pdfs:
            # Use the most recently modified one
            all_pdfs.sort(
                key=lambda f: os.path.getmtime(os.path.join(resumes_dir, f)),
                reverse=True
            )
            return os.path.join(resumes_dir, all_pdfs[0])
        return None
    
    return os.path.join(resumes_dir, candidates[0])


def run_linkedin_scanner() -> list:
    """
    Main entry point. Runs the Node.js LinkedIn scanner, processes each
    genuine hiring post, drafts + sends a personalized email, and logs
    the outreach to the database.

    Returns a list of job IDs created.
    """
    if not os.path.exists(SCANNER_JS):
        print("[LinkedIn Scanner] linkedin_post_scanner.js not found — skipping.")
        return []

    linkedin_email = os.getenv("LINKEDIN_EMAIL", "")
    if not linkedin_email:
        print("[LinkedIn Scanner] LINKEDIN_EMAIL not set in .env — skipping.")
        return []

    print("[LinkedIn Scanner] Running headless LinkedIn post scan...")
    try:
        result = subprocess.run(
            ["node", SCANNER_JS],
            capture_output=True,
            text=True,
            timeout=300,
            env={**os.environ}
        )
        output = result.stdout.strip()
        if not output:
            print("[LinkedIn Scanner] No output returned.")
            return []
        posts = json.loads(output)
        print(f"[LinkedIn Scanner] {len(posts)} genuine hiring post(s) found.")
    except Exception as e:
        print(f"[LinkedIn Scanner] Failed to run scanner: {e}")
        return []

    kb = load_kb()
    created_ids = []

    for post in posts:
        company = post.get('company', '')
        post_text = post.get('post_text', '')
        poster_name = post.get('poster_name', '')

        # Final ghost-detector check on the Python side
        is_ghost, reason = detect_ghost_job(post_text, 'India', company=company, title=post.get('poster_title', ''))
        if is_ghost:
            print(f"[LinkedIn Scanner] Skipping ghost/scam post from {company}: {reason}")
            continue

        # Resolve the best email to send to
        email_in_post = post.get('email')
        email_to = email_in_post or get_best_email(post_text, poster_name, company)

        if not email_to:
            print(f"[LinkedIn Scanner] No email found for {poster_name} @ {company} — routing to Human Apply Queue.")
            # Still log it so the user can manually follow up
            _log_linkedin_application(post, "Not found — manual follow-up needed", "No email found.")
            created_ids.append(f"linkedin_noemail_{company}")
            continue

        # Draft the personalized cold email
        subject, body = _draft_cold_email(post, kb)

        # Find a resume to attach
        resume_path = _find_resume_pdf(company)

        # Send via Gmail
        success = send_email(
            to=email_to,
            subject=subject,
            body_text=body,
            attachment_path=resume_path
        )

        status_note = "Sent via Gmail" if success else "Gmail send failed — check credentials"
        job_id = _log_linkedin_application(post, email_to, f"**Status:** {status_note}\n\n{body}")
        created_ids.append(job_id)

        print(f"[LinkedIn Scanner] {'✓' if success else '✗'} {poster_name} @ {company} → {email_to}")

    return created_ids
