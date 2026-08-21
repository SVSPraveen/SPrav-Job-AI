"""
engine/ats_matcher.py

High-Fidelity Deterministic & Hybrid ATS Matcher.

Computes:
    1. Hard Skill Alignment: (Matched JD Skills in Master Profile) / (Total Detected JD Skills) * 100
    2. Role & Title Alignment: Matching targeted roles against Job Title.
    3. Semantic Context Alignment: Sentence embedding similarity for nuanced requirement coverage.
    
Produces transparent match telemetry (matched_skills, missing_skills, ats_score).
"""
from __future__ import annotations

import os
import re
import json

from engine.utils import get_data_dir
from engine.skill_taxonomy import expand_candidate_skills, skill_implies_candidate_has

# Global caches
_resume_text_cache: str | None = None
_candidate_skills_cache: set[str] | None = None
_known_skills_cache: list[str] | None = None
_resume_emb_cache = None
_model_cache = None

KNOWN_SKILLS_PATH = os.path.join(os.path.dirname(__file__), "data", "known_skills.json")

def load_known_skills() -> list[str]:
    global _known_skills_cache
    if _known_skills_cache is not None:
        return _known_skills_cache
    if os.path.exists(KNOWN_SKILLS_PATH):
        try:
            with open(KNOWN_SKILLS_PATH, "r", encoding="utf-8") as f:
                _known_skills_cache = json.load(f)
                return _known_skills_cache
        except Exception:
            pass
    return [
        "python", "javascript", "typescript", "react", "fastapi", "docker", "aws", "gcp", "azure",
        "sql", "postgresql", "mongodb", "redis", "langchain", "langgraph", "llamaindex",
        "rag", "vector databases", "qdrant", "pinecone", "pgvector", "pytorch", "tensorflow",
        "scikit-learn", "git", "linux", "rest apis", "graphql", "kubernetes", "ci/cd"
    ]

def load_candidate_skills() -> set[str]:
    """Loads all verified skills and keywords from me.json and resume text."""
    global _candidate_skills_cache
    if _candidate_skills_cache is not None:
        return _candidate_skills_cache

    skills = set()
    me_path = os.path.join(get_data_dir(), "knowledge_base", "me.json")
    if os.path.exists(me_path):
        try:
            with open(me_path, "r", encoding="utf-8") as f:
                me = json.load(f)
            # 6-category skills schema
            skills_obj = me.get("skills", {})
            for cat, sk_list in skills_obj.items():
                if isinstance(sk_list, list):
                    for s in sk_list:
                        skills.add(s.lower().strip())
                elif isinstance(sk_list, str):
                    skills.add(sk_list.lower().strip())

            # Also extract from work history bullets and project tech stacks
            for w in me.get("work_history", []):
                for b in w.get("bullets", []):
                    if isinstance(b, dict):
                        for kw in b.get("ats_keywords", []):
                            skills.add(kw.lower().strip())
            for p in me.get("projects", []):
                for t in p.get("tech_stack", []):
                    skills.add(t.lower().strip())
        except Exception:
            pass

    _candidate_skills_cache = expand_candidate_skills(skills)
    return _candidate_skills_cache

def _get_model():
    global _model_cache
    if _model_cache is None:
        from sentence_transformers import SentenceTransformer
        _model_cache = SentenceTransformer('all-MiniLM-L6-v2')
    return _model_cache

def _resume_text() -> str:
    global _resume_text_cache
    if _resume_text_cache is not None:
        return _resume_text_cache

    pdf_path = os.path.join(get_data_dir(), "knowledge_base", "master_resume.pdf")
    if not os.path.exists(pdf_path):
        _resume_text_cache = ""
        return ""

    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            _resume_text_cache = " ".join(
                (page.extract_text() or "") for page in pdf.pages
            )
    except Exception:
        _resume_text_cache = ""

    return _resume_text_cache

def _resume_emb():
    global _resume_emb_cache
    if _resume_emb_cache is not None:
        return _resume_emb_cache

    resume_text = _resume_text()
    if not resume_text:
        return None

    try:
        model = _get_model()
        _resume_emb_cache = model.encode(resume_text)
        return _resume_emb_cache
    except Exception:
        return None

def load_target_roles() -> list[str]:
    """Loads target roles from application_scope.json, falling back to me.json."""
    roles = []
    scope_path = os.path.join(get_data_dir(), "config", "application_scope.json")
    if not os.path.exists(scope_path):
        scope_path = os.path.join(get_data_dir(), "application_scope.json")
    if os.path.exists(scope_path):
        try:
            with open(scope_path, "r", encoding="utf-8") as f:
                scope = json.load(f)
            roles = [r.strip().lower() for r in scope.get("target_roles", []) if r.strip()]
        except Exception:
            pass

    if not roles:
        me_path = os.path.join(get_data_dir(), "knowledge_base", "me.json")
        if os.path.exists(me_path):
            try:
                with open(me_path, "r", encoding="utf-8") as f:
                    me = json.load(f)
                for w in me.get("work_history", []):
                    r = w.get("role", "").strip().lower()
                    if r and r not in roles:
                        roles.append(r)
            except Exception:
                pass

    if not roles:
        roles = ["software engineer", "developer", "engineer"]
    return roles


