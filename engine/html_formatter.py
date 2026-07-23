import json


def generate_html_context(tailored_resume: dict, kb: dict) -> str:
    """
    Takes the structured, hallucination-free tailored resume (from tailor.py)
    and formats it into the exact placeholder variables expected by resume-template.html.

    ATS Rules enforced here:
    - Competencies: plain comma-separated string (NO pill badges / flex children)
    - Skills: "Category: item1, item2" per line using <div> blocks (NOT a flex grid)
    - Experience / Projects: float-based two-column header, plain <ul><li> bullets
    - Education / Certs: float-based header, no inline styles
    """
    personal = kb.get("personal", {})

    context = {}
    context["LANG"] = "en"
    context["PAGE_WIDTH"] = "210mm"

    context["NAME"] = personal.get("name", "Your Name")
    context["PHONE"] = personal.get("phone", "")
    context["EMAIL"] = personal.get("email", "")

    linkedin = personal.get("linkedin", "")
    context["LINKEDIN_URL"] = linkedin
    context["LINKEDIN_DISPLAY"] = linkedin.replace("https://", "").replace("www.", "") if linkedin else ""

    github = personal.get("github", personal.get("portfolio", ""))
    context["PORTFOLIO_URL"] = github
    context["PORTFOLIO_DISPLAY"] = github.replace("https://", "").replace("www.", "") if github else ""

    context["LOCATION"] = personal.get("location", "")

    # ── SUMMARY ─────────────────────────────────────────────────────────────
    context["SECTION_SUMMARY"] = "Professional Summary"
    context["SUMMARY_TEXT"] = tailored_resume.get(
        "tailored_summary", personal.get("summary", "")
    )

    # ── CORE COMPETENCIES ────────────────────────────────────────────────────
    # ATS reads plain comma-separated text perfectly. Pill badges in a flex
    # container are frequently skipped by ATS parsers. Build a flat string.
    context["SECTION_COMPETENCIES"] = "Core Competencies"
    competencies: set[str] = set()
    for bullet in tailored_resume.get("hydrated_bullets", []):
        competencies.update(bullet.get("ats_keywords", []))

    if competencies:
        # Cap at 18 keywords — ATS keyword stuffing above ~20 can trigger spam filters
        competency_text = " &bull; ".join(list(competencies)[:18])
    else:
        # Fallback to skills from KB
        skills_kb = kb.get("skills", {})
        fallback = []
        for items in skills_kb.values():
            fallback.extend(items)
        competency_text = " &bull; ".join(dict.fromkeys(fallback)[:18])

    context["COMPETENCIES"] = competency_text

    # ── WORK EXPERIENCE ──────────────────────────────────────────────────────
    context["SECTION_EXPERIENCE"] = "Work Experience"
    work_histories = {w["id"]: w for w in kb.get("work_history", [])}
    exp_map: dict = {}

    for bullet in tailored_resume.get("hydrated_bullets", []):
        pid = bullet.get("parent_id")
        if pid in work_histories:
            if pid not in exp_map:
                exp_map[pid] = {"parent": work_histories[pid], "bullets": []}
            exp_map[pid]["bullets"].append(bullet)

    exp_html = ""
    for pid, data in exp_map.items():
        parent = data["parent"]
        bullets = data["bullets"]
        location_html = f'<span class="job-location"> &mdash; {parent.get("location", "")}</span>' if parent.get("location") else ""
        bullets_html = "".join(f"<li>{b.get('text', '')}</li>" for b in bullets)

        exp_html += f'''
<div class="job">
  <div class="job-header">
    <span class="job-period">{parent.get("start_date", "")} &ndash; {parent.get("end_date", "Present")}</span>
    <span class="job-company">{parent.get("company", "")}</span>
  </div>
  <div class="job-role">{parent.get("role", "")}{location_html}</div>
  <ul>{bullets_html}</ul>
</div>'''

    context["EXPERIENCE"] = exp_html

    # ── PROJECTS ─────────────────────────────────────────────────────────────
    context["SECTION_PROJECTS"] = "Projects"
    projects_map = {p["id"]: p for p in kb.get("projects", [])}
    proj_map: dict = {}

    for bullet in tailored_resume.get("hydrated_bullets", []):
        pid = bullet.get("parent_id")
        if pid in projects_map:
            if pid not in proj_map:
                proj_map[pid] = {"parent": projects_map[pid], "bullets": []}
            proj_map[pid]["bullets"].append(bullet)

    proj_html = ""
    for pid, data in proj_map.items():
        parent = data["parent"]
        bullets = data["bullets"]
        tagline = parent.get("tagline", "")
        tagline_html = f'<div class="project-tagline">{tagline}</div>' if tagline else ""
        bullets_html = "".join(f"<li>{b.get('text', '')}</li>" for b in bullets)
        end_date = parent.get("end_date", "")

        proj_html += f'''
<div class="project">
  <div class="project-header">
    <span class="project-period">{parent.get("start_date", "")} {("&ndash; " + end_date) if end_date else ""}</span>
    <span class="project-title">{parent.get("name", "")}</span>
  </div>
  {tagline_html}
  <ul>{bullets_html}</ul>
</div>'''

    context["PROJECTS"] = proj_html

    # ── EDUCATION ────────────────────────────────────────────────────────────
    context["SECTION_EDUCATION"] = "Education"
    edu_html = ""
    for edu in kb.get("education", []):
        desc = edu.get("description", "")
        desc_html = f'<div class="edu-desc">{desc}</div>' if desc else ""
        edu_html += f'''
<div class="edu-item">
  <div class="edu-header">
    <span class="edu-year">{edu.get("year", "")}</span>
    <span class="edu-institution">{edu.get("institution", "")}</span>
  </div>
  <div class="edu-degree">{edu.get("degree", "")}</div>
  {desc_html}
</div>'''

    context["EDUCATION"] = edu_html

    # ── CERTIFICATIONS ───────────────────────────────────────────────────────
    context["SECTION_CERTIFICATIONS"] = "Certifications"
    cert_html = ""
    for cert in kb.get("certifications", []):
        year = cert.get("date_earned", "")[:4]
        cert_html += f'''
<div class="cert-item">
  <span class="cert-name">{cert.get("name", "")}</span>
  <span class="cert-meta"> &mdash; {cert.get("issuer", "")}{(", " + year) if year else ""}</span>
</div>'''

    context["CERTIFICATIONS"] = cert_html

    # ── SKILLS ───────────────────────────────────────────────────────────────
    # Format: "Languages: Python, TypeScript, Go" — one row per category.
    # This is the highest ATS-parseable format. No flex grid, no pill badges.
    context["SECTION_SKILLS"] = "Skills"
    skills = kb.get("skills", {})
    skills_html = ""
    for category, items in skills.items():
        if items:
            skills_html += (
                f'<div class="skill-row">'
                f'<span class="skill-category-label">{category.title()}: </span>'
                f'{", ".join(items)}'
                f"</div>"
            )
    context["SKILLS"] = skills_html

    return json.dumps(context)
