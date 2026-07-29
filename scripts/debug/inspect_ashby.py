import sys
import re
from playwright.sync_api import sync_playwright

def inspect_ashby(url):
    print(f"\n--- Inspecting Ashby: {url} ---")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        
        # If it doesn't have /application in the URL, try clicking "Apply"
        if "/application" not in url:
            try:
                page.locator("text=Apply").first.click(force=True, timeout=5000)
                page.wait_for_timeout(3000)
            except:
                pass
                
        print(f"Number of frames: {len(page.frames)}")
        
        html = page.content()
        inputs = re.findall(r'<input[^>]*>', html)
        print(f"Found {len(inputs)} inputs. First 10:")
        for inp in inputs[:10]:
            print(inp)
            
        browser.close()

if __name__ == "__main__":
    inspect_ashby("https://jobs.ashbyhq.com/benchling/b3c9b312-6e2b-4dbc-9b15-0b0310d75a7f/application")
