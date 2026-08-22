# SPrav Job AI — Technical Documentation & Architecture Reference (v2.4.5 Pro)

---

## 1. System Architecture Overview

SPrav Job AI is an autonomous, local-first career intelligence system. It eliminates hallucinated resume claims via a closed-loop verification feedback loop, matches candidate profiles against 28,700+ verified corporate ATS career boards, and automates high-fidelity job applications.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            SPRAV™ COMMAND CENTER                            │
│                  (React 18 + Glassmorphism + Live Telemetry)                │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ REST / WebSocket
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                              FASTAPI BACKEND                                │
│        (/api/system/readiness, /api/scope, /api/jobs, /api/metrics)         │
└───────┬──────────────────────────────┬──────────────────────────────┬───────┘
        │                              │                              │
┌───────▼──────────────┐   ┌───────────▼──────────┐   ┌───────────────▼───────┐
│ DISCOVERY ENGINE     │   │ INTELLIGENCE & SCOPE │   │ TAILORING & VERIFIER  │
│ • 28,700+ ATS Boards │   │ • 800+ Job Taxonomy  │   │ • Zero-Hallucination  │
│ • Greenhouse/Lever   │   │ • 246 Countries Geo  │   │ • Ollama / Groq MoE   │
│ • Workday / Ashby    │   │ • Remote Barrier     │   │ • Fact-Checker Loop   │
└──────────────────────┘   └──────────────────────┘   └───────────────────────┘
```

---

## 2. Core Engine Components

### 2.1 Universal Document Intelligence & KB Extraction (`engine/kb_extractor.py`)
* **Multi-Engine Cascading Fallback:** `pypdfium2` -> `pdfplumber` -> `PyPDF2` -> `pdfminer`.
* **Zero-Hardcoding Guarantee:** Dynamically extracts any candidate's profile worldwide across all fields:
  - Personal details, portfolios, international contact numbers, GitHub, LinkedIn.
  - Granular technical & domain skills mapped dynamically into 10 structured domains.
  - Work history, role titles, companies, dates, and quantitative bullet points.
  - Projects, tech stacks, live links, and descriptions.
  - Degrees, institutions, CGPA/GPA, and professional certifications.

### 2.2 Application Scope & Geo-Taxonomy (`engine/scope_enforcer.py`)
* **Standardized Job Taxonomy:** Over 800 curated technical, engineering, and domain job titles (`engine/job_roles_taxonomy.py`).
* **Global Geo-Spatial Taxonomy:** Over 246 countries, states, and major global tech hubs (`engine/location_taxonomy.py`).
* **Remote Country Barrier (`RemoteCountryBarrier`):** Intelligent screening preventing disqualification from international remote roles.
* **Throughput:** Evaluates `26,000+ jobs/second` in-memory.

### 2.3 First-Time User Experience (FTUX) Safety Guard (`api.py`)
* Dual-step readiness check (`GET /api/system/readiness`):
  - **Step 1 (Ground Truth):** Requires Master Resume PDF extraction.
  - **Step 2 (Targeting Rules):** Requires Application Scope configuration.
* Gated launch (`POST /api/loop/start`) blocks autonomous runs until both steps are complete.

---

## 3. API Reference

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/api/system/readiness` | `GET` | Returns readiness status for Master Resume & Scope |
| `/api/loop/start` | `POST` | Starts autonomous continuous discovery and scoring |
| `/api/loop/stop` | `POST` | Stops autonomous background loop |
| `/api/metrics` | `GET` | Returns live Single-Source-of-Truth pipeline counts |
| `/api/jobs` | `GET` | Lists discovered jobs with status filtering and pagination |
| `/api/scope` | `GET/POST` | Reads and updates active Application Scope |
| `/api/settings/master-resume` | `POST` | Uploads and triggers AI extraction for Master Resume PDF |
| `/api/analytics/conversion` | `GET` | Returns conversion funnel stats across application stages |

---

## 4. Benchmark Performance Metrics

* **Concurrent API Throughput:** `154.4 requests/second` with 0 dropped connections.
* **Scope Evaluation Speed:** Evaluates `7,230 jobs` across 27 roles and 10 locations in `277.4 ms`.
* **Database Concurrency:** 40 simultaneous SQLite WAL transactions with 0 lock contentions.