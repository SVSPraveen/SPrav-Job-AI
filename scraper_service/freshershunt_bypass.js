const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());
const AdblockerPlugin = require('puppeteer-extra-plugin-adblocker');
puppeteer.use(AdblockerPlugin({ blockTrackers: true }));

async function scrapeFreshershunt(limit = 10) {
    const browser = await puppeteer.launch({ 
        headless: "new",
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-web-security']
    });
    const page = await browser.newPage();
    const jobs = [];

    try {
        await page.goto('https://www.freshershunt.com/', { waitUntil: 'domcontentloaded', timeout: 60000 });
        
        const postLinks = await page.evaluate(() => {
            const links = Array.from(document.querySelectorAll('h2 a, h3 a, article a'));
            return links.map(a => ({ title: a.innerText, url: a.href })).filter(j => j.url && j.title);
        });

        // Deduplicate
        const uniqueLinksMap = new Map();
        for (const post of postLinks) {
            if (!uniqueLinksMap.has(post.url)) {
                uniqueLinksMap.set(post.url, post);
            }
        }
        const uniqueLinks = Array.from(uniqueLinksMap.values()).slice(0, limit);

        for (const post of uniqueLinks) {
            const jobPage = await browser.newPage();
            try {
                await jobPage.goto(post.url, { waitUntil: 'domcontentloaded', timeout: 30000 });
                
                // Find "Apply Now" or "Click Here" link in the article body
                const applyLink = await jobPage.evaluate(() => {
                    const buttons = Array.from(document.querySelectorAll('a'));
                    const applyBtn = buttons.find(b => {
                        const t = b.innerText.toLowerCase();
                        return t.includes('apply') || t.includes('click here') || t.includes('registration link');
                    });
                    return applyBtn ? applyBtn.href : null;
                });
                
                if (applyLink) {
                    await jobPage.goto(applyLink, { waitUntil: 'domcontentloaded', timeout: 30000 });
                    
                    // Ad-gateway bypass logic
                    // If it redirects immediately, we just wait a bit
                    await new Promise(r => setTimeout(r, 6000));
                    
                    let finalUrl = await jobPage.evaluate(() => {
                        // Sometimes there's a skip button
                        const skipBtn = document.querySelector('.skip-btn, #skip, a.get-link, a#getlink');
                        if (skipBtn && skipBtn.href) return skipBtn.href;
                        return window.location.href; 
                    });
                    
                    // Basic sanity check - if the final URL is still freshershunt, it failed to extract
                    if (!finalUrl.includes('freshershunt.com')) {
                        jobs.push({
                            title: post.title,
                            source: 'freshershunt',
                            url: finalUrl,
                            original_post: post.url
                        });
                    }
                }
            } catch (err) {
                // Silently skip on error to keep processing
            } finally {
                await jobPage.close();
            }
        }
    } catch (err) {
        console.error('Failed to scrape Freshershunt:', err);
    } finally {
        await browser.close();
    }
    
    console.log(JSON.stringify(jobs));
}

scrapeFreshershunt(process.argv[2] ? parseInt(process.argv[2]) : 10);
