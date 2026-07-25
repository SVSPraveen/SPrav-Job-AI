# The Complete SPrav Journey: From Chaos to Sniper

Building SPrav Job AI wasn't a straight line. It was a brutal series of technical roadblocks, hardware limitations, and psychological realizations about the job market. This document serves as the master record of every major struggle we faced, everything we added, and everything we ruthlessly cut to get to the current ultra-refined architecture.

---

## 1. The Hardware Struggle: The 8GB VRAM Bottleneck
**The Goal:** We wanted the AI to be fully localized and private, processing resumes and jobs entirely on our own hardware without paying cloud API fees.
**The Struggle:** Most AI models that are smart enough to write a good resume require 16GB or 24GB of VRAM. Our target hardware was heavily constrained to just 8GB of VRAM. Early prototypes crashed constantly with Out-Of-Memory (OOM) errors. We tried running models simultaneously, but the system would completely freeze up.
**What We Added (The Solution):**
- We invented the **SPrav MOE (Mixture of Experts) Architecture**. Instead of using one massive model, we split the brain into tiny, specialized experts (Extractor, Verifier, Tailor).
- We implemented a strict **Global GPU Mutex** thread lock (`gpu_mutex` in `llm_provider.py`). We passed `keep_alive: 0` to Ollama. This forced the system to strictly serialize tasks: load a model, do a task, instantly purge it from memory, and load the next one. It eliminated OOM crashes entirely.
**What We Updated:**
- We eventually realized our first localized models (`llama3.1:8b` and `magnum-v4:9b`) were hallucinating or writing generic "AI slop". 
- Based on a deep-dive research report, we overhauled the entire stack, ripping out the old models and integrating **Hermes 3** (for elite copy) and **Bespoke-Minicheck** (for state-of-the-art hallucination detection).

---

## 2. The LinkedIn Struggle: A Cat-and-Mouse Nightmare
**The Goal:** We wanted to bypass the ATS entirely by finding Founders and HR Managers directly posting jobs on LinkedIn, and auto-emailing them.
**The Struggle:** This was far from easy. LinkedIn has some of the most aggressive anti-bot security on the internet. 
- First, we had to build `stealth_crawler.js` using Puppeteer and heavy evasion plugins to mimic human behavior. 
- Then, we hit login walls. The crawler would try to log in, but LinkedIn would trigger 2FA, Captchas, and "Security Checkpoints" that completely broke the automation. 
- We spent hours building a massive UI in the React Frontend (`WatchlistManager.jsx` and `Settings.jsx`) just to manage LinkedIn credentials and track specific HR profiles.
- Even when the scraper worked, the posts were unstructured and messy.

**The Breaking Point & Removal:** 
After all that intense engineering struggle, we realized a fatal flaw in our logic: *Automating LinkedIn actively destroys a candidate's perceived value.* 
If an HR manager makes a post, and our bot perfectly replies to it 3 minutes later, it doesn't look impressive—it looks robotic and desperate. It creates massive reputational risk. It's not about avoiding getting caught; it's about looking high-value when you *do* get noticed.
**What We Removed:**
- We ruthlessly deleted the entire `linkedin_posts.js` backend crawler.
- We purged every single trace of the LinkedIn Post Scanner and credential inputs from the React Frontend UI. 
- We completely abandoned social media scraping in favor of standard ATS parsing (Indeed, YC, Wellfound).

---

## 3. The Automation Nightmares: Unifying the UX
**The Goal:** We wanted SPrav to be a 1-click native desktop experience.
**The Struggle:** We had three wildly different systems running simultaneously:
1. The local Ollama Engine (C++)
2. The FastAPI Python Backend
3. The React/Vite Frontend
Initially, the user had to open multiple terminals, manually launch Ollama, start the backend, and run `npm run dev` for the UI. If Ollama crashed, the whole pipeline silently failed. If the user asked the Copilot a question, it threw a connection error.
**What We Added:**
- We built `LaunchJobAssistant.bat` and `desktop_app.py` to wrap everything into a single native Windows Webview2 application. 
- We added `ensure_ollama_running()` to the engine. It pings localhost, and if Ollama is asleep, it silently boots it in the background using `subprocess.Popen` without interrupting the user.
- We pre-compiled the entire React frontend into static assets (`dist/`) and had FastAPI serve them directly, completely eliminating the need for Node.js in production.

**The Lingering Bugs We Fixed:**
- When we upgraded the AI models, we forgot to update the desktop bootstrapper (`ollama_manager.py`). The app would try to boot, see the old models were missing, and forcefully open a black terminal window to download gigabytes of old data! It was a frustrating UX disaster. 
- We executed a system-wide codebase audit, ripping out every hardcoded reference to the old architecture, unifying the health checks, and finally achieving a true, seamless 1-click boot sequence.

---

## 4. The Application Cap Pivot: Shotgun vs. Sniper
**The Goal:** Get as many interviews as possible.
**The Struggle:** We started with the assumption that volume equals success (The Shotgun Approach). We set the AI to apply to 150 jobs a day, with a max of 30 per company, using a low Fit Threshold of 4.0. 
We quickly learned that ATS platforms (like Lever and Greenhouse) group candidate profiles. If a recruiter saw our bot applied for *Software Engineer*, *Data Analyst*, and *IT Support* at the same company on the same day, they immediately flagged us as spam. High volume was getting us blacklisted.
**What We Updated:**
- We transitioned to the **Sniper Approach**.
- We lowered the `COMPANY_DAILY_CAP` to a hard limit of `3`. 
- We lowered the total daily cap to `50`.
- We aggressively increased the `FIT_AUTO_APPLY_THRESHOLD` to `4.2`. 
By doing this, the AI brutally rejects jobs that are "just okay" and spends its limited daily bullets *only* on absolute perfect matches. We chose intention and high value over blind spam.

*Update: We recently refined this to a **Three-Tier Limit** system to perfectly balance volume and safety:*
- *Company Cap: 5 per day*
- *Portal Cap: 25 per day*
- *Global Cap: 150 per day*
