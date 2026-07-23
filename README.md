# SPrav — Autonomous Job Application AI

> **100% local. 100% private. Zero API costs.** Your resume and career data never leave your machine.

SPrav is a self-hosted, offline AI pipeline that discovers job listings, filters them against your profile, tailors a fresh ATS-optimised resume for each one using the Google XYZ formula, fact-checks it against your real data, and either auto-applies or queues it for your manual click — all while you sleep.

> 📚 **Developer Note**: See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed technical diagrams, state machine flows, and data routing architectures. Every subfolder also contains its own detailed `README.md`.

---

## ⚡ Pros & Cons

### ✅ Pros
- **100% Free Inference**: Runs entirely on your local GPU via Ollama. Zero API costs.
- **Total Privacy**: Your email, phone number, and resume data never touch OpenAI or Anthropic servers.
- **First-Mover Advantage**: Direct-to-ATS scraping catches jobs the minute they are posted, bypassing noisy aggregators.
- **Adversarial Fact-Checking**: Prevents AI hallucinations. If the AI invents a metric (e.g. 50% revenue growth instead of 20%), the Fact Checker catches it and forces a rewrite.
- **Cloud Accelerators (Optional)**: Can route to Groq for insanely fast JSON extraction or OpenRouter (Claude 3.5 Sonnet) for elite-tier resume prose if you want to speed up the local pipeline.

### ❌ Cons
- **Strict Hardware Floor**: Requires a dedicated GPU with at least **8GB VRAM**.
- **Not a "Spray and Pray" bot**: SPrav applies to 10-20 highly relevant jobs a day, perfectly tailored. It does not spam 1,000 jobs a day with a generic PDF.
- **Setup Complexity**: Requires installing Playwright, Ollama, Node, and pulling multiple models before first run.
- **No GUI for Configuration**: Core pipeline logic (like changing models) requires editing `config.json` or Python files.

---

## AI Model Architecture (Mixture-of-Experts, Local Only)

The system uses a **Mixture-of-Experts (MoE)** routing pattern. Instead of one giant model for everything, each specialist task is routed to the best-in-class model for that exact job. All models run locally via **Ollama** on your GPU.

| Task | Model | Why This Model |
|------|-------|----------------|
| **JD Extraction** (Phase 1) | `qwen2.5:7b-instruct` | Best-in-class at structured JSON extraction from noisy HR text. Beats GPT-3.5 on extraction benchmarks at 7B scale. |
| **Logic Filter / Fit Scoring** (Phase 2) | `deepseek-r1:7b` (DeepSeek-R1-Distill-Qwen-7B) | Step-by-step `<think>` chain-of-thought reasoning. Scores job fit on a rubric like a rational evaluator, not a pattern matcher. |
| **Toxic Culture Forensics** (Phase 0.5) | `magnum-v4:9b` (Magnum-V4-9b-Abliterated) | Uncensored roleplay-tuned model. Uniquely capable of seeing *through* corporate euphemisms ("cross-functional autonomy" = understaffed). Standard models refuse or miss these patterns. |
| **Resume Drafting / XYZ Rewriting** (Phase 3) | `llama3.1:8b` (Meta-Llama-3.1-8B-Instruct) | Best prose quality at 8B scale. Clean, professional tone without AI slop. Avoids the robotic cadence of Qwen/Mistral instruction models. |
| **RAG Embeddings** | `nomic-embed-text` | 274MB, 8192-token context window, runs entirely on CPU RAM. Zero VRAM consumed, leaving all 8GB for the generation models. |

---

## Hardware Specs (Tested On)

| Component | Spec |
|-----------|------|
| GPU | NVIDIA RTX 5060 — **8 GB VRAM** |
| CPU | AMD Ryzen 7 250 |
| RAM | 16 GB |
| OS | Windows 11 |

> **Why 8 GB VRAM matters:** All 5 models are selected at Q4_K_M quantisation to fit within 8 GB. They are loaded and unloaded sequentially (never simultaneously) via the GPU Mutex in `engine/llm_provider.py`. Attempting to run two models at once would OOM the GPU.

---

## Known Limitations

### Hardware Limits: 8GB VRAM is a HARD REQUIREMENT
- **8 GB VRAM Floor:** To run this pipeline in 100% local mode, you **MUST** have a GPU with at least 8GB of VRAM (e.g., RTX 3060, 4060, or Mac M-series equivalent). The 7B and 8B models (quantized at Q4) require ~5.5GB of VRAM to load, leaving headroom for the context window. **If you have less than 8GB VRAM, the local pipeline will crash with an Out-of-Memory (OOM) error.**
  - *Workaround:* If you lack the hardware, you must add a Groq or OpenRouter API key to `.env` to offload the LLM inference to the cloud.
- **One model at a time.** The GPU mutex serialises all generation calls. The 2-worker parallel daemon provides CPU-level concurrency, but GPU inference is strictly sequential. Running 2 jobs in parallel gives zero GPU speedup.
- **Slow on cold start.** The first job of each daemon cycle takes ~15–30 seconds longer because Ollama loads the model from SSD into VRAM. Subsequent jobs on the same model are fast.

