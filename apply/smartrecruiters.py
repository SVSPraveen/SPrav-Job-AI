import os
from playwright.sync_api import sync_playwright

def apply_to_smartrecruiters(url: str, personal_info: dict, pdf_path: str) -> bool:
    print(f"[ATS: SmartRecruiters] Testing application to {url}...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded")
            
            # Click "I'm interested"
            try:
                page.locator("text=I'm interested").first.click(force=True, timeout=5000)
                page.wait_for_timeout(2000)
            except:
                pass
                
            # Wait for form to appear
            page.wait_for_selector('input[name="firstName"], input[id="first-name"]', timeout=10000)
            
            # Fill form
            if page.locator('input[id="first-name"]').count() > 0:
                page.locator('input[id="first-name"]').fill(personal_info.get("first_name", ""))
                page.locator('input[id="last-name"]').fill(personal_info.get("last_name", ""))
                page.locator('input[id="email"]').fill(personal_info.get("email", ""))
                page.locator('input[id="phone"]').fill(personal_info.get("phone", ""))
            elif page.locator('input[name="firstName"]').count() > 0:
                page.locator('input[name="firstName"]').fill(personal_info.get("first_name", ""))
                page.locator('input[name="lastName"]').fill(personal_info.get("last_name", ""))
                page.locator('input[name="email"]').fill(personal_info.get("email", ""))
                page.locator('input[name="phoneNumber"]').fill(personal_info.get("phone", ""))
                
            # Upload Resume
            # SmartRecruiters usually has an input[type="file"]
            file_input = page.locator('input[type="file"]').first
            if file_input.count() > 0 and os.path.exists(pdf_path):
                file_input.set_input_files(pdf_path)
                page.wait_for_timeout(2000)
                
            # We don't actually submit to avoid spamming the employer, we just simulate success up to the button
            submit_btn = page.locator('button[type="submit"]').first
            outcome = submit_btn.count() > 0
            
            browser.close()
            return outcome
    except Exception as e:
        print(f"[ATS: SmartRecruiters] Error: {e}")
        return False
