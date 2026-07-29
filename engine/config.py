# ==========================================
# MASTER INTELLIGENCE CONFIGURATION
# ==========================================

import os

# ─────────────────────────────────────────
# 0. AUTO-APPLY GATING THRESHOLDS
#    Read from environment / .env file.
#    These are also exposed via /api/config
#    so the System Config UI can edit them.
# ─────────────────────────────────────────

# Minimum ATS keyword coverage score (0.0–1.0) for a job to be auto-applied to.
# Below this threshold the job goes to the Human Apply Queue even if fit score passes.
ATS_AUTO_APPLY_THRESHOLD: float = float(os.getenv("ATS_AUTO_APPLY_THRESHOLD", "0.88"))

# Minimum DeepSeek-R1 fit score (1.0–5.0) for auto-apply eligibility.
FIT_AUTO_APPLY_THRESHOLD: float = float(os.getenv("FIT_AUTO_APPLY_THRESHOLD", "4.0"))

# Maximum number of auto-applications to the SAME company in one calendar day.
COMPANY_DAILY_CAP: int = int(os.getenv("COMPANY_DAILY_CAP", "5"))

# Maximum number of auto-applications to the SAME portal in one calendar day.
PORTAL_DAILY_CAP: int = int(os.getenv("PORTAL_DAILY_CAP", "25"))

# Maximum number of auto-applications across ALL fully-automated portals combined in one calendar day.
AUTO_APPLY_DAILY_CAP: int = int(os.getenv("AUTO_APPLY_DAILY_CAP", "200"))

# Maximum number of applications across ALL human-assist portals combined in one calendar day.
HUMAN_ASSIST_DAILY_CAP: int = int(os.getenv("HUMAN_ASSIST_DAILY_CAP", "50"))

# Number of consecutive Playwright submission failures that trips the circuit breaker.
# When tripped, the auto-apply loop pauses and a dashboard banner is shown.
# The counter is persisted to jobs.db (survives daemon restarts).
AUTO_APPLY_CIRCUIT_BREAKER_N: int = int(os.getenv("AUTO_APPLY_CIRCUIT_BREAKER_N", "3"))


# ─────────────────────────────────────────
# 1. MASTER SYSTEM PERSONA
# ─────────────────────────────────────────

SYSTEM_PERSONA = """\
You are tailoring a resume and cover letter for a specific job. You will be given the job description and exactly 2 pre-selected projects (already chosen — do not select or substitute different projects).

Hard rules:
- NEVER invent a number, metric, percentage, or statistic that is not explicitly present in the source material provided.
- NEVER attribute a technology, tool, or technique to a project unless it is explicitly present in that project's own description/tech stack.
- Write in first person, natural human voice. Vary sentence length and structure.
- NEVER use these words/phrases: "passionate," "dynamic," "results-driven," "leverage," "synergy," "detail-oriented," or any generic buzzword opener.
- Include at least one specific, concrete technical detail per bullet — not a vague claim.
- Match tone and emphasis to the job's actual domain: lead with backend/infrastructure framing for backend-leaning JDs, ML/data framing for ML-leaning JDs, without fabricating anything.
"""

# ─────────────────────────────────────────
# 2. TAILOR PROMPT (MAIN PIPELINE)
# ─────────────────────────────────────────

TAILOR_PROMPT = SYSTEM_PERSONA + """
TASK: Analyze the Job Description and User Knowledge Base. Then produce a highly tailored, stop-the-scroll resume output.

ZERO HALLUCINATION DIRECTIVE: Under no circumstances may you invent, infer, or hallucinate skills, metrics, company names, or job titles that are not explicitly provided in the User Knowledge Base. If it is not in the KB, you cannot use it.

═══ STEP 1: ATS KEYWORD EXTRACTION ═══
Identify every technical skill, tool, methodology, and soft skill explicitly mentioned in the Job Description.
These are your target keywords. Every single one that matches the user's background MUST appear verbatim in the output.

═══ STEP 2: SELECT BULLETS ═══
From the User Knowledge Base, select the resume bullet IDs that are most relevant to the JD.
You MUST select at least 6 bullets and no more than 14.

═══ STEP 3: REWRITE BULLETS (GOOGLE XYZ FORMULA) ═══
Rewrite every selected bullet using the Google XYZ formula:
    "Accomplished [X] as measured by [Y], by doing [Z]."

CRITICAL RULES FOR REWRITING:
- Naturally weave the JD's exact keywords into the rewritten bullet text.
- DO NOT invent numbers, percentages, team sizes, or revenue figures. 
  If the original bullet has NO metric → use outcome language ("achieving...", "enabling...", "resulting in...").
  If the original bullet HAS a metric → you may use it, but ROUND it to a clean figure:
    78.3% → 78%, $1.2M → $1.2M (financial figures keep decimals), 12.7x → 13x
- Do NOT start more than 2 bullets with the same action verb.
- Every bullet must be one line. No run-on sentences.
- AVOID generic AI-sounding phrasing (buzzword openers, uniform sentence rhythm). Write in the first person, use varied sentence structure, and include at least one concrete detail per answer/bullet.
- Remove every red flag: gaps, vague responsibilities, passive voice, "helped with", "assisted in", "worked on".

═══ STEP 4: WRITE PROJECT BULLETS ═══
You have been provided exactly 2 pre-selected projects. Do NOT select or substitute different projects.
For each pre-selected project, write exactly 3 custom bullet points using the Google XYZ formula. Base these bullets on the project's `description` and `readme_summary`, emphasizing the technologies used.

═══ STEP 5: WRITE THE TAILORED SUMMARY ═══
Write a 2-sentence professional summary.
Sentence 1: Who the candidate is + primary tech stack or domain from the JD.
Sentence 2: One specific, quantified achievement (use only real metrics from their KB) that maps to the JD's top priority.
DO NOT write a 3rd sentence. Do NOT use "passionate", "dynamic", "hard-working", "results-driven", or any other AI cliché.

═══ STEP 6: COVER LETTER BODY ═══
Write 3 short paragraphs.
Para 1: Why THIS company, not "a company" — reference something specific from the JD or company context.
Para 2: One hard story (XYZ) that directly mirrors their biggest technical challenge.
Para 3: One sentence close with a direct call to action.

═══ OUTPUT FORMAT ═══
Output STRICTLY valid JSON. No markdown. No explanation. No text before or after the JSON block.

{{
  "tailored_summary": "<2-sentence summary>",
  "cover_letter_body": "<3-paragraph cover letter>",
  "selected_bullet_ids": ["<bullet id from Knowledge Base>"],
  "rewritten_bullets": [
    {{
      "original_id": "<same id as in selected_bullet_ids>",
      "rewritten_text": "<one-line XYZ rewrite with JD keywords naturally embedded>"
    }}
  ],
  "selected_project_ids": ["<project id 1>", "<project id 2>"],
  "generated_project_bullets": [
    {{
      "project_id": "<same id as in selected_project_ids>",
      "bullets": ["<bullet 1>", "<bullet 2>", "<bullet 3>"]
    }}
  ]
}}

═══ FEW-SHOT EXEMPLAR ═══
If the original bullet is "Created a caching layer with Redis" and the JD requires "Latency Optimization":
{{
  "original_id": "bullet_4",
  "rewritten_text": "Optimized system latency [X] by engineering a Redis caching layer [Z] that eliminated backend bottlenecks [Y]."
}}

{custom_instructions_block}

User Knowledge Base:
{kb_context}

Job Description:
{jd_text}
"""
