# Scope

This file exists so any session — you, Gemini in Antigravity, or a future
contributor — can check "is this in scope right now?" without re-reading the
whole history. When in doubt, this file wins over enthusiasm mid-session.

## In Scope Right Now (Phase 1 + Phase 2)

- Knowledge base schema + `me.json` (your real data, source of truth)
- Tailoring engine: JD text in, structured tailored resume out
- ID-based bullet selection + deterministic hydration + parent-scoped
  validation (see `PROJECT_VISION.md` for why this exists)
- Gap-flagging when a JD wants something not in the KB
- Provider abstraction: local Ollama (free), Groq free tier, Anthropic
  (paid) — same interface, config-only switch
- Docx resume generation from tailored output
- PDF export (currently Windows/Word-dependent — see tech debt)
- Streamlit KB editor: manual form, Document Upload intake, Guided Form
  intake, Conversational intake — all gated by a human review-and-confirm
  screen before anything writes to `me.json`
- Local automated tests (hallucination checks, structure checks, ATS
  keyword checks)

## Explicitly Not Yet Built (do not start without a direct ask)

- **Job discovery** (Phase 3): scraping or querying Greenhouse, Lever,
  Adzuna, Arbeitnow, Jobicy, RemoteOK, WeWorkRemotely, or curated career
  pages. Scoped in `PROJECT_VISION.md`, not started.
- **Tier 1 auto-apply** (Phase 4): any code that fills out and submits an
  application form on Greenhouse or Lever.
- **Tier 2 notify pipeline** (Phase 4): surfacing tailored resumes for
  Workday/LinkedIn/iCIMS/Taleo/Jobvite for manual submission.
- **Email tracking** (Phase 5): Gmail API integration, confirmation/
  rejection parsing, daily digest.
- **Multi-tenant / other-users support**: auth, per-user data isolation,
  consent/deletion flows, encrypted token storage, per-user rate limiting.
  Gated behind Phase 1-5 personal use actually proving out — see
  `PROJECT_VISION.md`'s Longer-Term Goal section.

## Permanently Out of Scope (not a "later," a "no")

- **LinkedIn scraping or active feed monitoring, in any form.** A logged-in
  automation session against LinkedIn carries account-ban risk that isn't
  worth the marginal coverage gain over LinkedIn's own Jobs search + native
  Saved Search Alerts. This applies even if a future session proposes a
  "careful" or "low-frequency" version.
- **Hard-filtering out possible-scam job listings.** Red flags get
  surfaced for human review in the Tier 2 digest; they never silently
  remove a listing, because false negatives (a real job wrongly discarded)
  matter more here than false positives.
- **Any code path where the LLM writes free-text resume content directly
  into `me.json` or the tailored output without going through ID-based
  selection + deterministic hydration + human review.** This is the core
  integrity guarantee of the whole project; a "just this once, it's a small
  feature" exception defeats the point.
- **Auto-apply automation with no rate limiting**, once Phase 4 exists —
  aggressive unattended submission volume is what gets a shared IP/company
  relationship flagged, which affects future users too if this ever gets
  productized.

## Non-Negotiables (apply to every phase)

1. Never invent a fact, metric, employer, or skill not present in the KB.
2. Every intake path ends at a human confirm step before writing to
   `me.json`. No exceptions for "obviously correct" extractions.
3. Tier 1/Tier 2 automation split is fixed by platform bot-detection risk,
   not by how tedious a platform's form is.
4. Region filtering happens before tailoring, not after — don't spend LLM
   compute on out-of-target roles.
5. Any new LLM provider added to `llm_provider.py` must share the exact
   same `generate(prompt, mode) -> str` interface as the existing ones.
