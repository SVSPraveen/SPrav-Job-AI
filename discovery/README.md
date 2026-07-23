# 🕵️‍♂️ Discovery Module (`/discovery`)

The Discovery layer is responsible for aggressively hunting down job listings before they hit the mainstream aggregators.

## 🛡️ Anti-Bot Evasion
Modern job boards utilize sophisticated fingerprinting to block automated scraping. Our Discovery module utilizes stealth configurations in `puppeteer-core` to mask WebDriver flags, randomize viewport metrics, and bypass Cloudflare challenges.

## 🌐 Supported Targets
* LinkedIn
* Naukri
* Indeed
* Wellfound
* YC Work at a Startup

## 📥 Output
The scrapers output raw, unstructured HTML payloads directly to the local SQLite database, where they await parsing by the `Qwen` extraction model in the Engine layer.
