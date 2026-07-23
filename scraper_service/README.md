# Scraper Service (`scraper_service/`)

The `scraper_service` directory contains specialized, direct-to-ATS scraping tools. 

While generic job boards (like LinkedIn or Indeed) are extremely noisy, heavily scraped by bots, and often feature stale "ghost" jobs, this service bypasses aggregators entirely by crawling the ATS pages of companies directly.

---

## 🎯 Direct-to-ATS Strategy

By maintaining a curated list of target companies, this module programmatically iterates through their known ATS endpoints (Greenhouse, Lever, Workday) to find postings the exact minute they go live. This strategy grants a significant "first-mover" advantage in highly competitive application pools.

## 📂 Key Files

- **`ats_direct.py`**: The core direct scraping logic. It parses the DOM of Greenhouse/Lever company boards, looking for `<script>` JSON blobs or standard HTML job listings to extract raw Job Descriptions and posting URLs.
- **`company_list.txt`**: A plain-text, newline-separated list of company names or target URLs. This acts as the seed list for the `ats_direct.py` crawler.

## 🔄 Integration with Discovery

When `ats_direct.py` successfully finds a new job link, it passes the URL and raw HTML description over to the `discovery/db.py` logic, which inserts it into the `jobs.db` database as a `new` job. From there, the `engine`'s daemon picks it up for processing.
