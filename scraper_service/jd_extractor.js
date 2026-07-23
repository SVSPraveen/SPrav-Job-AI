/**
 * jd_extractor.js
 * 
 * Playwright fallback for JD extraction on JavaScript-heavy career pages.
 * Usage: node jd_extractor.js <url>
 * Output: { "text": "<jd text>" } on stdout
 */

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

const JD_SELECTORS = [
    '.job-description', '.jobDescriptionContent', '.job-desc',
    '.description__text', '.show-more-less-html__markup',
    '[class*="job-description"]', '[class*="jd-desc"]',
    '[class*="description"]', '[data-testid="job-description"]',
    'article', '.content', 'main',
];

async function extract(url) {
    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    const page = await browser.newPage();
    let text = '';
    try {
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 25000 });
        await new Promise(r => setTimeout(r, 2500));

        text = await page.evaluate((selectors) => {
            for (const sel of selectors) {
                const el = document.querySelector(sel);
                if (el && el.innerText.length > 200) {
                    return el.innerText.substring(0, 4000);
                }
            }
            return document.body.innerText.substring(0, 4000);
        }, JD_SELECTORS);
    } catch (e) {
        console.error('[jd_extractor.js]', e.message);
    } finally {
        await browser.close();
    }
    console.log(JSON.stringify({ text }));
}

const url = process.argv[2];
if (!url) {
    console.log(JSON.stringify({ text: '' }));
} else {
    extract(url);
}
