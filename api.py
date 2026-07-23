from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Body, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import sqlite3
import os
import json
import subprocess
import PyPDF2
import re
from engine.llm_provider import generate
from engine.negotiator import generate_negotiation_script
from engine.upskill_oracle import get_upskill_directive
from engine.auth import (
    create_access_token, verify_token, get_user_credentials,
    has_any_account, create_user, authenticate_user,
    save_credential, get_credentials, get_all_credentials,
    get_user_id_from_token, save_copilot_message, get_copilot_history
)
from engine.intake import parse_resume, fetch_github, parse_linkedin_export, parse_portfolio, manual_entries
from engine.kb_merger import merge, resolve_conflicts, apply_detail_updates, kb_is_ready
from engine.config import (
    ATS_AUTO_APPLY_THRESHOLD,
    FIT_AUTO_APPLY_THRESHOLD,
    COMPANY_DAILY_CAP,
    AUTO_APPLY_CIRCUIT_BREAKER_N,
)
from discovery.db import get_daemon_state, set_daemon_state
from engine.scope_enforcer import load_scope, save_scope
import tempfile
import shutil

app = FastAPI()

if not os.path.exists("resumes"):
    os.makedirs("resumes")
app.mount("/resumes", StaticFiles(directory="resumes"), name="resumes")

# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "jobs.db"
KB_PATH = "knowledge_base/me.json"
CONFIG_PATH = "config.json"
BLACKLIST_PATH = "blacklist.txt"

class KBUpdate(BaseModel):
    kb_data: dict

class ConfigData(BaseModel):
    threshold: float = 4.0
    filter_prompt: str = ""
    resume_prompt: str = ""
    max_applications_per_day: int = 30
    target_salary: str = ""
    scoring_caps: list = []
    # Auto-apply gating thresholds (editable via System Config UI)
    ats_auto_apply_threshold: float = ATS_AUTO_APPLY_THRESHOLD
    fit_auto_apply_threshold: float = FIT_AUTO_APPLY_THRESHOLD
    company_daily_cap: int = COMPANY_DAILY_CAP
    auto_apply_circuit_breaker_n: int = AUTO_APPLY_CIRCUIT_BREAKER_N

def get_default_config():
    return {
        "threshold": 4.0,
        "filter_prompt": "You are a logical filter. Read the Job Requirements and User Context.\nRule: If Job YoE > User YoE, output strictly False. If User skills mismatch core requirements, output False. If {threshold}% match, output True.\nUse <think> tags to reason, then output a final JSON: {\"match\": true} or {\"match\": false}",
        "resume_prompt": "Write a highly dense, ATS-optimized 1-page resume tailored for the job. Do not invent any experience.",
        "max_applications_per_day": 30,
        "target_salary": "",
        "scoring_caps": [
            {
                "condition": "title contains 'Lead' or 'Principal'",
                "cap": 3.0
            }
        ],
        # Auto-apply gating — defaults from config.py / environment
        "ats_auto_apply_threshold": ATS_AUTO_APPLY_THRESHOLD,
        "fit_auto_apply_threshold": FIT_AUTO_APPLY_THRESHOLD,
        "company_daily_cap": COMPANY_DAILY_CAP,
        "auto_apply_circuit_breaker_n": AUTO_APPLY_CIRCUIT_BREAKER_N,
    }

class LoginData(BaseModel):
    email: str
    password: str

class SignupData(BaseModel):
    name: str
    email: str
    password: str

class CredentialData(BaseModel):
    service: str
    credentials: dict  # {key: value}

class CopilotQuery(BaseModel):
    message: str
    page_context: str = ""  # which page/tab the user is on

@app.get("/api/setup-check")
def setup_check():
    """Returns whether any account exists. Frontend uses this to show Signup vs Login."""
    return {"has_account": has_any_account()}

@app.post("/api/signup")
def signup(data: SignupData):
    """Creates the first (and only) user account on this machine."""
    if has_any_account():
        raise HTTPException(status_code=400, detail="An account already exists. Please log in.")
    user = create_user(data.name, data.email, data.password)
    token = create_access_token(user)
    return {"access_token": token, "token_type": "bearer", "name": user["name"]}

@app.post("/api/login")
def login(data: LoginData):
    user = authenticate_user(data.email, data.password)
    token = create_access_token(user)
    return {"access_token": token, "token_type": "bearer", "name": user["name"]}

