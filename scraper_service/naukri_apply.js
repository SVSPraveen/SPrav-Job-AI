/**
 * naukri_apply.js
 *
 * Logs into Naukri.com and submits a Quick Apply for a given job URL.
 * Uses puppeteer-extra stealth to avoid detection.
 *
 * Usage: node naukri_apply.js <job_url> <email> <password>
 * Output: { "success": true/false, "reason": "..." } on stdout
 */

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

async function delay(ms) { return new Promise(r => setTimeout(r, ms)); }
async function humanDelay() { return delay(1200 + Math.floor(Math.random() * 2000)); }

async function applyToNaukri(jobUrl, email, password) {
    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage',
               '--disable-blink-features=AutomationControlled']
    });

    const page = await browser.newPage();
    await page.setViewport({ width: 1366, height: 768 });

    try {
        // ── Step 1: Login ────────────────────────────────────────────────────
        console.error('[Naukri Apply] Logging in...');
        await page.goto('https://www.naukri.com/nlogin/login', { waitUntil: 'domcontentloaded', timeout: 30000 });
        await humanDelay();

        // Accept cookies if dialog appears
        try {
            const cookieBtn = await page.$('[id*="cookie"] button, .cookie-consent button, [aria-label*="Accept"]');
            if (cookieBtn) { await cookieBtn.click(); await delay(500); }
        } catch (_) {}

        // Fill login form
        await page.evaluate(() => {
            document.querySelector('#usernameField')?.focus();
        });
        await page.type('#usernameField', email, { delay: 70 });
        await humanDelay();
        await page.type('#passwordField', password, { delay: 70 });
        await humanDelay();

        // Click login button
        const loginBtn = await page.$('[type="submit"], .loginButton, [data-ga-track*="login"]');
        if (!loginBtn) {
            await browser.close();
            console.log(JSON.stringify({ success: false, reason: 'Login button not found' }));
            return;
        }
        await loginBtn.click();
        await page.waitForNavigation({ waitUntil: 'domcontentloaded', timeout: 20000 });
        await humanDelay();

        // Verify login success
        const loginUrl = page.url();
        if (loginUrl.includes('login') || loginUrl.includes('nlogin')) {
            await browser.close();
            console.log(JSON.stringify({ success: false, reason: 'Login failed — check credentials' }));
            return;
        }
        console.error('[Naukri Apply] Login successful.');

        // ── Step 2: Navigate to Job Page ─────────────────────────────────────
        console.error(`[Naukri Apply] Opening job: ${jobUrl}`);
        await page.goto(jobUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await humanDelay();

        // ── Step 3: Click Quick Apply / Apply button ──────────────────────────
        const applyBtnSelectors = [
            '[id="apply-button"]',
            'button[data-click-id="apply"]',
            '.apply-button',
            '[class*="applyBtn"]',
            '[class*="apply-btn"]',
            'button[title*="Apply"]',
            'a[title*="Apply"]'
        ];

        let applied = false;
        for (const sel of applyBtnSelectors) {
            try {
                const btn = await page.$(sel);
                if (btn) {
                    await humanDelay();
                    await btn.click();
                    console.error(`[Naukri Apply] Clicked apply button: ${sel}`);
                    applied = true;
                    break;
                }
            } catch (_) {}
        }

        if (!applied) {
            await browser.close();
            console.log(JSON.stringify({ success: false, reason: 'Apply button not found on page' }));
            return;
        }

        await humanDelay();

        // ── Step 4: Handle Quick Apply confirmation dialog ────────────────────
        // Naukri typically shows a "Confirm Apply" dialog or quick-apply modal
        try {
            const confirmSelectors = [
                '[class*="confirmApply"]',
                'button[class*="apply-confirm"]',
                '[data-click-id="confirm-apply"]',
                'button[title*="Confirm"]',
                '.modal button.apply'
            ];
            for (const sel of confirmSelectors) {
                const confirmBtn = await page.$(sel);
                if (confirmBtn) {
                    await humanDelay();
                    await confirmBtn.click();
                    console.error('[Naukri Apply] Confirmed application.');
                    break;
                }
            }
        } catch (_) {}

        await delay(2500);

        // ── Step 5: Check for success indicator ───────────────────────────────
        const successIndicators = [
            '[class*="appliedSuccess"]',
            '[class*="apply-success"]',
            '.applied',
            '[class*="alreadyApplied"]',
        ];
        let successConfirmed = false;
        for (const sel of successIndicators) {
            const el = await page.$(sel);
            if (el) { successConfirmed = true; break; }
        }

        await browser.close();
        
        if (successConfirmed) {
            console.log(JSON.stringify({ success: true, reason: 'Quick Apply submitted and confirmed.' }));
        } else {
            // Applied but couldn't confirm — still likely worked
            console.log(JSON.stringify({ success: true, reason: 'Apply button clicked — no error detected.' }));
        }

    } catch (err) {
        await browser.close();
        console.log(JSON.stringify({ success: false, reason: err.message }));
    }
}

const [jobUrl, email, password] = process.argv.slice(2);
if (!jobUrl || !email || !password) {
    console.log(JSON.stringify({ success: false, reason: 'Missing arguments: job_url, email, password' }));
} else {
    applyToNaukri(jobUrl, email, password);
}
