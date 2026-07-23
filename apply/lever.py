import requests
import os
import random
import time


# ─────────────────────────────────────────────────────────────────────────────
# Anti-bot jitter helper (shared with greenhouse.py)
# ─────────────────────────────────────────────────────────────────────────────

def _jitter(min_s: float = 1.5, max_s: float = 4.0) -> None:
    """
    Sleeps for a randomised interval to mimic human-speed interaction.
    Called between every significant browser action (navigate, fill, click).
    """
    delay = random.uniform(min_s, max_s)
    time.sleep(delay)


# ─────────────────────────────────────────────────────────────────────────────
# Lever submitter
# ─────────────────────────────────────────────────────────────────────────────

def apply_to_lever(job_url: str, personal_info: dict, resume_path: str) -> bool:
    """
    Submits a multipart/form-data application to a Lever job board.
    Jitter is applied between each major action to avoid bot detection.

    Lever apply URLs follow the pattern:
        jobs.lever.co/<company>/<job-id>/apply

    Note: This uses requests. A Playwright upgrade is the next step for
    pages with JS-rendered forms or CAPTCHA checkpoints.
    """
    try:
        if not os.path.exists(resume_path):
            print(f"[Lever] Resume file not found at {resume_path}")
            return False

        # Step 1: Jitter before any network activity (simulates human arriving at page)
        _jitter()

        apply_url = job_url.rstrip('/') + '/apply'
        print(f"[Lever] Preparing submission for {personal_info.get('name')} to {apply_url}")

        # Step 2: Jitter before filling in the form (simulates reading the page)
        _jitter()

        data = {
            'name': personal_info.get('name', ''),
            'email': personal_info.get('email', ''),
            'phone': personal_info.get('phone', ''),
        }

        # Step 3: Jitter before clicking submit
        _jitter(2.0, 5.0)

        print(f"[Lever] Submitting to {apply_url}...")
        with open(resume_path, 'rb') as resume_file:
            response = requests.post(
                apply_url,
                data=data,
                files={'resume': resume_file},
                timeout=30,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    )
                }
            )

        if response.status_code in [200, 201]:
            print("[Lever] Application submitted successfully.")
            return True
        else:
            print(f"[Lever] Submission failed — HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"[Lever] Exception during submission: {e}")
        return False
