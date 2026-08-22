# SPrav Job AI — Architecture Specification (v2.4.5 Pro)

---

## 1. High-Level System Architecture

SPrav Job AI is designed with a **modular, local-first architecture** running on FastAPI, SQLite (WAL mode), and React 18:

```
[Master Resume PDF] ──────► [Universal KB Extractor] ──────► [knowledge_base/me.json]
                                                                     │
[28,700+ Career Boards] ──► [Discovery Scraper]                      │
                                   │                                 │
                                   ▼                                 │
                        [Application Scope Gate]                     │
                         (Roles, Geo & Remote)                       │
                                   │ (In Scope)                      │
                                   ▼                                 │
                        [Hybrid ATS Match Scorer] ◄──────────────────┤
                                   │                                 │
                                   ▼                                 │
                        [Tailor & Verifier Loop] ◄───────────────────┘
                                   │
                                   ▼
                       [Guided 1-Click Dispatch] ──► [Playwright Automation]
```

---

## 2. Directory Layout & Module Structure

```
SPrav-Job-AI/
├── api.py                    # FastAPI server & route handlers
├── launcher.py               # Desktop system-tray launcher & process supervisor
├── engine/
│   ├── continuous_loop.py    # Background autonomous discovery & scoring loop
│   ├── kb_extractor.py       # Universal zero-hardcoding resume intelligence parser
│   ├── scope_enforcer.py     # In-memory Application Scope gating (< 1ms per job)
│   ├── job_roles_taxonomy.py # 800+ standardized career titles
│   ├── location_taxonomy.py  # 246-country geo-taxonomy & Remote Country Barrier
│   ├── tailor.py             # Resume & cover letter tailoring engine
│   ├── fact_checker.py       # Automated verifier loop preventing hallucinations
│   └── llm_provider.py       # Hybrid local Ollama & Groq Cloud MoE router
├── discovery/
│   ├── scraper.py            # Multi-portal scraper (Greenhouse, Lever, Workday, etc.)
│   └── db.py                 # SQLite database models & state management
└── frontend/
    ├── src/
    │   ├── App.jsx           # SPrav™ Command Center Dashboard & Navigation
    │   ├── CommandCenter.css # Glassmorphic design system tokens & animations
    │   └── pages/
    │       ├── ApplicationScope.jsx  # Multi-select typeahead scope manager
    │       ├── MasterJobPortal.jsx   # Searchable ATS job portal
    │       └── KnowledgeBaseEditor.jsx # Candidate ground truth profile editor
```

---

## 3. Data Flow & Security Model

* **Local-First Privacy:** Candidate resumes, API keys, and application histories are stored locally on the user's machine (`%LOCALAPPDATA%/SPravJobAI`).
* **Deterministic Verification:** Tailored bullet points are validated against `me.json` ground truth before applications are dispatched.