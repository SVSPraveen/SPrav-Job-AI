/**
 * career_watcher.js
 * 
 * Polls every company in watchlist.json. For each company it:
 *   1. Fetches the career page using a stealth headless browser
 *   2. Extracts all job listings (title + URL)
 *   3. Compares against a stored snapshot hash
 *   4. If NEW jobs are detected, outputs them as JSON to stdout
 * 
 * Usage: node career_watcher.js
 * The Python discovery layer calls this script and consumes stdout.
 */

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const WATCHLIST_PATH = path.join(__dirname, '..', 'watchlist.json');
const SNAPSHOTS_DIR = path.join(__dirname, 'snapshots');

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getSnapshotPath(companyName) {
    const slug = companyName.toLowerCase().replace(/[^a-z0-9]/g, '_');
    return path.join(SNAPSHOTS_DIR, `${slug}.json`);
}

function loadSnapshot(companyName) {
    const p = getSnapshotPath(companyName);
    if (!fs.existsSync(p)) return { hash: null, jobs: [] };
    try {
        return JSON.parse(fs.readFileSync(p, 'utf8'));
    } catch {
        return { hash: null, jobs: [] };
    }
}

function saveSnapshot(companyName, hash, jobs) {
    const p = getSnapshotPath(companyName);
    fs.writeFileSync(p, JSON.stringify({ hash, jobs, updated_at: new Date().toISOString() }, null, 2));
}

function hashContent(str) {
    return crypto.createHash('md5').update(str).digest('hex');
}

// ─── Generic job list extractor ───────────────────────────────────────────────
// Tries multiple common selectors to find job links on any career page

async function extractJobs(page, companyUrl) {
    return await page.evaluate((baseUrl) => {
        const selectors = [
            'a[href*="job"]',
            'a[href*="position"]',
            'a[href*="career"]',
            'a[href*="opening"]',
            '[class*="job"] a',
            '[class*="position"] a',
            '[class*="role"] a',
            '[class*="listing"] a',
            '[data-job-id] a',
            'li a',
        ];

        const seen = new Set();
        const jobs = [];

        for (const sel of selectors) {
            const els = Array.from(document.querySelectorAll(sel));
            for (const el of els) {
                const title = el.innerText ? el.innerText.trim() : '';
                const href = el.href || '';
                if (title.length < 5 || title.length > 200) continue;
                if (!href || seen.has(href)) continue;
                // Filter out generic nav links
                const lower = title.toLowerCase();
                if (['home', 'about', 'contact', 'login', 'sign in', 'sign up', 'blog', 'help'].includes(lower)) continue;
                seen.add(href);
                jobs.push({ title, url: href });
            }
        }
        return jobs;
    }, companyUrl);
}

// ─── Main watcher loop ────────────────────────────────────────────────────────

async function watchAll() {
    if (!fs.existsSync(WATCHLIST_PATH)) {
        console.error('watchlist.json not found');
        process.exit(1);
    }

    const { companies } = JSON.parse(fs.readFileSync(WATCHLIST_PATH, 'utf8'));
    if (!fs.existsSync(SNAPSHOTS_DIR)) fs.mkdirSync(SNAPSHOTS_DIR, { recursive: true });

    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });

    const allNewJobs = [];

    for (const company of companies) {
        const { name, careers_url } = company;
        console.error(`[Watcher] Checking: ${name}`);
        const page = await browser.newPage();

        try {
            await page.setDefaultNavigationTimeout(30000);
            await page.goto(careers_url, { waitUntil: 'domcontentloaded' });
            // Extra wait for JS-heavy SPAs
            await new Promise(r => setTimeout(r, 3000));

            const jobs = await extractJobs(page, careers_url);

            if (jobs.length === 0) {
                console.error(`[Watcher] ${name}: No jobs extracted (may need custom selector)`);
                await page.close();
                continue;
            }

            // Build a stable hash from the sorted job titles+urls
            const contentStr = jobs.map(j => `${j.title}|${j.url}`).sort().join('\n');
            const liveHash = hashContent(contentStr);

            const snapshot = loadSnapshot(name);

            if (snapshot.hash === liveHash) {
                console.error(`[Watcher] ${name}: No changes (${jobs.length} jobs, hash unchanged)`);
            } else {
                // Find genuinely new jobs by comparing URLs
                const snapshotUrls = new Set((snapshot.jobs || []).map(j => j.url));
                const newJobs = snapshot.hash === null
                    ? [] // First run — just save baseline, don't flood the pipeline
                    : jobs.filter(j => !snapshotUrls.has(j.url));

                if (newJobs.length > 0) {
                    console.error(`[Watcher] ${name}: 🚨 ${newJobs.length} NEW job(s) detected!`);
                    for (const job of newJobs) {
                        allNewJobs.push({
                            title: job.title,
                            company: name,
                            url: job.url,
                            source: 'company_watcher',
                            location: 'India',
                        });
                    }
                } else {
                    console.error(`[Watcher] ${name}: Hash changed but no new unique URLs (page re-ordered or UI update)`);
                }

                saveSnapshot(name, liveHash, jobs);
            }
        } catch (err) {
            console.error(`[Watcher] ${name}: ERROR — ${err.message}`);
        } finally {
            await page.close();
        }
    }

    await browser.close();

    // Output new jobs as a single JSON line on stdout for Python to consume
    console.log(JSON.stringify(allNewJobs));
}

watchAll().catch(err => {
    console.error('Career watcher fatal error:', err);
    console.log('[]'); // Always output valid JSON so Python doesn't crash
    process.exit(1);
});
