import asyncio
from playwright.async_api import async_playwright

async def capture():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto('http://localhost:5173')
        await page.wait_for_timeout(1000)
        
        # Click the Scope tab
        await page.evaluate('''() => {
            const tabs = document.querySelectorAll('.sidebar-nav button');
            const scopeTab = Array.from(tabs).find(t => t.innerText.includes('Scope'));
            if (scopeTab) scopeTab.click();
        }''')
        await page.wait_for_timeout(1000)
        
        # Type into the location input
        await page.type('input[placeholder*="City, Country"]', 'san f')
        await page.wait_for_timeout(1000)
        
        await page.screenshot(path='item_c_typeahead.png')
        await browser.close()

asyncio.run(capture())
