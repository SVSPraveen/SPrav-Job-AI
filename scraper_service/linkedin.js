const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const axios = require('axios');
const { v4: uuidv4 } = require('uuid');

puppeteer.use(StealthPlugin());

async function scrapeLinkedIn() {
    console.log("=========================================");
    console.log("🥷 [Node Scraper] Launching stealth browser...");
    console.log("=========================================");
    
    const browser = await puppeteer.launch({ headless: true });
    const page = await browser.newPage();
    
    // We will scrape a basic public search for Remote jobs posted in the last 24 hours.
    // In production, this can pull from a dynamic user config.
    const url = "https://www.linkedin.com/jobs/search?keywords=Software%20Engineer&location=Remote&f_TPR=r86400";
    
    console.log(`[Node Scraper] Navigating to ${url}`);
    await page.goto(url, { waitUntil: 'networkidle2' });
    
    console.log("[Node Scraper] Bypassing anti-bot checks and scrolling...");
    // Scroll down multiple times to trigger infinite scrolling
    for(let i=0; i<3; i++) {
        await page.evaluate(() => window.scrollBy(0, document.body.scrollHeight));
        await new Promise(r => setTimeout(r, 2000));
    }
    
    console.log("[Node Scraper] Extracting job data...");
    
    const jobs = await page.evaluate(() => {
        const jobCards = document.querySelectorAll('.base-card');
        const results = [];
        jobCards.forEach(card => {
            const titleEl = card.querySelector('.base-search-card__title');
            const companyEl = card.querySelector('.base-search-card__subtitle');
            const urlEl = card.querySelector('.base-card__full-link');
            const locEl = card.querySelector('.job-search-card__location');
            
            if (titleEl && companyEl && urlEl) {
                results.push({
                    title: titleEl.innerText.trim(),
                    company: companyEl.innerText.trim(),
                    url: urlEl.href.trim(),
                    location: locEl ? locEl.innerText.trim() : "Remote",
                    description: "Detailed description requires full page load. Extracting summary for now.",
                });
            }
        });
        return results;
    });
    
    await browser.close();
    
    console.log(`[Node Scraper] Successfully extracted ${jobs.length} jobs from LinkedIn.`);
    
    if (jobs.length === 0) {
        console.log("[Node Scraper] No jobs found or blocked by captcha. Try again later.");
        return;
    }
    
    const formattedJobs = jobs.map(j => ({
        id: `linkedin_${uuidv4()}`,
        title: j.title,
        company: j.company,
        url: j.url,
        description: `Source: LinkedIn Public Search\nTitle: ${j.title}\nCompany: ${j.company}\n${j.description}`,
        location: j.location,
        source: "LinkedIn"
    }));
    
    try {
        console.log(`[Node Scraper] Injecting into Python FastAPI Database...`);
        const res = await axios.post('http://127.0.0.1:8000/api/jobs/bulk', formattedJobs);
        console.log(`[Node Scraper] Success! Inserted ${res.data.inserted} NEW unique jobs into SQLite.`);
    } catch (e) {
        console.error(`[Node Scraper] Failed to send jobs to backend:`, e.message);
    }
}

scrapeLinkedIn().catch(console.error);