@app.get("/api/credentials", dependencies=[Depends(verify_token)])
def get_creds(token_data: dict = Depends(verify_token)):
    """Returns all stored credentials for the logged-in user (masked for display)."""
    user_id = get_user_id_from_token(token_data)
    return get_all_credentials(user_id)

@app.post("/api/credentials", dependencies=[Depends(verify_token)])
def save_creds(data: CredentialData, token_data: dict = Depends(verify_token)):
    """Saves credentials for a service. Credentials are encrypted at rest."""
    user_id = get_user_id_from_token(token_data)
    for key, value in data.credentials.items():
        save_credential(user_id, data.service, key, value)
        # Also write to .env so the Node.js scrapers can read them
        if data.service == "linkedin":
            _write_env_var("LINKEDIN_EMAIL" if key == "email" else "LINKEDIN_PASSWORD", value)
    return {"status": "saved"}

@app.post("/api/copilot", dependencies=[Depends(verify_token)])
def copilot_chat(query: CopilotQuery, token_data: dict = Depends(verify_token)):
    """AI copilot endpoint. Answers questions about the app and guides the user."""
    user_id = get_user_id_from_token(token_data)
    history = get_copilot_history(user_id, limit=10)

    system_prompt = """You are SPrav Copilot, a friendly AI assistant built into the SPrav Job AI application.
You help the user understand how the app works, what to do next, and answer any questions about their job search.

App Overview:
- SPrav is a local AI job-hunting engine that discovers jobs from 9+ platforms (Naukri, Indeed, LinkedIn, Internshala, etc.)
- It scores each job for fit using DeepSeek-R1, tailors your resume, and auto-applies using Playwright.
- You can manage your watchlist (companies to monitor 24/7), see applied jobs, check the Human Apply Queue, and configure auto-apply thresholds.
- First-time setup: go to Settings to add your LinkedIn credentials and configure your job search keywords.
- The Knowledge Base (me.json) is your profile — the more you fill it in, the better the AI tailors your resume.

Current page context: {page_context}
Be concise, warm, and practical. If the user seems lost, proactively guide them to their next step.""".format(page_context=query.page_context or "dashboard")

    # Build conversation
    messages = [{"role": "system", "content": system_prompt}]
    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": query.message})

    try:
        # Use the local LLM for copilot responses
        full_prompt = system_prompt + "\n\nUser: " + query.message
        if history:
            context = "\n".join([f"{h['role'].title()}: {h['content']}" for h in history[-4:]])
            full_prompt = system_prompt + "\n\nRecent conversation:\n" + context + "\n\nUser: " + query.message
        reply = generate(full_prompt, use_case="extraction")
    except Exception as e:
        reply = f"I'm having trouble connecting to the local AI right now. ({e})"

    save_copilot_message(user_id, "user", query.message)
    save_copilot_message(user_id, "assistant", reply)
    return {"reply": reply}

def _write_env_var(key: str, value: str):
    """Updates a key=value line in the local .env file."""
    env_path = ".env"
    lines = []
    found = False
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}\n"
                found = True
                break
    if not found:
        lines.append(f"{key}={value}\n")
    with open(env_path, "w") as f:
        f.writelines(lines)

@app.get("/api/config", dependencies=[Depends(verify_token)])
def get_config():
    defaults = get_default_config()
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w") as f:
            json.dump(defaults, f, indent=4)
        return defaults
    with open(CONFIG_PATH, "r") as f:
        saved = json.load(f)
    # Merge: saved values override defaults but ensure all keys always exist
    merged = {**defaults, **saved}
    return merged

@app.post("/api/config")
def save_config(config: ConfigData):
    # Load existing to preserve keys not in the Pydantic model (like scoring_caps)
    existing = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            existing = json.load(f)
    updated = {**existing, **config.dict()}
    with open(CONFIG_PATH, "w") as f:
        json.dump(updated, f, indent=4)
    return {"status": "success"}

@app.get("/api/circuit-breaker/status", dependencies=[Depends(verify_token)])
def circuit_breaker_status():
    """Returns current circuit breaker state for the dashboard banner."""
    paused = get_daemon_state("auto_apply_paused", "false").lower() == "true"
    failures = int(get_daemon_state("cb_consecutive_failures", "0"))
    return {
        "paused": paused,
        "consecutive_failures": failures,
        "threshold": AUTO_APPLY_CIRCUIT_BREAKER_N,
    }

