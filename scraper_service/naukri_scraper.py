import json
import logging
import os
import random
import time
from urllib.parse import quote_plus
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from engine.utils import get_data_dir

logger = logging.getLogger(__name__)

def load_seen(seen_path: str) -> set:
    if not os.path.exists(seen_path):
        return set()
    try:
        with open(seen_path, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    except Exception:
        return set()

def save_seen(seen_path: str, seen: set):
    arr = list(seen)[-2000:]
    try:
        os.makedirs(os.path.dirname(seen_path), exist_ok=True)
        with open(seen_path, 'w', encoding='utf-8') as f:
            json.dump(arr, f)
    except Exception as e:
        logger.error(f"[naukri_scraper.py] Failed to save seen jobs: {e}")

def scrape_naukri(keyword: str = 'software developer', limit: int = 30) -> list:
    snapshots_dir = os.path.join(get_data_dir(), "snapshots")
    seen_path = os.path.join(snapshots_dir, "naukri_seen.json")
    seen = load_seen(seen_path)
    
    encoded = quote_plus(keyword).lower().replace('+', '-')
    url = f"https://www.naukri.com/{encoded}-jobs?k={quote_plus(keyword)}&experience=0&freshness=1"
    
    logger.info(f"[Naukri] Searching: \"{keyword}\" | URL: {url}")
    
    jobs = []
    stealth = Stealth()
    
    try:
        with sync_playwright() as p:
            with p.chromium.launch(
                channel="chrome",
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-blink-features=AutomationControlled']
            ) as browser:
                context = browser.new_context(
                    viewport={"width": 1366, "height": 768}
                )
                page = context.new_page()
                stealth.apply_stealth_sync(page)
                
                page.goto(url, wait_until='domcontentloaded', timeout=45000)
                time.sleep(3)
                
                # Human-like scroll
                for _ in range(4):
                    page.evaluate("window.scrollBy(0, window.innerHeight * 0.7)")
                    time.sleep(1.2)
                
                with open("naukri_debug.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
                
                # We do the exact JS logic from JS version
                extracted = page.evaluate("""(lim) => {
                    const cards = Array.from(document.querySelectorAll('.jobTuple, article.jobListingCard, [class*="job-card"], [class*="jobCard"]'));
                    const results = [];

                    for (const card of cards.slice(0, lim)) {
                        const titleEl = card.querySelector('[class*="title"], h2, h3, .job-title');
                        const title = titleEl ? titleEl.innerText.trim() : '';
                        if (!title) continue;

                        const compEl = card.querySelector('[class*="company"], [class*="org-name"], .company-name');
                        const company = compEl ? compEl.innerText.trim() : '';

                        const locEl = card.querySelector('[class*="location"], [class*="loc"]');
                        const location = locEl ? locEl.innerText.trim() : '';

                        const expEl = card.querySelector('[class*="exp"]');
                        const experience = expEl ? expEl.innerText.trim() : '';

                        const linkEl = card.querySelector('a[href*="naukri.com"]') || card.querySelector('a');
                        const url = linkEl ? linkEl.href : '';

                        let jobId = Math.random().toString(36).slice(2);
                        const idMatch1 = url.match(/jid=(\\d+)/);
                        const idMatch2 = url.match(/-(\\d+)\\?/);
                        if (idMatch1) jobId = idMatch1[1];
                        else if (idMatch2) jobId = idMatch2[1];

                        results.push({ title, company, location, experience, url, jobId });
                    }
                    return results;
                }""", limit)
                
                logger.info(f"[Naukri] Extracted {len(extracted)} raw cards.")
                
                for item in extracted:
                    if item['jobId'] in seen:
                        continue
                    seen.add(item['jobId'])
                    
                    description = f"{item['title']} at {item['company']}. Location: {item['location']}. Experience: {item['experience']}"
                    
                    if item['url'] and str(item['url']).startswith('http'):
                        try:
                            jd_page = context.new_page()
                            stealth.apply_stealth_sync(jd_page)
                            jd_page.goto(item['url'], wait_until='domcontentloaded', timeout=20000)
                            time.sleep(1.5)
                            jd_text = jd_page.evaluate("""() => {
                                const el = document.querySelector('.job-desc, [class*="job-desc"], [class*="description"], .jd-desc');
                                return el ? el.innerText.substring(0, 3000) : '';
                            }""")
                            if jd_text:
                                description = jd_text
                            jd_page.close()
                        except Exception:
                            pass
                    
                    jobs.append({
                        "title": item['title'],
                        "company": item['company'],
                        "url": item['url'],
                        "description": description,
                        "location": item.get('location', 'India'),
                        "source": 'naukri'
                    })
                    
                    if len(jobs) >= limit:
                        break
                    time.sleep(0.8)
                    
        save_seen(seen_path, seen)
        logger.info(f"[Naukri] Done. {len(jobs)} new jobs found.")
    except Exception as e:
        logger.error(f"[Naukri] Error: {e}")
        
    return jobs

if __name__ == "__main__":
    import sys; logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    # For testing direct
    res = scrape_naukri(sys.argv[1] if len(sys.argv) > 1 else 'software developer', 3)
    print(json.dumps(res, indent=2))
