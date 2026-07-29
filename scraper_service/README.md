# 🌐 Scraper Service

This directory houses the stealth web scrapers that power SPrav's "Discovery" phase. Instead of relying on expensive APIs, these scrapers mimic human browser behavior to extract job postings directly from the source.

## Supported Integrations

### Global Markets
* **`ats_direct.py`**: Generic fallback scraper for parsing ATS links (Greenhouse, Lever, Ashby) directly from raw URLs.
* **Indeed, YC, HN, Wellfound**: Built-in integrations for major startup and enterprise job boards.

### Indian Market Specializations
* **`naukri_scraper.py`**: Native integration for Naukri.com, India's largest job portal.
* **`internshala_scraper.py`**: Scraper for entry-level and internship roles on Internshala.
* **`hirist_scraper.py`**: Tech-focused hiring portal scraper.
* **`freshersnow_bypass.py` & `fresherstech_bypass.py`**: Specialized bypass scrapers for freshers-focused aggregators.
* **`freshershunt_bypass.py`**: Stealth bypass for FreshersHunt.

## How it works
These modules are executed asynchronously by `daemon.py`. They extract raw, unstructured job descriptions and yield them to the AI pipeline for structuring into clean JSON. They use headless browser techniques (Playwright) and anti-bot evasions to ensure high uptime.
