# Scraper Service (`/scraper_service`)

The Scraper Service is a specialized, headless automation suite designed to navigate complex Applicant Tracking Systems (ATS) and job board frontends that lack public APIs.

## 🏗️ Architectural Overview

Built on Node.js and Puppeteer Extra, this microservice handles the high-friction aspects of job discovery, including bypassing bot-mitigation platforms (e.g., Cloudflare, DataDome) through stealth plugins and behavioral emulation.

## 🧩 Core Capabilities

- **Stealth Browsing**: Utilizes `puppeteer-extra-plugin-stealth` to mask automated signatures, ensuring high-reliability scraping without triggering IP bans.
- **Dynamic DOM Parsing**: Extracts structured JSON data (job titles, requirements, salary bands) directly from deeply nested, dynamically rendered React/Vue DOM trees.
- **IPC Communication**: Runs as a localized microservice, communicating with the primary Python orchestration daemon via lightweight inter-process communication (IPC) sockets.

## ⚙️ Configuration

The service can be scaled or adjusted via the local configuration files to manage concurrency limits and rate-limit backoffs, protecting the user's IP integrity.
