<p align="center">
  <img src="frontend/public/favicon.png" alt="SPrav Logo" width="150" height="150">
</p>

<h1 align="center">
  SPrav Job AI
</h1>

<h4 align="center">
  A local-first, human-in-the-loop job-search assistant that discovers relevant roles, evaluates candidate fit, tailors application materials, and verifies generated claims.
</h4>

<p align="center">
  <a href="#-what-it-does">What</a> •
  <a href="#-how-it-works">How</a> •
  <a href="#-for-teams">For Teams</a> •
  <a href="#-security--offline-auth">Security</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-repository-structure">Structure</a> •
  <a href="#-configuration-env">Config</a> •
  <a href="#-installation">Install</a> •
  <a href="#-current-limitations">Limitations</a>
</p>

<p align="center">
  <a href="https://github.com/SVSPraveen/SPrav-Job-AI/stargazers"><img src="https://img.shields.io/github/stars/SVSPraveen/SPrav-Job-AI?style=for-the-badge&color=FF6B6B" alt="Stars"></a>
  <a href="https://github.com/SVSPraveen/SPrav-Job-AI/network/members"><img src="https://img.shields.io/github/forks/SVSPraveen/SPrav-Job-AI?style=for-the-badge&color=4ECDC4" alt="Forks"></a>
  <a href="https://github.com/SVSPraveen/SPrav-Job-AI/issues"><img src="https://img.shields.io/github/issues/SVSPraveen/SPrav-Job-AI?style=for-the-badge&color=FFD93D" alt="Issues"></a>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/React-18.x-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React">
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
</p>

<br/>

> *Companies use AI to screen candidates. SPrav helps candidates discover relevant roles and prepare accurate, tailored applications.*

---

## 📖 Why I Built This

I built SPrav Job AI because I found the repetitive parts of job hunting—finding relevant roles, tailoring resumes, and tracking applications—time-consuming. The goal was to automate repetitive work while keeping humans responsible for every application submitted.

---

## 🎯 What it does

Job hunting is a full-time job. **SPrav automates the most repetitive, exhausting parts of it — while keeping a human in the loop wherever automation is genuinely risky.**

- 🌐 **Monitors job postings** across multiple sources — Hacker News "Who's Hiring," Y Combinator jobs, Naukri (discovery only), Internshala, Hirist, and several India-specific off-campus drive boards. SPrav uses a mix of terms-aware, credential-free HTTP connectors and browser-based connectors for supported public pages. For platforms like Indeed, it relies on safer approaches such as public employer career pages, official APIs/feeds, ATS job-board endpoints, user-provided job URLs, email job alerts, or manual browser imports.
- 📬 **Wellfound is handled differently on purpose**: instead of directly scraping the platform, SPrav reads job-alert emails from the user's Gmail account through user-authorized access. This keeps the integration under the user's control and avoids direct platform scraping.
- 🚫 **LinkedIn is never automated, at all** — no login, no scraping, no auto-sending. Every LinkedIn-related feature generates a manual search URL and a drafted note for you to copy, paste, and send yourself. This is a deliberate, non-negotiable design choice to protect your real account from ban risk.
- 🎯 **Application Scope Enforcer** — you define target locations and roles (with AI-suggested broad candidates you can accept or dismiss), and every job is checked against your rules *before* any LLM call is made, so nothing outside your actual criteria burns compute or gets considered.
- 🏢 **Watchlist Management** — track specific companies' career pages with typeahead search, so the daemon prioritizes roles from places you actually want to work.
- ✍️ **Resume tailoring** that rewrites bullets per job to improve ATS keyword coverage, while a **deterministic (non-LLM) matching step** picks the best 2 projects for each job from your GitHub/portfolio work — project selection was deliberately moved off the LLM after testing showed even capable models could confidently pick the wrong project and invent supporting details for it.
- 📄 **Local PDF generation** via ReportLab, without requiring Microsoft Word, LaTeX, or an external document-generation service. The renderer can dynamically adjust font sizes and trim selected bullet content to produce a single-page resume.
- 🛡️ **The system verifies generated claims against the user’s knowledge base:** The application checks generated content against the user's knowledge base and rejects inconsistencies when detected. This reduces hallucinations but does not eliminate them, falling back to your real, original wording when needed.
- 🤝 **Referral & recruiter outreach** — finds real people at target companies (via GitHub, company team pages, and blog bylines — never LinkedIn scraping) and drafts a personalized note for you to send manually, plus a curated (not scraped) list of recruiters/agencies ranked against your actual skill profile.
- 🎓 **Prep Center** — turns detected skill gaps into an actionable list with free resources, and generates STAR-format behavioral interview stories tailored to each role you're applying to.
- 📅 **Gateway Test Tracker** — a reminder/calendar feature for recurring fresher-hiring gateway tests (TCS NQT, Infosys InfyTQ, Wipro Elite NLTH, Capgemini), since a single qualifying test can open doors to hundreds of affiliated companies at once.

