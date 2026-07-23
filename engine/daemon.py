import os
import sqlite3
import time
import random
import subprocess
from datetime import datetime
import json
import re
import hashlib
import concurrent.futures
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, END

from engine.db_utils import db_mutex
from engine.llm_provider import generate
from engine.html_compiler import render_html_to_pdf
from engine.tailor import tailor_resume, load_kb
from engine.html_formatter import generate_html_context
from engine.brain import brain # SPrav ChromaDB Context
from engine.evaluator import KnowledgeDistiller
from engine.skill_analyzer import analyze_skill_gap
from engine.fact_checker import verify_resume_facts
from engine.strategy_generator import generate_strategy_report, generate_application_email
from engine.ghost_detector import detect_ghost_job
from engine.memory_palace import get_relevant_lessons
from engine.knowledge_graph import add_triple
from engine.compaction_daemon import run_compaction
from engine.liveness_verifier import verify_job_liveness
from engine.archetype_classifier import classify_archetype, get_rubric_for_archetype
from scraper_service.ats_direct import run_ats_discovery
from apply.greenhouse import apply_to_greenhouse
from apply.lever import apply_to_lever
from apply.naukri import extract_real_apply_url, touch_naukri_profile
from tracking.notifier import send_email_notification
from discovery.linkedin_scanner import run_linkedin_scanner
from engine.config import (
    ATS_AUTO_APPLY_THRESHOLD,
    FIT_AUTO_APPLY_THRESHOLD,
    COMPANY_DAILY_CAP,
    AUTO_APPLY_CIRCUIT_BREAKER_N,
)
from discovery.db import (
    get_company_applies_today,
    has_been_applied_to,
    log_auto_apply_attempt,
    get_daemon_state,
    set_daemon_state,
)
from engine.scope_enforcer import load_scope, check_scope

DB_PATH = "jobs.db"
CONFIG_PATH = "config.json"

def get_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {
        "threshold": 4.0,
        "filter_prompt": "You are a logical filter. Read the Job Requirements and User Context.\nRule: If Job YoE > User YoE, output strictly False. If User skills mismatch core requirements, output False. If {threshold}% match, output True.\nUse <think> tags to reason, then output a final JSON: {\"match\": true} or {\"match\": false}",
        "resume_prompt": "Write a highly dense, ATS-optimized 1-page resume tailored for the job. Do not invent any experience."
    }

def update_job_status(job_id: str, status: str):
    with db_mutex:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now_str = datetime.utcnow().isoformat()
        cursor.execute("UPDATE jobs SET status = ?, updated_at = ? WHERE id = ?", (status, now_str, job_id))
        conn.commit()
        conn.close()

# --- LANGGRAPH STATE & NODES ---

class JobState(TypedDict):
    job: dict
    master_identity: str
    sys_config: dict
    distiller: any

    status: str
    extracted_json: dict
    matched_skills: list
    missing_skills: list
    tailor_context: str
    tailored_resume: dict
    resume_json_str: str
    invented_claims: list
    retry_count: int
    pdf_path: str
    # Gating state — set in tailor_node, consumed by fact_check and dispatch
    auto_apply_eligible: bool   # True only if BOTH ATS >= threshold AND fit >= threshold
    ats_score_raw: float        # 0.0–1.0 (not 0–100) for threshold comparison
    fit_score_raw: float        # 1.0–5.0 from DeepSeek evaluation
    disagreement_reason: str    # Human-readable reason when scores disagree
    scope_reason: str           # Reason string when job is out_of_scope

