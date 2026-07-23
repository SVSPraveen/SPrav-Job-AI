"""
apply/naukri.py
===============
Naukri.com Apply Strategy Module — Real Apply Path (NOT Quick Apply).

STRATEGY (Updated):
───────────────────
Quick Apply / Easy Apply is a trap. 10,000+ applicants hit that button.
The real path is:
  1. Open the Naukri job listing page.
  2. Extract the company's ACTUAL apply URL (the "Apply on Company Website" 
     button that most genuine listings expose).
  3. Route that URL back to the dispatcher so it can try Greenhouse / Lever 
     auto-apply, or land in the Human Apply Queue with the direct link.

If no external apply URL is found, the job goes to the Human Apply Queue 
with a strategy report — the user applies manually through the real form.

Profile Freshness:
──────────────────
A separate function `touch_naukri_profile()` logs into Naukri and makes
a micro-edit to the resume headline, pushing the profile to the top of
recruiter keyword searches (Naukri sorts by "Last Active").

Usage:
  from apply.naukri import extract_real_apply_url, touch_naukri_profile
"""

import os
import subprocess
import json

NAUKRI_APPLY_JS = os.path.join(
    os.path.dirname(__file__), "..", "scraper_service", "naukri_apply.js"
)
NAUKRI_TOUCH_JS = os.path.join(
    os.path.dirname(__file__), "..", "scraper_service", "naukri_profile_touch.js"
)


def _run_node(script: str, *args, timeout: int = 120) -> dict:
    """Runs a Node.js script and parses its JSON stdout."""
    try:
        result = subprocess.run(
            ["node", script, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ}
        )
        output = result.stdout.strip()
        if not output:
            stderr = (result.stderr or "")[-300:]
            print(f"[Naukri] Node script returned no output. Stderr: {stderr}")
            return {}
        return json.loads(output)
    except Exception as e:
        print(f"[Naukri] Node script error: {e}")
        return {}


def extract_real_apply_url(naukri_job_url: str) -> str | None:
    """
    Opens a Naukri job listing in a headless browser and looks for the
    "Apply on Company Website" button — which leads to the real ATS 
    (Greenhouse, Lever, Workday, etc.).

    Returns the external apply URL if found, None otherwise.
    """
    if not os.path.exists(NAUKRI_APPLY_JS):
        return None

    data = _run_node(NAUKRI_APPLY_JS, naukri_job_url, "--extract-only")
    real_url = data.get("external_apply_url")
    
    if real_url:
        print(f"[Naukri] Found real apply URL: {real_url}")
    else:
        print(f"[Naukri] No external apply URL found on listing — routing to Human Apply Queue.")
    
    return real_url


def touch_naukri_profile(email: str, password: str) -> bool:
    """
    Runs the profile freshness bot: logs into Naukri and makes a
    micro-edit to the resume headline so the profile appears as
    "Active Today" in recruiter searches.
    
    Returns True on success.
    """
    if not email or not password:
        print("[Naukri Touch] No Naukri credentials — skipping profile refresh.")
        return False

    if not os.path.exists(NAUKRI_TOUCH_JS):
        print("[Naukri Touch] naukri_profile_touch.js not found.")
        return False

    print("[Naukri Touch] Running daily profile refresh...")
    data = _run_node(NAUKRI_TOUCH_JS, email, password, timeout=180)
    success = data.get("success", False)
    reason = data.get("reason", "")
    print(f"[Naukri Touch] {'✓' if success else '✗'} {reason}")
    return success
