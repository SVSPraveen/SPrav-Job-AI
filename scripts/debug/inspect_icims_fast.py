import sys
import re
from playwright.sync_api import sync_playwright

def inspect_icims(url):
    print(f"\n--- Inspecting iCIMS: {url} ---")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)
        
        # Check for an iframe
        for frame in page.frames:
            if 'icims.com' in frame.url:
                try:
                    btn = frame.locator("a[title*='Apply'], button:has-text('Apply')").first
                    if btn.count() > 0:
                        print(f"Found Apply in frame {frame.name}, clicking...")
                        btn.click(force=True)
                        page.wait_for_timeout(3000)
                except: pass
                        
        print(f"Number of frames: {len(page.frames)}")
        for i, frame in enumerate(page.frames):
            try:
                html = frame.content()
                inputs = re.findall(r'<input[^>]*>', html)
                print(f"Frame {i} ({frame.url}): Found {len(inputs)} inputs. First 5:")
                for inp in inputs[:5]:
                    print("  " + inp)
            except: pass
            
        browser.close()

if __name__ == "__main__":
    inspect_icims("https://careers-sas.icims.com/jobs/39616/software-development-engineer-in-test/job")