def verify_job_node(state: JobState) -> JobState:
    job = state['job']
    print("\n==============================================")
    print(f"[Thread] Processing Job: {job['url']}")
    
    print("\n[Phase 0.25] Pinging ATS to verify job is still alive...")
    is_alive, dead_reason = verify_job_liveness(job['url'])
    if not is_alive:
        print(f"[Phase 0.25] ABORT: Job is dead. Reason: {dead_reason}")
        update_job_status(job['id'], 'stale')
        state['status'] = 'stale'
        return state
        
    print("\n[Phase 0.5] Executing Block G Posting-Legitimacy Check...")
    is_ghost, scam_reason = detect_ghost_job(
        job['description'],
        job.get('location', ''),
        company=job.get('company', ''),
        title=job.get('title', '')
    )
    if is_ghost:
        print(f"[Phase 0.5] WARNING: Job rejected! Reason: {scam_reason}")
        with db_mutex:
            conn_up = sqlite3.connect(DB_PATH)
            c_up = conn_up.cursor()
            c_up.execute("UPDATE jobs SET status = 'rejected', scam_flags = ? WHERE id = ?", (scam_reason, job['id']))
            conn_up.commit()
            conn_up.close()
        state['status'] = 'rejected'
        return state
        
    print("\n[Phase 0.75] Hashing Job Description to detect reposts...")
    semantic_text = job['description'].lower()
    semantic_text = re.sub(r'\d{1,2}/\d{1,2}/\d{2,4}', '', semantic_text)
    semantic_text = re.sub(r'posted \d+ days ago', '', semantic_text)
    semantic_text = re.sub(r'\s+', '', semantic_text)
    jd_hash = hashlib.md5(semantic_text.encode('utf-8')).hexdigest()
    
    with db_mutex:
        conn_check = sqlite3.connect(DB_PATH)
        c_check = conn_check.cursor()
        c_check.execute("SELECT id FROM jobs WHERE jd_hash = ? AND id != ?", (jd_hash, job['id']))
        repost_match = c_check.fetchone()
        if repost_match:
            print("[Phase 0.75] REPOST DETECTED! Skipping to save compute.")
            conn_check.close()
            update_job_status(job['id'], 'repost')
            state['status'] = 'repost'
            return state
        c_check.execute("UPDATE jobs SET jd_hash = ? WHERE id = ?", (jd_hash, job['id']))
        conn_check.commit()
        conn_check.close()
        
    state['status'] = 'active'
    return state


