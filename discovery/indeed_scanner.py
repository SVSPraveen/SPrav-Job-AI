import subprocess
import os
from engine.utils import get_node_path, get_data_dir

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
        env = os.environ.copy()
        env["SPRAV_DATA_DIR"] = get_data_dir()
        subprocess.run(
            [get_node_path(), script_path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=300,
            env=env
        )
        print("[Indeed Scanner] Stealth Crawler finished successfully.")
    except Exception as e:
        print(f"[Indeed Scanner] Error running crawler: {e}")
        
    return []
