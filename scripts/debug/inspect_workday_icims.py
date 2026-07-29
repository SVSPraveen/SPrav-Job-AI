import sys
import re
from playwright.sync_api import sync_playwright

def inspect_site(name, url):
    print(f"\n--- Inspecting {name}: {url} ---")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")
        print("Page Title:", page.title())
        
        # Click Apply
        try:
            btn = page.get_by_role("button", name=re.compile("apply", re.IGNORECASE)).first
            if btn.count() > 0:
                print("Found Apply button, clicking...")
                btn.click(force=True, timeout=5000)
                page.wait_for_timeout(3000)
            else:
                link = page.get_by_role("link", name=re.compile("apply", re.IGNORECASE)).first
                if link.count() > 0:
                    print("Found Apply link, clicking...")
                    link.click(force=True, timeout=5000)
                    page.wait_for_timeout(3000)
                else:
                    print("No Apply button/link found.")
        except Exception as e:
            print(f"Error clicking apply: {e}")
            
        print(f"Number of frames: {len(page.frames)}")
        for i, frame in enumerate(page.frames):
            print(f"Frame {i}: {frame.name} | {frame.url}")
            
        html = page.content()
        inputs = re.findall(r'<input[^>]*>', html)
        print(f"Found {len(inputs)} inputs in main frame. First 5:")
        for inp in inputs[:5]:
            print(inp)
            
        browser.close()

if __name__ == "__main__":
    inspect_site("Workday", "https://intel.wd1.myworkdayjobs.com/en-US/External/job/Senior-Software-Engineer_JR0285595")
    inspect_site("iCIMS", "https://social.icims.com/job/Entry-Level-Software-Engineer-Job-US-43986332.html")
