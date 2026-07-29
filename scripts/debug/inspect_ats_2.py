import sys
import re
from playwright.sync_api import sync_playwright

def inspect_ats_click_apply(url):
    print(f"Inspecting: {url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        
        # Click "Apply" if it exists
        try:
            btn = page.get_by_role("button", name=re.compile("apply", re.IGNORECASE)).first
            if btn:
                print("Found Apply button, clicking...")
                btn.click()
                page.wait_for_timeout(3000)
        except Exception as e:
            print(f"No simple apply button found: {e}")
            
        try:
            btn = page.get_by_role("link", name=re.compile("apply", re.IGNORECASE)).first
            if btn:
                print("Found Apply link, clicking...")
                btn.click()
                page.wait_for_timeout(3000)
        except Exception as e:
            pass
            
        print("Final URL:", page.url)
        
        # Extract all input fields
        inputs = page.evaluate('''() => {
            return Array.from(document.querySelectorAll('input, select, textarea, button')).map(el => {
                let text = el.innerText || el.value || '';
                if(el.tagName === 'BUTTON') {
                    text = el.textContent.trim();
                }
                return {
                    tag: el.tagName,
                    type: el.type,
                    id: el.id,
                    name: el.name,
                    aria_label: el.getAttribute('aria-label'),
                    text: text.substring(0, 50)
                };
            });
        }''')
        
        for i in inputs:
            if i['type'] != 'hidden':
                print(i)
                
        browser.close()

if __name__ == "__main__":
    inspect_ats_click_apply("https://jobs.smartrecruiters.com/WesternDigital/744000138717897-software-engineer")
    print("\n-----------------------\n")
    inspect_ats_click_apply("https://jobs.ashbyhq.com/Valon/580ec8b6-c894-497e-9769-270e6e21efbe")
