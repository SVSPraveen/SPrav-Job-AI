# Engine Subsystem (`/engine`)

The Engine module serves as the primary orchestration and intelligence layer of the SPrav Job Application pipeline. It implements a robust Mixture-of-Experts (MoE) Large Language Model architecture managed via LangGraph, automating the complete lifecycle of job evaluation, resume tailoring, and strict fact-checking.

## 🏗️ Architectural Overview

The subsystem utilizes a state-machine architecture to transition discovered job listings through a deterministic operational pipeline:

1. **Intake & Verification**: Ingests job postings, sanitizes data, and strictly enforces user-defined application constraints (location, remote vs. on-site, seniority).
2. **Data Extraction**: Leverages structured LLM parsing to convert noisy, unstructured job descriptions into highly typed JSON schemas.
3. **Fit Evaluation**: Employs Chain-of-Thought (CoT) reasoning to calculate holistic fit scores against the user's canonical knowledge base.
4. **Targeted Tailoring**: Re-engineers resume bullet points using the Google XYZ framework, maximizing ATS keyword velocity without compromising factual integrity.
5. **Adversarial Fact-Checking**: Instantiates a secondary LLM auditor to compare tailored outputs against the canonical database, enforcing zero-tolerance for AI hallucinations.
6. **Application Dispatch**: Routes validated profiles to either the headless ATS automation queue or the human-in-the-loop dashboard.

## 🧩 Core Components

- **`daemon.py`**: The central LangGraph orchestrator. Maintains the persistent event loop and governs node transitions across the state machine.
- **`llm_provider.py`**: The MoE routing abstraction layer. Dynamically allocates inference tasks to specific local models (e.g., Qwen for parsing, DeepSeek for logic) via GPU-aware mutexes.
- **`fact_checker.py`**: The integrity enforcement module that prevents hallucinated claims from entering the dispatch queue.
- **`brain.py`**: A localized Retrieval-Augmented Generation (RAG) implementation powered by ChromaDB, enabling semantic querying of historical career data.

## ⚙️ Configuration

System thresholds and behavioral tuning are managed via `config.json` and environmental variables, allowing fine-grained control over ATS parsing sensitivities, auto-apply confidence thresholds, and model allocations.
