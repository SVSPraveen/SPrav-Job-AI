import sys
from playwright.sync_api import sync_playwright

def inspect_workday(url):
    print(f"\n--- Inspecting Workday: {url} ---")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        print("Page Title:", page.title())
        print(page.content()[:2000])
        browser.close()

if __name__ == "__main__":
    inspect_workday("https://intel.wd1.myworkdayjobs.com/en-US/External/job/Senior-Software-Engineer_JR0285595")
