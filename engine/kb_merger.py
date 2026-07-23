"""
engine/kb_merger.py — Knowledge Base Merge Engine
==================================================
Takes outputs from one or more intake.py parse functions and merges them
into the canonical me.json schema.

Key behaviours:
  - Dedup: same company + overlapping date range = one entry. Never duplicates.
  - Conflict detection: two sources disagree on a field → queued in
    `pending_conflicts[]`, NOT silently resolved.
  - Gap detection: bullets with no numeric metric → queued in `needs_detail[]`
    with a targeted clarification prompt. This is the highest-leverage
    improvement: get the number before tailoring, not after.
  - Versioning: backs up the previous me.json to
    knowledge_base/history/me.json.<timestamp> before overwriting.

Output shape (also written to me.json):
{
    "personal": {...},
    "work_history": [...],          # all employment (full_time, internship, freelance, contract)
    "projects": [...],              # hand-written projects from previous me.json
    "github_projects": [...],       # fetched from GitHub API
    "portfolio_projects": [...],    # from portfolio scrape, confirmed: bool
    "education": [...],
    "certifications": [...],
    "skills": {...},
    "needs_detail": [...],          # bullets lacking a measurable outcome
    "pending_conflicts": [...]       # fields where sources disagree
}
"""

import json
import os
import re
import shutil
from datetime import datetime


KB_PATH = "knowledge_base/me.json"
HISTORY_DIR = "knowledge_base/history"

# Regex that matches any numeric metric: %, $, x, k, M, B, or plain numbers
_METRIC_RE = re.compile(
    r"\b\d+(?:[.,]\d+)?\s*(?:%|\$|£|€|x\b|k\b|M\b|B\b|ms\b|s\b|users\b|requests\b|repos?\b|commits?\b|days?\b|hours?\b|minutes?\b|seconds?\b|months?\b|years?\b|"
    r"engineers?\b|teams?\b|services?\b|customers?\b|clients?\b|employees?\b)?",
    re.IGNORECASE,
)

# Gap-detection prompt templates (chosen based on common role keywords)
_DETAIL_PROMPTS = {
    "performance": "You mentioned a performance improvement — do you have a before/after scale, latency number, or % reduction?",
    "speed": "You mentioned speed/time savings — how much time was saved (minutes, hours, days)?",
    "reduc": "You mentioned a reduction — by what percentage or absolute amount?",
    "scale": "You mentioned scale — how many users, requests/sec, or data volume?",
    "built": "You mention building something — what was the scope? (# users, requests/day, team size, lines of code?)",
    "migrat": "You mention a migration — how large was the codebase/system? How long did it take?",
    "improv": "You mention an improvement — do you have a before-vs-after number?",
    "lead": "You mention leading — how large was the team, and over what time period?",
    "default": "Can you add a measurable outcome (%, time saved, users affected, scale) to make this bullet concrete?",
}


def _has_metric(text: str) -> bool:
    return bool(_METRIC_RE.search(text))


def _pick_detail_prompt(text: str) -> str:
    lower = text.lower()
    for keyword, prompt in _DETAIL_PROMPTS.items():
        if keyword == "default":
            continue
        if keyword in lower:
            return prompt
    return _DETAIL_PROMPTS["default"]


# ─────────────────────────────────────────────────────────────────────────────
# Date helpers
# ─────────────────────────────────────────────────────────────────────────────

def _parse_year(date_str: str) -> int:
    """Extracts a 4-digit year from various date formats."""
    if not date_str:
        return 9999  # "Present" / unknown → treat as future
    match = re.search(r"\b(19|20)\d{2}\b", date_str)
    return int(match.group()) if match else 9999


def _dates_overlap(a_start: str, a_end: str, b_start: str, b_end: str) -> bool:
    """Returns True if two date ranges overlap (year-level precision is enough for dedup)."""
    a_s, a_e = _parse_year(a_start), _parse_year(a_end)
    b_s, b_e = _parse_year(b_start), _parse_year(b_end)
    return a_s <= b_e and b_s <= a_e


