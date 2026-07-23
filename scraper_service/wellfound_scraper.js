/**
 * wellfound_scraper.js
 *
 * Scrapes Wellfound (formerly AngelList Talent) for startup tech jobs.
 * Wellfound is the premier source for seed/series-A startup engineering
 * roles — many of these are NEVER posted on Naukri/LinkedIn and move fast.
 *
 * Usage: node wellfound_scraper.js [keyword] [limit]
 * Output: JSON array on stdout
 */

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

const path = require('path');
const fs = require('fs');

const SEEN_PATH = path.join(__dirname, 'snapshots', 'wellfound_seen.json');

function loadSeen() {
    if (!fs.existsSync(SEEN_PATH)) return new Set();
    try { return new Set(JSON.parse(fs.readFileSync(SEEN_PATH, 'utf8'))); }
    catch { return new Set(); }
}
function saveSeen(seen) {
    fs.writeFileSync(SEEN_PATH, JSON.stringify(Array.from(seen).slice(-2000)));
}
async function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

async function scrapeWellfound(keyword = 'software engineer', limit = 20) {
    const seen = loadSeen();
    const encoded = encodeURIComponent(keyword);
    // Wellfound job search URL with India location filter and sorting by recent
    const url = `https://wellfound.com/jobs?q=${encoded}&l=India&t=1`;
    console.error(`[Wellfound] Searching: "${keyword}"`);

    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });
    const page = await browser.newPage();
    await page.setViewport({ width: 1440, height: 900 });

    const jobs = [];
    try {
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
        await delay(4000);

        // Human-like scroll to load more cards
        for (let i = 0; i < 5; i++) {
            await page.evaluate(() => window.scrollBy(0, window.innerHeight));
            await delay(1500);
        }

        const cards = await page.evaluate((lim) => {
            const results = [];
            // Wellfound's React-rendered cards
            const items = Array.from(document.querySelectorAll(
                '[data-test="JobListing"], [class*="styles_component"], [class*="job-listing"]'
            ));

            for (const item of items.slice(0, lim)) {
                const titleEl   = item.querySelector('[class*="role"], h2, [class*="title"]');
                const compEl    = item.querySelector('[class*="startupName"], [class*="company"], h3');
                const locEl     = item.querySelector('[class*="location"], [class*="loc"]');
                const salEl     = item.querySelector('[class*="salary"], [class*="compensation"]');
                const linkEl    = item.querySelector('a[href*="/jobs/"], a[href*="wellfound.com"]');

                const title   = titleEl ? titleEl.innerText.trim() : '';
                const company = compEl  ? compEl.innerText.trim()  : '';
                const loc     = locEl   ? locEl.innerText.trim()   : '';
                const salary  = salEl   ? salEl.innerText.trim()   : '';
                const href    = linkEl  ? (linkEl.href.startsWith('http') ? linkEl.href : `https://wellfound.com${linkEl.getAttribute('href')}`) : '';

                // Use URL path as ID
                const idMatch = href.match(/\/jobs\/(\d+)/);
                const jobId   = idMatch ? idMatch[1] : href;

                if (title && href) {
                    results.push({ title, company, location: loc, salary, url: href, jobId });
                }
            }
            return results;
        }, limit);

        console.error(`[Wellfound] Found ${cards.length} cards.`);

        for (const card of cards) {
            if (seen.has(card.jobId)) continue;
            seen.add(card.jobId);

            let description = `${card.title} at ${card.company}. Location: ${card.location}. Compensation: ${card.salary}.`;

            if (card.url.startsWith('http')) {
                try {
                    const jdPage = await browser.newPage();
                    await jdPage.goto(card.url, { waitUntil: 'domcontentloaded', timeout: 25000 });
                    await delay(2000);
                    const jdText = await jdPage.evaluate(() => {
                        const el = document.querySelector(
                            '[class*="description"], [class*="jobDescription"], main, article, .prose'
                        );
                        return el ? el.innerText.substring(0, 3500) : '';
                    });
                    if (jdText && jdText.length > 100) description = jdText;
                    await jdPage.close();
                } catch (_) {}
            }

            jobs.push({
                title:       card.title,
                company:     card.company,
                url:         card.url,
                description,
                location:    card.location || 'Remote / India',
                source:      'wellfound',
            });
            await delay(800);
        }

        saveSeen(seen);
        console.error(`[Wellfound] Done. ${jobs.length} new jobs.`);
    } catch (err) {
        console.error(`[Wellfound] Error: ${err.message}`);
    } finally {
        await browser.close();
    }

    console.log(JSON.stringify(jobs));
}

const keyword = process.argv[2] || 'software engineer';
const limit   = parseInt(process.argv[3] || '20', 10);
scrapeWellfound(keyword, limit);