@app.post("/api/circuit-breaker/reset", dependencies=[Depends(verify_token)])
def circuit_breaker_reset():
    """Manually resets the circuit breaker after you've diagnosed and fixed the issue."""
    set_daemon_state("auto_apply_paused", "false")
    set_daemon_state("cb_consecutive_failures", "0")
    return {"status": "success", "message": "Circuit breaker reset. Auto-apply is now enabled."}

# ─────────────────────────────────────────────────────────────────────────────
# Application Scope endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/scope", dependencies=[Depends(verify_token)])
def get_scope():
    """Returns the current Application Scope configuration."""
    return load_scope()

@app.post("/api/scope", dependencies=[Depends(verify_token)])
def post_scope(scope: dict = Body(...)):
    """
    Saves a new Application Scope config. Takes effect immediately on the next
    discovery cycle — no daemon restart required.
    """
    save_scope(scope)
    return {"status": "success", "message": "Application Scope saved. Active on next discovery cycle."}

@app.get("/api/metrics", dependencies=[Depends(verify_token)])
def get_metrics():
    if not os.path.exists(DB_PATH):
        return {"total": 0, "applied": 0, "interviews": 0, "rejected": 0, "new": 0, "manual": 0}
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status")
    rows = dict(cursor.fetchall())
    conn.close()
    
    total = sum(rows.values())
    return {
        "total": total,
        "applied": rows.get("applied", 0),
        "interviews": rows.get("interviewing", 0),
        "rejected": rows.get("rejected", 0),
        "new": rows.get("new", 0),
        "manual": rows.get("manual_review", 0),
        "pending_approval": rows.get("pending_cover_letter", 0)
    }

@app.get("/api/jobs", dependencies=[Depends(verify_token)])
def get_jobs():
    if not os.path.exists(DB_PATH):
        return []
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, company, fit_score, status, scam_flags, location, url, missing_skills, matched_skills FROM jobs ORDER BY fit_score DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(ix) for ix in rows]

@app.get("/api/jobs/manual")
def get_manual_jobs():
    if not os.path.exists(DB_PATH):
        return []
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # Include both manual_review and pending_cover_letter so the Cover Letter Gate is visible in UI
    cursor.execute("SELECT id, title, company, fit_score, status, scam_flags, location, url, missing_skills, matched_skills, strategy_report FROM jobs WHERE status IN ('manual_review', 'pending_cover_letter')")
    rows = cursor.fetchall()
    conn.close()
    return [dict(ix) for ix in rows]

@app.post("/api/jobs/{job_id}/apply")
def mark_job_applied(job_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE jobs SET status = 'applied' WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}

# ─── Watchlist Endpoints ──────────────────────────────────────────────────────

WATCHLIST_PATH = "watchlist.json"
SNAPSHOTS_DIR = os.path.join("scraper_service", "snapshots")

