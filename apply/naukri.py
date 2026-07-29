"""
apply/naukri.py
===============
Naukri.com Apply Strategy Module — Manual Assist Route

STRATEGY (Updated):
───────────────────
Automated apply on Naukri is deprecated due to advanced Akamai anti-bot detection.
Jobs sourced from Naukri are pushed directly to the Human Apply Queue.
The UI surfaces a "Manual Assist" component giving the user a direct link, 
their tailored resume/cover letter, and pre-drafted answers from the knowledge base.

Usage:
  from apply.naukri import extract_real_apply_url
"""

def extract_real_apply_url(naukri_job_url: str) -> str | None:
    """
    Since automated browsing is disabled for Naukri, this simply returns None,
    forcing the job into the Human Apply Queue for manual processing.
    """
    print(f"[Naukri] Manual apply required for {naukri_job_url} — routing to Human Apply Queue.")
    return None
