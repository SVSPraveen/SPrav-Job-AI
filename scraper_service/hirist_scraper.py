import json
import logging
import os
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
        logger.error(f"[hirist_scraper.py] Failed to save seen jobs: {e}")

def scrape_hirist(keyword: str = 'software developer', limit: int = 25) -> list:
    snapshots_dir = os.path.join(get_data_dir(), "snapshots")
    seen_path = os.path.join(snapshots_dir, "hirist_seen.json")
    seen = load_seen(seen_path)
    
    import re
    slug = re.sub(r'[^a-z0-9-]', '', re.sub(r'\s+', '-', keyword.lower()))
    url = f"https://www.hirist.tech/search-jobs/{slug}"
    
    logger.info(f"[Hirist] Searching: \"{keyword}\" → {url}")
    
    jobs = []
    stealth = Stealth()
    
    try:
        with sync_playwright() as p:
            with p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-blink-features=AutomationControlled']
            ) as browser:
                context = browser.new_context(viewport={"width": 1366, "height": 768}, extra_http_headers={'Accept-Language': 'en-US,en;q=0.9'})
                page = context.new_page()
                stealth.apply_stealth_sync(page)
                
                page.goto(url, wait_until='domcontentloaded', timeout=40000)
                time.sleep(3)
                
                for _ in range(4):
                    page.evaluate("window.scrollBy(0, window.innerHeight * 0.8)")
                    time.sleep(1)
                
                extracted = page.evaluate("""(lim) => {
                    const results = [];
                    const items = Array.from(document.querySelectorAll('.job-listing-card, .job-card, [class*="job-item"], [class*="jobCard"], article'));

                    for (const item of items.slice(0, lim)) {
                        const titleEl = item.querySelector('h2, h3, .job-title, [class*="title"]');
                        const compEl  = item.querySelector('.company-name, [class*="company"]');
                        const locEl   = item.querySelector('.location, [class*="location"], [class*="loc"]');
                        const linkEl  = item.querySelector('a[href*="hirist.tech"], a[href*="/job/"], a');
                        const expEl   = item.querySelector('[class*="exp"], [class*="experience"]');
                        const salEl   = item.querySelector('[class*="salary"], [class*="sal"]');

                        const title   = titleEl ? titleEl.innerText.trim() : '';
                        const company = compEl  ? compEl.innerText.trim()  : '';
                        const loc     = locEl   ? locEl.innerText.trim()   : '';
                        const href    = linkEl  ? (linkEl.href.startsWith('http') ? linkEl.href : `https://www.hirist.tech${linkEl.getAttribute('href')}`) : '';
                        const exp     = expEl   ? expEl.innerText.trim()   : '';
                        const salary  = salEl   ? salEl.innerText.trim()   : '';

                        const idMatch = href.match(/\\/job\\/([^\\/?\\s]+)/);
                        const jobId   = idMatch ? idMatch[1] : href;

                        if (title && href && jobId) {
                            results.push({ title, company, location: loc, url: href, jobId, experience: exp, salary });
                        }
                    }
                    return results;
                }""", limit)
                
                logger.info(f"[Hirist] Found {len(extracted)} cards.")
                
                for item in extracted:
                    if item['jobId'] in seen:
                        continue
                    seen.add(item['jobId'])
                    
                    description = f"{item['title']} at {item['company']}. Location: {item['location']}. Experience: {item['experience']}. Salary: {item['salary']}."
                    
                    if str(item['url']).startswith('http'):
                        try:
                            jd_page = context.new_page()
                            stealth.apply_stealth_sync(jd_page)
                            jd_page.goto(item['url'], wait_until='domcontentloaded', timeout=20000)
                            time.sleep(1.5)
                            jd_text = jd_page.evaluate("""() => {
                                const el = document.querySelector('.job-description, [class*="job-desc"], [class*="description"], .jd-content, .about-job, main');
                                return el ? el.innerText.substring(0, 3500) : '';
                            }""")
                            if jd_text and len(jd_text) > 100:
                                description = jd_text
                            jd_page.close()
                        except Exception:
                            pass
                    
                    jobs.append({
                        "title": item['title'],
                        "company": item['company'],
                        "url": item['url'],
                        "description": description,
                        "location": item.get('location') or 'India',
                        "source": 'hirist'
                    })
                    
                    time.sleep(0.7)
                    
        save_seen(seen_path, seen)
        logger.info(f"[Hirist] Done. {len(jobs)} new jobs.")
    except Exception as e:
        logger.error(f"[Hirist] Error: {e}")
        
    return jobs

if __name__ == "__main__":
    import sys
    res = scrape_hirist(sys.argv[1] if len(sys.argv) > 1 else 'software developer', int(sys.argv[2]) if len(sys.argv) > 2 else 25)
    print(json.dumps(res))
