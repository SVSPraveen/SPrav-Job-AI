import sys
import re
from playwright.sync_api import sync_playwright

def inspect_smartrecruiters(url):
    print(f"\n--- Inspecting SmartRecruiters: {url} ---")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")
        
        # Click "I'm interested"
        try:
            page.locator("text=I'm interested").first.click(force=True, timeout=5000)
            page.wait_for_timeout(3000)
        except:
            pass
            
        print(f"Number of frames: {len(page.frames)}")
        for i, frame in enumerate(page.frames):
            print(f"Frame {i}: {frame.name} | {frame.url}")
            
        if len(page.frames) > 1:
            print("Form might be in an iframe. Look at the frame URLs above.")
        else:
            print("Only 1 frame. Extracting HTML around inputs...")
            html = page.content()
            # Let's find snippets that have "name=" or "id=" near input fields
            inputs = re.findall(r'<input[^>]*>', html)
            print(f"Found {len(inputs)} inputs. First 10:")
            for inp in inputs[:10]:
                print(inp)
                
            textareas = re.findall(r'<textarea[^>]*>', html)
            print(f"Found {len(textareas)} textareas. First 5:")
            for ta in textareas[:5]:
                print(ta)
                
        browser.close()

if __name__ == "__main__":
    inspect_smartrecruiters("https://jobs.smartrecruiters.com/WesternDigital/744000138717897-software-engineer")
