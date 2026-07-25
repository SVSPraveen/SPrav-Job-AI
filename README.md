<div align="center">
  <img src="frontend/public/favicon.png" alt="SPrav Job AI Logo" width="120" height="120">

  # SPrav Job AI

  **An autonomous, privacy-first AI agent that finds jobs, tailors your resume, and automates applications entirely on your local machine.**

  <p>
    <a href="#-features">Features</a> •
    <a href="#-how-it-works">Architecture</a> •
    <a href="#-security--privacy">Security</a> •
    <a href="#-installation">Installation</a> •
    <a href="#-configuration">Configuration</a>
  </p>

  <p>
    <img src="https://img.shields.io/badge/Python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/React-18.x-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React">
    <img src="https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
  </p>
</div>

---

## 🎯 Overview

Job hunting is a full-time job. **SPrav Job AI** acts as your personal, highly-coordinated AI workforce. It completely automates the most exhausting parts of the job search process—from discovering open roles to drafting custom resumes and auto-applying—while guaranteeing that your personal data never leaves your machine.

> *Companies use AI to filter candidates. SPrav gives candidates AI to filter and apply to companies.*

---

## ✨ Key Features

- **Autonomous Job Discovery:** Monitors top platforms (Indeed, Hacker News, Y Combinator, Wellfound) using native, credential-free HTTP scrapers. Bypasses captchas seamlessly.
- **Precision Matching:** Mathematically calculates your fit for a role based on your background and target markets (e.g., Remote, India).
- **Intelligent Tailoring:** Custom-rewrites your resume for each specific job to bypass ATS keyword filters. Intelligently scans your portfolio to highlight the top two best-matching projects.
- **Automated Execution:** Drops a completely finished application package and cold-email draft directly into your Human Review queue. Automatically navigates ATS platforms (like Greenhouse/Lever) to submit applications.
- **Zero-Trust Local Auth:** Employs a local encrypted credential vault and Master Recovery Keys. **No central cloud servers are used.**

*(Note: LinkedIn automation has been explicitly excluded to ensure your personal accounts remain safe from bot detection).*

---

## ⚙️ How It Works

SPrav utilizes a custom **Mixture of Experts (MOE)** pipeline. It intelligently routes tasks across specialized models for data extraction, fit scoring, tailoring, and verification.

1. **Discovery:** Stealth scrapers silently pull unstructured job postings into your pipeline without requiring login credentials.
2. **Extraction:** The AI converts the unstructured text of the job description into clean, structured JSON data.
3. **Reasoning:** A deep-thinking logic model cross-references your profile and calculates a strict mathematical "Fit Score".
4. **Tailoring:** If the score meets your threshold, the local AI drafts a custom resume and a personalized cold email. 
5. **Execution:** An automation bot auto-applies on supported ATS platforms or stages a tailored email draft for 1-click manual sending for startup roles.

### Fault Tolerance & Performance
The core `daemon.py` orchestrator is heavily hardened with automatic database migrations, aggressive zero-token ATS extraction, and Null-safe fallback logic. It operates on a strict **8GB VRAM** ceiling. If high-tier cloud models (e.g., `gpt-oss-120b` via Groq) hit rate limits, the system seamlessly triggers a **Dual Local Fallback** (`qwen2.5-coder:7b-instruct` ➔ `hermes3:8b`).

For detailed architectural diagrams, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 🛡️ Security & Privacy

**SPrav operates on a strict single-source-of-truth paradigm.** Every generated bullet point and claim traces back to a verifiable entry in your canonical Knowledge Base. The system highlights actual skill gaps rather than hallucinating false proficiencies.

- **Encrypted Credential Vault:** Platform credentials are XOR-encrypted in a local SQLite database (`users.db`) using your private `.env` key.
- **Master Recovery Key:** Generates a unique `SPRAV-XXXX-XXXX` key upon sign-up as an ultimate fallback.
- **100% Local Data:** Your data never leaves your hard drive unless you explicitly configure an optional cloud AI provider.

---

## 🚀 Installation

