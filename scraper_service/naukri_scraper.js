/**
 * naukri_scraper.js
 *
 * Scrapes Naukri.com for fresh job listings matching your target keywords.
 * Uses puppeteer-extra stealth to avoid detection.
 *
 * Usage: node naukri_scraper.js [keyword] [limit]
 *   keyword  — search term (default: "software developer")
 *   limit    — max jobs to extract (default: 30)
 *
 * Output: JSON array on stdout (one line), logs on stderr.
 */

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

const path = require('path');
const fs = require('fs');

const SEEN_PATH = path.join(__dirname, 'snapshots', 'naukri_seen.json');

function loadSeen() {
    if (!fs.existsSync(SEEN_PATH)) return new Set();
    try { return new Set(JSON.parse(fs.readFileSync(SEEN_PATH, 'utf8'))); }
    catch { return new Set(); }
}

function saveSeen(seen) {
    const arr = Array.from(seen).slice(-2000);
    fs.writeFileSync(SEEN_PATH, JSON.stringify(arr));
}

async function delay(ms) {
    return new Promise(r => setTimeout(r, ms));
}

async function scrapeNaukri(keyword = 'software developer', limit = 30) {
    const seen = loadSeen();
    const encoded = encodeURIComponent(keyword);
    // freshness=1 = last 24 hours, experience=0-2 for freshers/juniors
    const url = `https://www.naukri.com/${encoded.toLowerCase().replace(/%20/g, '-')}-jobs?k=${encoded}&experience=0&freshness=1`;

    console.error(`[Naukri] Searching: "${keyword}" | URL: ${url}`);

    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-blink-features=AutomationControlled']
    });
    const page = await browser.newPage();
    await page.setViewport({ width: 1366, height: 768 });
    await page.setExtraHTTPHeaders({ 'Accept-Language': 'en-US,en;q=0.9' });

    const jobs = [];

    try {
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
        await delay(3000);

        // Human-like scroll
        for (let i = 0; i < 4; i++) {
            await page.evaluate(() => window.scrollBy(0, window.innerHeight * 0.7));
            await delay(1200);
        }

        const extracted = await page.evaluate((lim) => {
            const cards = Array.from(document.querySelectorAll('.jobTuple, article.jobListingCard, [class*="job-card"], [class*="jobCard"]'));
            const results = [];

            for (const card of cards.slice(0, lim)) {
                // Title
                const titleEl = card.querySelector('[class*="title"], h2, h3, .job-title');
                const title = titleEl ? titleEl.innerText.trim() : '';
                if (!title) continue;

                // Company
                const compEl = card.querySelector('[class*="company"], [class*="org-name"], .company-name');
                const company = compEl ? compEl.innerText.trim() : '';

                // Location
                const locEl = card.querySelector('[class*="location"], [class*="loc"]');
                const location = locEl ? locEl.innerText.trim() : '';

                // Experience
                const expEl = card.querySelector('[class*="exp"]');
                const experience = expEl ? expEl.innerText.trim() : '';

                // Link
                const linkEl = card.querySelector('a[href*="naukri.com"]') || card.querySelector('a');
                const url = linkEl ? linkEl.href : '';

                // Job ID (from URL or random)
                const idMatch = url.match(/jid=(\d+)/) || url.match(/-(\d+)\?/);
                const jobId = idMatch ? idMatch[1] : Math.random().toString(36).slice(2);

                results.push({ title, company, location, experience, url, jobId });
            }
            return results;
        }, limit);

        console.error(`[Naukri] Extracted ${extracted.length} raw cards.`);

        for (const item of extracted) {
            if (seen.has(item.jobId)) continue;
            seen.add(item.jobId);

            // Fetch job description from the JD page
            let description = `${item.title} at ${item.company}. Location: ${item.location}. Experience: ${item.experience}`;
            if (item.url && item.url.startsWith('http')) {
                try {
                    const jdPage = await browser.newPage();
                    await jdPage.goto(item.url, { waitUntil: 'domcontentloaded', timeout: 20000 });
                    await delay(1500);
                    const jdText = await jdPage.evaluate(() => {
                        const el = document.querySelector('.job-desc, [class*="job-desc"], [class*="description"], .jd-desc');
                        return el ? el.innerText.substring(0, 3000) : '';
                    });
                    if (jdText) description = jdText;
                    await jdPage.close();
                } catch (_) { /* use fallback description */ }
            }

            jobs.push({
                title: item.title,
                company: item.company,
                url: item.url,
                description,
                location: item.location || 'India',
                source: 'naukri',
            });

            if (jobs.length >= limit) break;
            await delay(800); // polite pace between JD fetches
        }

        saveSeen(seen);
        console.error(`[Naukri] Done. ${jobs.length} new jobs found.`);
    } catch (err) {
        console.error(`[Naukri] Error: ${err.message}`);
    } finally {
        await browser.close();
    }

    console.log(JSON.stringify(jobs));
}

const keyword = process.argv[2] || 'software developer';
const limit = parseInt(process.argv[3] || '30', 10);
scrapeNaukri(keyword, limit);