def extract_jd_skills(jd_text: str) -> list[str]:
    """Extracts technical skills detected in the JD text with strict boundary protection."""
    if not jd_text:
        return []
    known = load_known_skills()
    detected = []
    
    # Pre-clean text for matching
    cleaned_jd = " " + jd_text.replace("/", " / ").replace(",", " , ") + " "
    
    for skill in known:
        sk_raw = skill.strip()
        sk_lower = sk_raw.lower()
        
        # Single-letter and symbol protection: C, R, Go, .NET, C#, C++
        if sk_lower in ("c", "r"):
            # Must be surrounded by programming/language context or explicit keyword
            pattern = re.compile(rf'(?i)(?:language[s]?\s*[:\s]|programming in\s+|proficient in\s+|using\s+)?(?<![a-zA-Z0-9_#+]){re.escape(sk_raw)}(?![a-zA-Z0-9_#+])')
        elif sk_lower == "go":
            pattern = re.compile(rf'(?i)(?:golang|(?<![a-zA-Z0-9_])go\s+(?:language|lang|developer|engineer|backend|microservices)|(?<![a-zA-Z0-9_])go(?=\s*[,/]))')
        elif sk_lower in ("c#", "c++", ".net"):
            pattern = re.compile(rf'(?i)(?<![a-zA-Z0-9_]){re.escape(sk_raw)}(?![a-zA-Z0-9_#+])')
        else:
            pattern = re.compile(rf'(?<![a-zA-Z0-9_]){re.escape(sk_lower)}(?![a-zA-Z0-9_])', re.IGNORECASE)
            
        if pattern.search(cleaned_jd):
            detected.append(sk_raw)
            
    # Deduplicate while preserving order
    seen = set()
    result = []
    for d in detected:
        if d.lower() not in seen:
            seen.add(d.lower())
            result.append(d)
    return result


def compute_ats_details(jd_text: str | None, title: str = "") -> dict:
    """
    Computes comprehensive ATS match metrics:
    - ats_score: 0.0 to 100.0 (Properly calibrated hybrid scale)
    - matched_skills: list of matched skill names
    - missing_skills: list of missing skill names
    - jd_skills: all skills found in the JD
    """
    text_to_eval = (jd_text or "").strip()
    if not text_to_eval:
        text_to_eval = (title or "").strip()

    if not text_to_eval:
        return {"ats_score": 0.0, "matched_skills": [], "missing_skills": [], "jd_skills": []}

    candidate_skills = load_candidate_skills()
    resume_text = _resume_text().lower()
    jd_skills = extract_jd_skills(text_to_eval)

    matched = []
    missing = []
    for sk in jd_skills:
        sk_lower = sk.lower()
        # Use the inference engine: direct match, alias match, or logical implication
        if (skill_implies_candidate_has(candidate_skills, sk) or
            re.search(rf'(?<![a-zA-Z0-9_]){re.escape(sk_lower)}(?![a-zA-Z0-9_])', resume_text)):
            matched.append(sk)
        else:
            missing.append(sk)

    # 1. Deterministic Skill Score (0-100)
    if jd_skills:
        skill_score = (len(matched) / len(jd_skills)) * 100.0
    else:
        skill_score = 65.0 # Neutral positive baseline if JD lists zero detectable hard skills

    # 2. Dynamic Role Title Relevance (0-100 scale)
    combined_title = (title + " " + text_to_eval[:300]).lower()
    target_roles = load_target_roles()
    
    role_score = 40.0 # Base relevance
    for target in target_roles:
        t_words = [w for w in target.split() if len(w) > 2]
        if target in combined_title:
            role_score = 100.0
            break
        elif t_words and all(w in combined_title for w in t_words):
            role_score = 90.0
            break
        elif t_words and any(w in combined_title for w in t_words):
            role_score = max(role_score, 75.0)

    # General tech engineering role match fallback
    if role_score == 40.0:
        general_tech_terms = ["engineer", "developer", "architect", "lead", "specialist", "scientist", "analyst"]
        if any(term in combined_title for term in general_tech_terms):
            role_score = 60.0

    # 3. Semantic Similarity Component (0-100)
    semantic_score = 60.0
    try:
        resume_emb = _resume_emb()
        if resume_emb is not None:
            model = _get_model()
            jd_emb = model.encode(text_to_eval[:2000])
            from sentence_transformers import util
            cos_sim = util.cos_sim(resume_emb, jd_emb).item()
            # Normalize cosine similarity (0.20 - 0.75) to (30.0 - 100.0)
            semantic_score = max(30.0, min(100.0, ((cos_sim - 0.20) / 0.55) * 70.0 + 30.0))
    except Exception:
        semantic_score = 60.0

    # Hybrid Weighted Final Score:
    # 60% Hard Skills + 25% Semantic Alignment + 15% Role Title Match
    if jd_skills:
        final_score = (skill_score * 0.60) + (semantic_score * 0.25) + (role_score * 0.15)
    else:
        final_score = (semantic_score * 0.70) + (role_score * 0.30)

    # Ensure score bounds
    final_score = round(max(0.0, min(100.0, final_score)), 1)

    return {
        "ats_score": final_score,
        "matched_skills": matched,
        "missing_skills": missing,
        "jd_skills": jd_skills
    }

def compute_ats_match(jd_text: str | None, title: str = "") -> float:
    """Returns 0-100 float ATS match score for backward compatibility."""
    return compute_ats_details(jd_text, title)["ats_score"]

def get_friendly_resume_filename() -> str:
    """Returns the user-facing filename for the master resume."""
    kb_dir = os.path.join(get_data_dir(), "knowledge_base")
    me_path = os.path.join(kb_dir, "me.json")
    try:
        with open(me_path, "r", encoding="utf-8") as f:
            me = json.load(f)
        name = me.get("personal", {}).get("name", "").strip()
        if name:
            return name.replace(" ", "_") + "_Resume.pdf"
        orig = me.get("master_resume_original_filename", "")
        if orig:
            return orig
    except Exception:
        pass
    return "master_resume.pdf"