## ⚙️ How it works

When the engine is running, this is the real pipeline every job goes through:

1. **Discovery** — terms-aware connectors (Python HTTP-based, plus a small number of Node.js browser-based connectors for supported public pages) find new postings.
2. **Liveness / legitimacy / repost checks** — dead links, likely scam postings, and duplicate reposts are filtered out before anything else runs.
3. **Scope gate** — the job is checked against your location/role rules *before any LLM call*, so out-of-scope postings never cost compute.
4. **Extraction** — an LLM converts the unstructured job description into structured data (title, requirements, years of experience).
5. **Fit evaluation** — a reasoning model scores the job against your actual profile, with explicit leniency for postings labeled Entry-Level/Graduate/Junior/Intern that tend to overstate experience requirements.
6. **Tailoring** — if the job passes, the system deterministically selects your best-matching 2 projects, rewrites your resume bullets and cover letter for this specific job, and verifies generated claims against the user’s knowledge base before accepting it.
7. **Human-Approved Dispatch** — SPrav prepares the complete application package (resume, cover letter, and extracted form data) and routes it to your **Application Review queue**. The system performs the repetitive analysis and tailoring, but you remain explicitly responsible for every submitted application. For supported ATS endpoints, the dashboard provides a controlled, guided submission workflow; for everything else, you use the provided direct link to submit the tailored documents yourself.

## 👥 For Teams

SPrav is built as a personal tool, but it's designed so a small group of people (different tracks — AI/ML, backend, cloud, cybersecurity, whatever) can each run it independently:

- Each person runs their **own separate installation** with their **own credentials** (Groq API key, GitHub token, Gmail OAuth) entered through the in-app Settings screen — nothing is shared, pooled, or pre-filled between installs.
- All personal data (resumes, job history, credentials, logs) lives entirely in that person's own `%LOCALAPPDATA%\SPravJobAI` folder — never synced, never uploaded, never shared across installs.
- If you're cloning this to share with friends/teammates, make sure your own `.env`, real `config.json`, and populated `me.json` are never committed — only the `.example` templates should ever go into the repo.

## 🔒 Security & Offline Auth

Because SPrav runs independently of any central cloud service, it uses a local-first authentication and credential model:

- **AES-GCM Encrypted Credential Vault** — platform credentials are cryptographically secured in a local SQLite database using industry-standard AES-GCM and bcrypt for password hashing.
- **Local-first recovery** — account recovery does not depend on any third-party auth server.
- **Bring-your-own API keys** — Groq and GitHub tokens are entered per-install through the Settings screen (or `.env`, if you prefer), never hardcoded or shared.
- **SPrav Copilot & Guide Tour** — an in-app assistant and walkthrough panel to help you configure the app and understand what each screen does, without needing to read source code.

---

## 🧠 Architecture

