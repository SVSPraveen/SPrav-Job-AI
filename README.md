<div align="center">

# 🚀 SPrav™ Job AI (v2.4.5 Pro Edition)
### Autonomous Career Intelligence & Agentic Job-Application Platform

[![Version](https://img.shields.io/badge/version-2.4.5--pro-8b5cf6?style=for-the-badge)](https://github.com/SVSPraveen/SPrav-Job-AI)
[![License](https://img.shields.io/badge/license-MIT-blue?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20x64-0078d4?style=for-the-badge)](https://github.com/SVSPraveen/SPrav-Job-AI)
[![Local First](https://img.shields.io/badge/privacy-100%25%20Local--First-10b981?style=for-the-badge)](https://github.com/SVSPraveen/SPrav-Job-AI)
[![Live Landing](https://img.shields.io/badge/website-sprav--job--ai.pages.dev-f43f5e?style=for-the-badge)](https://sprav-job-ai.pages.dev)

*Architected & Built with High-Fidelity ATS Grounding, 28,700+ Verified Corporate ATS Portals, Closed-Loop Verifier Feedback, and Playwright Automation.*

</div>

---

## 🌟 What is SPrav Job AI?

**SPrav Job AI** is a local-first, autonomous career intelligence agent. It anchors your career journey against your **Master Resume (Ground Truth)**, continuously scans 28,700+ verified corporate career boards, eliminates hallucinated claims through a multi-pass verifier loop, and enables guided 1-click tailored job applications.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            SPRAV™ COMMAND CENTER                            │
│           (React 18 + Glassmorphism + Live Telemetry + MoE Router)          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                              AGENTIC PIPELINE                               │
│  [1. Discovery] ──► [2. Scope Gate] ──► [3. ATS Match] ──► [4. Verifier]   │
│         ▲                                                          │        │
│         └────────── 28,700+ Verified Career ATS Boards ────────────┘        │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ 1-Click Guided Dispatch
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                    PLAYWRIGHT BROWSER AUTOMATION ENGINE                     │
│           (Greenhouse • Lever • Ashby • Workday • SmartRecruiters)          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features in v2.4.5 Pro Edition

### 1. 🧠 Universal AI Document Intelligence (`engine/kb_extractor.py`)
* **100% Zero-Hardcoding Guarantee:** Dynamically parses any candidate's resume worldwide from any university, degree, country, or industry.
* **4-Engine Cascading Text Fallback:** `pypdfium2` -> `pdfplumber` -> `PyPDF2` -> `pdfminer` with full Unicode and byte-order cleanup.
* **10 Dynamic Skill Domains:** Automatically maps extracted skills into *AI & Agentic Systems, Retrieval & Search, LLMs & Vector Databases, ML & Evaluation, Full-Stack & Backend, Cloud & Security, Product & UI/UX, Business, Marketing, and Domain Expertise*.

### 2. 🎯 Standardized Application Scope & Global Geo-Taxonomy
* **800+ Standardized Career Titles:** Standardized tech roles taxonomy with instant multi-select typeahead search (`RoleTypeahead.jsx`).
* **246-Country Geo-Spatial Engine:** Standardized location taxonomy covering all countries, regions, and tech hubs (`LocationTypeahead.jsx`).
* **Intelligent Remote Country Barrier (`RemoteCountryBarrier`):** Screens out location-restricted international remote jobs while preserving eligible roles.
* **Ultra-Fast In-Memory Filtering:** Evaluates 26,000+ jobs/second with sub-millisecond latency.

### 3. 🛡️ First-Time User Experience (FTUX) Setup Guard
* Interactive 2-step setup banner on the Command Center ensuring both Master Resume and Application Scope are active before launching the autonomous engine.
* Real-time readiness telemetry API (`GET /api/system/readiness`).

### 4. 🎛️ SPrav™ Command Center Dashboard
* Redesigned with an ultra-premium glassmorphic interface, animated gradient header border, and live model pulse.
* Clean 4-card operational cockpit (*Jobs Discovered, Action Required, Applications Sent, Target Scope*).
* Live telemetry terminal and 1-click continuous loop controls.

### 5. ⚡ Enterprise Benchmark Performance
* **154.4 Requests / Second** under 100-request high-concurrency API stress testing (0 failed requests).
* **26,062 Jobs / Second** in-memory scope evaluation throughput.
* **0 SQLite Database Locks** under 40 simultaneous read/write WAL transactions.

---

## 🚀 Quickstart & Installation

### Option A: Portable Windows App (.exe)
1. Download the latest release from the [Releases](https://github.com/SVSPraveen/SPrav-Job-AI/releases) page.
2. Unzip and launch `SPrav Job AI.exe`.
3. Open `http://127.0.0.1:8000/` in your browser.

### Option B: Run from Source
```bash
# Clone the repository
git clone https://github.com/SVSPraveen/SPrav-Job-AI.git
cd SPrav-Job-AI

# Set up Python virtual environment
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Start backend & launcher
python launcher.py
```

---

## 📚 Documentation & Technical References

* 📖 **[User Guide](docs/USER_GUIDE.md)** — Step-by-step setup and application dispatch instructions.
* 🏛️ **[Architecture Specification](docs/ARCHITECTURE.md)** — Complete module layout, data flow, and privacy boundary.
* 🔄 **[Autonomous Workflow](docs/WORKFLOW.md)** — Detailed 5-stage agentic execution lifecycle.
* 📋 **[Technical Documentation](docs/DOCUMENTATION.md)** — API reference, schemas, and stress test benchmarks.

---

## 🔒 Security & Privacy

* **100% Local-First:** Your resumes, credentials, and application logs remain strictly on your local machine (`%LOCALAPPDATA%/SPravJobAI`).
* **Zero Hallucination:** Resume pitches and cover letters are strictly grounded against your Knowledge Base.

---

<div align="center">

**Built with ❤️ by SVS Praveen**  
*© 2026 SVS Praveen • SPrav™ Job AI*

</div>