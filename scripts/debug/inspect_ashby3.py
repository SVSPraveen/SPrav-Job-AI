import sys
from playwright.sync_api import sync_playwright

def inspect_ashby(url):
    print(f"\n--- Inspecting Ashby: {url} ---")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        try:
            page.wait_for_selector('input', timeout=10000)
        except:
            pass
        
        print("Page Title:", page.title())
        html = page.content()
        import re
        inputs = re.findall(r'<input[^>]*>', html)
        print(f"Found {len(inputs)} inputs. First 10:")
        for inp in inputs[:10]:
            print(inp)
            
        print("Body text snippet:", page.locator("body").inner_text()[:500])
        browser.close()

if __name__ == "__main__":
    inspect_ashby("https://jobs.ashbyhq.com/notion/5b15697c-fa91-4511-9482-c98a6ff29f90/application")
