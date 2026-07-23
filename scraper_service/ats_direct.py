import httpx
import sqlite3
import random
import time

DB_PATH = "../jobs.db"
# Public datasets of companies that use Greenhouse and Lever
DATASET_BASE = "https://raw.githubusercontent.com/Feashliaa/job-board-aggregator/main/data"

def fetch_companies():
    """Fetches the latest list of Greenhouse and Lever companies."""
    try:
        greenhouse_resp = httpx.get(f"{DATASET_BASE}/greenhouse_companies.json", timeout=10)
        lever_resp = httpx.get(f"{DATASET_BASE}/lever_companies.json", timeout=10)
        return greenhouse_resp.json(), lever_resp.json()
    except Exception as e:
        print(f"Error fetching company datasets: {e}")
        return [], []

def scan_greenhouse(company: str, keywords: list) -> list:
    url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
    try:
        resp = httpx.get(url, timeout=5)
        if resp.status_code != 200:
            return []
        
        data = resp.json()
        jobs = []
        for j in data.get('jobs', []):
            title = j.get('title', '').lower()
            if any(k.lower() in title for k in keywords):
                jobs.append({
                    "title": j.get('title', ''),
                    "company": company,
                    "url": j.get('absolute_url', ''),
                    "location": j.get('location', {}).get('name', ''),
                    "description": "" # Greenhouse doesn't send desc in the list API, requires individual fetch
                })
        return jobs
    except Exception:
        return []

def scan_lever(company: str, keywords: list) -> list:
    url = f"https://api.lever.co/v0/postings/{company}"
    try:
        resp = httpx.get(url, timeout=5)
        if resp.status_code != 200:
            return []
        
        data = resp.json()
        jobs = []
        for j in data:
            title = j.get('text', '').lower()
            if any(k.lower() in title for k in keywords):
                jobs.append({
                    "title": j.get('text', ''),
                    "company": company,
                    "url": j.get('hostedUrl', ''),
                    "location": j.get('categories', {}).get('location', ''),
                    "description": j.get('descriptionPlain', '') # Lever includes full desc!
                })
        return jobs
    except Exception:
        return []

def run_ats_discovery(keywords=["engineer", "developer", "react", "python", "backend", "frontend"]):
    greenhouse_list, lever_list = fetch_companies()
    
    print(f"Loaded {len(greenhouse_list)} Greenhouse companies and {len(lever_list)} Lever companies.")
    
    # Shuffle and pick a small sample to avoid taking hours
    random.shuffle(greenhouse_list)
    random.shuffle(lever_list)
    
    sample_gh = greenhouse_list[:20]
    sample_lv = lever_list[:20]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    discovered_count = 0
    
    for comp in sample_gh:
        print(f"Scanning Greenhouse: {comp}")
        jobs = scan_greenhouse(comp, keywords)
        for job in jobs:
            try:
                cursor.execute(
                    "INSERT INTO jobs (title, company, description, url, status) VALUES (?, ?, ?, ?, ?)",
                    (job['title'], job['company'], job['description'], job['url'], 'new')
                )
                discovered_count += 1
            except sqlite3.IntegrityError:
                pass # URL is UNIQUE in DB
        time.sleep(0.5)
        
    for comp in sample_lv:
        print(f"Scanning Lever: {comp}")
        jobs = scan_lever(comp, keywords)
        for job in jobs:
            try:
                cursor.execute(
                    "INSERT INTO jobs (title, company, description, url, status) VALUES (?, ?, ?, ?, ?)",
                    (job['title'], job['company'], job['description'], job['url'], 'new')
                )
                discovered_count += 1
            except sqlite3.IntegrityError:
                pass
        time.sleep(0.5)
        
    conn.commit()
    conn.close()
    
    print(f"ATS Discovery Complete. Found {discovered_count} matching jobs.")

if __name__ == "__main__":
    run_ats_discovery()
