import requests
import os
import uuid
import json
import subprocess

def load_targeting() -> dict:
    return {"target_locations": ["Remote", "Worldwide"]}

def is_target_location(job_location: str, target_locations: list) -> bool:
    """Checks if the job location matches any of our target locations."""
    if not job_location:
        return False
    job_loc_lower = job_location.lower()
    for target in target_locations:
        if target.lower() in job_loc_lower:
            return True
    return False

def scrape_arbeitnow() -> list:
    """Scrapes the free Arbeitnow API for remote jobs."""
    url = "https://arbeitnow.com/api/job-board-api"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Failed to fetch Arbeitnow: {e}")
        return []

    targeting = load_targeting()
    target_locations = targeting.get("target_locations", ["Remote"])
    
    scraped_jobs = []
    for item in data.get("data", []):
        location = item.get("location", "")
        # Fallback to check if it's explicitly remote
        if item.get("remote") and "Remote" in target_locations:
            pass # Valid
        elif not is_target_location(location, target_locations):
            continue # Skip job, doesn't match region

        job = {
            "id": f"arbeitnow_{item.get('slug', uuid.uuid4())}",
            "title": item.get("title", ""),
            "company": item.get("company_name", ""),
            "url": item.get("url", ""),
            "description": item.get("description", ""),
            "location": location,
            "source": "Arbeitnow",
            "fit_score": 0,
            "scam_flags": "",
            "status": "new"
        }
        scraped_jobs.append(job)
        
    return scraped_jobs

def scrape_remotive() -> list:
    """Scrapes Remotive for remote jobs."""
    url = "https://remotive.com/api/remote-jobs"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Failed to fetch Remotive: {e}")
        return []

    targeting = load_targeting()
    target_locations = targeting.get("target_locations", ["Remote"])
    
    scraped_jobs = []
    for item in data.get("jobs", [])[:30]:  # Limit to 30 for now
        location = item.get("candidate_required_location", "")
        if not is_target_location(location, target_locations) and "worldwide" not in location.lower():
            continue

        job = {
            "id": f"remotive_{item.get('id', uuid.uuid4())}",
            "title": item.get("title", ""),
            "company": item.get("company_name", ""),
            "url": item.get("url", ""),
            "description": item.get("description", ""),
            "location": location,
            "source": "Remotive",
            "fit_score": 0,
            "scam_flags": "",
            "status": "new"
        }
        scraped_jobs.append(job)
        
    return scraped_jobs

def scrape_remoteok() -> list:
    """Scrapes RemoteOK (using headers to bypass simple blocks)."""
    url = "https://remoteok.com/api"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Failed to fetch RemoteOK: {e}")
        return []

    targeting = load_targeting()
    target_locations = targeting.get("target_locations", ["Remote"])
    
    scraped_jobs = []
    # RemoteOK API returns a legal disclaimer as the first item
    for item in data[1:30]: 
        location = item.get("location", "")
        if not is_target_location(location, target_locations) and "worldwide" not in location.lower():
            continue

        job = {
            "id": f"remoteok_{item.get('id', uuid.uuid4())}",
            "title": item.get("position", ""),
            "company": item.get("company", ""),
            "url": item.get("url", ""),
            "description": item.get("description", ""),
            "location": location,
            "source": "RemoteOK",
            "fit_score": 0,
            "scam_flags": "",
            "status": "new"
        }
        scraped_jobs.append(job)
        
    return scraped_jobs

def scrape_freshershunt() -> list:
    """Uses Playwright/Puppeteer-extra to bypass ads and extract official links from Freshershunt."""
    print("Scraping Freshershunt via headless Node.js ad-bypasser...")
    js_script = os.path.join(os.path.dirname(__file__), "..", "scraper_service", "freshershunt_bypass.js")
    
    if not os.path.exists(js_script):
        print("Freshershunt JS scraper not found.")
        return []
        
    try:
        # We pass 10 as the limit
        result = subprocess.run(["node", js_script, "10"], capture_output=True, text=True, timeout=120)
        
        # The JS script outputs JSON on the very last line
        output = result.stdout.strip()
        # Find the last line that looks like an array
        json_str = "[]"
        for line in reversed(output.split('\n')):
            if line.startswith("[") and line.endswith("]"):
                json_str = line
                break
                
        data = json.loads(json_str)
    except Exception as e:
        print(f"Failed to execute Freshershunt scraper: {e}")
        return []

    scraped_jobs = []
    for item in data:
        job = {
            "id": f"freshershunt_{uuid.uuid4().hex[:8]}",
            "title": item.get("title", ""),
            "company": "Freshershunt Extracted", # Usually need deeper extraction for company name
            "url": item.get("url", ""),
            "description": f"Extracted from {item.get('original_post')}",
            "location": "India / Remote",
            "source": "Freshershunt",
            "fit_score": 0,
            "scam_flags": "",
            "status": "new"
        }
        scraped_jobs.append(job)
        
    return scraped_jobs

def run_all_scrapers() -> list:
    """Runs all configured scrapers and returns a combined list of jobs."""
    print("Scraping Arbeitnow...")
    jobs = scrape_arbeitnow()
    print("Scraping Remotive...")
    jobs.extend(scrape_remotive())
    print("Scraping RemoteOK...")
    jobs.extend(scrape_remoteok())
    
    print("Scraping Freshershunt...")
    jobs.extend(scrape_freshershunt())
    
    print(f"Total jobs discovered: {len(jobs)}")
    return jobs