# ─────────────────────────────────────────────────────────────────────────────
# Core merge functions
# ─────────────────────────────────────────────────────────────────────────────

def _merge_personal(sources: list[dict], existing: dict) -> tuple[dict, list]:
    """
    Merges personal info. Last non-empty value wins per field.
    Conflicts (two non-empty, different values) are queued.
    """
    merged = dict(existing.get("personal", {}))
    conflicts = []

    for source in sources:
        for key, value in source.get("personal", {}).items():
            if not value:
                continue
            current = merged.get(key, "")
            if current and current != value and current not in ("YOUR FULL NAME", "your.email@gmail.com"):
                conflicts.append({
                    "field": f"personal.{key}",
                    "values": [
                        {"source": existing.get("_source", "existing"), "value": current},
                        {"source": source.get("_source", "unknown"), "value": value},
                    ],
                })
            else:
                merged[key] = value

    return merged, conflicts


def _find_existing_role(work_history: list, company: str, start: str, end: str) -> dict | None:
    """Finds an existing role entry by company + overlapping date range."""
    company_lower = company.lower().strip()
    for entry in work_history:
        if entry.get("company", "").lower().strip() == company_lower:
            if _dates_overlap(entry.get("start_date", ""), entry.get("end_date", ""), start, end):
                return entry
    return None


def _merge_work_history(sources: list[dict], existing: list) -> tuple[list, list]:
    """
    Merges work history from all sources.
    Same company + overlapping dates = one entry (dedup).
    Conflicting fields (e.g. different end dates) → pending_conflicts.
    Bullets from all sources are combined under the same entry.
    """
    merged: list[dict] = [dict(e) for e in existing]
    conflicts = []

    for source in sources:
        source_name = source.get("source", "unknown")
        for entry in source.get("work_history", []):
            company = entry.get("company", "").strip()
            if not company:
                continue

            existing_entry = _find_existing_role(
                merged, company, entry.get("start_date", ""), entry.get("end_date", "")
            )

            if existing_entry:
                # ── Dedup: merge bullets into existing ──────────────────────
                existing_bullet_texts = {b["text"].strip().lower() for b in existing_entry.get("bullets", [])}
                for bullet in entry.get("bullets", []):
                    if bullet.get("text", "").strip().lower() not in existing_bullet_texts:
                        existing_entry.setdefault("bullets", []).append(bullet)

                # ── Conflict detection on date fields ───────────────────────
                for date_field in ("start_date", "end_date"):
                    existing_val = existing_entry.get(date_field, "")
                    new_val = entry.get(date_field, "")
                    if (existing_val and new_val and existing_val != new_val
                            and _parse_year(existing_val) != _parse_year(new_val)):
                        conflicts.append({
                            "field": f"work_history[{company}].{date_field}",
                            "values": [
                                {"source": "existing", "value": existing_val},
                                {"source": source_name, "value": new_val},
                            ],
                        })
                # Keep type if more specific than 'full_time' default
                if entry.get("type") in ("internship", "freelance", "contract"):
                    existing_entry["type"] = entry["type"]
            else:
                # ── New entry ────────────────────────────────────────────────
                merged.append(dict(entry))

    # Remove internal _source markers from output
    for entry in merged:
        entry.pop("_source", None)
        for b in entry.get("bullets", []):
            b.pop("_source", None)

    return merged, conflicts


def _merge_simple_list(key: str, sources: list[dict], existing: list, id_field: str = "name") -> list:
    """
    Merges a simple list (education, certifications) by deduplication on `id_field`.
    No conflict detection — last non-empty value wins.
    """
    seen: dict[str, dict] = {e.get(id_field, "").lower(): e for e in existing}
    for source in sources:
        for item in source.get(key, []):
            item_key = item.get(id_field, "").lower()
            if item_key and item_key not in seen:
                clean = dict(item)
                clean.pop("_source", None)
                seen[item_key] = clean
    return list(seen.values())


