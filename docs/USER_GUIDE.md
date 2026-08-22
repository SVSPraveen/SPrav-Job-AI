# SPrav Job AI — Official User Guide (v2.4.5 Pro)

Welcome to **SPrav Job AI**, the autonomous career intelligence platform that connects your Master Resume to 28,700+ verified tech company career boards and automatically discovers, scores, tailors, and dispatches job applications.

---

## 🚀 1. Quickstart & First-Time Setup (2 Quick Steps)

When you first launch SPrav Job AI, the **First-Time Setup Guard** ensures the autonomous engine only targets your preferred roles and preserves 100% resume fidelity.

```
┌─────────────────────────────────────────────────────────────┐
│ 🚀 Welcome! Complete 2 Quick Steps to Activate SPrav AI     │
├──────────────────────────────┬──────────────────────────────┤
│ Step 1: Ground Truth         │ Step 2: Targeting Rules      │
│ [📄 Upload Master Resume PDF]│ [🎯 Configure Target Scope]  │
└──────────────────────────────┴──────────────────────────────┘
```

### Step 1: Upload Your Master Resume (Ground Truth)
1. Go to **Knowledge Base** (or click **Setup Knowledge Base** on the Dashboard).
2. Upload your Master Resume PDF (e.g. `resume.pdf`).
3. The **Universal AI Document Intelligence Engine** extracts:
   - Your contact details, LinkedIn, GitHub, and Portfolio links.
   - All **Technical & Domain Skills** categorized across 10 skill domains.
   - Complete **Work History** and bullet points with exact metrics.
   - All **Projects**, tech stacks, and live demo links.
   - All **Degrees, Universities, CGPA/GPA**, and **Certifications**.

### Step 2: Configure Your Application Scope
1. Navigate to **Application Scope** in the sidebar.
2. **Target Roles:** Select from 800+ standardized titles (*e.g., AI Engineer, Full Stack Developer, Python Backend*) or type custom titles.
3. **Target Locations:** Select from 246 countries and global tech hubs (*e.g., India, United States, Germany, Bengaluru, New York, London, Remote*).
4. **Work Mode & Job Types:** Choose *Any, Remote Only, or On-site Only*, and select desired job types (*Full-time, Internship, Contract*).
5. Click **💾 Save Scope**. The autonomous engine unlocks immediately!

---

## 🎛️ 2. The SPrav™ Command Center Dashboard

The redesigned **Command Center** provides an ultra-premium operational cockpit:

* **Live AI Engine Status:** Displays active inference provider (`Local Ollama ⚡` vs `Groq Cloud ☁️`) with 1-click model switching.
* **4-Card Core Operational Row:**
  - 🟢 **Jobs Discovered:** Live count of all 28,700+ scraped and indexed positions.
  - 🟡 **Action Required:** Qualified jobs matching your 80%+ ATS threshold ready for 1-click tailored application.
  - 🔵 **Applications Sent:** Historical record of all submitted applications.
  - 🟣 **Target Scope:** Summary of active target roles and cities.
* **Continuous Discovery & Scoring Cockpit:**
  - **Start Loop / Stop Loop:** Starts the background scanner and scoring worker.
  - **Scan Now:** Forces an immediate real-time scan of 28,700+ company boards.
* **Master Resume Fidelity Box:** Shows active PDF status, size, and real-time extraction progress.

---

## 🎯 3. Automated Discovery, Scoring & Dispatch Pipeline

1. **Phase 1: Autonomous Discovery (`scraper.py`)**  
   Continuously monitors Greenhouse, Lever, Ashby, Workday, SmartRecruiters, Y Combinator, and Hacker News.
2. **Phase 2: Application Scope Gate (`scope_enforcer.py`)**  
   Evaluates discovered roles against your active titles, cities, and remote barriers in `< 1ms` (26,000+ jobs/sec).
3. **Phase 3: ATS Match Scoring (`ats_matcher.py`)**  
   Scores the job description against your Master Resume skills and highlights missing keywords.
4. **Phase 4: Resume Tailoring & Verifier Loop (`tailor.py` & `fact_checker.py`)**  
   Re-ranks bullet points to emphasize relevant projects and runs an automated verification loop to prevent hallucinated claims.
5. **Phase 5: Guided 1-Click Dispatch (`GuidedDispatch.jsx`)**  
   Review tailored applications in **Action Required** and click **Apply** to dispatch via Playwright automation.

---

## 📊 4. Benchmark Performance & Stress Testing

* **API Burst Throughput:** `154.4 requests/second` with 0 dropped connections.
* **In-Memory Filtering:** Evaluates `7,230 jobs` across 27 roles and 10 locations in `277.4 ms`.
* **Database Reliability:** Zero lock contentions under 40 simultaneous SQLite WAL transactions.