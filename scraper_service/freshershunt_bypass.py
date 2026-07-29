import json
import logging
import sys
import time
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

def scrape_freshershunt(limit: int = 10) -> list:
    jobs = []
    stealth = Stealth()
    
    try:
        with sync_playwright() as p:
            with p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-web-security']
            ) as browser:
                context = browser.new_context()
                page = context.new_page()
                stealth.apply_stealth_sync(page)
                
                # We can't trivially adblock like puppeteer-extra-plugin-adblocker, 
                # but Playwright's router can abort image/media requests if needed.
                page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media", "font"] else route.continue_())
                
                page.goto('https://www.freshershunt.com/', wait_until='domcontentloaded', timeout=60000)
                
                post_links = page.evaluate("""() => {
                    const links = Array.from(document.querySelectorAll('h2 a, h3 a, article a'));
                    return links.map(a => ({ title: a.innerText, url: a.href })).filter(j => j.url && j.title);
                }""")
                
                unique_links = {}
                for post in post_links:
                    if post['url'] not in unique_links:
                        unique_links[post['url']] = post
                
                posts_to_process = list(unique_links.values())[:limit]
                
                for post in posts_to_process:
                    job_page = context.new_page()
                    stealth.apply_stealth_sync(job_page)
                    try:
                        job_page.goto(post['url'], wait_until='domcontentloaded', timeout=30000)
                        
                        apply_link = job_page.evaluate("""() => {
                            const buttons = Array.from(document.querySelectorAll('a'));
                            const applyBtn = buttons.find(b => {
                                const t = b.innerText.toLowerCase();
                                return t.includes('apply') || t.includes('click here') || t.includes('registration link');
                            });
                            return applyBtn ? applyBtn.href : null;
                        }""")
                        
                        if apply_link:
                            job_page.goto(apply_link, wait_until='domcontentloaded', timeout=30000)
                            time.sleep(6)
                            
                            final_url = job_page.evaluate("""() => {
                                const skipBtn = document.querySelector('.skip-btn, #skip, a.get-link, a#getlink');
                                if (skipBtn && skipBtn.href) return skipBtn.href;
                                return window.location.href; 
                            }""")
                            
                            if 'freshershunt.com' not in final_url:
                                jobs.append({
                                    "title": post['title'],
                                    "source": 'freshershunt',
                                    "url": final_url,
                                    "original_post": post['url']
                                })
                    except Exception:
                        pass
                    finally:
                        job_page.close()
    except Exception as e:
        logger.error(f"Failed to scrape Freshershunt: {e}")
        
    return jobs

if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    res = scrape_freshershunt(limit)
    print(json.dumps(res))
