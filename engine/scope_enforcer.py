"""
engine/scope_enforcer.py — Application Scope Gate (Pre-Phase 2)
===============================================================
Checks a discovered job against the user's saved Application Scope preferences
(knowledge_base/scope.json) BEFORE Phase 2 (Fit Evaluation) runs.

If a job fails a hard "exclude" rule, it is immediately marked 'out_of_scope'
with a human-readable reason. No LLM inference is wasted on it.

Rules applied in order:
  1. Work mode gate (remote-only / onsite-only)
  2. Location gate   (per-location exclude tags)
  3. Role/title gate (per-keyword exclude tags, fuzzy match)
  4. Job type gate   (job type category excludes)
  5. Experience level gate

"No preference" / "any" categories pass through without filtering.
"""

import json
import os
import re
from difflib import SequenceMatcher

SCOPE_PATH = "knowledge_base/scope.json"

# ─────────────────────────────────────────────────────────────────────────────
# Scope loading
# ─────────────────────────────────────────────────────────────────────────────

_DEFAULT_SCOPE = {
    "locations": [],
    "work_mode": "any",
    "roles": [],
    "job_types": {
        "full_time": "include",
        "part_time": "include",
        "internship": "include",
        "contract": "include",
        "freelance": "include",
    },
    "experience_level": "any",
}


