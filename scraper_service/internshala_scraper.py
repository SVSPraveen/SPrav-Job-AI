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
        logger.error(f"[internshala_scraper.py] Failed to save seen jobs: {e}")

def scrape_internshala(keyword: str = 'software developer', limit: int = 20) -> list:
    snapshots_dir = os.path.join(get_data_dir(), "snapshots")
    seen_path = os.path.join(snapshots_dir, "internshala_seen.json")
    seen = load_seen(seen_path)
    
    import re
    slug = re.sub(r'\s+', '-', keyword.lower())
    url = f"https://internshala.com/jobs/{slug}-jobs"
    
    logger.info(f"[Internshala] Searching: \"{keyword}\"")
    
    jobs = []
    stealth = Stealth()
    
    try:
        with sync_playwright() as p:
            with p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-blink-features=AutomationControlled']
            ) as browser:
                context = browser.new_context(viewport={"width": 1366, "height": 768})
                page = context.new_page()
                stealth.apply_stealth_sync(page)
                
                page.goto(url, wait_until='domcontentloaded', timeout=40000)
                time.sleep(3)
                
                for _ in range(3):
                    page.evaluate("window.scrollBy(0, window.innerHeight)")
                    time.sleep(1)
                
                extracted = page.evaluate("""(lim) => {
                    const results = [];
                    const items = Array.from(document.querySelectorAll('.job-internship-card, [class*="container"][data-internship_id], .individual_internship'));

                    for (const item of items.slice(0, lim)) {
                        const titleEl = item.querySelector('.job-title, .profile, h3');
                        const companyEl = item.querySelector('.company-name, .company');
                        const locationEl = item.querySelector('.locations span, .location_link, [class*="location"]');
                        const linkEl = item.querySelector('a[href*="/jobs/detail"], a[href*="/job/"]') || item.querySelector('a');

                        const title = titleEl ? titleEl.innerText.trim() : '';
                        const company = companyEl ? companyEl.innerText.trim() : '';
                        const location = locationEl ? locationEl.innerText.trim() : '';
                        const href = linkEl ? (linkEl.href.startsWith('http') ? linkEl.href : `https://internshala.com${linkEl.getAttribute('href')}`) : '';
                        const idMatch = href.match(/\\/jobs\\/detail\\/(\\d+)/) || href.match(/job\\/(\\d+)/);
                        const jobId = idMatch ? idMatch[1] : href;

                        if (title && href) {
                            results.push({ title, company, location, url: href, jobId });
                        }
                    }
                    return results;
                }""", limit)
                
                logger.info(f"[Internshala] Got {len(extracted)} cards.")
                
                for item in extracted:
                    if item['jobId'] in seen:
                        continue
                    seen.add(item['jobId'])
                    
                    description = f"{item['title']} at {item['company']}. Location: {item['location']}"
                    
                    if str(item['url']).startswith('http'):
                        try:
                            jd_page = context.new_page()
                            stealth.apply_stealth_sync(jd_page)
                            jd_page.goto(item['url'], wait_until='domcontentloaded', timeout=20000)
                            time.sleep(1.5)
                            jd_text = jd_page.evaluate("""() => {
                                const el = document.querySelector('.job_description, .internship_other_details_container, [class*="about_company"], .about_internship');
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
                        "location": item.get('location') or 'India',
                        "source": 'internshala'
                    })
                    time.sleep(0.6)
                    
        save_seen(seen_path, seen)
        logger.info(f"[Internshala] Done. {len(jobs)} new jobs.")
    except Exception as e:
        logger.error(f"[Internshala] Error: {e}")
        
    return jobs

if __name__ == "__main__":
    import sys
    res = scrape_internshala(sys.argv[1] if len(sys.argv) > 1 else 'software developer', int(sys.argv[2]) if len(sys.argv) > 2 else 20)
    print(json.dumps(res))