def scope_gate_node(state: JobState) -> JobState:
    """
    Phase 0.9 — Application Scope Gate.
    Runs after liveness/ghost/repost checks but before ANY LLM call.
    If the job violates a hard 'exclude' rule in scope.json, it is immediately
    marked out_of_scope and removed from the processing queue.
    """
    job = state['job']
    scope = load_scope()   # hot-read from disk each cycle so changes take effect without restart
    passes, reason = check_scope(job, scope)

    if not passes:
        print(f"[Phase 0.9] OUT OF SCOPE: {reason}")
        with db_mutex:
            conn_s = sqlite3.connect(DB_PATH)
            c_s = conn_s.cursor()
            # Migrate scope_reason column if this is an older jobs.db
            try:
                c_s.execute("ALTER TABLE jobs ADD COLUMN scope_reason TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists
            c_s.execute(
                "UPDATE jobs SET status='out_of_scope', scope_reason=?, updated_at=? WHERE id=?",
                (reason, datetime.utcnow().isoformat(), job['id'])
            )
            conn_s.commit()
            conn_s.close()
        state['status'] = 'out_of_scope'
        state['scope_reason'] = reason
    else:
        print(f"[Phase 0.9] Scope gate passed for '{job.get('title', '')}' @ '{job.get('company', '')}'");
        state['status'] = 'in_scope'
        state['scope_reason'] = ''

    return state

def extraction_node(state: JobState) -> JobState:
    job = state['job']
    print("\n[Phase 1] Extracting structured data from raw HR post...")
    extraction_prompt = """Extract Job Title, Requirements, and Years of Experience (YoE) from this unstructured text. 
Strict JSON output only. If no YoE is stated, put 0.
Text: {job['description']}"""
    
    extracted_data_raw = generate(extraction_prompt, use_case="extraction")
    try:
        json_match = re.search(r"\{.*?\}", extracted_data_raw, re.DOTALL)
        state['extracted_json'] = json.loads(json_match.group(0)) if json_match else {"YoE": 0, "Requirements": ""}
    except Exception as e:
        print(f"[Phase 1] JSON extraction failed, using empty defaults. Error: {e}")
        state['extracted_json'] = {"YoE": 0, "Requirements": ""}
        
    print(f"Extracted: {state['extracted_json']}")
    
    print("\n[Phase 1.5] Analyzing Skill Gaps using Regex...")
    matched, supported, missing = analyze_skill_gap(job['description'])
    state['matched_skills'] = matched
    state['supported_skills'] = supported
    state['missing_skills'] = missing
    
    with db_mutex:
        conn_up = sqlite3.connect(DB_PATH)
        c_up = conn_up.cursor()
        
        matched_str = ", ".join(matched)
        if supported:
            matched_str += " | Supported: " + ", ".join(supported)
            
        c_up.execute("UPDATE jobs SET missing_skills = ?, matched_skills = ? WHERE id = ?", (", ".join(missing), matched_str, job['id']))
        conn_up.commit()
        conn_up.close()
        
    return state

def evaluate_fit_node(state: JobState) -> JobState:
    job = state['job']
    extracted_json = state['extracted_json']
    
    print("\n[Phase 1.75] Classifying Job Archetype...")
    job_title = extracted_json.get("Job Title", job.get('title', ''))
    archetype = classify_archetype(job_title, str(extracted_json))
    
    threshold = state['sys_config'].get("threshold", 4.0)
    scoring_caps = state['sys_config'].get("scoring_caps", [])
    dynamic_rubric = get_rubric_for_archetype(archetype, threshold, scoring_caps)
    
    print("\n[Phase 2] Executing Archetype-Specific Evaluator...")
    company_name = job.get('company', 'Unknown')
    evaluation = state['distiller'].evaluate_job(state['master_identity'], extracted_json, dynamic_rubric, threshold, company_name)
    is_match = evaluation.get("match", False)
    score = evaluation.get("score", 0.0)
    rubric_data = {
        "grades": evaluation.get("rubric", {}),
        "positioning": evaluation.get("block_c", {}),
        "compensation": evaluation.get("block_d", {})
    }
    rubric = json.dumps(rubric_data)
    
    with db_mutex:
        conn_up = sqlite3.connect(DB_PATH)
        c_up = conn_up.cursor()
        c_up.execute("UPDATE jobs SET fit_score = ?, evaluation_rubric = ? WHERE id = ?", (score, rubric, job['id']))
        conn_up.commit()
        conn_up.close()
    
    if not is_match:
        print(f"[Phase 2] Rejected based on profile fit. Score: {score}")
        update_job_status(job['id'], 'rejected')
        state['status'] = 'rejected'
    else:
        print(f"[Phase 2] MATCH FOUND! Score: {score}")
        state['status'] = 'matched'
    
    # Store the full rubric in state so strategy_generator can reference it
    state['evaluation_rubric'] = rubric_data
        
    return state

def prep_interview_node(state: JobState) -> JobState:
    job = state['job']
    extracted_json = state['extracted_json']
    master_identity = state['master_identity']
    
    print("\n[Phase 2.5] Career-Ops Prep: Generating STAR stories and Contact Message...")
    from engine.star_bank import extract_star_stories
    from engine.contact_discovery import generate_contact_message
    
    stories = extract_star_stories(master_identity, extracted_json)
    contact_msg = generate_contact_message(master_identity, extracted_json)
    
    with db_mutex:
        conn_up = sqlite3.connect(DB_PATH)
        c_up = conn_up.cursor()
        c_up.execute("UPDATE jobs SET star_stories = ?, contact_message = ? WHERE id = ?", 
                     (json.dumps(stories), contact_msg, job['id']))
        conn_up.commit()
        conn_up.close()
        
    return state

def tailor_node(state: JobState) -> JobState:
    job = state['job']
    extracted_json = state['extracted_json']
    retry_count = state.get('retry_count', 0)

    print(f"\n[Phase 3] Tailoring Pipeline (Attempt {retry_count + 1})...")
    kb = load_kb()

    tailor_context = f"Job Reqs: {extracted_json}\nRaw JD: {job['description']}"
    if retry_count > 0 and state.get('invented_claims'):
        tailor_context += (
            "\n\nCRITICAL WARNING: In your previous attempt, you hallucinated the "
            f"following claims: {state['invented_claims']}. "
            "YOU MUST ONLY USE FACTS FROM THE KNOWLEDGE BASE."
        )

    try:
        tailored_resume = tailor_resume(tailor_context)
        state['tailored_resume'] = tailored_resume
        state['resume_json_str'] = generate_html_context(tailored_resume, kb)

        # ── Phase 3.5: ATS keyword coverage + combined gating decision ──────
        total_skills = state['matched_skills'] + state['missing_skills']
        ats_score_pct = 0.0
        ats_score_ratio = 0.0
        if total_skills:
            hits = sum(1 for s in total_skills if s.lower() in state['resume_json_str'].lower())
            ats_score_pct = (hits / len(total_skills)) * 100
            ats_score_ratio = hits / len(total_skills)   # 0.0–1.0 for threshold comparison
            print(f"[Phase 3.5] ATS Coverage: {ats_score_pct:.1f}%  "
                  f"(threshold: {ATS_AUTO_APPLY_THRESHOLD * 100:.0f}%)")

        # Retrieve fit score from state (set by evaluate_fit_node)
        fit_score = state.get('fit_score_raw', 0.0)
        state['ats_score_raw'] = ats_score_ratio

        # Persist ATS score to DB
        with db_mutex:
            conn_up = sqlite3.connect(DB_PATH)
            c_up = conn_up.cursor()
            c_up.execute("UPDATE jobs SET ats_score = ? WHERE id = ?",
                         (ats_score_pct, job['id']))
            conn_up.commit()
            conn_up.close()

        # ── Combined gating decision ─────────────────────────────────────────
        ats_passes  = ats_score_ratio >= ATS_AUTO_APPLY_THRESHOLD
        fit_passes  = fit_score >= FIT_AUTO_APPLY_THRESHOLD

        if ats_passes and fit_passes:
            state['auto_apply_eligible'] = True
            state['disagreement_reason'] = ""
            print("[Phase 3.5] GATE PASS — eligible for auto-apply "
                  f"(ATS {ats_score_pct:.1f}%, Fit {fit_score:.1f}/5).")

        elif ats_passes and not fit_passes:
            # High keyword match but weak overall fit — route to Human Apply
            reason = (f"High ATS coverage ({ats_score_pct:.0f}%) but fit score "
                      f"{fit_score:.1f}/5 is below threshold {FIT_AUTO_APPLY_THRESHOLD:.1f}/5")
            state['auto_apply_eligible'] = False
            state['disagreement_reason'] = reason
            print(f"[Phase 3.5] DISAGREEMENT — {reason}")
            with db_mutex:
                conn_d = sqlite3.connect(DB_PATH)
                c_d = conn_d.cursor()
                c_d.execute("UPDATE jobs SET status='human_review_disagreement', "
                            "disagreement_reason=? WHERE id=?", (reason, job['id']))
                conn_d.commit()
                conn_d.close()
            state['status'] = 'human_review_disagreement'

        elif not ats_passes and fit_passes:
            # Good fit but resume didn't include enough JD keywords — route to Human Apply
            reason = (f"Fit score {fit_score:.1f}/5 passes but ATS coverage "
                      f"{ats_score_pct:.0f}% is below threshold "
                      f"{ATS_AUTO_APPLY_THRESHOLD * 100:.0f}%")
            state['auto_apply_eligible'] = False
            state['disagreement_reason'] = reason
            print(f"[Phase 3.5] DISAGREEMENT — {reason}")
            with db_mutex:
                conn_d = sqlite3.connect(DB_PATH)
                c_d = conn_d.cursor()
                c_d.execute("UPDATE jobs SET status='human_review_disagreement', "
                            "disagreement_reason=? WHERE id=?", (reason, job['id']))
                conn_d.commit()
                conn_d.close()
            state['status'] = 'human_review_disagreement'

        else:
            # Both fail — should have been caught by evaluate_fit_node, but handle defensively
            state['auto_apply_eligible'] = False
            state['disagreement_reason'] = ""

    except Exception as e:
        print(f"[Phase 3] Tailoring failed: {e}")
        update_job_status(job['id'], 'failed_generation')
        state['status'] = 'failed_generation'

    return state

def fact_check_node(state: JobState) -> JobState:
    job = state['job']
    auto_eligible = state.get('auto_apply_eligible', False)
    intent = "auto_apply" if auto_eligible else "human_review"

    print(f"\n[Phase 4] Verifying CV Facts (intent={intent})...")
    is_passed, invented_claims = verify_resume_facts(state['resume_json_str'], intent=intent)

    if not is_passed:
        state['invented_claims'] = invented_claims
        if intent == "auto_apply":
            # Zero-tolerance: immediately downgrade to Human Apply Queue, no retry
            print("[Phase 4] AUTO-APPLY DOWNGRADE: routing to Human Apply Queue.")
            with db_mutex:
                conn_d = sqlite3.connect(DB_PATH)
                c_d = conn_d.cursor()
                c_d.execute(
                    "UPDATE jobs SET status='failed_fact_check_auto_downgrade' WHERE id=?",
                    (job['id'],)
                )
                conn_d.commit()
                conn_d.close()
            state['auto_apply_eligible'] = False   # Force human path in dispatch
            state['status'] = 'failed_fact_check_auto_downgrade'
        else:
            # Human-review path: signal for retry (graph router handles max retries)
            state['retry_count'] = state.get('retry_count', 0) + 1
            state['status'] = 'hallucinated'
    else:
        state['status'] = 'verified'

    return state

def _increment_circuit_breaker():
    """Increments the persistent failure counter. Trips the breaker at N."""
    count = int(get_daemon_state("cb_consecutive_failures", "0")) + 1
    set_daemon_state("cb_consecutive_failures", str(count))
    if count >= AUTO_APPLY_CIRCUIT_BREAKER_N:
        set_daemon_state("auto_apply_paused", "true")
        print(
            f"[CircuitBreaker] TRIPPED after {count} consecutive failures. "
            "Auto-apply is now PAUSED. Dashboard alert will appear. "
            "Fix the underlying issue and clear via /api/circuit-breaker/reset."
        )


def _reset_circuit_breaker():
    """Resets the failure counter on a successful submission."""
    set_daemon_state("cb_consecutive_failures", "0")
    set_daemon_state("auto_apply_paused", "false")


def _auto_apply_is_paused() -> bool:
    return get_daemon_state("auto_apply_paused", "false").lower() == "true"


def compile_dispatch_node(state: JobState) -> JobState:
    job = state['job']
    kb = load_kb()
    personal_info = kb.get("personal", {})
    safe_name = personal_info.get("name", "User_Name").replace(" ", "_")
    safe_title = str(state['extracted_json'].get("Job Title", "Role")).replace(" ", "_").replace("/", "-")
    pdf_path = f"output/{safe_name}_{safe_title}.pdf"

    success = render_html_to_pdf(state['resume_json_str'], "templates/cv-template.html", pdf_path)
    if not success:
        update_job_status(job['id'], 'failed_generation')
        state['status'] = 'failed_generation'
        return state

    url = job["url"].lower()
    auto_eligible = state.get('auto_apply_eligible', False)
    company = job.get('company', 'Unknown')
    title = job.get('title', 'Unknown')
    jd_hash = job.get('jd_hash', '')
    ats_score = state.get('ats_score_raw', 0.0) * 100   # back to pct for audit log
    fit_score = state.get('fit_score_raw', 0.0)

    # ── Global daily rate limit (unchanged) ──────────────────────────────────
    with db_mutex:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM jobs WHERE status = 'applied' AND source = ? "
            "AND substr(updated_at, 1, 10) = date('now')",
            (job.get('source', 'Unknown'),)
        )
        apps_today = cursor.fetchone()[0]
        conn.close()

    max_apps = state['sys_config'].get('max_applications_per_day', 30)
    global_limit_reached = apps_today >= max_apps

    # ── Playwright auto-apply path (Greenhouse / Lever only) ─────────────────
    is_auto_portal = "greenhouse.io" in url or "lever.co" in url

    if is_auto_portal and auto_eligible:
        # ── Circuit breaker ──────────────────────────────────────────────────
        if _auto_apply_is_paused():
            print("[Dispatcher] Circuit breaker is OPEN. Skipping auto-apply, routing to Human Apply.")
            log_auto_apply_attempt(job['id'], company, title, jd_hash, pdf_path,
                                   ats_score, fit_score, 'circuit_open')
            generate_strategy_report(job['id'], company, title,
                                     state['extracted_json'], state['master_identity'],
                                     state.get('evaluation_rubric'))
            update_job_status(job['id'], 'pending_cover_letter')
            state['status'] = 'pending_cover_letter'
            return state

        # ── Global daily rate limit ──────────────────────────────────────────
        if global_limit_reached:
            print(f"[Dispatcher] Global rate limit reached ({apps_today}/{max_apps}). Human Apply.")
            update_job_status(job['id'], 'manual_review')
            state['status'] = 'dispatched'
            return state

        # ── Per-company daily cap ────────────────────────────────────────────
        company_apps_today = get_company_applies_today(company)
        if company_apps_today >= COMPANY_DAILY_CAP:
            reason = f"company_cap_reached: {company_apps_today}/{COMPANY_DAILY_CAP} today"
            print(f"[Dispatcher] Per-company cap reached for '{company}': {reason}")
            log_auto_apply_attempt(job['id'], company, title, jd_hash, pdf_path,
                                   ats_score, fit_score, 'capped')
            update_job_status(job['id'], 'company_cap_reached')
            state['status'] = 'pending_cover_letter'
            return state

        # ── Dedup check ──────────────────────────────────────────────────────
        if has_been_applied_to(jd_hash, company, title):
            print(f"[Dispatcher] DEDUP: already applied to '{title}' @ '{company}'. Skipping.")
            log_auto_apply_attempt(job['id'], company, title, jd_hash, pdf_path,
                                   ats_score, fit_score, 'deduped')
            update_job_status(job['id'], 'already_applied')
            state['status'] = 'dispatched'
            return state
        # ── Actually invoke Playwright ─────────────────────────────────────────
        print(f"[Dispatcher] All gates passed. Checking if URL is a supported ATS for Auto-Apply...")

        apply_fn = None
        naukri_creds = None

        if "greenhouse.io" in url:
            apply_fn = apply_to_greenhouse
        elif "lever.co" in url:
            apply_fn = apply_to_lever
        elif "naukri.com" in url or job.get('source', '').lower() == 'naukri':
            # Strategy: extract the REAL company career page URL from the Naukri listing.
            # Quick Apply is avoided — it puts you in a pile with 10,000 others.
            naukri_email    = os.getenv('NAUKRI_EMAIL', '')
            naukri_password = os.getenv('NAUKRI_PASSWORD', '')
            real_url = extract_real_apply_url(url)
            if real_url:
                print(f"[Dispatcher] Naukri: Found real ATS URL → {real_url}")
                url = real_url  # redirect to the actual company portal
                job['url'] = real_url
                if 'greenhouse.io' in real_url:
                    apply_fn = apply_to_greenhouse
                elif 'lever.co' in real_url:
                    apply_fn = apply_to_lever
                # else: unsupported ATS — falls through to Human Apply Queue below
            else:
                print("[Dispatcher] Naukri: No real ATS URL found — routing to Human Apply Queue with direct link.")
                # apply_fn stays None → will generate strategy report below

        if apply_fn is None:
            # It's an unsupported ATS (e.g. Workday, custom portal extracted from Freshershunt)
            print(f"[Dispatcher] {url} is not a supported Auto-Apply ATS. Routing to Human Apply Queue.")
            generate_strategy_report(job['id'], company, title,
                                     state['extracted_json'], state['master_identity'],
                                     state.get('evaluation_rubric'))
            update_job_status(job['id'], 'pending_cover_letter')
            state['status'] = 'pending_cover_letter'
            return state

        print(f"[Dispatcher] Invoking Playwright for {url}...")
        apply_success = apply_fn(job["url"], personal_info, pdf_path)

        if apply_success:
            _reset_circuit_breaker()
            update_job_status(job['id'], 'applied')
            log_auto_apply_attempt(job['id'], company, title, jd_hash, pdf_path,
                                   ats_score, fit_score, 'submitted')
            with db_mutex:
                add_triple("User", "APPLIED_TO", company)
            print("[Dispatcher] Application submitted. Sleeping 60s for rate safety.")
            time.sleep(60)
        else:
            _increment_circuit_breaker()
            log_auto_apply_attempt(job['id'], company, title, jd_hash, pdf_path,
                                   ats_score, fit_score, 'failed')
            update_job_status(job['id'], 'failed_submission')

        state['status'] = 'dispatched'
        return state

    # ── Disagreement / downgraded paths → Human Apply Queue ──────────────────
    # Covers: human_review_disagreement, failed_fact_check_auto_downgrade,
    # non-auto portals, and any job where auto_eligible is False.

    if state.get('status') in ('human_review_disagreement', 'failed_fact_check_auto_downgrade'):
        print(f"[Dispatcher] Human Apply Queue — reason: {state.get('disagreement_reason') or state['status']}")
        generate_strategy_report(job['id'], company, title,
                                 state['extracted_json'], state['master_identity'],
                                 state.get('evaluation_rubric'))
        update_job_status(job['id'], state['status'])
        state['status'] = 'pending_cover_letter'
        return state

    # ── Standard human portals (Workday, direct email, unknown) ──────────────
    if "mailto:" in url or "@" in url:
        print("[Dispatcher] Direct Email Application Detected.")
        generate_application_email(job['id'], company, title,
                                   state['extracted_json'], state['master_identity'])
        update_job_status(job['id'], 'pending_cover_letter')
        state['status'] = 'pending_cover_letter'
    else:
        print("[Dispatcher] Manual Portal — generating Strategy Report...")
        generate_strategy_report(job['id'], company, title,
                                 state['extracted_json'], state['master_identity'],
                                 state.get('evaluation_rubric'))
        send_email_notification(safe_title, company, job['url'], pdf_path)
        update_job_status(job['id'], 'pending_cover_letter')
        state['status'] = 'pending_cover_letter'

    return state

