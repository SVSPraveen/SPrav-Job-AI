import sys
import re
from playwright.sync_api import sync_playwright

def inspect_site(name, url):
    print(f"\n--- Inspecting {name}: {url} ---")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        print("Page Title:", page.title())
        
        # Click Apply for iCIMS (since URL doesn't have /apply)
        if name == "iCIMS":
            try:
                # wait for any frame to load since iCIMS uses iframes a lot
                page.wait_for_timeout(3000)
                
                # Check for an iframe
                for frame in page.frames:
                    if 'icims.com' in frame.url:
                        btn = frame.locator("a[title*='Apply'], button:has-text('Apply')").first
                        if btn.count() > 0:
                            print(f"Found Apply in frame {frame.name}, clicking...")
                            btn.click(force=True)
                            page.wait_for_timeout(3000)
                            break
                            
                btn = page.get_by_role("link", name=re.compile("apply", re.IGNORECASE)).first
                if btn.count() > 0:
                    print("Found Apply link on main page, clicking...")
                    btn.click(force=True)
                    page.wait_for_timeout(3000)
            except Exception as e:
                print(f"Error clicking apply on iCIMS: {e}")
                
        # Wait for Workday
        if name == "Workday":
            page.wait_for_timeout(3000)
            
        print(f"Number of frames: {len(page.frames)}")
        for i, frame in enumerate(page.frames):
            print(f"Frame {i}: {frame.name} | {frame.url}")
            
        # Get inputs from all frames
        for i, frame in enumerate(page.frames):
            try:
                html = frame.content()
                inputs = re.findall(r'<input[^>]*>', html)
                if len(inputs) > 0:
                    print(f"Found {len(inputs)} inputs in Frame {i}. First 10:")
                    for inp in inputs[:10]:
                        print("  " + inp)
                
                buttons = re.findall(r'<button[^>]*>.*?</button>', html, re.DOTALL)
                if len(buttons) > 0:
                    print(f"Found {len(buttons)} buttons in Frame {i}. Sample:")
                    for b in buttons[:3]:
                        print("  " + b.strip().replace('\n', ' '))
            except Exception as e:
                print(f"Cannot read frame {i}: {e}")
            
        browser.close()

if __name__ == "__main__":
    inspect_site("Workday", "https://visa.wd5.myworkdayjobs.com/Visa/job/US---Austin-TX/Software-Engineer--New-College-Grad---2026--Austin--TX_REF082999W-1/apply")
    inspect_site("iCIMS", "https://careers-sas.icims.com/jobs/39616/software-development-engineer-in-test/job")
