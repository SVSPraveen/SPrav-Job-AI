const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth')();
chromium.use(stealth);

async function main() {
    const url = process.argv[2];
    if (!url) {
        console.log(JSON.stringify({ text: '' }));
        process.exit(1);
    }

    let browser;
    try {
        browser = await chromium.launch({ headless: true });
        const context = await browser.newContext();
        const page = await context.newPage();
        
        await page.goto(url, { waitUntil: 'networkidle', timeout: 25000 });
        await page.waitForTimeout(1000);
        const text = await page.evaluate(() => document.body.innerText || '');
        
        console.log(JSON.stringify({ text: text.trim() }));
    } catch (e) {
        console.log(JSON.stringify({ text: '' }));
    } finally {
        if (browser) await browser.close();
    }
}

main();