# --- GRAPH DEFINITION ---

def build_job_graph():
    workflow = StateGraph(JobState)
    
    workflow.add_node("verify", verify_job_node)
    workflow.add_node("scope_gate", scope_gate_node)  # Phase 0.9 — before any LLM
    workflow.add_node("extract", extraction_node)
    workflow.add_node("evaluate", evaluate_fit_node)
    workflow.add_node("prep_interview", prep_interview_node)
    workflow.add_node("tailor", tailor_node)
    workflow.add_node("fact_check", fact_check_node)
    workflow.add_node("dispatch", compile_dispatch_node)

    workflow.set_entry_point("verify")

    workflow.add_conditional_edges("verify", lambda x: x['status'], {
        'active': 'scope_gate',
        'stale': END,
        'rejected': END,
        'repost': END
    })

    workflow.add_conditional_edges("scope_gate", lambda x: x['status'], {
        'in_scope': 'extract',
        'out_of_scope': END,
    })

    workflow.add_edge("extract", "evaluate")
    
    workflow.add_conditional_edges("evaluate", lambda x: x['status'], {
        'matched': 'prep_interview',
        'rejected': END
    })
    
    workflow.add_edge("prep_interview", "tailor")
    
    workflow.add_conditional_edges("tailor", lambda x: x['status'], {
        'failed_generation': END,
        # Disagreement jobs skip fact-check and go directly to dispatch
        # (dispatch will route them to Human Apply with the reason note)
        'human_review_disagreement': 'dispatch',
    }, default="fact_check")

    def route_fact_check(state: JobState):
        status = state['status']
        auto_eligible = state.get('auto_apply_eligible', False)

        if status == 'verified':
            return 'dispatch'

        if status == 'failed_fact_check_auto_downgrade':
            # Zero-tolerance auto-apply downgrade — skip retry, go to dispatch
            # (dispatch will route to Human Apply Queue)
            return 'dispatch'

        # Human-review retry path
        if state.get('retry_count', 0) >= 2 or not auto_eligible:
            print("[Graph] Fact check failed. Aborting retry (max retries reached or not auto-eligible).")
            update_job_status(state['job']['id'], 'failed_fact_check')
            return END

        return 'tailor'

    workflow.add_conditional_edges("fact_check", route_fact_check)
    workflow.add_edge("dispatch", END)
    
    return workflow.compile()

