/**
 * internshala_scraper.js
 *
 * Scrapes Internshala for fresher/junior job listings (not internships — jobs).
 * Focuses on their "Jobs" section which has full-time roles for fresh graduates.
 * Uses puppeteer-extra stealth. Outputs JSON array on stdout.
 *
 * Usage: node internshala_scraper.js [keyword] [limit]
 */

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

const path = require('path');
const fs = require('fs');

const SEEN_PATH = path.join(__dirname, 'snapshots', 'internshala_seen.json');

function loadSeen() {
    if (!fs.existsSync(SEEN_PATH)) return new Set();
    try { return new Set(JSON.parse(fs.readFileSync(SEEN_PATH, 'utf8'))); }
    catch { return new Set(); }
}
function saveSeen(seen) {
    fs.writeFileSync(SEEN_PATH, JSON.stringify(Array.from(seen).slice(-2000)));
}

async function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

async function scrapeInternshala(keyword = 'software developer', limit = 20) {
    const seen = loadSeen();
    const slug = keyword.toLowerCase().replace(/\s+/g, '-');
    const url = `https://internshala.com/jobs/${slug}-jobs`;
    console.error(`[Internshala] Searching: "${keyword}"`);

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

        for (let i = 0; i < 3; i++) {
            await page.evaluate(() => window.scrollBy(0, window.innerHeight));
            await delay(1000);
        }

        const cards = await page.evaluate((lim) => {
            const results = [];
            const items = Array.from(document.querySelectorAll('.job-internship-card, [class*="container"][data-internship_id], .individual_internship'));

            for (const item of items.slice(0, lim)) {
                const titleEl = item.querySelector('.job-title, .profile, h3');
                const companyEl = item.querySelector('.company-name, .company');
                const locationEl = item.querySelector('.locations span, .location_link, [class*="location"]');
                const linkEl = item.querySelector('a[href*="/jobs/detail"], a[href*="/job/"]') || item.querySelector('a');

                const title = titleEl ? titleEl.innerText.trim() : '';
                const company = companyEl ? companyEl.innerText.trim() : '';
                const location = locationEl ? locationEl.innerText.trim() : '';
                const href = linkEl ? (linkEl.href.startsWith('http') ? linkEl.href : `https://internshala.com${linkEl.getAttribute('href')}`) : '';
                const idMatch = href.match(/\/jobs\/detail\/(\d+)/) || href.match(/job\/(\d+)/);
                const jobId = idMatch ? idMatch[1] : href;

                if (title && href) {
                    results.push({ title, company, location, url: href, jobId });
                }
            }
            return results;
        }, limit);

        console.error(`[Internshala] Got ${cards.length} cards.`);

        for (const card of cards) {
            if (seen.has(card.jobId)) continue;
            seen.add(card.jobId);

            let description = `${card.title} at ${card.company}. Location: ${card.location}`;
            if (card.url.startsWith('http')) {
                try {
                    const jdPage = await browser.newPage();
                    await jdPage.goto(card.url, { waitUntil: 'domcontentloaded', timeout: 20000 });
                    await delay(1500);
                    const jdText = await jdPage.evaluate(() => {
                        const el = document.querySelector('.job_description, .internship_other_details_container, [class*="about_company"], .about_internship');
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
                source: 'internshala',
            });
            await delay(600);
        }

        saveSeen(seen);
        console.error(`[Internshala] Done. ${jobs.length} new jobs.`);
    } catch (err) {
        console.error(`[Internshala] Error: ${err.message}`);
    } finally {
        await browser.close();
    }

    console.log(JSON.stringify(jobs));
}

const keyword = process.argv[2] || 'software developer';
const limit = parseInt(process.argv[3] || '20', 10);
scrapeInternshala(keyword, limit);
