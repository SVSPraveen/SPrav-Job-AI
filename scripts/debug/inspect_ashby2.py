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
    inspect_ashby("https://jobs.ashbyhq.com/benchling/b3c9b312-6e2b-4dbc-9b15-0b0310d75a7f/application")
