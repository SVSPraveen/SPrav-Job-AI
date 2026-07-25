import subprocess
import os

def run_indeed_scanner() -> list:
    """
    Triggers the Node.js Stealth Crawler for Indeed to bypass Cloudflare captchas.
    The crawler extracts raw job data and pushes it to the /api/jobs/bulk endpoint,
    where the AI (NuExtract) structures it and places it in the Action Required queue.
    """
    print("[Indeed Scanner] Launching Stealth Node.js Crawler for Indeed...")
    
    script_path = os.path.join("scraper_service", "stealth_crawler.js")
    if not os.path.exists(script_path):
        print("[Indeed Scanner] stealth_crawler.js not found.")
        return []

    try:
        # The stealth crawler automatically posts to the backend API,
        # so this Python wrapper simply orchestrates the execution.
        subprocess.run(
            ["node", script_path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=300
        )
        print("[Indeed Scanner] Stealth Crawler finished successfully.")
    except Exception as e:
        print(f"[Indeed Scanner] Error running crawler: {e}")
        
    return []
