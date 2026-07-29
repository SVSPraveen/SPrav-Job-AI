import json
import logging
import os
import sys
import time
import hashlib
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from engine.utils import get_data_dir

logging.basicConfig(level=logging.ERROR, stream=sys.stderr)
logger = logging.getLogger(__name__)

def get_snapshot_path(company_name: str) -> str:
    import re
    slug = re.sub(r'[^a-z0-9]', '_', company_name.lower())
    snapshots_dir = os.path.join(get_data_dir(), 'snapshots')
    os.makedirs(snapshots_dir, exist_ok=True)
    return os.path.join(snapshots_dir, f"{slug}.json")

def load_snapshot(company_name: str) -> dict:
    p = get_snapshot_path(company_name)
    if not os.path.exists(p):
        return {"hash": None, "jobs": []}
    try:
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {"hash": None, "jobs": []}

def save_snapshot(company_name: str, hash_val: str, jobs: list):
    p = get_snapshot_path(company_name)
    from datetime import datetime
    with open(p, 'w', encoding='utf-8') as f:
        json.dump({"hash": hash_val, "jobs": jobs, "updated_at": datetime.utcnow().isoformat()}, f, indent=2)

def hash_content(s: str) -> str:
    return hashlib.md5(s.encode('utf-8')).hexdigest()

def extract_jobs(page, company_url):
    return page.evaluate("""(baseUrl) => {
        const selectors = [
            'a[href*="job"]', 'a[href*="position"]', 'a[href*="career"]', 'a[href*="opening"]',
            '[class*="job"] a', '[class*="position"] a', '[class*="role"] a', '[class*="listing"] a',
            '[data-job-id] a', 'li a',
        ];
        const seen = new Set();
        const jobs = [];
        for (const sel of selectors) {
            const els = Array.from(document.querySelectorAll(sel));
            for (const el of els) {
                const title = el.innerText ? el.innerText.trim() : '';
                const href = el.href || '';
                if (title.length < 5 || title.length > 200) continue;
                if (!href || seen.has(href)) continue;
                const lower = title.toLowerCase();
                if (['home', 'about', 'contact', 'login', 'sign in', 'sign up', 'blog', 'help'].includes(lower)) continue;
                seen.add(href);
                jobs.push({ title, url: href });
            }
        }
        return jobs;
    }""", company_url)

def watch_all() -> list:
    watchlist_path = os.path.join(get_data_dir(), 'watchlist.json')
    if not os.path.exists(watchlist_path):
        logger.error('watchlist.json not found')
        sys.exit(1)
        
    try:
        with open(watchlist_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            companies = data.get('companies', [])
    except Exception as e:
        logger.error(f'Error reading watchlist.json: {e}')
        sys.exit(1)
        
    all_new_jobs = []
    stealth = Stealth()
    
    try:
        with sync_playwright() as p:
            with p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            ) as browser:
                for company in companies:
                    name = company.get('name')
                    careers_url = company.get('careers_url')
                    if not name or not careers_url:
                        continue
                        
                    logger.error(f"[Watcher] Checking: {name}")
                    context = browser.new_context()
                    page = context.new_page()
                    stealth.apply_stealth_sync(page)
                    
                    try:
                        page.goto(careers_url, wait_until='domcontentloaded', timeout=30000)
                        time.sleep(3)
                        
                        jobs = extract_jobs(page, careers_url)
                        
                        if not jobs:
                            logger.error(f"[Watcher] {name}: No jobs extracted (may need custom selector)")
                            continue
                            
                        # Sort jobs to create stable hash
                        sorted_jobs = sorted(jobs, key=lambda x: x['url'])
                        content_str = "\n".join(f"{j['title']}|{j['url']}" for j in sorted_jobs)
                        live_hash = hash_content(content_str)
                        
                        snapshot = load_snapshot(name)
                        
                        if snapshot.get('hash') == live_hash:
                            logger.error(f"[Watcher] {name}: No changes ({len(jobs)} jobs, hash unchanged)")
                        else:
                            snapshot_urls = {j['url'] for j in snapshot.get('jobs', [])}
                            if snapshot.get('hash') is None:
                                new_jobs = [] # First run — just save baseline
                            else:
                                new_jobs = [j for j in jobs if j['url'] not in snapshot_urls]
                                
                            if new_jobs:
                                logger.error(f"[Watcher] {name}: 🚨 {len(new_jobs)} NEW job(s) detected!")
                                for job in new_jobs:
                                    all_new_jobs.append({
                                        "title": job['title'],
                                        "company": name,
                                        "url": job['url'],
                                        "source": 'company_watcher',
                                        "location": 'India'
                                    })
                            else:
                                logger.error(f"[Watcher] {name}: Hash changed but no new unique URLs (page re-ordered or UI update)")
                                
                            save_snapshot(name, live_hash, jobs)
                            
                    except Exception as e:
                        logger.error(f"[Watcher] {name}: ERROR — {e}")
                    finally:
                        page.close()
    except Exception as e:
        logger.error(f"Career watcher fatal error: {e}")
        
    return all_new_jobs

if __name__ == "__main__":
    try:
        res = watch_all()
        print(json.dumps(res))
    except Exception as e:
        logger.error(f'Career watcher fatal error: {e}')
        print('[]')
        sys.exit(1)