def _load_watchlist() -> dict:
    if not os.path.exists(WATCHLIST_PATH):
        return {"companies": []}
    with open(WATCHLIST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_watchlist(data: dict):
    with open(WATCHLIST_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@app.get("/api/watchlist", dependencies=[Depends(verify_token)])
def get_watchlist():
    wl = _load_watchlist()
    # Augment with snapshot metadata for the UI
    companies = wl.get("companies", [])
    for company in companies:
        slug = company["name"].lower().replace(" ", "_").replace(r"[^a-z0-9_]", "")
        snap_path = os.path.join(SNAPSHOTS_DIR, f"{slug}.json")
        if os.path.exists(snap_path):
            with open(snap_path, "r", encoding="utf-8") as sf:
                snap = json.load(sf)
            company["last_checked"] = snap.get("updated_at", "Never")
            company["job_count"] = len(snap.get("jobs", []))
        else:
            company["last_checked"] = "Never"
            company["job_count"] = 0
    return companies

@app.post("/api/watchlist", dependencies=[Depends(verify_token)])
def update_watchlist(payload: dict = Body(...)):
    """Replace the entire companies list or add/remove a single entry."""
    action = payload.get("action", "replace")
    wl = _load_watchlist()

    if action == "replace":
        wl["companies"] = payload.get("companies", [])
    elif action == "add":
        entry = payload.get("company")
        if entry and not any(c["name"] == entry["name"] for c in wl["companies"]):
            wl["companies"].append(entry)
    elif action == "remove":
        name = payload.get("name", "")
        wl["companies"] = [c for c in wl["companies"] if c["name"] != name]
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'replace', 'add', or 'remove'.")

    _save_watchlist(wl)
    return {"status": "ok", "count": len(wl["companies"])}


def is_blacklisted(company: str) -> bool:
    if not os.path.exists(BLACKLIST_PATH):
        return False
    with open(BLACKLIST_PATH, "r", encoding="utf-8") as f:
        blacklisted_companies = [line.strip().lower() for line in f.readlines() if line.strip()]
    return company.strip().lower() in blacklisted_companies

def is_repost(company: str, title: str) -> bool:
    if not company or not title:
        return False
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Find any job with the exact same company and title
    c.execute("SELECT id FROM jobs WHERE company = ? AND title = ? LIMIT 1", (company, title))
    result = c.fetchone()
    conn.close()
    return bool(result)


@app.post("/api/jobs")
async def add_job(job: dict):
    if is_blacklisted(job.get('company', '')):
        return {"status": "skipped_blacklisted"}
    if is_repost(job.get('company', ''), job.get('title', '')):
        return {"status": "skipped_repost"}
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO jobs (id, title, company, url, description, location, source, fit_score, scam_flags, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (job['id'], job['title'], job['company'], job['url'], job['description'], job.get('location', ''), job.get('source', 'Unknown'), 0, "", "new"))
    conn.commit()
    return {"status": "ok"}

@app.post("/api/jobs/bulk")
async def add_jobs_bulk(jobs: list = Body(...)):
    """Endpoint for Node.js Microservice to inject scraped jobs."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    inserted = 0
    for job in jobs:
        if is_blacklisted(job.get('company', '')):
            continue
        if is_repost(job.get('company', ''), job.get('title', '')):
            continue
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO jobs (id, title, company, url, description, location, source, fit_score, scam_flags, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (job['id'], job['title'], job['company'], job['url'], job['description'], job.get('location', ''), job.get('source', 'Unknown'), 0, "", "new"))
            if cursor.rowcount > 0:
                inserted += 1
        except Exception as e:
            print(f"Failed to insert job {job.get('id')}: {e}")
            
    conn.commit()
    conn.close()
    return {"status": "ok", "inserted": inserted}

@app.get("/api/kb")
def get_kb():
    if os.path.exists(KB_PATH):
        with open(KB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"personal": {}, "work_history": [], "resume_bullets": [], "skills": {}}

@app.post("/api/kb")
def update_kb(data: KBUpdate):
    os.makedirs(os.path.dirname(KB_PATH), exist_ok=True)
    with open(KB_PATH, "w", encoding="utf-8") as f:
        json.dump(data.kb_data, f, indent=2)
    return {"status": "success"}

@app.post("/api/kb/extract_pdf")
async def extract_pdf(file: UploadFile = File(...)):
    reader = PyPDF2.PdfReader(file.file)
    text = "".join([page.extract_text() + "\n" for page in reader.pages])
    prompt = f"Parse this resume into JSON strictly matching our comprehensive schema: {{'work_history': [], 'education': [], 'projects': [], 'certifications': [], 'hobbies': '', 'resume_bullets': [], 'skills': {{}}}}\n\nText:\n{text}"
    try:
        response = generate(prompt, use_case="pdf_extraction").strip()
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
        if json_match: response = json_match.group(1)
        parsed_data = json.loads(response)
        return parsed_data
    except Exception as e:
        return {"error": str(e)}

def run_script(args):
    subprocess.Popen(["python", "main.py"] + args)

@app.post("/api/action/discover", dependencies=[Depends(verify_token)])
def trigger_discover():
    run_script(["--discover"])
    return {"status": "started"}

@app.post("/api/action/apply")
def trigger_apply():
    run_script(["--apply"])
    return {"status": "started"}

@app.post("/api/action/track")
def trigger_track():
    run_script(["--track"])
    return {"status": "started"}

class NegotiateRequest(BaseModel):
    company: str
    role: str
    offer_salary: str
    target_salary: str
    competing: str
    discount: str

@app.post("/api/action/negotiate")
def trigger_negotiate(req: NegotiateRequest):
    draft = generate_negotiation_script(req.company, req.role, req.offer_salary, req.target_salary, req.competing, req.discount)
    return {"status": "success", "draft": draft}

@app.get("/api/action/upskill")
def trigger_upskill():
    directive = get_upskill_directive()
    return {"status": "success", "directive": directive}

@app.post("/api/jobs/{job_id}/approve-cover")
async def approve_cover_letter(job_id: str):
    """
    Approves the cover letter draft and marks the job ready for final dispatch.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE jobs SET status = 'approved_for_dispatch' WHERE id = ?", (job_id,))
        conn.commit()
        conn.close()
        return {"status": "success", "message": f"Cover letter approved for job {job_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class InviteMatchRequest(BaseModel):
    email_text: str

@app.post("/api/invites/match")
def match_invite_email(req: InviteMatchRequest):
    """Fuzzy-match an interview invite email against the jobs database."""
    try:
        from invite_matcher import match_invite
        result = match_invite(req.email_text)
        return {"status": "success", "match": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/friction")
async def get_friction_analytics():
    """Returns the ghost/rejection rates for all applied companies."""
    try:
        from engine.friction_tracker import get_all_friction_rates
        rates = get_all_friction_rates()
        return {"status": "success", "data": rates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/salary-gaps")
def get_salary_gap_analytics():
    """Returns salary gap analysis between target salary and estimated offers."""
    try:
        from engine.salary_analyzer import get_salary_gaps
        result = get_salary_gaps()
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─────────────────────────────────────────────────────────────────────────────
# Phase 0: Intake & Onboarding Endpoints
# ─────────────────────────────────────────────────────────────────────────────

class GithubRequest(BaseModel):
    username: str = None       # a GitHub username — fetches all public repos
    repo_urls: list[str] = []  # OR: specific repo URLs to fetch
    token: str = None

class PortfolioRequest(BaseModel):
    url: str

class MergeRequest(BaseModel):
    sources: list[dict]

class ResolveRequest(BaseModel):
    resolutions: list[dict] = []
    detail_updates: list[dict] = []

@app.post("/api/intake/resume", dependencies=[Depends(verify_token)])
async def api_intake_resume(file: UploadFile = File(...)):
    ext = ".pdf" if file.filename.lower().endswith(".pdf") else ".docx"
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    try:
        result = parse_resume(tmp_path)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.remove(tmp_path)

@app.post("/api/intake/github", dependencies=[Depends(verify_token)])
def api_intake_github(req: GithubRequest):
    try:
        # Accept either a username OR a list of specific repo URLs
        if req.repo_urls:
            source = fetch_github(req.repo_urls, github_token=req.token)
        elif req.username:
            source = fetch_github(req.username, github_token=req.token)
        else:
            raise HTTPException(status_code=422, detail="Provide either 'username' or 'repo_urls'")
        return {"status": "success", "data": source}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/intake/linkedin", dependencies=[Depends(verify_token)])
async def api_intake_linkedin(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    try:
        result = parse_linkedin_export(tmp_path)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.remove(tmp_path)

@app.post("/api/intake/portfolio", dependencies=[Depends(verify_token)])
def api_intake_portfolio(req: PortfolioRequest):
    try:
        result = parse_portfolio(req.url)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/intake/manual", dependencies=[Depends(verify_token)])
def api_intake_manual(req: dict = Body(...)):
    try:
        result = manual_entries(req)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/intake/merge", dependencies=[Depends(verify_token)])
def api_intake_merge(req: MergeRequest):
    try:
        merged = merge(req.sources)
        return {
            "status": "success",
            "needs_detail": merged.get("needs_detail", []),
            "pending_conflicts": merged.get("pending_conflicts", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/intake/resolve", dependencies=[Depends(verify_token)])
def api_intake_resolve(req: ResolveRequest):
    try:
        if req.resolutions:
            resolve_conflicts(req.resolutions)
        if req.detail_updates:
            apply_detail_updates(req.detail_updates)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/intake/status", dependencies=[Depends(verify_token)])
def api_intake_status():
    return {"status": "success", "is_ready": kb_is_ready()}
