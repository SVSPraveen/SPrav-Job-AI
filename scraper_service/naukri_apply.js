/**
 * naukri_apply.js
 *
 * Two modes:
 *
 * 1. EXTRACT MODE (--extract-only):
 *    Opens a Naukri job page and extracts the real "Apply on Company Website"
 *    URL without applying. The Python dispatcher then tries to route that URL
 *    to Greenhouse/Lever auto-apply or creates a strategy report.
 *    Output: { "external_apply_url": "https://..." }
 *
 * 2. (Reserved for future use) Logged-in apply when no external URL exists.
 *
 * Usage:
 *   node naukri_apply.js <job_url> --extract-only
 *   node naukri_apply.js <job_url> <email> <password>
 */

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

async function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

// Selectors that lead to the real company apply page
const EXTERNAL_APPLY_SELECTORS = [
    'a[href*="greenhouse.io"]',
    'a[href*="lever.co"]',
    'a[href*="workday.com"]',
    'a[href*="myworkdayjobs.com"]',
    'a[href*="smartrecruiters.com"]',
    'a[href*="icims.com"]',
    'a[href*="taleo.net"]',
    'a[href*="bamboohr.com"]',
    'a[href*="ashby.io"]',
    'a[href*="recruitee.com"]',
    // Generic "Apply on company website" button
    'a[data-ga-track*="apply-company-site"]',
    '.applyOnCompSite',
    '[class*="apply-company"]',
    'a[title*="Company Website" i]',
    'a[title*="Apply on" i]',
];

async function extractApplyUrl(jobUrl) {
    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });
    const page = await browser.newPage();
    await page.setViewport({ width: 1366, height: 768 });

    try {
        await page.goto(jobUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await delay(3000);

        // Try each selector
        for (const sel of EXTERNAL_APPLY_SELECTORS) {
            try {
                const el = await page.$(sel);
                if (el) {
                    const href = await page.evaluate(el => el.href, el);
                    if (href && href.startsWith('http') && !href.includes('naukri.com')) {
                        await browser.close();
                        console.log(JSON.stringify({ external_apply_url: href }));
                        return;
                    }
                }
            } catch (_) {}
        }

        // Look for any link that opens a non-Naukri domain in the apply section
        const externalUrl = await page.evaluate(() => {
            const applySection = document.querySelector('[class*="applyBtn"], [class*="apply-section"], #apply-button');
            if (applySection) {
                const link = applySection.closest('a') || applySection.querySelector('a');
                if (link && link.href && !link.href.includes('naukri.com')) {
                    return link.href;
                }
            }
            // Last resort: look for any link with known ATS patterns in the page
            const allLinks = Array.from(document.querySelectorAll('a[href]'));
            const atsPatterns = ['greenhouse.io', 'lever.co', 'workday.com', 'myworkdayjobs.com', 
                                 'smartrecruiters.com', 'ashby.io', 'bamboohr.com', 'recruitee.com'];
            for (const link of allLinks) {
                if (atsPatterns.some(p => link.href.includes(p))) {
                    return link.href;
                }
            }
            return null;
        });

        await browser.close();

        if (externalUrl) {
            console.log(JSON.stringify({ external_apply_url: externalUrl }));
        } else {
            // No external URL found — Naukri-native application only
            console.log(JSON.stringify({ external_apply_url: null }));
        }
    } catch (err) {
        await browser.close();
        console.log(JSON.stringify({ external_apply_url: null, error: err.message }));
    }
}

const jobUrl = process.argv[2];
const mode   = process.argv[3];

if (!jobUrl) {
    console.log(JSON.stringify({ error: 'No job URL provided.' }));
} else if (mode === '--extract-only') {
    extractApplyUrl(jobUrl);
} else {
    // For now, default to extract mode — Quick Apply is deprecated
    extractApplyUrl(jobUrl);
}
