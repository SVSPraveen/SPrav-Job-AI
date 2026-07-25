<p align="center">
  <img src="frontend/public/favicon.png" alt="SPrav Logo" width="150" height="150">
</p>

<h1 align="center">
  SPrav Job AI
</h1>

<h4 align="center">SPrav finds matching jobs, tailors your resume, fact-checks every claim, and submits the application — running locally, end to end.</h4>

<p align="center">
  <a href="#-what-it-does">What</a> •
  <a href="#-how-it-works">How</a> •
  <a href="#-security--offline-auth">Security</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-repository-structure">Structure</a> •
  <a href="#-configuration-env">Config</a> •
  <a href="#-installation">Install</a>
</p>

<p align="center">
  <a href="https://github.com/SVSPraveen/SPrav-Job-AI/stargazers"><img src="https://img.shields.io/github/stars/SVSPraveen/SPrav-Job-AI?style=for-the-badge&color=FF6B6B" alt="Stars"></a>
  <a href="https://github.com/SVSPraveen/SPrav-Job-AI/network/members"><img src="https://img.shields.io/github/forks/SVSPraveen/SPrav-Job-AI?style=for-the-badge&color=4ECDC4" alt="Forks"></a>
  <a href="https://github.com/SVSPraveen/SPrav-Job-AI/issues"><img src="https://img.shields.io/github/issues/SVSPraveen/SPrav-Job-AI?style=for-the-badge&color=FFD93D" alt="Issues"></a>
  <img src="https://img.shields.io/badge/Python-3.13+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/React-18.x-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React">
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
</p>

<br/>

> *Companies use AI to filter candidates. SPrav gives candidates AI to filter and apply to companies.*

---

## 🎯 What it does

Job hunting is a full-time job. **SPrav completely automates the most exhausting parts of the process.** 

Instead of mindlessly scrolling through job boards, SPrav acts as your personal, highly-coordinated AI workforce:
- 🌐 **Monitors the internet** for new job postings (Indeed, Hacker News, Y Combinator, Wellfound) using native, credential-free HTTP scrapers.
- 🎯 **Explicitly targets** your preferred markets (e.g., India, Remote) and mathematically calculates if you are a good fit based on your background.
- ✍️ **Custom-rewrites** your resume for that specific job to effortlessly bypass ATS keyword filters, while intelligently scanning your GitHub/Portfolio repositories to highlight **only the top 2 best-matching projects**.
- 📨 **Drops a completely finished application** package and cold-email draft directly into your Human Review queue.

*(Note: LinkedIn automation has been explicitly removed from this project to ensure your personal accounts remain safe from bot detection and ID verification).*

## ⚙️ How it works

When you turn on the engine, this is the exact flow that happens on your machine:

1. **Discovery:** Python-based stealth scrapers silently wake up and scan top platforms (Indeed, YC, HN) without requiring any login credentials, bypassing Cloudflare and captchas to pull raw job postings directly into your pipeline.
2. **Extraction:** The AI extracts the unstructured text of the job description and converts it into clean, structured JSON data.
3. **Reasoning:** A deep-thinking logic model reads the job, cross-references your profile, and calculates a strict mathematical "Fit Score".
4. **Tailoring:** If the score is high enough, the local AI drafts a custom resume and a personalized cold email. The orchestrator dynamically optimizes context windows (e.g., automatically truncating huge GitHub READMEs) to ensure flawless local execution without exceeding token limits.
5. **Execution:** An automation bot navigates to ATS application pages (like Greenhouse or Lever) to auto-apply. For startup roles (YC/Hacker News), the system pushes a tailored email draft to your Dashboard's "Action Required" inbox for 1-click manual sending.

## 🔒 Security & Offline Auth

Because SPrav operates independently of any central cloud, traditional password recovery mechanisms (like an external auth server sending you an email) pose a security risk. We built a zero-trust local authentication system:

