import os
import json
from playwright.sync_api import sync_playwright

def render_html_to_pdf(json_data_str: str, template_path: str, output_path: str) -> bool:
    """
    Takes a JSON string with resume sections, injects it into the HTML template,
    and uses Playwright to render a pixel-perfect A4 PDF.
    """
    try:
        data = json.loads(json_data_str)
        
        with open(template_path, "r", encoding="utf-8") as f:
            html = f.read()
            
        # Basic variable injection
        for key, value in data.items():
            # For simplicity, replace {{key}} in the template
            placeholder = f"{{{{{key}}}}}"
            # Ensure value is string
            html = html.replace(placeholder, str(value))
            
        # Render with Playwright
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content(html)
            page.pdf(path=output_path, format="A4", print_background=True)
            browser.close()
            
        print(f"[HTML-to-PDF Engine] Successfully rendered {output_path}")
        return True
    except Exception as e:
        print(f"[HTML-to-PDF Engine] Failed to render PDF: {e}")
        return False