# --- DAEMON LOOP ---

def execute_sprav_moe_pipeline():
    with db_mutex:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE status = 'new'")
        jobs = [dict(ix) for ix in cursor.fetchall()]
        conn.close()
    
    if not jobs:
        print("[Dispatcher] No new jobs to process.")
        return
        
    sys_config = get_config()
    distiller = KnowledgeDistiller()
    master_identity = distiller.get_master_identity()
    graph = build_job_graph()
    
    print(f"\n[Parallel Sub-Agents] Spawning {min(len(jobs), 2)} headless CLI workers to process jobs concurrently...")
    
    def run_graph(job):
        initial_state = {
            'job': job,
            'master_identity': master_identity,
            'sys_config': sys_config,
            'distiller': distiller,
            'retry_count': 0,
            'status': 'new'
        }
        graph.invoke(initial_state)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(run_graph, job) for job in jobs]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"[Daemon Error] Parallel Job Worker crashed: {e}")

def check_ollama_models():
    import requests
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        if resp.status_code == 200:
            models = [m['name'] for m in resp.json().get('models', [])]
            required = ["qwen2.5:7b-instruct", "deepseek-r1:7b", "magnum-v4:9b", "llama3.1:8b", "nomic-embed-text:latest"]
            missing = [m for m in required if not any(m in available for available in models)]
            if missing:
                print(f"[WARNING] Missing recommended local models: {missing}. Fallbacks will be used or execution may fail.")
            else:
                print("[Ollama] All 5 required GGUF models are present and ready.")
    except Exception:
        print("[WARNING] Could not connect to local Ollama instance on port 11434.")