* **Encrypted Credential Vault:** Your platform credentials are XOR-encrypted in a local SQLite database (`users.db`) using your private `.env` key. They are never stored in plain text.
* **Master Recovery Key:** Upon sign-up, the system generates a unique `SPRAV-XXXX-XXXX` Master Recovery Key. If you forget your local password, this physical key is your ultimate fallback to regain access to your encrypted vault.
* **Bring-Your-Own-SMTP (Optional):** If you prefer a modern Web 2.0 experience, you can hook up your own Gmail App Password to the `.env` file. The backend will natively generate and securely email you a 6-digit OTP for password recovery.
* **SPrav Copilot:** A built-in AI assistant integrated directly into the UI to guide you through your job search, configure settings, and answer questions.
* **Themed UI:** A sleek, fully responsive React frontend with built-in Light/Dark mode toggles to manage your agents in comfort, served entirely via FastAPI without needing Node.js in production.

---

## 🧠 Architecture

SPrav utilizes a custom pipeline called the **SPrav MOE Model** (Mixture of Experts in spirit). Rather than relying on a monolithic Large Language Model, it intelligently routes tasks across highly specialized models for data extraction, fit scoring, tailoring, and verification. 

**Fault Tolerant Engine:** The core `daemon.py` orchestrator is heavily hardened. It features automatic database migrations, aggressive zero-token ATS extraction, Null-safe fallback logic for ghost jobs, and forced UTF-8 encoding checks on all native sub-processes to guarantee the daemon never crashes during an overnight discovery run.

For Resume Tailoring, the system primarily routes to a high-tier cloud model (like `gpt-oss-120b` via Groq). If the cloud API hits a rate limit or exhausts, the system seamlessly triggers a **Dual Local Fallback**—falling back to `qwen2.5-coder:7b-instruct` for strict JSON outputs, and then `hermes3:8b` as an ultimate failsafe. The entire orchestrator is strictly memory-managed to run on an **8GB VRAM** ceiling without crashing.

For the full details on the orchestrator design, pipeline diagram, and the models used, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 📁 Repository Structure

SPrav is a monolithic repository containing a Python FastAPI backend and a React frontend compiled down and served natively. Node.js is completely eliminated from the production runtime for lower memory usage.

```text
SPrav-Job-AI/
├── engine/              # Python Backend (Core AI Logic)
│   ├── auth.py          # SQLite auth and credential encryption
│   ├── daemon.py        # Pipeline orchestrating the scrapers and AI logic
│   └── llm_provider.py  # Advanced routing for Local Ollama (with optional Cloud API fallback)
├── frontend/            # React UI (Dashboard & Auth)
│   ├── src/             # Vite application source code
│   └── dist/            # Compiled static React assets (Served by FastAPI)
├── knowledge_base/      # Your local RAG memory bank
├── discovery/           # Python HTTP Scrapers (HN, YC, Indeed, Wellfound)
├── api.py               # FastAPI server bridging Frontend, Engine, and Scraper
├── desktop_app.py       # PyWebview wrapper for native desktop experience
├── users.db             # Local SQLite (Auto-generated on first run)
└── jobs.db              # Local SQLite tracking applied/rejected jobs
```

---

## ⚙️ Configuration (`.env`)

To protect your privacy, all API keys and thresholds are stored strictly in a `.env` file at the root of the project.

