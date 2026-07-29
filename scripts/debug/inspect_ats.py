import sys
from playwright.sync_api import sync_playwright

def inspect_ats(url):
    print(f"Inspecting: {url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        
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
    inspect_ats("https://jobs.smartrecruiters.com/WesternDigital/744000138717897-software-engineer")
    print("\n-----------------------\n")
    inspect_ats("https://jobs.ashbyhq.com/Valon/580ec8b6-c894-497e-9769-270e6e21efbe")
