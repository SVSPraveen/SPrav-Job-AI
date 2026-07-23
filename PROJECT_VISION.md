# Project Vision & Architecture

## Current Status
Fresh build. This is an informed restart — the architecture below is
already shaped by real failure modes found in an earlier prototype (see
"Anticipated Failure Modes" below). We're building the guardrails in from
day one instead of discovering them one bug at a time.

Key architecture decisions:

- **Full-KB-Context Injection**: Given the relatively small size of a
  personal resume knowledge base, we inject the entire context into the LLM
  prompt. There is no need for vector databases or traditional RAG
  complexity.
- **ID-Based Bullet Selection**: Instead of allowing the LLM to generate
  free-text bullets, it is strictly forced to output an array of
  `selected_bullet_ids`. The engine deterministically hydrates the text from
  the knowledge base. This structurally prevents the LLM from hallucinating
  metrics or blindly copying text from the Job Description (JD-copying).
- **Summary Paragraph Gets the Same Guarantee**: The top-of-resume summary
  is the one place a naive implementation would let the LLM write free
  prose. Either template-slot it from KB facts, or run every claim in it
  through the same KB fact-check the bullets get. Do not treat it as a
  low-risk exception just because it's short.
- **Deterministic Hydration**: For projects and experience, fields like
  `tech_stack` and `tagline` are hydrated deterministically from the
  knowledge base rather than relying on the LLM's generation, mitigating
  missing or fabricated data.
- **In-Progress Distinction**: Specific roadmap items or uncompleted work
  (marked by `in_progress_extension_do_not_treat_as_completed`) are strictly
  separated to prevent the engine from passing off uncompleted work as
  shipped metrics.
- **Tri-State Verification, Not Boolean**: Each bullet's `metric_verified`
  field is `verified` (you have a concrete artifact backing the number),
  `self_reported` (you're confident it's true, no artifact), or `estimated`
  (approximate). This lets tailoring logic be more conservative for
  high-stakes applications without losing the bullet entirely.
- **Staleness Tracking**: Every KB entry carries a `last_reviewed` date. A
  script/UI warning surfaces entries not reviewed in N months — claims about
  in-progress work or fast-moving metrics go stale fastest.
- **Validation**: Strict validation ensures that the LLM only selects IDs
  that actually belong to the specific parent entity (company or project),
  avoiding cross-attribution.
- **Human-Gated Intake**: All KB intake paths (Document Upload, Guided Form,
  Conversational) route through a single Review Screen. No intake path
  writes to `me.json` without an explicit "Confirm & Save."

## Multi-Provider Strategy (built in from day one)
`config/mode.yaml` supports three interchangeable providers behind one
`generate(prompt: str, mode: str) -> str` interface in
`engine/llm_provider.py`:
- `free` — local Ollama (llama3.1:8b), zero cost, works offline, weakest on
  strict negative-constraint instructions (e.g. "output IDs only")
- `groq` — Groq's free tier (OpenAI-compatible endpoint, Llama 3.3 70B by
  default), meaningfully stronger instruction-following at zero token cost,
  rate-limited (verify current limits at implementation time — they shift)
- `paid` — Anthropic Claude, for benchmarking quality against the free tiers

Hardware constraint to design around: 8GB VRAM comfortably fits one 7-8B
local model, not two run concurrently. Use the local model for lightweight
tasks (e.g. JD technical-vs-generalist classification) and the hosted free
tier for heavier extraction/tailoring calls, rather than running multiple
large local models at once.

## The Evolving Motive & Vision
**Original Goal**:
A free, personal tool designed to help apply to jobs without inventing facts
about one's own experience. It must be safe to run unattended for safe
automation tiers only (e.g., Greenhouse, Lever) and notify-only for riskier
platforms (e.g., Workday, LinkedIn).

**Longer-Term Goal (Not yet in scope)**:
If this proves genuinely excellent for personal use, there is potential to
open it up — eventually as an at-cost or small-margin tool — to help other
early-career professionals. Many face the exact same problem: knowing how to
translate real project work into resume language that passes ATS and reads
credibly to a human.

