import os
from playwright.sync_api import sync_playwright

def apply_to_ashby(url: str, personal_info: dict, pdf_path: str) -> bool:
    print(f"[ATS: Ashby] Testing application to {url}...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # If the URL doesn't end with /application, append it or click Apply
            if not url.endswith("/application"):
                url = url.rstrip('/') + "/application"
                
            page.goto(url, wait_until="networkidle")
            
            # Wait for form
            page.wait_for_selector('input[name="_systemfield_name"]', timeout=10000)
            
            # Fill form fields
            page.locator('input[name="_systemfield_name"]').fill(f'{personal_info.get("first_name", "")} {personal_info.get("last_name", "")}')
            page.locator('input[name="_systemfield_email"]').fill(personal_info.get("email", ""))
            
            # Resume upload
            file_input = page.locator('input[id="_systemfield_resume"]')
            if file_input.count() > 0 and os.path.exists(pdf_path):
                file_input.set_input_files(pdf_path)
                page.wait_for_timeout(2000)
                
            # Submit button
            import re
            submit_btn = page.get_by_role("button", name=re.compile("submit", re.IGNORECASE)).first
            outcome = submit_btn.count() > 0
            
            browser.close()
            return outcome
    except Exception as e:
        print(f"[ATS: Ashby] Error: {e}")
        return False