### AI / Output Limits
- **The model cannot write what you didn't give it.** If your `me.json` has vague, unpunchy bullets ("Worked on backend systems"), the XYZ rewriter has nothing to work with. The output is only as good as your input data.
- **Hallucination guard has a 2-retry limit.** After 2 failed fact-check attempts, the job is marked `failed_fact_check` and paused. You will need to check it in the Action Required tab.
- **The ATS score is a coverage estimate, not a certified score.** It measures keyword hit-rate from the extracted JD skills vs. the resume text. It does not emulate the actual scoring algorithm of Workday, Greenhouse, or Lever.
- **Magnum-v4 (toxic forensics) can over-flag.** Being an abliterated model, it sometimes reads valid demanding roles as toxic. If it incorrectly rejects a legitimate job, you can override the status in the dashboard.

### Scraper Limits
- **Arbeitnow, RemoteOK, Remotive**: 30 jobs per source per discovery cycle.
- **LinkedIn, Indeed, Naukri, Internshala**: These portals block programmatic access. The system scrapes their job listings into the **Human Apply Queue** — you see the JD, the tailored resume, and the apply link. You do the final click.
- **No IP rotation.** Your identity (email, phone, resume fingerprint) is permanent regardless of IP. The 30/day/portal rate limit exists to protect your account, not to evade IP bans.

### Auth Limits
- **Single-user only.** The JWT auth system is designed for one person. The login credentials come from `knowledge_base/me.json`. Multi-user support is not in scope.
- **7-day token expiry.** You will need to log in again after 7 days. Tokens are stored in `localStorage`.

---

## Quick Start

```powershell
# 1. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install Playwright browser (for ATS direct applications)
playwright install chromium

# 4. Install and start Ollama
# Download from: https://ollama.com
# Then pull all 5 required models:
ollama pull qwen2.5:7b-instruct
ollama pull deepseek-r1:7b
ollama pull magnum-v4:9b
ollama pull llama3.1:8b
ollama pull nomic-embed-text

# 5. Install frontend dependencies
cd frontend
npm install
cd ..

# 6. Copy and configure environment
copy .env.example .env
# Open .env and set JWT_SECRET to a long random string

# 7. Fill in your profile
# Open knowledge_base/me.json and replace all placeholder values
# OR launch the app and use the Knowledge Base editor in the UI

# 8. Launch everything
LaunchJobAssistant.bat
```

> Your browser will open automatically to `http://localhost:5173`.  
> Default login: the email and password you set in `me.json → personal.email / personal.password`.

---

## Project Structure

```
/engine/
  llm_provider.py       # MoE router — routes tasks to the correct local model
  daemon.py             # LangGraph 7-phase job processing pipeline
  brain.py              # ChromaDB RAG memory (nomic-embed-text embeddings)
  tailor.py             # Resume tailoring + XYZ bullet rewriting
  config.py             # System prompts (3-role AI persona + TAILOR_PROMPT)
  ghost_detector.py     # Regex + Magnum-v4 toxic culture analysis
  fact_checker.py       # Post-generation hallucination detection
  evaluator.py          # DeepSeek-R1 hard logic fit scoring
  auth.py               # JWT token creation and verification
  html_formatter.py     # Renders tailored data into ATS-safe HTML blocks

/discovery/
  scraper.py            # Arbeitnow + RemoteOK + Remotive scrapers
  db.py                 # SQLite jobs database initialisation and queries

/templates/
  resume-template.html  # ATS-optimised single-page resume (v4.0)

/frontend/src/
  App.jsx               # Main React dashboard (with JWT auth gate)
  Login.jsx             # Login screen
  HumanApply.jsx        # Manual apply queue (LinkedIn/Naukri jobs)
  pages/ManualReview.jsx # Cover letter approval gate

/knowledge_base/
  me.json               # YOUR profile data (gitignored) — source of truth
  schema.md             # JSON schema documentation

api.py                  # FastAPI backend (JWT-protected endpoints)
main.py                 # CLI entrypoint (--jd, --discover, --apply, --track)
LaunchJobAssistant.bat  # One-click launcher for all services
```

---

## The One Rule

Every fact in a generated resume **must trace back to a real entry in `knowledge_base/me.json`**. If a job description requires a skill you don't have in there, the system flags it as a **skill gap** — it does not quietly invent it. This applies to every field including the summary, not just bullets. Numbers are only used if they already existed in your KB, and they are rounded to clean figures before printing.

---

## Build Status

| Phase | Status | Description |
|-------|--------|-------------|
| 1 | ✅ Complete | Knowledge base schema + tailoring engine |
| 2 | ✅ Complete | HTML/PDF resume generation + KB editor UI |
| 3 | ✅ Complete | Job discovery (Arbeitnow, RemoteOK, Remotive) |
| 4 | ✅ Complete | Auto-apply (Greenhouse, Lever) + Human Apply Queue |
| 5 | ✅ Complete | JWT auth, per-portal rate limits, ATS score tracking |
| 6 | ✅ Complete | XYZ bullet rewriting + 3-role AI persona system prompt |
