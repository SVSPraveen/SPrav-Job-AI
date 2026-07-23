<div align="center">
  <h1>SPrav Job AI</h1>
  <p><strong>Autonomous, local-first AI agent for hyper-personalized job applications.</strong></p>
  <p>
    <a href="https://github.com/SVSPraveen/SPrav-Job-AI/stargazers"><img src="https://img.shields.io/github/stars/SVSPraveen/SPrav-Job-AI?style=for-the-badge&color=gold" alt="Stars"></a>
    <a href="https://github.com/SVSPraveen/SPrav-Job-AI/network/members"><img src="https://img.shields.io/github/forks/SVSPraveen/SPrav-Job-AI?style=for-the-badge&color=blue" alt="Forks"></a>
    <a href="https://github.com/SVSPraveen/SPrav-Job-AI/issues"><img src="https://img.shields.io/github/issues/SVSPraveen/SPrav-Job-AI?style=for-the-badge&color=red" alt="Issues"></a>
    <img src="https://img.shields.io/badge/Python-3.13+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/React-18.x-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React">
  </p>
</div>

<br />

SPrav is an enterprise-grade, offline-first AI pipeline designed to discover job listings, evaluate fit, tailor ATS-optimized resumes using the Google XYZ formula, fact-check claims against your baseline data, and dispatch applications autonomously. 

Running 100% locally on your GPU, your personal data never leaves your machine. Zero cloud API costs, zero data leakage.

> 📚 **Technical Documentation**: Please refer to [ARCHITECTURE.md](ARCHITECTURE.md) for state machine flows, MoE routing designs, and data architectures.

---

## ⚡ Core Features

- **Offline Inference**: Powered entirely by local Ollama models. Your email, phone, and employment history never touch third-party servers.
- **Mixture-of-Experts (MoE) Architecture**: Routes specialized tasks to domain-specific models (e.g., Qwen for JSON extraction, DeepSeek-R1 for logical fit scoring, Llama 3.1 for prose generation).
- **Adversarial Fact-Checking**: Employs a zero-tolerance hallucination detection layer. Any generated metric not explicitly supported by your canonical data triggers a forced regeneration.
- **ATS Direct Integration**: Bypasses noisy aggregators by scraping and applying directly to native Applicant Tracking Systems (Greenhouse, Lever) via Playwright.

---

## 🧠 Model Architecture

The system avoids monolithic LLM patterns by leveraging a targeted Mixture-of-Experts methodology:

| Subsystem | Model | Purpose |
|-----------|-------|---------|
| **Data Extraction** | `qwen2.5:7b-instruct` | High-fidelity structured JSON extraction from unstructured HR text. |
| **Logic & Evaluation** | `deepseek-r1:7b` | Chain-of-thought `<think>` reasoning for holistic candidate-to-job fit scoring. |
| **Culture Forensics** | `magnum-v4:9b` | Uncensored parsing of corporate vernacular to detect toxic organizational patterns. |
| **Generative Prose** | `llama3.1:8b` | Professional, AI-slop-free resume drafting and XYZ bullet engineering. |
| **Vector Embeddings** | `nomic-embed-text` | High-efficiency 8192-token context window for localized RAG memory. |

---

## ⚙️ Hardware Requirements

To guarantee pipeline stability without Out-of-Memory (OOM) failures, the following hardware floor is strictly enforced for local execution:

* **GPU**: Minimum **8 GB VRAM** (e.g., RTX 3060, RTX 4060, or Apple Silicon equivalents). 
* **RAM**: 16 GB minimum.
* **Storage**: 20 GB free space for localized models.

*(Note: Users lacking the requisite hardware may utilize the optional cloud accelerators by configuring OpenRouter/Groq API keys in the `.env` file.)*

---

## 🚀 Quick Start Guide

### 1. Environment Setup

```powershell
# Clone the repository and initialize the virtual environment
git clone https://github.com/SVSPraveen/SPrav-Job-AI.git
cd SPrav-Job-AI
python -m venv .venv
.venv\Scripts\activate

# Install core dependencies and ATS automation browsers
pip install -r requirements.txt
playwright install chromium
```

### 2. Model Initialization

Ensure [Ollama](https://ollama.com/) is installed and running, then pull the required architecture stack:

```powershell
ollama pull qwen2.5:7b-instruct
ollama pull deepseek-r1:7b
ollama pull magnum-v4:9b
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

### 3. Dashboard Configuration

```powershell
# Install frontend dependencies
cd frontend
npm install
cd ..

# Initialize configuration
copy .env.example .env
```

### 4. Launch

Execute the bootstrapper to spin up the LangGraph daemon, FastAPI backend, and React dashboard:

```powershell
LaunchJobAssistant.bat
```

Navigate to `http://localhost:5173` in your browser.

---

## 📖 Module Documentation

For deep dives into specific subsystems, refer to the module-level documentation:

- [Engine Orchestration (`/engine`)](engine/README.md)
- [Job Discovery (`/discovery`)](discovery/README.md)
- [ATS Automation (`/apply`)](apply/README.md)
- [Analytics & Tracking (`/tracking`)](tracking/README.md)

---

## 🛡️ Data Integrity Guarantee

SPrav operates on a strict single-source-of-truth paradigm. Every generated bullet point and claim must trace back to a verifiable entry in your canonical `knowledge_base/me.json`. The system is explicitly engineered to flag skill gaps rather than hallucinate proficiencies. 

---

<div align="center">
  <p>Engineered for privacy, precision, and performance.</p>
</div>
