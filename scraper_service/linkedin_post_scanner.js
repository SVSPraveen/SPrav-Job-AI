/**
 * linkedin_post_scanner.js
 *
 * Logs into LinkedIn using credentials from environment variables,
 * then searches for recent posts containing hiring-intent keywords
 * from people at your target companies.
 *
 * Usage: node linkedin_post_scanner.js
 * Output: JSON array on stdout (one line), diagnostic logs on stderr
 *
 * Environment:
 *   LINKEDIN_EMAIL    — your LinkedIn account email
 *   LINKEDIN_PASSWORD — your LinkedIn account password
 */

require('dotenv').config({ path: require('path').join(__dirname, '..', '.env') });
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

const path = require('path');
const fs = require('fs');

const WATCHLIST_PATH = path.join(__dirname, '..', 'watchlist.json');
const SEEN_POSTS_PATH = path.join(__dirname, 'snapshots', 'linkedin_seen_posts.json');

// Hiring intent keywords to search for in post text
const HIRING_INTENT = [
    'we are hiring', "we're hiring", 'we are looking for',
    'now hiring', 'open position', 'job opening', 'job opportunity',
    'dm me your resume', 'dm me your cv', 'send your resume',
    'interested candidates', 'apply by', 'send me your resume',
    'share your resume', 'looking to hire', 'actively hiring',
    'positions available', 'immediate opening', 'urgent opening',
];

// Ed-tech and scam signals — mirror of ghost_detector blacklist
const SKIP_SIGNALS = [
    'placement guarantee', 'course fee', 'batch starting',
    'training fee', 'enroll now', 'pay after placement',
    'income share', 'like and comment', 'repost to apply',
];

function loadSeenPosts() {
    if (!fs.existsSync(SEEN_POSTS_PATH)) return new Set();
    try {
        return new Set(JSON.parse(fs.readFileSync(SEEN_POSTS_PATH, 'utf8')));
    } catch {
        return new Set();
    }
}

function saveSeenPosts(seen) {
    // Keep only the last 1000 post IDs to prevent unbounded growth
    const arr = Array.from(seen).slice(-1000);
    fs.writeFileSync(SEEN_POSTS_PATH, JSON.stringify(arr));
}

function extractEmail(text) {
    const match = text.match(/[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}/);
    return match ? match[0] : null;
}

function isHiringPost(text) {
    const lower = text.toLowerCase();
    return HIRING_INTENT.some(kw => lower.includes(kw));
}

function isScamPost(text) {
    const lower = text.toLowerCase();
    return SKIP_SIGNALS.some(kw => lower.includes(kw));
}

async function humanDelay(min = 1500, max = 3500) {
    const delay = Math.floor(Math.random() * (max - min) + min);
    await new Promise(r => setTimeout(r, delay));
}

async function loginToLinkedIn(page) {
    const email = process.env.LINKEDIN_EMAIL;
    const password = process.env.LINKEDIN_PASSWORD;

    if (!email || !password) {
        console.error('[LinkedIn] LINKEDIN_EMAIL or LINKEDIN_PASSWORD not set in .env');
        return false;
    }

    console.error('[LinkedIn] Navigating to login page...');
    await page.goto('https://www.linkedin.com/login', { waitUntil: 'domcontentloaded' });
    await humanDelay();

    await page.type('#username', email, { delay: 80 });
    await humanDelay(500, 1000);
    await page.type('#password', password, { delay: 80 });
    await humanDelay(500, 1000);
    await page.click('[type="submit"]');
    await page.waitForNavigation({ waitUntil: 'domcontentloaded', timeout: 15000 });

    const url = page.url();
    if (url.includes('checkpoint') || url.includes('challenge')) {
        console.error('[LinkedIn] WARNING: Security challenge detected. Manual intervention needed.');
        return false;
    }

    console.error('[LinkedIn] Login successful.');
    return true;
}

async function searchHiringPosts(page, companyNames) {
    const results = [];
    const seen = loadSeenPosts();

    // Search for hiring posts mentioning target companies
    for (const company of companyNames.slice(0, 10)) {
        const query = encodeURIComponent(`"${company}" hiring`);
        const searchUrl = `https://www.linkedin.com/search/results/content/?keywords=${query}&f_C=&datePosted=past-24h&sortBy=date_posted`;

        console.error(`[LinkedIn] Searching posts about: ${company}`);
        try {
            await page.goto(searchUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
            await humanDelay(3000, 5000);

            const posts = await page.evaluate(() => {
                const items = Array.from(document.querySelectorAll('.search-results__list > li'));
                return items.slice(0, 5).map(item => {
                    const textEl = item.querySelector('.feed-shared-update-v2__description, .update-components-text');
                    const nameEl = item.querySelector('.app-aware-link span[aria-hidden="true"]');
                    const titleEl = item.querySelector('.update-components-actor__description');
                    const postLinkEl = item.querySelector('a.app-aware-link[data-control-name="view_component"]');
                    const postId = postLinkEl ? postLinkEl.href : Math.random().toString();

                    return {
                        post_id: postId,
                        text: textEl ? textEl.innerText : '',
                        poster_name: nameEl ? nameEl.innerText.trim() : 'Unknown',
                        poster_title: titleEl ? titleEl.innerText.trim() : '',
                        post_url: postLinkEl ? postLinkEl.href : '',
                    };
                });
            });

            for (const post of posts) {
                if (!post.text) continue;
                if (seen.has(post.post_id)) continue;
                if (!isHiringPost(post.text)) continue;
                if (isScamPost(post.text)) {
                    console.error(`[LinkedIn] Skipping scam post: ${post.post_id}`);
                    continue;
                }

                seen.add(post.post_id);
                const email = extractEmail(post.text);

                results.push({
                    company,
                    poster_name: post.poster_name,
                    poster_title: post.poster_title,
                    post_text: post.text.substring(0, 1000),
                    post_url: post.post_url,
                    email,
                    source: 'linkedin_post',
                });

                console.error(`[LinkedIn] FOUND hiring post from ${post.poster_name} @ ${company}`);
            }

            await humanDelay(2000, 4000);
        } catch (err) {
            console.error(`[LinkedIn] Failed to search for ${company}: ${err.message}`);
        }
    }

    saveSeenPosts(seen);
    return results;
}

async function main() {
    let companies = [];
    if (fs.existsSync(WATCHLIST_PATH)) {
        const wl = JSON.parse(fs.readFileSync(WATCHLIST_PATH, 'utf8'));
        companies = (wl.companies || []).map(c => c.name);
    }

    if (companies.length === 0) {
        console.error('[LinkedIn] No companies in watchlist.json — nothing to search.');
        console.log('[]');
        return;
    }

    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
    });
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 800 });

    let results = [];

    try {
        const loggedIn = await loginToLinkedIn(page);
        if (loggedIn) {
            results = await searchHiringPosts(page, companies);
        }
    } catch (err) {
        console.error('[LinkedIn] Fatal error:', err.message);
    } finally {
        await browser.close();
    }

    console.log(JSON.stringify(results));
}

main();
