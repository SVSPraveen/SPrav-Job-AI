import sys
from playwright.sync_api import sync_playwright

def inspect_smartrecruiters(url):
    print(f"\nInspecting SmartRecruiters: {url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        
        btn = page.get_by_role("button", name="I'm interested").first
        if btn:
            print("Found 'I\\'m interested' button, clicking...")
            btn.click()
            page.wait_for_timeout(3000)
        else:
            print("Button not found!")
            
        inputs = page.evaluate('''() => {
            return Array.from(document.querySelectorAll('input, select, textarea, button')).map(el => {
                let text = el.innerText || el.value || '';
                if(el.tagName === 'BUTTON') text = el.textContent.trim();
                return {
                    tag: el.tagName,
                    type: el.type,
                    id: el.id,
                    name: el.name,
                    text: text.substring(0, 50)
                };
            });
        }''')
        
        for i in inputs:
            if i['type'] != 'hidden':
                print(i)
                
        browser.close()

if __name__ == "__main__":
    inspect_smartrecruiters("https://jobs.smartrecruiters.com/WesternDigital/744000138717897-software-engineer")
