# Engine Module (`engine/`)

The `engine` directory represents the core intelligence, orchestration, and evaluation layers of the SPrav Job Application pipeline. It utilizes a local Mixture-of-Experts (MoE) LLM architecture (Qwen2.5, DeepSeek-R1, Llama3.1) managed via LangGraph to fully automate the discovery, evaluation, tailoring, and fact-checking of job applications.

This module acts as the "Brain" of the operation, executing the multi-phase pipeline that filters out noise, tailors your resume, and ensures absolute factual integrity.

---

## 🧠 Core Architecture

The engine is built around a state-machine architecture using **LangGraph** (defined in `daemon.py`), which transitions discovered jobs through strict operational phases:

1. **Phase 0: Intake & Verification**
   - Parses incoming job postings.
   - Rejects stale, ghost, or reposted jobs before any heavy LLM inference is spent.
   - Enforces user-defined application constraints (Application Scope).
2. **Phase 1: Extraction**
   - Uses structured LLM parsing to extract structured JSON (salary, requirements, tech stack) from noisy job description text.
3. **Phase 2: Fit Evaluation**
   - Uses **DeepSeek-R1** reasoning to evaluate a strict fit score based on the extracted requirements and the user's canonical `me.json`.
4. **Phase 3: Tailoring**
   - Re-writes and selects the optimal resume bullets from the user's Knowledge Base to highlight relevance to the specific JD.
5. **Phase 4: Fact Checking**
   - Zero-tolerance hallucination detection. A separate LLM acts as an adversarial auditor, ensuring the tailored resume contains NO invented claims and strictly aligns with `me.json`.
6. **Phase 5: Dispatch**
   - Routes the job to the auto-apply queue or the human-review queue based on the final confidence and fit scores.

---

## 📂 Key Modules & Responsibilities

### Orchestration & Control
- **`daemon.py`**: The primary LangGraph workflow orchestrator. Defines the nodes and edges for the job processing state machine and runs the persistent background loop.
- **`config.py`**: Centralizes tuning parameters, LLM model selection logic, and system thresholds (e.g. `ATS_AUTO_APPLY_THRESHOLD`, `FIT_AUTO_APPLY_THRESHOLD`).

### Intake & Pre-Processing
- **`intake.py` & `kb_merger.py`**: The "Phase 0" onboarding engine. Parses legacy PDFs, DOCX files, and LinkedIn data exports, resolving conflicts and merging them into the canonical `me.json` format.
- **`scope_enforcer.py`**: A deterministic logic gate that checks a job against the user's `scope.json` (location, role, remote/onsite, job type) to immediately reject out-of-scope roles before spending LLM tokens.
- **`ghost_detector.py`**: Analyzes job descriptions for red flags indicating a "ghost job" (data harvesting) or an MLM scam.
- **`liveness_verifier.py`**: Pings the ATS to ensure the job posting is still accepting applications.

### Evaluation & Intelligence
- **`evaluator.py`**: The `KnowledgeDistiller` class. Computes verified Years of Experience (YoE) and queries DeepSeek-R1 with a dynamic rubric to determine if the candidate is a strong fit for the role.
- **`llm_provider.py`**: The abstraction layer for the MoE architecture. Routes requests to the appropriate local model (e.g. Qwen for extraction, DeepSeek for reasoning, Llama for prose).
- **`brain.py`**: The local RAG (Retrieval-Augmented Generation) engine, allowing the system to semantically query historical projects, older resumes, and proof points.
- **`skill_analyzer.py` & `salary_analyzer.py`**: Analyzes the tech stack overlap and extracts/predicts salary ranges from opaque JDs.

### Tailoring & Formatting
- **`tailor.py`**: Re-orders and rewrites resume bullets to match the job requirements, aiming for maximum ATS keyword coverage.
- **`fact_checker.py`**: The adversarial auditor. It compares the tailored output against `me.json` line-by-line. If an hallucination is detected, it fails the job or requests a re-generation.
- **`html_compiler.py`**: Ingests the finalized, fact-checked resume JSON and compiles it into a beautiful, ATS-friendly PDF using HTML/CSS templates.

---

## 🛠️ Usage within the Pipeline

You generally do not run files in this directory directly. They are imported and executed by the main application entry point (e.g. `LaunchJobAssistant.bat` or `main.py`).

If you wish to modify the behavior of the AI, the most critical files to adjust are:
- `evaluator.py` to change how strict the Fit Evaluation is.
- `tailor.py` to adjust how aggressively the AI rewrites resume bullets.
- `llm_provider.py` to swap out the underlying local models (e.g. upgrading to a new DeepSeek or Qwen version).
