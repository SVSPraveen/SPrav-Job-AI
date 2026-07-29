# ⚙️ SPrav AI Engine (Backend)

Welcome to the central nervous system of SPrav Job AI. This folder contains the entire Python backend and the Mixture of Experts (MoE) orchestration logic that powers the autonomous job application process.

## Core Modules

* **`daemon.py`**: The master orchestrator. Runs in an infinite loop managing background scrapers, evaluating new jobs via the LLM pipeline, tailoring resumes, and auto-applying. Contains the `db_mutex` concurrency logic to prevent SQLite lockouts.
* **`llm_provider.py`**: The dynamic routing layer. Intelligently routes requests to cloud providers (e.g., Groq) and seamlessly fails over to local Ollama models (`qwen2.5-coder`, `deepseek-r1`) if rate limits are hit.
* **`evaluator.py`**: Reads unstructured job descriptions and calculates a strict mathematical "Fit Score" to determine if a job is worth applying to.
* **`tailor.py`**: Re-writes resume bullet points to bypass ATS keyword filters while adhering to strict hallucination guardrails.
* **`formatter.py`**: The dynamic PDF engine. Uses ReportLab to generate a gorgeous, single-page PDF resume by intelligently shrinking fonts and truncating older bullets if necessary.
* **`scope_enforcer.py`**: Strict rule engine that instantly rejects jobs that don't match your location, visa, or seniority requirements.
* **`star_bank.py`**: Extracts behavioral gaps and generates custom STAR-format interview stories tailored to the specific role.
* **`recruiter_dataset.py` & `contact_discovery.py`**: Modules for sourcing hiring managers and drafting personalized networking emails.

## Technical Notes
- **Memory Ceiling**: The entire pipeline is explicitly designed to run on a machine with an **8GB VRAM** ceiling when using local Ollama fallbacks.
- **Data Storage**: All state is persisted to a local SQLite database (`jobs.db`) typically stored in your `%LOCALAPPDATA%` directory.
