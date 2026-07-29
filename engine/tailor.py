from engine.utils import get_data_dir
import os
import json
import re
from engine.llm_provider import generate
from engine.config import TAILOR_PROMPT
from engine.fact_checker import extract_metric_claims

class TailoringError(Exception):
    pass


def load_kb(path: str = None) -> dict:
    if path is None: path = os.path.join(get_data_dir(), "knowledge_base", "me.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_all_kb_metrics(kb: dict, all_bullets: list) -> set:
    """Extract all valid metrics from the entire KB to validate cover letters."""
    kb_text = json.dumps(kb)
    return extract_metric_claims(kb_text)


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
    
    custom_inst = kb.get("personal", {}).get("custom_instructions", "").strip()
    if custom_inst:
        custom_block = f"═══ USER CUSTOM INSTRUCTIONS ═══\nTHE USER HAS PROVIDED OVERRIDE INSTRUCTIONS. YOU MUST OBEY THESE STRICTLY:\n{custom_inst}\n"
    else:
        custom_block = ""

    return TAILOR_PROMPT.format(kb_context=kb_str, jd_text=jd_text, custom_instructions_block=custom_block)


def jaccard_score(jd_words: set, proj: dict) -> float:
    stopwords = {"and","the","a","of","to","in","for","with","on","by","an","as","is","are","at","this","that","it","from","or"}
    score = 0.0
    
    tech_words = set()
    for t in proj.get("tech_stack", []) + proj.get("topics", []):
        tech_words.update(re.findall(r'\b[a-zA-Z0-9_]+\b', t.lower()))
        
    desc = proj.get("description", "") + " " + str(proj.get("readme_summary", ""))
    desc_words = set(re.findall(r'\b[a-zA-Z0-9_]+\b', desc.lower())) - stopwords
    
    for w in tech_words:
        if w in jd_words:
            score += 3.0
    for w in desc_words:
        if w in jd_words:
            score += 1.0
            
    return score


def validate_selection(selected_ids: list, valid_ids: set) -> list:
    """Validate bullet IDs exist in the KB to prevent cross-attribution hallucinations."""
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
    relevant_ids, distances = brain.query_kb(jd_text, n_results=20)
    
    # Store distance for relevance scoring later (lower distance = better score)
    dist_map = {bid: dist for bid, dist in zip(relevant_ids, distances)}

    # Feed only the relevant subset to the LLM to save tokens and improve focus
    if relevant_ids and all_bullets:
        kb["resume_bullets"] = [b for b in all_bullets if b["id"] in relevant_ids]
        
    # Deterministic Project Selection
    jd_words = set(re.findall(r'\b[a-zA-Z0-9_]+\b', jd_text.lower()))
    all_projects = kb.get("projects", []) + kb.get("github_projects", []) + kb.get("portfolio_projects", [])
    
    scored_projects = []
    for p in all_projects:
        if not p.get("id"): continue
        score = jaccard_score(jd_words, p)
        scored_projects.append((score, p))
        
    scored_projects.sort(key=lambda x: x[0], reverse=True)
    top_2_projects = [p for s, p in scored_projects[:2]]
    
    # Create a truncated copy of KB for the LLM to avoid context limits
    llm_kb = dict(kb)
    llm_kb.pop("work_history", None)
    llm_kb.pop("projects", None)
    
    # Truncate long readmes and ONLY pass the top 2 projects
    llm_kb["github_projects"] = []
    llm_kb["portfolio_projects"] = []
    for p in top_2_projects:
        p_copy = dict(p)
        if "readme_summary" in p_copy and isinstance(p_copy["readme_summary"], str):
            rs = p_copy["readme_summary"]
            p_copy["readme_summary"] = rs[:300] + ("..." if len(rs) > 300 else "")
        llm_kb["github_projects"].append(p_copy)

    prompt = construct_prompt(jd_text, llm_kb)

    # Restore full bullet list for hydration step
    kb["resume_bullets"] = all_bullets

    valid_bullet_ids = {b["id"] for b in all_bullets if "id" in b}
    valid_project_ids = set()
    for ptype in ["projects", "github_projects", "portfolio_projects"]:
        valid_project_ids.update(p["id"] for p in kb.get(ptype, []) if "id" in p)
    
    # Get all permissible metrics for the cover letter
    allowed_metrics = get_all_kb_metrics(kb, all_bullets)
    
    attempts = 0
    max_attempts = 2
    hallucinated_logs = []
    parsed_response = None
    
    while attempts < max_attempts:
        attempts += 1
        raw_response = generate(prompt, use_case="resume_tailoring")
    
        try:
            raw_response = raw_response.strip()
            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_response, re.DOTALL)
            if json_match:
                raw_response = json_match.group(1)
            parsed_response = json.loads(raw_response)
        except json.JSONDecodeError as e:
            if attempts == max_attempts:
                raise ValueError(f"Failed to parse LLM response as JSON: {raw_response[:500]}") from e
            continue
            
        selected_bullets = parsed_response.get("selected_bullet_ids", [])
        bad_bullets = [b for b in selected_bullets if b not in valid_bullet_ids]
        
        gen_projects = {gb.get("project_id") for gb in parsed_response.get("generated_project_bullets", []) if gb.get("project_id")}
        missing_projects = [p["id"] for p in top_2_projects if p["id"] not in gen_projects]
        
        cl_text = parsed_response.get("cover_letter_body", "")
        cl_metrics = extract_metric_claims(cl_text)
        invented_cl_metrics = cl_metrics - allowed_metrics
        
        if not bad_bullets and not missing_projects and not invented_cl_metrics:
            break # Success!
            
        # Error/Hallucination detected
        bad_str = f"Bad Bullets: {bad_bullets} | Missing Projects: {missing_projects} | CL Metrics: {invented_cl_metrics}"
        print(f"[Tailor] Issue detected on attempt {attempts}: {bad_str}")
        hallucinated_logs.append(f"Attempt {attempts}: {bad_str}")
        
        if attempts < max_attempts:
            # Append error instruction to prompt for retry
            valid_b_str = ", ".join(valid_bullet_ids)
            retry_msg = f"\n\n[SYSTEM ERROR]: You failed to follow instructions. "
            if bad_bullets:
                retry_msg += f"Invalid bullet IDs: {bad_bullets}. You must ONLY select from exact bullet IDs: [{valid_b_str}]. "
            if missing_projects:
                retry_msg += f"You forgot to generate bullets for these required projects: {missing_projects}. You MUST generate an entry for EVERY project provided in the context. "
            if invented_cl_metrics:
                retry_msg += f"You invented numbers in the cover letter: {invented_cl_metrics}. NEVER invent metrics that aren't in the provided context."
            prompt += retry_msg
        else:
            if bad_bullets:
                raise TailoringError(f"LLM hallucinated non-existent IDs after {max_attempts} attempts. Logs:\n" + "\n".join(hallucinated_logs))
            
            if invented_cl_metrics:
                print(f"[Tailor] Cover letter metric hallucination persisted. Falling back to generic cover letter.")
                parsed_response["cover_letter_body"] = "[Fallback Triggered] I am writing to express my strong interest in this position. My enclosed resume details my extensive background and achievements, which I believe align closely with your requirements."
            
            # Missing projects will be handled by the fallback mechanism down below.
            break

    # ── Validate selected IDs (just in case) ────────────────────────────────────────────────
    parsed_response["selected_bullet_ids"] = validate_selection(
        parsed_response.get("selected_bullet_ids", []), valid_bullet_ids
    )

    # ── Build rewritten bullet lookup map ────────────────────────────────────
    rewritten_map: dict[str, str] = {}
    for rw in parsed_response.get("rewritten_bullets", []):
        oid = rw.get("original_id", "")
        text = rw.get("rewritten_text", "").strip()
        if oid and text:
            rewritten_map[oid] = text

    # ── Hydration & Metric Guardrails ──────────────────────────────────────────
    hydrated_bullets = []
    reverted_count = 0
    bullet_lookup = {b["id"]: b for b in all_bullets}
    
    valid_skills = kb.get("skills", {}).get("languages", []) + kb.get("skills", {}).get("frameworks", []) + kb.get("skills", {}).get("tools", [])
    ignore_list = {"I", "The", "A", "An", "In", "On", "At", "To", "For", "With", "By", "As", "And", "Or", "Using", "Developed", "Implemented", "Designed", "Created", "Built", "Managed", "Led", "Architected", "Integrated", "Ensuring", "Achieving", "Reducing", "Enhancing", "Role", "Based", "Access", "Control", "Data", "Processing", "System", "Performance", "Accuracy", "Latency", "Model", "Pipeline", "Models", "Pipelines", "Tools", "Tool"}
    
    for bullet_id in parsed_response["selected_bullet_ids"]:
        if bullet_id in bullet_lookup:
            bullet = dict(bullet_lookup[bullet_id])  # shallow copy to avoid mutating KB
            
            # Check for hallucinated metrics and tech in rewritten text
            if bullet_id in rewritten_map:
                original_text = bullet.get("text", "")
                rewritten_text = rewritten_map[bullet_id]
                
                original_metrics = extract_metric_claims(original_text)
                rewritten_metrics = extract_metric_claims(rewritten_text)
                
                invented_metrics = rewritten_metrics - original_metrics
                hallucinated_tech = None
                
                # Check global valid skills
                for skill in valid_skills:
                    if len(skill) > 2 and re.search(r'\b' + re.escape(skill) + r'\b', rewritten_text, re.IGNORECASE):
                        if not re.search(r'\b' + re.escape(skill) + r'\b', original_text, re.IGNORECASE):
                            hallucinated_tech = skill
                            break
                            
                # Check dynamic acronyms
                if not hallucinated_tech:
                    acronyms = re.findall(r'\b[A-Z][A-Z0-9\-]+\b', rewritten_text)
                    words = rewritten_text.split()
                    capitalized = []
                    if len(words) > 1:
                        for w in words[1:]:
                            clean_w = re.sub(r'[^a-zA-Z0-9\-]', '', w)
                            if clean_w and any(c.isupper() for c in clean_w) and clean_w not in ignore_list:
                                capitalized.append(clean_w)
                                
                    candidate_tokens = set(acronyms + capitalized)
                    for token in candidate_tokens:
                        if len(token) >= 2 and token not in ignore_list:
                            if not re.search(r'\b' + re.escape(token) + r'\b', original_text, re.IGNORECASE):
                                hallucinated_tech = token
                                break

                if invented_metrics:
                    print(f"[Tailor FactChecker] REJECTED Rewrite for {bullet_id}: Invented metrics {invented_metrics}. Falling back to original.")
                    reverted_count += 1
                elif hallucinated_tech:
                    print(f"[Tailor FactChecker] REJECTED Rewrite for {bullet_id}: Invented tech/acronym '{hallucinated_tech}'. Falling back to original.")
                    reverted_count += 1
                else:
                    bullet["text"] = rewritten_text
                    
            bullet["relevance_score"] = 1.0 / (1.0 + dist_map.get(bullet_id, 10.0))
            hydrated_bullets.append(bullet)


    parsed_response["hydrated_bullets"] = hydrated_bullets
    parsed_response["reverted_bullets_count"] = reverted_count
    # ── Projects Constraints & Tech Skill Fact-Checking ──────────────────────
    parsed_response["selected_project_ids"] = [p["id"] for p in top_2_projects]
    
    gen_bullets = parsed_response.get("generated_project_bullets", [])
    validated_project_bullets = []
    
    for gb in gen_bullets:
        pid = gb.get("project_id")
        if pid not in parsed_response["selected_project_ids"]:
            continue
            
        proj = next((p for p in top_2_projects if p["id"] == pid), None)
        if not proj:
            continue
            
        proj_text = (proj.get("description", "") + " " + str(proj.get("readme_summary", "")) + " " + " ".join(proj.get("tech_stack", [])) + " " + " ".join(proj.get("topics", []))).lower()
        
        safe_bullets = []
        ignore_list = {"I", "The", "A", "An", "In", "On", "At", "To", "For", "With", "By", "As", "And", "Or", "Using", "Developed", "Implemented", "Designed", "Created", "Built", "Managed", "Led", "Architected", "Integrated", "Ensuring", "Achieving", "Reducing", "Enhancing", "Role", "Based", "Access", "Control", "Data", "Processing", "System", "Performance", "Accuracy", "Latency", "Model", "Pipeline", "Models", "Pipelines", "Tools", "Tool"}
        for text in gb.get("bullets", []):
            hallucinated = False
            
            # 1. Global skills check
            for skill in valid_skills:
                if len(skill) > 2 and re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
                    if not re.search(r'\b' + re.escape(skill) + r'\b', proj_text, re.IGNORECASE):
                        print(f"[Tailor FactChecker] REJECTED Project Bullet for {pid}: Invented global tech skill '{skill}'.")
                        hallucinated = True
                        break
            
            # 2. Dynamic Acronym/Tech token check
            if not hallucinated:
                acronyms = re.findall(r'\b[A-Z][A-Z0-9\-]+\b', text)
                words = text.split()
                capitalized = []
                if len(words) > 1:
                    for w in words[1:]:
                        clean_w = re.sub(r'[^a-zA-Z0-9\-]', '', w)
                        if clean_w and any(c.isupper() for c in clean_w) and clean_w not in ignore_list:
                            capitalized.append(clean_w)
                            
                candidate_tokens = set(acronyms + capitalized)
                
                for token in candidate_tokens:
                    if len(token) >= 2 and token not in ignore_list:
                        if not re.search(r'\b' + re.escape(token) + r'\b', proj_text, re.IGNORECASE):
                            print(f"[Tailor FactChecker] REJECTED Project Bullet for {pid}: Invented tech/acronym '{token}'.")
                            hallucinated = True
                            break

            if not hallucinated:
                safe_bullets.append(text)
                
        if safe_bullets:
            validated_project_bullets.append({
                "project_id": pid,
                "bullets": safe_bullets
            })
            
    # ── Fallback for missing projects ─────────────────────────────────────────
    final_project_ids = [gb["project_id"] for gb in validated_project_bullets]
    for p in top_2_projects:
        pid = p["id"]
        if pid not in final_project_ids:
            print(f"[Tailor FactChecker] Fallback triggered for {pid}: missing or all bullets rejected.")
            fallback_text = p.get("description", "")
            if fallback_text:
                validated_project_bullets.append({
                    "project_id": pid,
                    "bullets": [fallback_text]
                })

    parsed_response["generated_project_bullets"] = validated_project_bullets
    
    return parsed_response
