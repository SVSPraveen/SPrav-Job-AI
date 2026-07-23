/**
 * indeed_scraper.js
 *
 * Scrapes Indeed India for fresh job listings.
 * Uses puppeteer-extra stealth. Outputs JSON array on stdout.
 *
 * Usage: node indeed_scraper.js [keyword] [limit]
 */

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());
const path = require('path');
const fs = require('fs');

const SEEN_PATH = path.join(__dirname, 'snapshots', 'indeed_seen.json');

function loadSeen() {
    if (!fs.existsSync(SEEN_PATH)) return new Set();
    try { return new Set(JSON.parse(fs.readFileSync(SEEN_PATH, 'utf8'))); }
    catch { return new Set(); }
}
function saveSeen(seen) {
    fs.writeFileSync(SEEN_PATH, JSON.stringify(Array.from(seen).slice(-2000)));
}

async function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

async function scrapeIndeed(keyword = 'software developer', limit = 20) {
    const seen = loadSeen();
    const encoded = encodeURIComponent(keyword);
    // fromage=1 = last 24 hours, l=India
    const url = `https://in.indeed.com/jobs?q=${encoded}&l=India&fromage=1&sort=date`;
    console.error(`[Indeed] Searching: "${keyword}"`);

    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });
    const page = await browser.newPage();
    await page.setViewport({ width: 1366, height: 768 });
    const jobs = [];

    try {
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 40000 });
        await delay(3000);

        // Scroll for lazy loading
        for (let i = 0; i < 3; i++) {
            await page.evaluate(() => window.scrollBy(0, window.innerHeight));
            await delay(1000);
        }

        const cards = await page.evaluate((lim) => {
            const results = [];
            const items = Array.from(document.querySelectorAll('[class*="job_seen_beacon"], .jobCard, [class*="tapItem"]'));
            for (const item of items.slice(0, lim)) {
                const titleEl = item.querySelector('[class*="jobTitle"] a, h2 a');
                const companyEl = item.querySelector('[data-testid="company-name"], .companyName');
                const locationEl = item.querySelector('[data-testid="text-location"], .companyLocation');
                const linkEl = item.querySelector('a[href*="/rc/clk"], a[href*="/pagead/clk"], a[id^="job_"]');
                
                const title = titleEl ? titleEl.innerText.trim() : '';
                const company = companyEl ? companyEl.innerText.trim() : '';
                const location = locationEl ? locationEl.innerText.trim() : '';
                const href = linkEl ? linkEl.href : (titleEl ? titleEl.href : '');
                const idMatch = href.match(/jk=([a-f0-9]+)/);
                const jobId = idMatch ? idMatch[1] : href;

                if (title && href) {
                    results.push({ title, company, location, url: href, jobId });
                }
            }
            return results;
        }, limit);

        console.error(`[Indeed] Got ${cards.length} cards.`);

        for (const card of cards) {
            if (seen.has(card.jobId)) continue;
            seen.add(card.jobId);

            // Fetch JD from the job detail page
            let description = `${card.title} at ${card.company}. Location: ${card.location}`;
            if (card.url.startsWith('http')) {
                try {
                    const jdPage = await browser.newPage();
                    await jdPage.goto(card.url, { waitUntil: 'domcontentloaded', timeout: 20000 });
                    await delay(1500);
                    const jdText = await jdPage.evaluate(() => {
                        const el = document.querySelector('#jobDescriptionText, .jobsearch-jobDescriptionText, [class*="description"]');
                        return el ? el.innerText.substring(0, 3000) : '';
                    });
                    if (jdText) description = jdText;
                    await jdPage.close();
                } catch (_) {}
            }

            jobs.push({
                title: card.title,
                company: card.company,
                url: card.url,
                description,
                location: card.location || 'India',
                source: 'indeed',
            });
            await delay(600);
        }

        saveSeen(seen);
        console.error(`[Indeed] Done. ${jobs.length} new jobs.`);
    } catch (err) {
        console.error(`[Indeed] Error: ${err.message}`);
    } finally {
        await browser.close();
    }

    console.log(JSON.stringify(jobs));
}

const keyword = process.argv[2] || 'software developer';
const limit = parseInt(process.argv[3] || '20', 10);
scrapeIndeed(keyword, limit);
