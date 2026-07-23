from playwright.sync_api import sync_playwright

def verify_job_liveness(url: str) -> tuple[bool, str]:
    """
    Physically pings the ATS portal using headless Chromium.
    Returns (True, "") if the job is alive.
    Returns (False, reason) if the job is dead, filled, or missing.
    """
    # If it's a direct email application, it's always "alive" to the system
    if "mailto:" in url or "@" in url:
        return True, ""
        
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36")
            page = context.new_page()
            
            # Fast ping with 5-second timeout
            response = page.goto(url, timeout=5000, wait_until="domcontentloaded")
            
            if response is None:
                browser.close()
                return False, "Failed to load URL."
                
            if response.status == 404:
                browser.close()
                return False, "HTTP 404 - Job Not Found."
                
            page_text = page.content().lower()
            
            # Common ATS "Dead Job" strings
            dead_strings = [
                "this job is no longer available",
                "job closed",
                "position has been filled",
                "we are no longer accepting applications",
                "sorry, this job has expired"
            ]
            
            for dead_string in dead_strings:
                if dead_string in page_text:
                    browser.close()
                    return False, f"Job closed: '{dead_string}' detected."
            
            # Some ATS systems redirect to their homepage if the job is gone
            if "greenhouse.io" in url or "lever.co" in url:
                if "all open positions" in page_text or "current openings" in page_text:
                    # If we got redirected to the main board, the specific job is likely gone
                    if "apply" not in page_text:
                        browser.close()
                        return False, "Redirected to main job board. Specific job is dead."
            
            browser.close()
            return True, ""
            
    except Exception as e:
        # If Playwright times out or fails to resolve, assume it's dead to save compute
        return False, f"Liveness Ping Failed: {str(e)}"
