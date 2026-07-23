/**
 * hirist_scraper.js
 *
 * Scrapes Hirist.tech for fresh tech-focused job listings.
 * Hirist is India's premium IT/Tech-only job board — every listing here
 * is a genuine tech role (no sales, no data entry, no BPO noise).
 *
 * Usage: node hirist_scraper.js [keyword] [limit]
 * Output: JSON array on stdout
 */

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

const path = require('path');
const fs = require('fs');

const SEEN_PATH = path.join(__dirname, 'snapshots', 'hirist_seen.json');

function loadSeen() {
    if (!fs.existsSync(SEEN_PATH)) return new Set();
    try { return new Set(JSON.parse(fs.readFileSync(SEEN_PATH, 'utf8'))); }
    catch { return new Set(); }
}
function saveSeen(seen) {
    fs.writeFileSync(SEEN_PATH, JSON.stringify(Array.from(seen).slice(-2000)));
}
async function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

async function scrapeHirist(keyword = 'software developer', limit = 25) {
    const seen = loadSeen();
    const slug = keyword.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
    // Hirist uses a clean URL slug pattern for search
    const url = `https://www.hirist.tech/search-jobs/${slug}`;
    console.error(`[Hirist] Searching: "${keyword}" → ${url}`);

    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });
    const page = await browser.newPage();
    await page.setViewport({ width: 1366, height: 768 });
    await page.setExtraHTTPHeaders({ 'Accept-Language': 'en-US,en;q=0.9' });

    const jobs = [];
    try {
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 40000 });
        await delay(3000);

        for (let i = 0; i < 4; i++) {
            await page.evaluate(() => window.scrollBy(0, window.innerHeight * 0.8));
            await delay(1000);
        }

        const cards = await page.evaluate((lim) => {
            const results = [];
            // Hirist job cards
            const items = Array.from(document.querySelectorAll(
                '.job-listing-card, .job-card, [class*="job-item"], [class*="jobCard"], article'
            ));

            for (const item of items.slice(0, lim)) {
                const titleEl = item.querySelector('h2, h3, .job-title, [class*="title"]');
                const compEl  = item.querySelector('.company-name, [class*="company"]');
                const locEl   = item.querySelector('.location, [class*="location"], [class*="loc"]');
                const linkEl  = item.querySelector('a[href*="hirist.tech"], a[href*="/job/"], a');
                const expEl   = item.querySelector('[class*="exp"], [class*="experience"]');
                const salEl   = item.querySelector('[class*="salary"], [class*="sal"]');

                const title   = titleEl ? titleEl.innerText.trim() : '';
                const company = compEl  ? compEl.innerText.trim()  : '';
                const loc     = locEl   ? locEl.innerText.trim()   : '';
                const href    = linkEl  ? (linkEl.href.startsWith('http') ? linkEl.href : `https://www.hirist.tech${linkEl.getAttribute('href')}`) : '';
                const exp     = expEl   ? expEl.innerText.trim()   : '';
                const salary  = salEl   ? salEl.innerText.trim()   : '';

                // Extract job ID from URL
                const idMatch = href.match(/\/job\/([^\/?\s]+)/);
                const jobId   = idMatch ? idMatch[1] : href;

                if (title && href && jobId) {
                    results.push({ title, company, location: loc, url: href, jobId, experience: exp, salary });
                }
            }
            return results;
        }, limit);

        console.error(`[Hirist] Found ${cards.length} cards.`);

        for (const card of cards) {
            if (seen.has(card.jobId)) continue;
            seen.add(card.jobId);

            let description = `${card.title} at ${card.company}. Location: ${card.location}. Experience: ${card.experience}. Salary: ${card.salary}.`;

            if (card.url.startsWith('http')) {
                try {
                    const jdPage = await browser.newPage();
                    await jdPage.goto(card.url, { waitUntil: 'domcontentloaded', timeout: 20000 });
                    await delay(1500);
                    const jdText = await jdPage.evaluate(() => {
                        const el = document.querySelector(
                            '.job-description, [class*="job-desc"], [class*="description"], .jd-content, .about-job, main'
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
                location:    card.location || 'India',
                source:      'hirist',
            });
            await delay(700);
        }

        saveSeen(seen);
        console.error(`[Hirist] Done. ${jobs.length} new jobs.`);
    } catch (err) {
        console.error(`[Hirist] Error: ${err.message}`);
    } finally {
        await browser.close();
    }

    console.log(JSON.stringify(jobs));
}

const keyword = process.argv[2] || 'software developer';
const limit   = parseInt(process.argv[3] || '25', 10);
scrapeHirist(keyword, limit);