Unlike incumbent tools (Teal, Rezi, Kickresume) that rely on 5,000+ resumes
of aggregate data, the differentiator here is a knowledge base grounded in
*real, specific project depth* that generic tools structurally cannot
replicate for a user. The value is not in a bigger model or more scoring
heuristics, but in structural factual grounding.

**Future Requirements (Do not build prematurely)**:
If/when that direction is pursued, it will require real additional work not
yet built:
- Multi-tenant auth and per-user data isolation
- DPDP/GDPR-compliant consent and deletion flows
- Encrypted storage for other users' OAuth tokens
- Conservative per-user rate limiting on auto-apply automation to avoid one
  user's behavior getting a shared IP/company relationship flagged for
  everyone.

## Anticipated Failure Modes (design around these pre-emptively)
Carried forward from an earlier prototype, so they get built out of the
system from the start instead of found and patched one at a time:

1. **Certification-as-Employer Hallucination**: An LLM can confuse a cloud
   cert (e.g. an Oracle OCI cert) for an actual employment role. Guard:
   explicit prompt instruction that certifications are not jobs, plus a
   validator that strips any experience entry that can't be fuzzy-matched to
   a real `work_history` entry.
2. **JD-Copying**: A weaker model asked to write bullets from facts will
   lazily echo JD phrasing back instead of synthesizing KB facts. Guard: ID-
   based bullet selection makes this structurally impossible for bullets;
   the summary paragraph needs its own guard (see above) since it's the
   remaining free-text surface.
3. **Cross-Attribution**: A project bullet can get assigned to the wrong
   parent (e.g. a personal-project bullet showing up under a work
   experience entry). Guard: validator filters selected IDs against the
   exact allowed-ID subset for the matched parent entity.
4. **Fabrication-by-Combination**: Two individually true facts can combine
   into a false implied claim (e.g. "used Docker" + "used Kubernetes" on
   separate projects becoming "built a production Kubernetes deployment
   pipeline"). No structural fix as clean as ID-selection exists for this
   yet — treat it as a required test case in the regression suite, not a
   solved problem.
5. **Token-Limit Truncation on Dense Real Data**: LLM JSON extraction on a
   real, detailed resume can exceed a default token budget and truncate
   mid-string. Guard: size `max_tokens` to the densest expected real input,
   not a round default, and validate/repair JSON output before parsing.

## Future Architecture: Phase 3 (Job Discovery) Guidelines
Phase 3 is scoped for the future and focuses on auto-discovery of roles. The
following non-negotiable guidelines apply:

1. **Pre-Tailoring Region Filtering**: Job results from platforms
   (Greenhouse, Lever, Adzuna) must be filtered against `target_locations`
   (in `targeting.yaml`) *before* they ever reach the tailoring engine.
2. **Lightweight Scam Detection (Red Flags)**: Heuristic flagger for common
   scam patterns (no verifiable company domain, requests for payment/
   deposit, wildly inconsistent salary, chat-app-only interview process).
   Never hard-filtered — surfaced in the Tier 2 digest for human review,
   since false negatives matter more than false positives here.
3. **Expanded Job Discovery Coverage**: ATS public feeds (Greenhouse,
   Lever), free job boards (Adzuna, Arbeitnow, Jobicy, RemoteOK,
   WeWorkRemotely), and direct career-page scraping (postings list only,
   never submission flows) for a manually-curated allowlist of target
   companies. Widens the pool for tailoring; does not change the Tier 1/
   Tier 2 automation split or daily rate limits.
4. **EXPLICITLY OUT OF SCOPE: LinkedIn Scraping**: Not built, not planned.
   Account-ban risk from a logged-in automation session outweighs the
   coverage gain over LinkedIn's own Jobs search + native Saved Search
   Alerts.

## Tech Debt to Avoid Reintroducing
The earlier prototype used `docx2pdf` for PDF export, which depends on a
local Microsoft Word install via Windows COM — ties PDF generation to
Windows-with-Word. Build the headless path (LibreOffice headless or
pypandoc) from the start this time rather than retrofitting it later.