SPrav routes different tasks to different models rather than relying on one monolithic LLM:

- **Reasoning-heavy tasks** (fit scoring, archetype classification): a dedicated reasoning model.
- **Structured generation** (JSON extraction, resume/bullet rewriting, STAR stories): a model optimized for reliable structured output.
- **Verification** (fact-checking, ghost-job/scam detection): a separate model acting as an independent checker, so the model generating content isn't the same one grading its own work.
- **Cloud-first for heavier workloads, with a local fallback**: resume tailoring uses Groq by default for speed and can fall back to a local Ollama model when the cloud call is unavailable. This allows core extraction, evaluation, and document-generation workflows to continue locally, although online job discovery and external integrations still require internet access.

**On reliability, honestly:** the daemon has real safeguards — SQLite concurrency handling with retry logic, a circuit breaker that pauses guided submission after repeated consecutive failures, defensive fallbacks so a single bad job can't take down the whole discovery cycle, and detailed logs (`api.log`, `daemon.log`, `crash.log`) written to your data directory for every run. It is *not* claimed to be crash-proof — like any long-running local automation, occasional issues surface, and checking those logs is the first step if something looks stuck.

For the full orchestrator design and pipeline diagram, see `ARCHITECTURE.md`.

---

## 📁 Repository Structure

```text
SPrav-Job-AI/
├── engine/              # Python backend — core AI logic and daemon orchestration
│   ├── auth.py          # Local auth and credential encryption
│   ├── daemon.py         # Pipeline orchestrating scrapers, scoring, tailoring, and dispatch
│   ├── scope_enforcer.py # Application Scope gate (runs before any LLM call)
│   ├── tailor.py         # Deterministic project selection + resume/cover-letter tailoring
│   ├── fact_checker.py   # Metric/technology hallucination detection
│   └── llm_provider.py   # Routing between cloud (Groq) and local (Ollama) models
├── frontend/            # React UI
│   ├── src/              # Vite application source
│   └── dist/              # Compiled static assets (served by FastAPI)
├── discovery/            # Python terms-aware HTTP connectors (HN, YC, ATS-direct discovery)
├── scraper_service/       # Node.js browser-based connectors for supported public pages
├── apply/                 # Guided submission integrations for supported ATS platforms
├── knowledge_base/        # Example configs and templates (never commit your real me.json/scope.json)
├── api.py                # FastAPI server bridging frontend, engine, and scrapers
├── desktop_app.py         # PyWebView wrapper and PyInstaller entrypoint
├── SPravJobAI.spec        # PyInstaller build configuration
└── installer.iss          # Inno Setup installer script
```

---

## ⚙️ Configuration (`.env`)

Application thresholds and non-sensitive runtime settings can be stored in a `.env` file inside `%LOCALAPPDATA%\SPravJobAI`. Secrets entered through the application Settings screen are stored in the encrypted credential vault. The `.env` method remains available as a developer fallback, but values placed there are stored as plaintext and must never be committed to Git.