```env
# -----------------------------
# Security
# -----------------------------
# Used to encrypt/decrypt your credentials in the local users.db
JWT_SECRET=super_secret_jwt_key_12345

# -----------------------------
# AI API Keys (Optional)
# -----------------------------
GROQ_API_KEY=your_groq_api_key

# -----------------------------
# SMTP Email Setup (Optional)
# -----------------------------
# Required if you want OTP Password Resets or daily job summary emails
EMAIL_SENDER=your-bot-email@gmail.com
EMAIL_PASSWORD=your_16_char_google_app_password
EMAIL_RECEIVER=your-personal-email@gmail.com

# -----------------------------
# AI Pipeline Tuning
# -----------------------------
# Minimum match score required to trigger an Auto-Apply (0.0 to 1.0)
ATS_AUTO_APPLY_THRESHOLD=0.88

# DeepSeek Fit Score required to consider a job a "Fit" (1.0 to 5.0)
FIT_AUTO_APPLY_THRESHOLD=4.0

# Max applications per company per day
COMPANY_DAILY_CAP=5

# Max applications per job portal per day
PORTAL_DAILY_CAP=25

# Max applications across the entire internet per day
TOTAL_DAILY_CAP=150

# Pause bot if it gets blocked/fails X times in a row
AUTO_APPLY_CIRCUIT_BREAKER_N=3

# -----------------------------
# Ollama 8GB VRAM Optimization
# -----------------------------
OLLAMA_MAX_LOADED_MODELS=1
OLLAMA_NUM_PARALLEL=1
OLLAMA_KV_CACHE_TYPE=q8_0
OLLAMA_FLASH_ATTENTION=1

---

## 🚀 Installation

> [!IMPORTANT]
> Running models entirely locally via Ollama requires a minimum of **8GB VRAM** and **16GB RAM** to prevent Out-of-Memory (OOM) failures. (Cloud APIs like Groq can be configured as an alternative).

### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/SVSPraveen/SPrav-Job-AI.git
cd SPrav-Job-AI

# Initialize virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install core dependencies and ATS automation browsers
pip install -r requirements.txt
pip install uuid_utils
playwright install chromium
```

### 2. Model Initialization

If you plan to use local fallbacks, ensure [Ollama](https://ollama.com/) is installed. 
*You do not need to manually pull models.* The SPrav `LaunchJobAssistant.bat` bootstrapper will automatically wake up Ollama in the background and pull `qwen2.5-coder:7b-instruct`, `hermes3:8b`, `deepseek-r1:7b`, `bespoke-minicheck`, and `nomic-embed-text` for you on first launch!

### 3. Dashboard Configuration

```bash
# Install frontend dependencies
cd frontend
npm install
npm run build
cd ..

# Initialize configuration
copy .env.example .env
# Open .env and customize as needed!
```

### 4. Launch

For Windows users, simply double-click the **`Start SPrav AI.vbs`** file. This will silently spin up the FastAPI backend, background daemon, and the pre-compiled desktop UI in the background without leaving an ugly command prompt window open. This will also automatically install Ollama and pull any missing models if you don't have them!

> [!TIP]
> **Pro Tip:** Right-click `Start SPrav AI.vbs` → **Send to** → **Desktop (create shortcut)**. Now you can launch SPrav just like any native desktop application with a simple double-click from your desktop!

```bash
Start SPrav AI.vbs
```

Alternatively, you can run the batch file directly if you want to see the startup logs:
```bash
LaunchJobAssistant.bat
```

Alternatively, you can launch the native desktop application window directly via python:
```bash
python desktop_app.py
```

---


## 👤 Author
**SVSPraveen** ([GitHub](https://github.com/SVSPraveen))
*Note: I designed and built the orchestration architecture (the SPrav MOE Model) to coordinate these tasks. I did not train or fine-tune any of the underlying LLMs.*

## ⚖️ Responsible Use
- **Terms of Service:** Users are solely responsible for ensuring their automated submissions comply with the Terms of Service of each respective job portal.
- **Human Review:** The Verifier Feedback Loop is designed to reduce hallucinated claims, but it does not catch everything. You should periodically review the Human Review queue.
- **Rate Limits:** The daily caps (`COMPANY_DAILY_CAP`, `PORTAL_DAILY_CAP`, `TOTAL_DAILY_CAP`) exist for a reason—do not remove them. They are designed to avoid overwhelming employers and ATS platforms with spam.

---
## 🛡️ Privacy & Data Guarantee

**SPrav operates on a strict single-source-of-truth paradigm.** Every generated bullet point and claim must trace back to a verifiable entry in your canonical Knowledge Base. The system is explicitly engineered to highlight your actual skill gaps rather than hallucinating false proficiencies. 

Your data never leaves your hard drive unless you explicitly configure an optional cloud AI provider. 

<br/>
<div align="center">
  <p>Engineered for privacy, precision, and performance.</p>
</div>
