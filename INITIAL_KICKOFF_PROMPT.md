# Initial Kickoff Prompt

Paste everything in the code block below into Antigravity as your very
first message to Gemini 3.1 Pro, after you've placed README.md,
PROJECT_VISION.md, SCOPE.md, PREPARATION_GUIDE.md, and job_assistant_plan.md
in your project folder.

---

```
You are acting as my technical architect and code reviewer for a personal
project. I'm using a two-model workflow inside Google Antigravity IDE:
- You (Gemini 3.1 Pro) write the actual code.
- I also consult Claude in a separate chat as architect/reviewer between
  sessions. You don't talk to Claude directly — I'm the relay.

I'm building a personal AI job application assistant. Before writing any
code, read these files in D:\Job Assistant Plan\ in full:
- job_assistant_plan.md  (phased build plan, tech stack, file structure)
- PROJECT_VISION.md      (architecture rationale, anticipated failure
                           modes — these are lessons from an earlier
                           prototype, treat them as requirements, not
                           suggestions)
- SCOPE.md                (what's in scope now vs explicitly not-yet vs
                           permanently out of scope — this overrides
                           anything that seems like a natural next step)
- README.md               (quick start, structure, the rules the engine
                           must enforce)

The single non-negotiable rule: the tailoring engine must never invent a
fact, metric, employer, or skill that isn't in knowledge_base/me.json.
Every architecture decision below exists to make that rule structurally
true, not just prompt-level true.

ENVIRONMENT CHECK (do this first):
- Confirm python, git, and node are available in this terminal and print
  their versions
- Confirm Ollama is running (`ollama list`) — if llama3.1:8b isn't pulled
  yet, run `ollama pull llama3.1:8b`
- Create a Python virtual environment in this folder (.venv) and activate
  it for all subsequent installs

BUILD PHASE 1 ONLY — knowledge base + tailoring engine. Do NOT build job
discovery, browser automation, or email tracking yet — see SCOPE.md.

Project structure:
/knowledge_base/   - my structured data: projects, resume bullets, skills, history
/engine/           - tailoring engine + LLM provider abstraction
/output/           - generated tailored resumes will go here later
/config/           - mode.yaml, targeting.yaml
/tests/            - tests for the tailoring engine, including regression
                     fixtures for known failure modes

Steps:

1. Set up requirements.txt (start minimal: requests, pyyaml, python-dotenv
   — we'll add docx/playwright/gmail libs in later phases) and install
   into the venv.

2. Design knowledge_base/schema.md — the JSON structure for my data.
   Required fields per PROJECT_VISION.md, not just the obvious ones:
   - Resume bullets: id, text, parent_id (which company/project it
     belongs to), metric_verified (tri-state enum: verified /
     self_reported / estimated — not boolean), ats_keywords, themes,
     last_reviewed (date)
   - Work history / projects: standard fields, plus an explicit
     in_progress flag (separate from completed work) and last_reviewed
   - Certifications kept in a structurally separate section from work
     history, never mergeable into it
   Then create knowledge_base/me.json with realistic placeholder data
   structured to that schema, so I know exactly what to fill in with my
   real info.

3. Create config/mode.yaml with three provider options:
   - free (default): local Ollama, model name + host configurable
   - groq: Groq's OpenAI-compatible endpoint, model name configurable
     (default llama-3.3-70b-versatile), API key referenced from env, never
     hardcoded
   - paid: Anthropic API, model name configurable, API key from env
   All three must work behind the exact same interface (next step).

4. Build engine/llm_provider.py: a single function
   `generate(prompt: str, mode: str) -> str` that routes to Ollama's REST
   API (localhost:11434), Groq's OpenAI-compatible endpoint, or the
   Anthropic API, based on config/mode.yaml. Same interface regardless of
   provider, so switching is a one-line config change.

5. Build engine/tailor.py: the core tailoring function. Input = job
   description text + knowledge_base/me.json. Output = tailored resume
   content (structured, not just prose — JSON with sections: summary,
   experience bullets, skills) that:
   - only uses facts present in the knowledge base, never invents metrics
   - selects bullets by ID only — never generates free-text bullet content
   - generates the summary paragraph either from a KB-fact template with
     slots, or runs it through a post-generation fact-check pass against
     the KB before returning it — it does not get a free pass just
     because it's short
   - naturally works in JD keywords for ATS matching, without copying JD
     sentences verbatim (this needs its own explicit prompt guard plus a
     similarity check against the JD text, since the summary paragraph
     is the one place ID-selection can't protect against copying)
   - validates every selected bullet ID against the exact allowed-ID
     subset of its claimed parent entity, stripping anything that doesn't
     match (cross-attribution guard)
   - flags in its output if the JD needs a skill/experience I don't have
     in the knowledge base, instead of quietly making it up

6. Build main.py as a CLI: takes a job description (from a text file or
   pasted in), runs it through the tailoring engine, and prints the
   structured tailored resume to console.

7. Write tests in /tests/ that specifically cover the anticipated failure
   modes from PROJECT_VISION.md, not just a happy-path check:
   - a sample JD run against placeholder KB doesn't invent a skill not in
     me.json
   - a certification in the KB never appears as a work_history entry
   - a bullet ID from one project never gets attributed to a different
     parent
   - a fabrication-by-combination case: two true, separate facts don't
     get merged into an unstated combined claim
   - a deliberately oversized/dense placeholder KB entry doesn't get
     truncated mid-JSON by the provider's token limit

Explain your architecture decisions briefly as you go, especially anywhere
you're deviating from what I described. Ask before running any command
that needs network access beyond localhost, and before installing
anything not in requirements.txt. Don't start on job discovery, docx
generation, or auto-submit — flag clearly when Phase 1 is done and ready
for review.
```

---

## Before you send this

Go through `PREPARATION_GUIDE.md` first — specifically the environment and
provider-key sections. The prompt above assumes Ollama is installed and,
if you want Groq available from day one, that you already have a
`GROQ_API_KEY`. You don't have to use Groq immediately (`free` is the
default mode), but it's cheaper to design the three-way branch in from the
start than to bolt it on later.
