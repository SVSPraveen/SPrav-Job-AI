import sys
from playwright.sync_api import sync_playwright

def inspect_buttons(url):
    print(f"\nInspecting buttons for: {url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        
        buttons = page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a, button, [role="button"]')).map(el => {
                return (el.innerText || el.textContent || '').trim().replace(/\\n/g, ' ');
            }).filter(t => t.length > 0 && t.length < 50);
        }''')
        
        # Deduplicate and print
        for b in sorted(list(set(buttons))):
            print(f"- {b}")
                
        browser.close()

if __name__ == "__main__":
    inspect_buttons("https://jobs.smartrecruiters.com/WesternDigital/744000138717897-software-engineer")
    inspect_buttons("https://jobs.ashbyhq.com/Valon/580ec8b6-c894-497e-9769-270e6e21efbe")
