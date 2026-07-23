# Preparation Guide

A checklist to work through before (or between) Antigravity sessions. None
of this requires Gemini — it's things only you can do.

## 1. Environment

- [ ] Python 3.13+, git, node available (already confirmed in earlier session)
- [ ] `.venv` created and activated
- [ ] `pip install -r requirements.txt` run inside the venv
- [ ] Ollama installed, `ollama serve` running, `llama3.1:8b` pulled
      (`ollama pull llama3.1:8b`) — this is your always-available free
      fallback even once Groq is added

## 2. Choose your provider(s) for this session

You don't need to pick one forever — `config/mode.yaml` is a one-line
switch. But decide what you're testing against today:

- [ ] **Local only (`MODE: free`)**: no keys needed, works offline, weakest
      instruction-following on strict ID-selection tasks
- [ ] **Groq (`MODE: groq`)**: sign up at console.groq.com (no card), copy
      your key into `.env` as `GROQ_API_KEY`. Free tier is rate-limited
      (roughly 30 req/min, low tokens/min on the 70B model) — fine for your
      personal usage volume, not for hammering it in a test loop
- [ ] **Anthropic (`MODE: paid`)**: `ANTHROPIC_API_KEY` in `.env`, only if
      you want to benchmark quality against the free options

- [ ] `.env` exists (copied from `.env.example`), and `.env` is in
      `.gitignore` — confirm before you commit anything

## 3. Your real data

This is the part that actually determines output quality — the engine can
only be as honest and as good as what's in `me.json`.

- [ ] Decide which resume/projects are your canonical source. If your
      real resume is denser than the placeholder data (yours is — see the
      truncation bug in the bug log), expect the LLM extraction to need the
      higher `max_tokens` already set
- [ ] Run the Streamlit editor (`streamlit run streamlit_kb_editor.py`) and
      use **Document Upload** to extract from your resume PDF
- [ ] On the Review Screen: check every bullet's `metric_verified` flag
      makes sense — a bullet with a real number should be `true`, vague
      claims should stay `false` so the engine knows to treat them
      cautiously
- [ ] Check bullets landed under the right parent (work_history vs
      projects) — this is exactly the cross-attribution bug class, worth a
      manual look even though the validator catches most of it
- [ ] Confirm certifications did **not** get parsed as work history entries
      (the Oracle bug)
- [ ] Only then click **Confirm & Save**
- [ ] Spot-check `knowledge_base/me.json` directly afterward — read it once
      end to end

## 4. Before you trust the pipeline on a real application

- [ ] Run `pytest tests/ -v` — should pass with your real data, not just
      the placeholder
- [ ] Run `python main.py --jd tests/sample_jd.txt` and read the full
      output, don't skim it
- [ ] Try it against a real JD you're actually planning to apply to, and
      manually check every bullet it selected against your KB — yes,
      every time, until you've built enough trust in the validator to
      spot-check instead
- [ ] Run `python scripts/verify_ats_keywords.py` if you're using it as a
      pre-submission check

## 5. Privacy check before any git push

- [ ] `knowledge_base/me.json` is gitignored (it's your real PII —
      email, phone, work history)
- [ ] `.env` is gitignored
- [ ] `/output/` (generated resumes) is gitignored
- [ ] If you ever plan to make the repo public (e.g. for portfolio
      purposes), do a final `git log -p` skim on anything that touched
      those paths before it was gitignored, in case something leaked into
      an early commit

## 6. Resuming an Antigravity session

Once the above is done, open `GEMINI_KICKOFF_PROMPT.md`, fill in the
`[CURRENT STATE]` block with whatever's actually true right now (which
files exist, what's mid-debug, what you just tested), and paste the whole
thing to Gemini 3.1 Pro as your first message of the session.
