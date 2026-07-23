import requests
import os
import uuid
import json
import subprocess
from engine.jd_extractor import fetch_jd_text

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

def scrape_company_watchlist() -> list:
    """
    Runs career_watcher.js to detect NEW jobs on watched company career pages.
    Only returns jobs that are new since the last run (diff against stored snapshot).
    On first run for a company it saves the baseline and returns nothing, so the
    pipeline is never flooded on initial setup.
    """
    print("Running Company Career Page Watcher...")
    js_script = os.path.join(os.path.dirname(__file__), "..", "scraper_service", "career_watcher.js")

    if not os.path.exists(js_script):
        print("career_watcher.js not found — skipping.")
        return []

    try:
        result = subprocess.run(
            ["node", js_script],
            capture_output=True,
            text=True,
            timeout=300  # 5 min max — 20 companies × ~15s each
        )

        # career_watcher.js outputs one JSON array as the LAST line on stdout
        # All other output is diagnostic (goes to stderr)
        output = result.stdout.strip()
        if not output:
            print("Career watcher returned no output.")
            return []

        data = json.loads(output)
        print(f"Career watcher found {len(data)} new job(s) across watched companies.")
    except json.JSONDecodeError as e:
        print(f"Career watcher JSON parse error: {e}")
        return []
    except Exception as e:
        print(f"Career watcher execution failed: {e}")
        return []

    scraped_jobs = []
    for item in data:
        job_url = item.get("url", "")
        company = item.get("company", "")
        title = item.get("title", "Unknown Role")

        # Fetch the actual JD so the pipeline can score/tailor properly
        print(f"  [Watcher] Fetching JD for '{title}' @ {company}...")
        description = fetch_jd_text(job_url) or (
            f"{title} at {company}. This is a newly posted role detected on "
            f"the official career page. Apply promptly as stealth listings often close within hours."
        )

        job = {
            "id": f"watcher_{uuid.uuid4().hex[:10]}",
            "title": title,
            "company": company,
            "url": job_url,
            "description": description,
            "location": item.get("location", "India"),
            "source": "company_watcher",
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

    print("Checking Company Career Page Watchlist...")
    jobs.extend(scrape_company_watchlist())

    print("Scraping Naukri.com...")
    jobs.extend(scrape_naukri())

    print("Scraping Indeed India...")
    jobs.extend(scrape_portal("indeed", "indeed_scraper.js"))

    print("Scraping Internshala Jobs...")
    jobs.extend(scrape_portal("internshala", "internshala_scraper.js"))

    print("Scraping Hirist.tech (IT-Only)...")
    jobs.extend(scrape_portal("hirist", "hirist_scraper.js"))

    print("Scraping Wellfound (Startup Ecosystem)...")
    jobs.extend(scrape_portal("wellfound", "wellfound_scraper.js",
                              keywords=["software engineer", "backend engineer",
                                        "frontend engineer", "full stack engineer"]))

    print(f"Total jobs discovered: {len(jobs)}")
    return jobs

def scrape_naukri(keywords: list = None, limit_per_keyword: int = 20) -> list:
    """
    Runs naukri_scraper.js for each target keyword and returns new job listings.
    Keywords default to common SDE/tech roles if not specified.
    """
    if keywords is None:
        keywords = [
            "software developer",
            "backend developer",
            "frontend developer",
            "full stack developer",
            "python developer",
            "react developer",
        ]

    js_script = os.path.join(os.path.dirname(__file__), "..", "scraper_service", "naukri_scraper.js")
    if not os.path.exists(js_script):
        print("naukri_scraper.js not found — skipping.")
        return []

    all_jobs = []
    for keyword in keywords:
        print(f"  Naukri: '{keyword}'...")
        try:
            result = subprocess.run(
                ["node", js_script, keyword, str(limit_per_keyword)],
                capture_output=True,
                text=True,
                timeout=120
            )
            output = result.stdout.strip()
            if not output:
                continue
            data = json.loads(output)
            for item in data:
                all_jobs.append({
                    "id": f"naukri_{uuid.uuid4().hex[:10]}",
                    "title": item.get("title", ""),
                    "company": item.get("company", ""),
                    "url": item.get("url", ""),
                    "description": item.get("description", ""),
                    "location": item.get("location", "India"),
                    "source": "Naukri",
                    "fit_score": 0,
                    "scam_flags": "",
                    "status": "new"
                })
        except json.JSONDecodeError as e:
            print(f"  Naukri JSON parse error for '{keyword}': {e}")
        except Exception as e:
            print(f"  Naukri scraper failed for '{keyword}': {e}")

    print(f"  Naukri: {len(all_jobs)} total new jobs found.")
    return all_jobs


DEFAULT_KEYWORDS = [
    "software developer",
    "backend developer",
    "full stack developer",
    "python developer",
    "react developer",
]


def scrape_portal(source_name: str, js_file: str, keywords: list = None, limit_per_keyword: int = 20) -> list:
    """
    Generic runner for Node.js portal scrapers (Indeed, Internshala, etc.).
    Calls the JS scraper per keyword, collects results, returns normalized jobs.
    """
    if keywords is None:
        keywords = DEFAULT_KEYWORDS

    js_script = os.path.join(os.path.dirname(__file__), "..", "scraper_service", js_file)
    if not os.path.exists(js_script):
        print(f"  {js_file} not found — skipping {source_name}.")
        return []

    all_jobs = []
    for keyword in keywords:
        print(f"  {source_name}: '{keyword}'...")
        try:
            result = subprocess.run(
                ["node", js_script, keyword, str(limit_per_keyword)],
                capture_output=True,
                text=True,
                timeout=120,
                env={**__import__('os').environ}
            )
            output = result.stdout.strip()
            if not output:
                continue
            data = json.loads(output)
            for item in data:
                all_jobs.append({
                    "id": f"{source_name}_{uuid.uuid4().hex[:10]}",
                    "title": item.get("title", ""),
                    "company": item.get("company", ""),
                    "url": item.get("url", ""),
                    "description": item.get("description", ""),
                    "location": item.get("location", "India"),
                    "source": source_name.capitalize(),
                    "fit_score": 0,
                    "scam_flags": "",
                    "status": "new"
                })
        except json.JSONDecodeError as e:
            print(f"  {source_name} JSON parse error for '{keyword}': {e}")
        except Exception as e:
            print(f"  {source_name} scraper failed for '{keyword}': {e}")

    print(f"  {source_name}: {len(all_jobs)} new jobs found.")
    return all_jobs