def run_daemon():
    print("=========================================")
    print("[Daemon] SPrav Multi-Threaded MoE Initialized (LangGraph Enabled).")
    print("=========================================")
    check_ollama_models()
    
    from engine.kb_merger import kb_is_ready
    if not kb_is_ready():
        print("[Daemon] WARNING: me.json is empty or missing required fields.")
        print("[Daemon] Open the dashboard -> Knowledge Base -> Rebuild from Sources to complete onboarding.")
    
    # Track which days the profile touch has run to avoid running it more than twice a day
    _profile_touch_dates = set()
    
    cycle = 1
    while True:
        now = datetime.now()

        if now.hour == 3:
            try:
                run_compaction()
            except Exception as e:
                print(f"[Daemon Error] Compaction failed: {e}")
                
        # Run Naukri profile touch at 9 AM and 6 PM (pushes profile to top of recruiter searches)
        touch_key = f"{now.date()}_{now.hour}"
        if now.hour in (9, 18) and touch_key not in _profile_touch_dates:
            naukri_email    = os.getenv('NAUKRI_EMAIL', '')
            naukri_password = os.getenv('NAUKRI_PASSWORD', '')
            if naukri_email and naukri_password:
                print("\n--- [Profile Boost] Running Naukri profile freshness touch ---")
                try:
                    touch_naukri_profile(naukri_email, naukri_password)
                    _profile_touch_dates.add(touch_key)
                except Exception as e:
                    print(f"[Profile Touch Error] {e}")

        print(f"\n--- [Cycle {cycle}] Starting Job Discovery ---")
        try:
            print("\n--- Triggering Node.js Stealth Scraper ---")
            subprocess.run(["cmd", "/c", "node scraper_service/stealth_crawler.js"], check=False)
            
            print("\n--- Triggering Zero-Token ATS Discovery ---")
            try:
                run_ats_discovery()
            except Exception as e:
                print(f"ATS Discovery error: {e}")
            
            print("\n--- Executing SPrav MoE Pipeline ---")
            execute_sprav_moe_pipeline()
            
        except Exception as e:
            print(f"[Daemon Error] Pipeline failed this cycle: {e}")
            
        # Run LinkedIn post scanner every other cycle (~30 min cadence)
        if cycle % 2 == 0:
            print("\n--- Triggering LinkedIn HR/CEO Post Scanner ---")
            try:
                run_linkedin_scanner()
            except Exception as e:
                print(f"LinkedIn Scanner error: {e}")

        sleep_minutes = random.randint(5, 15)
        print(f"\n[Daemon] Cycle {cycle} complete. Sleeping for {sleep_minutes} minutes...")
        time.sleep(sleep_minutes * 60)
        cycle += 1

if __name__ == "__main__":
    run_daemon()
