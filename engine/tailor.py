import json
import re
from engine.llm_provider import generate
from engine.config import TAILOR_PROMPT


def load_kb(path: str = "knowledge_base/me.json") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def flatten_bullets(kb: dict) -> list:
    """Flatten all bullets from work_history and projects into a single list."""
    bullets = []
    for job in kb.get("work_history", []):
        for bullet in job.get("bullets", []):
            bullet["parent_id"] = job.get("id", "")
            bullets.append(bullet)
    for project in kb.get("projects", []):
        for bullet in project.get("bullets", []):
            bullet["parent_id"] = project.get("id", "")
            bullets.append(bullet)
    return bullets


def construct_prompt(jd_text: str, kb: dict) -> str:
    kb_str = json.dumps(kb, indent=2)
    return TAILOR_PROMPT.format(kb_context=kb_str, jd_text=jd_text)


def validate_selection(selected_ids: list, kb: dict) -> list:
    """Validate bullet IDs exist in the KB to prevent cross-attribution hallucinations."""
    valid_ids = {b["id"] for b in flatten_bullets(kb)}
    return [bid for bid in selected_ids if bid in valid_ids]


def tailor_resume(jd_text: str, kb_path: str = "knowledge_base/me.json") -> dict:
    # Late import to avoid circular dependency at module load time
    from engine.brain import brain

    kb = load_kb(kb_path)

    # Build flat bullet list from nested structure
    all_bullets = flatten_bullets(kb)
    kb["resume_bullets"] = all_bullets

    # RAG Filtering: pre-filter bullets to the most semantically relevant
    brain.ingest_kb(kb)
    relevant_ids = brain.query_kb(jd_text, n_results=20)

    # Feed only the relevant subset to the LLM to save tokens and improve focus
    if relevant_ids and all_bullets:
        kb["resume_bullets"] = [b for b in all_bullets if b["id"] in relevant_ids]

    prompt = construct_prompt(jd_text, kb)

    # Restore full bullet list for hydration step
    kb["resume_bullets"] = all_bullets

    raw_response = generate(prompt, use_case="resume_tailoring")

    try:
        raw_response = raw_response.strip()
        # Strip markdown code fences if the model wraps the JSON
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_response, re.DOTALL)
        if json_match:
            raw_response = json_match.group(1)
        parsed_response = json.loads(raw_response)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse LLM response as JSON: {raw_response[:500]}") from e

    # ── Validate selected IDs ────────────────────────────────────────────────
    parsed_response["selected_bullet_ids"] = validate_selection(
        parsed_response.get("selected_bullet_ids", []), kb
    )

    # ── Build rewritten bullet lookup map ────────────────────────────────────
    # The LLM returns rewritten_bullets as [{original_id, rewritten_text}].
    # Build a dict for O(1) lookup during hydration.
    rewritten_map: dict[str, str] = {}
    for rw in parsed_response.get("rewritten_bullets", []):
        oid = rw.get("original_id", "")
        text = rw.get("rewritten_text", "").strip()
        if oid and text:
            rewritten_map[oid] = text

    # ── Hydration ────────────────────────────────────────────────────────────
    # Use the XYZ-rewritten text when available; fall back to the original.
    hydrated_bullets = []
    bullet_lookup = {b["id"]: b for b in all_bullets}
    for bullet_id in parsed_response["selected_bullet_ids"]:
        if bullet_id in bullet_lookup:
            bullet = dict(bullet_lookup[bullet_id])  # shallow copy to avoid mutating KB
            if bullet_id in rewritten_map:
                bullet["text"] = rewritten_map[bullet_id]
            hydrated_bullets.append(bullet)

    parsed_response["hydrated_bullets"] = hydrated_bullets
    return parsed_response
