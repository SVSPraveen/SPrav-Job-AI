import requests
import os
import random
import time
from bs4 import BeautifulSoup


# ─────────────────────────────────────────────────────────────────────────────
# Anti-bot jitter helper
# ─────────────────────────────────────────────────────────────────────────────

def _jitter(min_s: float = 1.5, max_s: float = 4.0) -> None:
    """
    Sleeps for a randomised interval to mimic human-speed interaction.
    Called between every significant browser action (navigate, fill, click).
    Prevents the machine-speed fingerprint that Cloudflare and ATS bot-detection
    flag as automated traffic.
    """
    delay = random.uniform(min_s, max_s)
    time.sleep(delay)


# ─────────────────────────────────────────────────────────────────────────────
# Greenhouse submitter
# ─────────────────────────────────────────────────────────────────────────────

def apply_to_greenhouse(job_url: str, personal_info: dict, resume_path: str) -> bool:
    """
    Submits a multipart/form-data application to a Greenhouse job board.
    Jitter is applied between each major action to avoid bot detection.

    Note: This currently uses requests (not a full Playwright browser session).
    The jitter here prevents machine-speed bursts between requests calls.
    A full Playwright upgrade is the next evolution for pages with JS-rendered
    forms or CAPTCHA checkpoints.
    """
    try:
        if not os.path.exists(resume_path):
            print(f"[Greenhouse] Resume file not found at {resume_path}")
            return False

        session = requests.Session()
        session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        })

        # Step 1: Fetch page to extract CSRF token (jitter before first request)
        _jitter()
        print(f"[Greenhouse] Fetching application page: {job_url}")
        response = session.get(job_url, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        token_input = soup.find('input', {'name': 'authenticity_token'})
        token = token_input['value'] if token_input else ''

        # Step 2: Jitter before form fill (simulates reading the page)
        _jitter()

        # Step 3: Prepare form data
        name_parts = personal_info.get('name', '').split(' ', 1)
        first_name = name_parts[0] if name_parts else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        data = {
            'authenticity_token': token,
            'job_board_url': job_url,
            'first_name': first_name,
            'last_name': last_name,
            'email': personal_info.get('email', ''),
            'phone': personal_info.get('phone', ''),
        }

        # Step 4: Jitter before the actual submit click
        _jitter(2.0, 5.0)

        print(f"[Greenhouse] Submitting application for {personal_info.get('name')} to {job_url}")
        post_url = job_url.rstrip('/') + '/'
        with open(resume_path, 'rb') as resume_file:
            res = session.post(
                post_url,
                data=data,
                files={'resume': resume_file},
                timeout=30
            )

        if res.status_code in [200, 201]:
            print("[Greenhouse] Application submitted successfully.")
            return True
        else:
            print(f"[Greenhouse] Submission failed — HTTP {res.status_code}")
            return False

    except Exception as e:
        print(f"[Greenhouse] Exception during submission: {e}")
        return False
