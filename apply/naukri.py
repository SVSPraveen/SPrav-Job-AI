"""
apply/naukri.py
===============
Playwright-based Naukri.com Quick Apply bot.

Naukri has a "Quick Apply" flow where logged-in users can apply with
1-2 clicks using their stored profile. This module logs into Naukri,
navigates to the job listing, and submits the Quick Apply form.

Requirements:
  - NAUKRI_EMAIL and NAUKRI_PASSWORD in .env (or users.db credentials store)
  - The Playwright browser context is kept headful=False (stealth mode)
"""

import os
import random
import time
import subprocess
import json


def _jitter(min_s=1.5, max_s=3.5):
    time.sleep(random.uniform(min_s, max_s))


# We call a Node.js Playwright script because browser automation in Node.js
# with puppeteer-extra stealth is more reliable than Python's Playwright
# for sites with aggressive bot detection like Naukri.

NAUKRI_JS = os.path.join(
    os.path.dirname(__file__), "..", "scraper_service", "naukri_apply.js"
)


def apply_to_naukri(job_url: str, email: str, password: str) -> bool:
    """
    Logs into Naukri and submits the Quick Apply for a given job URL.
    Returns True on success, False on failure.
    """
    if not email or not password:
        print("[Naukri Apply] No credentials provided — skipping.")
        return False

    if not os.path.exists(NAUKRI_JS):
        print("[Naukri Apply] naukri_apply.js not found.")
        return False

    print(f"[Naukri Apply] Attempting Quick Apply: {job_url}")
    try:
        result = subprocess.run(
            ["node", NAUKRI_JS, job_url, email, password],
            capture_output=True,
            text=True,
            timeout=120,
            env={**os.environ}
        )
        output = result.stdout.strip()
        if not output:
            stderr = result.stderr[-300:] if result.stderr else ""
            print(f"[Naukri Apply] No response. Stderr: {stderr}")
            return False

        data = json.loads(output)
        success = data.get("success", False)
        print(f"[Naukri Apply] {'✓ Applied' if success else '✗ Failed'}: {data.get('reason', '')}")
        return success
    except Exception as e:
        print(f"[Naukri Apply] Error: {e}")
        return False
