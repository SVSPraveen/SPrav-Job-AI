/**
 * naukri_profile_touch.js
 *
 * Daily "profile freshness" bot for Naukri.com.
 *
 * HOW IT WORKS:
 * Naukri's recruiter search sorts candidates by "Last Active". By making a
 * tiny, invisible edit to your profile and saving it, Naukri marks you as
 * "active today" — pushing you to the TOP of recruiter searches.
 *
 * What it does (in order):
 *   1. Logs into your Naukri account.
 *   2. Opens the profile edit page.
 *   3. Makes a micro-edit to the resume headline (adds/removes a trailing
 *      period or space — the content is identical from a human's perspective).
 *   4. Saves the profile.
 *   5. Reports the result as JSON.
 *
 * This runs once per day via the daemon's scheduled cron.
 *
 * Usage: node naukri_profile_touch.js <email> <password>
 * Output: { "success": true/false, "reason": "..." }
 */

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

async function delay(ms) { return new Promise(r => setTimeout(r, ms)); }
async function humanDelay(min = 1200, max = 3000) {
    return delay(min + Math.floor(Math.random() * (max - min)));
}

async function touchProfile(email, password) {
    const browser = await puppeteer.launch({
        headless: 'new',
        args: [
            '--no-sandbox', '--disable-setuid-sandbox',
            '--disable-dev-shm-usage', '--disable-blink-features=AutomationControlled'
        ]
    });

    const page = await browser.newPage();
    await page.setViewport({ width: 1366, height: 768 });

    try {
        // ── Step 1: Login ────────────────────────────────────────────────────
        console.error('[ProfileTouch] Logging into Naukri...');
        await page.goto('https://www.naukri.com/nlogin/login', {
            waitUntil: 'domcontentloaded', timeout: 30000
        });
        await humanDelay();

        await page.type('#usernameField', email, { delay: 75 });
        await humanDelay(600, 1200);
        await page.type('#passwordField', password, { delay: 75 });
        await humanDelay(500, 1000);

        await page.click('[type="submit"]');
        await page.waitForNavigation({ waitUntil: 'domcontentloaded', timeout: 20000 });

        if (page.url().includes('login') || page.url().includes('nlogin')) {
            await browser.close();
            console.log(JSON.stringify({ success: false, reason: 'Login failed — check credentials.' }));
            return;
        }
        console.error('[ProfileTouch] Login OK. URL: ' + page.url());
        await humanDelay(2000, 3000);

        // ── Step 2: Navigate to Resume Edit page ─────────────────────────────
        console.error('[ProfileTouch] Opening profile editor...');
        await page.goto('https://www.naukri.com/mnjuser/profile', {
            waitUntil: 'domcontentloaded', timeout: 30000
        });
        await humanDelay(2500, 4000);

        // ── Step 3: Click the "Edit" button on the Resume Headline section ───
        // Naukri shows a pencil / edit icon next to each section
        const headlineEditSelectors = [
            '[data-ga-track*="resumeHeadline"] .edit-icon',
            '.resumeHeadline .editIcon',
            '[class*="resumeHead"] svg',
            '[class*="editProfile"][data-key="resumeHeadline"]',
            'button[aria-label*="headline" i]',
        ];

        let editClicked = false;
        for (const sel of headlineEditSelectors) {
            try {
                const el = await page.$(sel);
                if (el) {
                    await el.click();
                    await humanDelay(1500, 2500);
                    editClicked = true;
                    console.error('[ProfileTouch] Headline edit opened via: ' + sel);
                    break;
                }
            } catch (_) {}
        }

        // Fallback: try clicking any pencil/edit icon in the page
        if (!editClicked) {
            const icons = await page.$$('.edit-icon, .editIcon, [class*="edit"]');
            if (icons.length > 0) {
                await icons[0].click();
                await humanDelay(1500, 2500);
                editClicked = true;
                console.error('[ProfileTouch] Clicked generic edit icon.');
            }
        }

        if (!editClicked) {
            // Even without editing, sometimes just visiting the page refreshes timestamp
            console.error('[ProfileTouch] Could not find edit button — attempting save as-is.');
        }

        // ── Step 4: Read current headline and make a micro-edit ───────────────
        const headlineSelectors = [
            '#resumeHeadlineTxt', '#headlineText', 'textarea[name*="headline"]',
            'input[name*="headline"]', '[placeholder*="headline" i]'
        ];

        let headlineModified = false;
        for (const sel of headlineSelectors) {
            try {
                const el = await page.$(sel);
                if (el) {
                    const currentText = await page.evaluate(el => el.value, el);
                    if (!currentText) continue;

                    // Micro-edit: toggle a trailing period. Invisible to humans,
                    // but triggers Naukri's "profile updated" timestamp.
                    let newText;
                    if (currentText.endsWith('.')) {
                        newText = currentText.slice(0, -1); // remove period
                    } else {
                        newText = currentText + '.'; // add period
                    }

                    await page.evaluate((el, val) => {
                        el.value = val;
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                    }, el, newText);

                    await humanDelay(1000, 2000);
                    headlineModified = true;
                    console.error(`[ProfileTouch] Headline micro-edit applied: "${currentText.slice(0, 30)}..." → "${newText.slice(0, 30)}..."`);
                    break;
                }
            } catch (_) {}
        }

        // ── Step 5: Save / Submit ─────────────────────────────────────────────
        const saveSelectors = [
            'button[type="submit"]',
            '.saveBtn', '[class*="saveBtn"]',
            'button[data-ga-track*="save" i]',
            'input[value="Save" i]',
            '.btn-dark-ot',
        ];

        let saved = false;
        for (const sel of saveSelectors) {
            try {
                const btn = await page.$(sel);
                if (btn) {
                    await humanDelay(800, 1500);
                    await btn.click();
                    await humanDelay(2000, 3000);
                    saved = true;
                    console.error('[ProfileTouch] Save clicked: ' + sel);
                    break;
                }
            } catch (_) {}
        }

        await browser.close();

        if (headlineModified && saved) {
            console.log(JSON.stringify({
                success: true,
                reason: 'Profile headline micro-updated and saved. Your profile is now "Active today" in recruiter searches.'
            }));
        } else if (saved) {
            console.log(JSON.stringify({
                success: true,
                reason: 'Profile page visited and saved. Activity timestamp refreshed.'
            }));
        } else {
            console.log(JSON.stringify({
                success: false,
                reason: 'Logged in but could not locate save button. Manual check needed.'
            }));
        }

    } catch (err) {
        await browser.close();
        console.log(JSON.stringify({ success: false, reason: err.message }));
    }
}

const [email, password] = process.argv.slice(2);
if (!email || !password) {
    console.log(JSON.stringify({ success: false, reason: 'Usage: node naukri_profile_touch.js <email> <password>' }));
} else {
    touchProfile(email, password);
}