def _merge_skills(sources: list[dict], existing: dict) -> dict:
    """Merges skills by category. Union of all lists, deduped."""
    merged: dict[str, list] = {k: list(v) for k, v in existing.items()}
    for source in sources:
        for category, items in source.get("skills", {}).items():
            current = merged.setdefault(category, [])
            current_lower = {s.lower() for s in current}
            for item in items:
                if item.strip().lower() not in current_lower:
                    current.append(item.strip())
    return merged


def _detect_needs_detail(work_history: list) -> list:
    """
    Scans every bullet across all work history entries.
    Bullets with no measurable metric are flagged with a targeted prompt.
    """
    flagged = []
    for entry in work_history:
        for bullet in entry.get("bullets", []):
            text = bullet.get("text", "").strip()
            if not text or _has_metric(text):
                continue
            flagged.append({
                "bullet_id": bullet.get("id", ""),
                "parent_company": entry.get("company", ""),
                "parent_role": entry.get("role", ""),
                "current_text": text,
                "prompt": _pick_detail_prompt(text),
            })
    return flagged


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def merge(sources: list[dict], kb_path: str = KB_PATH) -> dict:
    """
    Takes outputs from one or more intake.py parse functions plus the
    current me.json and produces a merged, deduped, conflict-flagged result.

    Args:
        sources: list of intermediate dicts from intake.py functions
        kb_path: path to the existing me.json (created empty if absent)

    Returns:
        The merged KB dict (also written to me.json, with backup).
    """
    # ── Load existing KB ─────────────────────────────────────────────────────
    existing_kb: dict = {}
    if os.path.exists(kb_path):
        try:
            with open(kb_path, "r", encoding="utf-8") as f:
                existing_kb = json.load(f)
        except json.JSONDecodeError:
            existing_kb = {}

    all_conflicts = []

    # ── Merge personal ───────────────────────────────────────────────────────
    merged_personal, personal_conflicts = _merge_personal(sources, existing_kb)
    all_conflicts.extend(personal_conflicts)

    # ── Merge work history ───────────────────────────────────────────────────
    merged_work, work_conflicts = _merge_work_history(sources, existing_kb.get("work_history", []))
    all_conflicts.extend(work_conflicts)

    # ── Merge education ──────────────────────────────────────────────────────
    merged_edu = _merge_simple_list("education", sources, existing_kb.get("education", []), "institution")

    # ── Merge certifications ─────────────────────────────────────────────────
    merged_certs = _merge_simple_list("certifications", sources, existing_kb.get("certifications", []), "name")

    # ── Merge skills ─────────────────────────────────────────────────────────
    merged_skills = _merge_skills(sources, existing_kb.get("skills", {}))

    # ── Merge GitHub projects ────────────────────────────────────────────────
    existing_gh = {p["id"]: p for p in existing_kb.get("github_projects", [])}
    for source in sources:
        for proj in source.get("github_projects", []):
            existing_gh.setdefault(proj["id"], proj)
            proj.pop("_source", None)
    merged_github = list(existing_gh.values())

    # ── Merge portfolio projects ─────────────────────────────────────────────
    existing_portfolio = {p["id"]: p for p in existing_kb.get("portfolio_projects", [])}
    for source in sources:
        for proj in source.get("portfolio_projects", []):
            proj.pop("_source", None)
            existing_portfolio.setdefault(proj["id"], proj)
    merged_portfolio = list(existing_portfolio.values())

    # ── Keep hand-written projects (not touched by intake) ───────────────────
    existing_projects = existing_kb.get("projects", [])

    # ── Gap detection ─────────────────────────────────────────────────────────
    needs_detail = _detect_needs_detail(merged_work)

    # ── Build final KB ───────────────────────────────────────────────────────
    merged_kb = {
        "personal": merged_personal,
        "work_history": merged_work,
        "projects": existing_projects,
        "github_projects": merged_github,
        "portfolio_projects": merged_portfolio,
        "education": merged_edu,
        "certifications": merged_certs,
        "skills": merged_skills,
        "needs_detail": needs_detail,
        "pending_conflicts": all_conflicts,
    }

    # ── Backup existing me.json before overwriting ───────────────────────────
    if os.path.exists(kb_path):
        os.makedirs(HISTORY_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(HISTORY_DIR, f"me.json.{timestamp}")
        shutil.copy2(kb_path, backup_path)
        print(f"[KBMerger] Backed up previous me.json → {backup_path}")

    # ── Write merged KB ──────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(kb_path), exist_ok=True)
    with open(kb_path, "w", encoding="utf-8") as f:
        json.dump(merged_kb, f, indent=2, ensure_ascii=False)

    print(f"[KBMerger] Merge complete: {len(merged_work)} roles, "
          f"{len(merged_github)} GitHub projects, "
          f"{len(needs_detail)} gaps flagged, "
          f"{len(all_conflicts)} conflicts queued.")

    return merged_kb


def resolve_conflicts(resolutions: list[dict], kb_path: str = KB_PATH) -> dict:
    """
    Applies user-resolved conflict choices and removes them from pending_conflicts.

    Args:
        resolutions: list of {"field": "...", "chosen_value": "..."}
        kb_path: path to me.json
    """
    with open(kb_path, "r", encoding="utf-8") as f:
        kb = json.load(f)

    for resolution in resolutions:
        field = resolution.get("field", "")
        value = resolution.get("chosen_value", "")
        # Apply simple top-level personal fields
        if field.startswith("personal."):
            key = field[len("personal."):]
            kb["personal"][key] = value

    # Remove resolved conflicts
    resolved_fields = {r["field"] for r in resolutions}
    kb["pending_conflicts"] = [
        c for c in kb.get("pending_conflicts", [])
        if c.get("field") not in resolved_fields
    ]

    with open(kb_path, "w", encoding="utf-8") as f:
        json.dump(kb, f, indent=2, ensure_ascii=False)

    return kb


def apply_detail_updates(updates: list[dict], kb_path: str = KB_PATH) -> dict:
    """
    Applies metric/detail updates submitted from the Onboarding 'Review' step.

    Args:
        updates: list of {"bullet_id": "...", "updated_text": "..."}
        kb_path: path to me.json
    """
    with open(kb_path, "r", encoding="utf-8") as f:
        kb = json.load(f)

    update_map = {u["bullet_id"]: u["updated_text"] for u in updates}
    updated_ids = set()

    for entry in kb.get("work_history", []):
        for bullet in entry.get("bullets", []):
            bid = bullet.get("id", "")
            if bid in update_map:
                bullet["text"] = update_map[bid]
                bullet["metric_verified"] = "self_reported"
                updated_ids.add(bid)

    # Remove resolved needs_detail items
    kb["needs_detail"] = [
        nd for nd in kb.get("needs_detail", [])
        if nd.get("bullet_id") not in updated_ids
    ]

    with open(kb_path, "w", encoding="utf-8") as f:
        json.dump(kb, f, indent=2, ensure_ascii=False)

    print(f"[KBMerger] Applied {len(updated_ids)} detail updates.")
    return kb


def kb_is_ready(kb_path: str = KB_PATH) -> bool:
    """
    Returns True if me.json has enough real data to start the discovery pipeline.
    Used by daemon startup check.
    """
    if not os.path.exists(kb_path):
        return False
    try:
        with open(kb_path, "r", encoding="utf-8") as f:
            kb = json.load(f)
        personal = kb.get("personal", {})
        name = personal.get("name", "").strip()
        has_name = bool(name) and name not in ("YOUR FULL NAME", "")
        has_work = len(kb.get("work_history", [])) > 0
        return has_name and has_work
    except Exception:
        return False
