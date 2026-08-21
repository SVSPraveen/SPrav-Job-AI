# 🏗️ SPrav™ Architecture & Engineering Rationale

This document explains the technical architecture of **SPrav™ Job AI** and why specific engineering decisions were made over traditional alternatives.

---

## 1. Why "Guided 1-Click Dispatch" over "100% Blind Auto-Spam"?

### The Failure of Blind Auto-Apply Bots:
Many modern browser extensions promise *"Apply to 500 jobs while you sleep"*. In practice, this creates devastating consequences:
1. **ATS Disqualification**: Enterprise ATS portals (Workday, Greenhouse, Lever) flag mass-submissions with low semantic relevance and auto-reject candidate emails.
2. **Loss of Candidate Reputation**: Submitting to mismatched roles damages the candidate's standing with technical recruiters.
3. **Ghosting & Zero Follow-up Context**: When a candidate has no idea which jobs were applied to, they cannot prepare for recruiter screening calls.

### The SPrav Solution: Human-in-the-Loop 1-Click Dispatch
* SPrav does **99% of the computational heavy lifting**:
  - Scans 28,700+ verified career boards continuously.
  - Calibrated hybrid scoring: 60% hard skill matching (549+ technologies), 25% semantic cosine alignment, 15% dynamic role title relevance.
  - Generates tailored cover notes and STAR project bullet suggestions.
* However, **the final application trigger requires your 1-click permission**.
* This preserves candidate integrity, maximizes interview conversion, and keeps you fully aware of every submission.

---

## 2. Why "Local Desktop Freeware" over a "Cloud SaaS"?

| Architectural Vector | Traditional Cloud SaaS | SPrav™ Desktop Architecture |
|---|---|---|
| **Resume & Data Privacy** | Candidate resumes, contact info, and API keys stored on 3rd-party servers. | **100% Local Storage**: Everything stays in `%LOCALAPPDATA%\SPravJobAI`. |
| **Pricing & Subscriptions** | $20 – $50 / month recurring charges. | **₹0 Free Forever**: Freeware with zero subscription fees. |
| **Data Ownership** | If the SaaS shuts down, your search history is lost. | **SQLite Database**: Candidate owns their `.db` file and application history. |
| **Latency & Performance** | Slow cloud queues and rate limits. | **Sub-millisecond Local Queries**: Fast, responsive desktop UI. |

---

## 3. The Multi-Tier Semantic Filtering Pipeline

SPrav uses a 3-stage funnel to isolate genuine opportunities from thousands of raw postings:

```text
┌───────────────────────────────────────────────────────────┐
│ 1. Autonomous Ingestion & Deduplication                   │
│    Scans Greenhouse, Lever, Ashby, Workday, RSS feeds     │
└─────────────────────────────┬─────────────────────────────┘
                              ▼
┌───────────────────────────────────────────────────────────┐
│ 2. Application Scope Matrix Filter                        │
│    Enforces Target Roles, Seniority, Tech Stacks, Locs    │
└─────────────────────────────┬─────────────────────────────┘
                              ▼
┌───────────────────────────────────────────────────────────┐
│ 3. Hybrid ATS & Cosine Matcher (ATS Score >= 65% - 80%+)  │
│    Scores resume embeddings & skills against job specs    │
└─────────────────────────────┬─────────────────────────────┘
                              ▼
┌───────────────────────────────────────────────────────────┐
│ 4. Action Required (Guided 1-Click Dispatch Queue)        │
│    Surfaces high-fidelity roles with tailored cover notes │
└───────────────────────────────────────────────────────────┘
```

---

## 4. Multi-Engine AI Support (Local GPU + Free Cloud)

To ensure that anyone with any PC can use SPrav without hardware barriers:
* **Cloud-First Mode (Recommended)**: Utilizes Google Gemini 2.0 Flash or Groq (GPT-OSS 120B) via free personal API keys. Generates tailored cover notes in under 1 second with 0% CPU/GPU overhead.
* **Local GPU Mode (Optional)**: Connects directly to local **Ollama** instances (`qwen2.5-coder:7b` / `deepseek-r1:8b`) for complete offline, air-gapped execution.

---

## 5. Creator Vision & Independence

SPrav™ was engineered by **SVS Praveen** as an independent personal initiative to give technical candidates a professional, uncompromised tool for career growth.
