const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const axios = require('axios');
const { v4: uuidv4 } = require('uuid');

puppeteer.use(StealthPlugin());

// Configurable multi-platform targets
const TARGETS = [
    { name: "LinkedIn", url: "https://www.linkedin.com/jobs/search?keywords=Software%20Engineer&location=Remote&f_TPR=r86400" },
    // You can add logic for Indeed, Naukri, WeWorkRemotely, Wellfound here
    // { name: "WeWorkRemotely", url: "https://weworkremotely.com/categories/remote-programming-jobs#job-listings" }
];

async function randomDelay(min = 2000, max = 5000) {
    const delay = Math.floor(Math.random() * (max - min + 1)) + min;
    await new Promise(r => setTimeout(r, delay));
}

async function scrapePlatform(browser, target) {
    console.log(`\n🥷 [Node Scraper] Navigating to ${target.name}...`);
    const page = await browser.newPage();
    
    // Set a random user agent or viewport if not using stealth defaults
    await page.setViewport({ width: 1280 + Math.floor(Math.random() * 100), height: 800 + Math.floor(Math.random() * 100) });
    
    try {
        await page.goto(target.url, { waitUntil: 'networkidle2', timeout: 60000 });
        
        console.log(`[Node Scraper] Performing human-like scrolling on ${target.name}...`);
        for(let i=0; i<3; i++) {
            await page.evaluate(() => window.scrollBy(0, window.innerHeight / 2));
            await randomDelay(1000, 3000);
        }

        console.log(`[Node Scraper] Extracting raw unstructured text...`);
        // Instead of strict CSS selectors (which break), we extract raw text blocks
        // The NuExtract model in Phase 1 will parse this raw text perfectly.
        const jobs = await page.evaluate(() => {
            const results = [];
            // Generic extraction strategy for HR posts and job cards
            const cards = document.querySelectorAll('li, .job-card, .base-card, .result-card');
            cards.forEach(card => {
                const text = card.innerText.trim();
                const links = Array.from(card.querySelectorAll('a')).map(a => a.href);
                // Basic filter to ensure it's a substantive block of text
                if (text.length > 50 && links.length > 0) {
                    results.push({
                        raw_text: text,
                        primary_url: links[0]
                    });
                }
            });
            return results;
        });
        
        await page.close();
        
        const formattedJobs = jobs.map(j => ({
            id: `${target.name.toLowerCase()}_${uuidv4()}`,
            title: "UNSTRUCTURED_EXTRACT", 
            company: "UNKNOWN",
            url: j.primary_url,
            description: `Source: ${target.name}\nRaw Text:\n${j.raw_text}`,
            location: "Remote",
            source: target.name
        }));
        
        return formattedJobs;

    } catch (e) {
        console.error(`[Node Scraper] Error scraping ${target.name}: ${e.message}`);
        await page.close();
        return [];
    }
}

async function runStealthScraper() {
    console.log("=========================================");
    console.log("🕷️ [Stealth Scraper] Initializing Multi-Platform Engine...");
    console.log("=========================================");
    
    // In production, configure proxy rotation here:
    // const browser = await puppeteer.launch({ args: ['--proxy-server=IP:PORT'] });
    const browser = await puppeteer.launch({ headless: true });
    
    let allJobs = [];
    
    for (const target of TARGETS) {
        const jobs = await scrapePlatform(browser, target);
        allJobs = allJobs.concat(jobs);
        await randomDelay(3000, 7000); // Delay between platforms
    }
    
    await browser.close();
    
    console.log(`\n[Stealth Scraper] Successfully extracted ${allJobs.length} raw job posts.`);
    
    if (allJobs.length === 0) return;
    
    try {
        console.log(`[Stealth Scraper] Injecting raw data into Python SPrav MoE Pipeline...`);
        const res = await axios.post('http://127.0.0.1:8000/api/jobs/bulk', allJobs);
        console.log(`[Stealth Scraper] Success! Inserted ${res.data.inserted} posts into SQLite for NuExtract processing.`);
    } catch (e) {
        console.error(`[Stealth Scraper] Failed to send jobs to backend:`, e.message);
    }
}

runStealthScraper().catch(console.error);