> [!IMPORTANT]
> Running models entirely locally via Ollama requires a minimum of **8GB VRAM** and **16GB RAM** to prevent Out-of-Memory (OOM) failures. (Cloud APIs like Groq can be configured as an alternative).

### 1. Download & Install
Download the latest `SPravJobAI-Setup.exe` from the Releases page and run the installer. 
- **Program Binaries** are installed safely to `%LOCALAPPDATA%\Programs\SPrav AI` (no admin rights required).
- **User Data** (databases, configurations, and private knowledge base) is stored separately in `%LOCALAPPDATA%\SPravJobAI`, ensuring your job history persists seamlessly across updates.

### 2. Model Initialization
If you plan to use local fallbacks, ensure [Ollama](https://ollama.com/) is installed. 
*You do not need to manually pull models.* SPrav will automatically wake up Ollama in the background and pull `qwen2.5-coder:7b-instruct`, `hermes3:8b`, `deepseek-r1:7b`, `bespoke-minicheck`, and `nomic-embed-text` for you on first launch.

### 3. Launch
Double-click the **SPrav AI** shortcut on your Desktop or Start Menu. On your first launch, the system will automatically seed your `%LOCALAPPDATA%\SPravJobAI` folder with example configurations for you to fill out.

*Note: For developers looking to build the PyInstaller executable from source, refer to the developer sections in `ARCHITECTURE.md`.*

---

## 📁 Repository Structure

```text
SPrav-Job-AI/
├── engine/              # Python Backend (Core AI Logic)
├── frontend/            # React UI (Dashboard & Auth)
├── knowledge_base/      # Example configs & templates
├── discovery/           # Python HTTP Scrapers (HN, YC, Indeed, Wellfound)
├── api.py               # FastAPI server bridging Frontend, Engine, and Scraper
├── desktop_app.py       # PyWebview wrapper & PyInstaller main entrypoint
├── SPravJobAI.spec      # PyInstaller build configuration
└── installer.iss        # Inno Setup compilation script
```

---

## ⚙️ Configuration

To protect your privacy, all API keys and thresholds are stored strictly in a `.env` file within your secure `%LOCALAPPDATA%\SPravJobAI` data directory. The application will automatically create this file for you on first launch.

```env
# -----------------------------
# Security & Credentials
# -----------------------------
JWT_SECRET=super_secret_jwt_key_12345
GROQ_API_KEY=your_groq_api_key

# -----------------------------
# SMTP Email Setup (Optional)
# -----------------------------
EMAIL_SENDER=your-bot-email@gmail.com
EMAIL_PASSWORD=your_16_char_google_app_password
EMAIL_RECEIVER=your-personal-email@gmail.com

# -----------------------------
# AI Pipeline Tuning
# -----------------------------
ATS_AUTO_APPLY_THRESHOLD=0.88      # Minimum match score required to trigger an Auto-Apply
FIT_AUTO_APPLY_THRESHOLD=4.0       # DeepSeek Fit Score required for a "Fit"
COMPANY_DAILY_CAP=5                # Max applications per company per day
PORTAL_DAILY_CAP=25                # Max applications per job portal per day
TOTAL_DAILY_CAP=150                # Max applications across the entire internet per day
AUTO_APPLY_CIRCUIT_BREAKER_N=3     # Pause bot if it gets blocked X times in a row

# -----------------------------
# Ollama Optimization
# -----------------------------
OLLAMA_MAX_LOADED_MODELS=1
OLLAMA_NUM_PARALLEL=1
OLLAMA_KV_CACHE_TYPE=q8_0
OLLAMA_FLASH_ATTENTION=1
```

---

## ⚖️ Responsible Use

- **Terms of Service:** Users are solely responsible for ensuring their automated submissions comply with the Terms of Service of each respective job portal.
- **Human Review:** The Verifier Feedback Loop is designed to reduce hallucinated claims, but it is not flawless. You must periodically review the Human Review queue.
- **Rate Limits:** The daily caps are designed to avoid overwhelming employers and ATS platforms with spam. **Do not bypass them.**

<br/>
<div align="center">
  <p><b>Engineered for privacy, precision, and performance.</b></p>
  <p>&copy; SVSPraveen</p>
</div>