```env
# -----------------------------
# Security
# -----------------------------
JWT_SECRET=replace_with_a_long_randomly_generated_secret

# -----------------------------
# AI API Keys (optional — falls back to local Ollama if unset)
# -----------------------------
GROQ_API_KEY=your_groq_api_key

# GitHub token, used to raise the rate limit on referral/contact discovery lookups
# (works fine unauthenticated too, just at GitHub's lower 60-requests/hour limit)
GITHUB_TOKEN=your_github_personal_access_token

# -----------------------------
# SMTP Email Setup (optional)
# -----------------------------
EMAIL_SENDER=your-bot-email@gmail.com
EMAIL_PASSWORD=your_16_char_google_app_password
EMAIL_RECEIVER=your-personal-email@gmail.com

# -----------------------------
# AI Pipeline Tuning
# -----------------------------
# Minimum ATS keyword coverage required to mark an application
# as ready for guided review
ATS_AUTO_APPLY_THRESHOLD=0.88

# Minimum fit score required to mark an application
# as ready for guided review
FIT_AUTO_APPLY_THRESHOLD=4.0

# Max applications per company per day
COMPANY_DAILY_CAP=1

# Max applications per job portal per day
PORTAL_DAILY_CAP=10

# Legacy internal variable name:
# maximum human-approved guided submissions per day
AUTO_APPLY_DAILY_CAP=10

# Human-assisted applications per day (everything routed to your Review queue)
HUMAN_ASSIST_DAILY_CAP=20

# Legacy internal variable name:
# pause guided submission after repeated portal failures
AUTO_APPLY_CIRCUIT_BREAKER_N=3

# -----------------------------
# Local Ollama Optimization
# -----------------------------
OLLAMA_MAX_LOADED_MODELS=1
OLLAMA_NUM_PARALLEL=1
OLLAMA_KV_CACHE_TYPE=q8_0
OLLAMA_FLASH_ATTENTION=1
```

---

## 🚀 Installation

> **Hardware Note:** The local-model configuration was designed and tested around a machine with **8 GB VRAM and 16 GB RAM**. This is the recommended configuration for running the LLM workloads locally. Smaller models or CPU execution may work on lower-specification hardware but will be slower and have not been tested as extensively. The daemon orchestrates small, quantized models strictly one at a time (`OLLAMA_MAX_LOADED_MODELS=1`) so you don't need a massive rig. If your machine doesn't meet these recommendations, you can configure a cloud provider (Groq, free tier) instead.

### Prerequisites (source/dev builds only)
- Python 3.10+
- Playwright (`playwright install`)
- Node.js (v18+) — used by a small number of browser-based connectors for supported public pages; bundled automatically in the packaged Windows installer, so end users don't need to install it separately.

### Install
Download the latest installer from the Releases page and run it.
- **Program binaries** install to `%LOCALAPPDATA%\Programs\SPrav AI` (no admin rights required).
- **Your data** (databases, config, resumes, knowledge base) lives separately in `%LOCALAPPDATA%\SPravJobAI`, so it survives app updates and reinstalls.

### First Launch
On first launch, SPrav seeds your data directory with example configuration files for you to fill in through the Knowledge Base and Application Scope screens. If you're using local models, Ollama will pull the required models automatically in the background the first time it runs.

*For building from source or developer setup, see `ARCHITECTURE.md`.*

---

## 👤 Author
**SVSPraveen** ([GitHub](https://github.com/SVSPraveen))
*I designed and built the orchestration architecture coordinating these tasks. I did not train or fine-tune any of the underlying LLMs.*

## ⚖️ Responsible Use
- **Platform terms** — users are responsible for ensuring that discovery and guided-submission workflows comply with the applicable platform and ATS terms.
- **Human Review matters** — the fact-checking system substantially reduces hallucinated claims, but it doesn't catch everything. Periodically review your Application Review queue and generated resumes carefully before approving.
- **Rate limits exist for a reason** — the daily caps are there to avoid spamming employers and ATS platforms. Don't remove them.

## 🛡️ Current Limitations
Being upfront about where this stands today, rather than overselling it:
- This is a personal automation tool, actively developed and tested by its author — not a polished commercial product.
- Resume/cover-letter fact-checking catches invented numbers and invented technologies, but you should still spot-check generated output yourself before it goes out, especially early on.
- Several discovery connectors depend on public page structures, feeds, or ATS endpoints that may change over time. A connector may temporarily stop returning results until its integration is updated.
- Contribution and testing on non-Windows platforms is limited; the packaged installer currently targets Windows.

---

## 🤝 Contributing

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

**Adding a new connector?** Look at the existing templates in `scraper_service/` and `discovery/`. New connectors should be credential-free where possible to be merged into `main`.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.

<br/>
<div align="center">
  <p>Built for one person's real job search — shared in case it helps yours too.</p>
</div>