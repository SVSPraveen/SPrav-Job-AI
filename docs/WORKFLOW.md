# SPrav Job AI — Autonomous Workflow & Execution Lifecycle

---

## The 5-Stage Agentic Pipeline

```
  ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
  │  1. DISCOVERY │ ──► │ 2. SCOPE GATE │ ──► │  3. MATCHING  │
  └───────────────┘     └───────────────┘     └───────────────┘
                                                      │
                                                      ▼
  ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
  │  5. DISPATCH  │ ◄── │  4. VERIFIER  │ ◄── │ 4. TAILORING  │
  └───────────────┘     └───────────────┘     └───────────────┘
```

### Stage 1: Continuous Autonomous Discovery
The background scraper continuously monitors over 28,700+ verified corporate job boards (Greenhouse, Lever, Ashby, Workday, SmartRecruiters) and startup job feeds.

### Stage 2: Scope Enforcement & Gating
Before any LLM compute is used, the job is evaluated against the user's active **Application Scope**:
- Title matches against preferred roles.
- Location matches against 246 countries and global tech hubs.
- Remote work eligibility verified by `RemoteCountryBarrier`.

### Stage 3: ATS Scoring & Keyword Extraction
The job description is analyzed against the candidate's Master Resume Knowledge Base (`me.json`) to compute a hybrid ATS match score (0–100%). Roles scoring 80%+ are qualified for application.

### Stage 4: Resume Tailoring & Closed-Loop Verification
- Bullet points are re-ordered and highlighted based on relevant experience.
- The **Fact-Checker Verifier Loop** cross-examines every claim against `me.json` to prevent hallucination.

### Stage 5: Guided 1-Click Dispatch
The application is staged in **Action Required**. With 1 click, the Playwright engine navigates to the job portal, fills out fields, attaches the tailored resume, and submits the application.