def load_scope() -> dict:
    """Loads scope.json, returning defaults if missing or malformed."""
    if not os.path.exists(SCOPE_PATH):
        return dict(_DEFAULT_SCOPE)
    try:
        with open(SCOPE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Merge with defaults so missing keys don't crash
        merged = dict(_DEFAULT_SCOPE)
        merged.update(data)
        return merged
    except Exception as e:
        print(f"[ScopeEnforcer] Failed to load scope.json: {e}. Using defaults.")
        return dict(_DEFAULT_SCOPE)


def save_scope(scope: dict) -> None:
    """Persists scope config to disk."""
    os.makedirs(os.path.dirname(SCOPE_PATH), exist_ok=True)
    with open(SCOPE_PATH, "w", encoding="utf-8") as f:
        json.dump(scope, f, indent=2, ensure_ascii=False)


# ─────────────────────────────────────────────────────────────────────────────
# Individual gate checks
# ─────────────────────────────────────────────────────────────────────────────

def _fuzzy_match(needle: str, haystack: str, threshold: float = 0.72) -> bool:
    """
    Returns True if needle appears in haystack as a substring OR via
    SequenceMatcher similarity above `threshold`. Case-insensitive.
    """
    needle = needle.lower().strip()
    haystack = haystack.lower()
    if needle in haystack:
        return True
    ratio = SequenceMatcher(None, needle, haystack).ratio()
    return ratio >= threshold


def _detect_work_mode(job: dict) -> str:
    """
    Infers the job's work mode from title, location, and description.
    Returns: 'remote' | 'onsite' | 'hybrid' | 'unknown'
    """
    text = " ".join([
        job.get("title", ""),
        job.get("location", ""),
        (job.get("description", "") or "")[:500],
    ]).lower()

    if "remote" in text:
        if "hybrid" in text or "on-site" in text or "onsite" in text:
            return "hybrid"
        return "remote"
    if "hybrid" in text:
        return "hybrid"
    if "on-site" in text or "onsite" in text or "in-office" in text or "in office" in text:
        return "onsite"
    return "unknown"


def _detect_job_type(job: dict) -> str:
    """
    Infers the job type from JD text.
    Returns: 'full_time' | 'part_time' | 'internship' | 'contract' | 'freelance' | 'unknown'
    """
    text = " ".join([
        job.get("title", ""),
        (job.get("description", "") or "")[:800],
    ]).lower()

    if any(w in text for w in ["intern", "internship", "trainee", "graduate trainee"]):
        return "internship"
    if any(w in text for w in ["freelance", "freelancer", "gig"]):
        return "freelance"
    if any(w in text for w in ["contract", "contractor", "fixed term", "fixed-term"]):
        return "contract"
    if any(w in text for w in ["part-time", "part time", "parttime"]):
        return "part_time"
    if any(w in text for w in ["full-time", "full time", "fulltime", "permanent"]):
        return "full_time"
    return "unknown"


def _detect_experience_level(job: dict) -> str:
    """
    Infers experience level from title and JD text.
    Returns: 'entry' | 'mid' | 'senior' | 'unknown'
    """
    text = " ".join([
        job.get("title", ""),
        (job.get("description", "") or "")[:800],
    ]).lower()

    if any(w in text for w in ["senior", "sr.", "lead", "principal", "staff", "head of", "vp", "director"]):
        return "senior"
    if any(w in text for w in ["junior", "entry", "entry-level", "graduate", "intern", "fresher", "0-1 year", "0-2 year"]):
        return "entry"
    if any(w in text for w in ["mid", "mid-level", "mid level", "associate", "2-4 year", "3-5 year"]):
        return "mid"
    return "unknown"


# ─────────────────────────────────────────────────────────────────────────────
# Main gate function
# ─────────────────────────────────────────────────────────────────────────────

def check_scope(job: dict, scope: dict | None = None) -> tuple[bool, str]:
    """
    Runs the job through all scope gates.

    Returns:
        (True, "")                     — job passes all gates, proceed to Phase 2
        (False, "reason string")       — job is out of scope; reason for the dashboard
    """
    if scope is None:
        scope = load_scope()

    job_location = (job.get("location") or "").lower()
    job_title    = (job.get("title")    or "").lower()

    # ── Gate 1: Work mode ────────────────────────────────────────────────────
    work_mode = scope.get("work_mode", "any")
    if work_mode != "any":
        detected_mode = _detect_work_mode(job)
        if work_mode == "remote_only" and detected_mode == "onsite":
            return False, "Work mode excluded: job is On-site, scope requires Remote only"
        if work_mode == "onsite_only" and detected_mode == "remote":
            return False, "Work mode excluded: job is Remote, scope requires On-site only"

    # ── Gate 2: Per-location rules ────────────────────────────────────────────
    for loc_rule in scope.get("locations", []):
        label = (loc_rule.get("label") or "").lower().strip()
        pref  = loc_rule.get("preference", "no_preference")
        if pref == "exclude" and label and label in job_location:
            return False, f"Location excluded: {loc_rule['label']}"

    # ── Gate 3: Role/title rules ──────────────────────────────────────────────
    for role_rule in scope.get("roles", []):
        keyword = (role_rule.get("keyword") or "").strip()
        pref    = role_rule.get("preference", "no_preference")
        if pref == "exclude" and keyword:
            if _fuzzy_match(keyword, job_title):
                return False, f"Role excluded: '{keyword}' matches job title '{job.get('title', '')}'"

    # ── Gate 4: Job type ──────────────────────────────────────────────────────
    job_types_scope = scope.get("job_types", {})
    detected_type   = _detect_job_type(job)
    if detected_type != "unknown":
        type_pref = job_types_scope.get(detected_type, "include")
        if type_pref == "exclude":
            readable = detected_type.replace("_", "-")
            return False, f"Job type excluded: {readable}"

    # ── Gate 5: Experience level ──────────────────────────────────────────────
    level_pref = scope.get("experience_level", "any")
    if level_pref != "any":
        detected_level = _detect_experience_level(job)
        # Only hard-exclude if we detected something AND it doesn't match what the user wants
        if detected_level != "unknown" and detected_level != level_pref:
            readable_detected = detected_level.capitalize()
            readable_wanted   = level_pref.capitalize()
            return False, (
                f"Experience level mismatch: job appears {readable_detected}-level, "
                f"scope is set to {readable_wanted}"
            )

    # All gates passed
    return True, ""
