import os
from docxtpl import DocxTemplate
from docx import Document

def create_default_template(template_path: str):
    """Generates a default Jinja-tagged Word template for docxtpl to consume."""
    os.makedirs(os.path.dirname(template_path), exist_ok=True)
    doc = Document()
    doc.add_heading("{{ personal.name }}", 0)
    
    p = doc.add_paragraph()
    p.add_run("{{ personal.email }} | {{ personal.phone }} | {{ personal.linkedin }} | {{ personal.github }}")
    
    doc.add_heading("Summary", level=1)
    doc.add_paragraph("{{ summary }}")
    
    doc.add_heading("Experience", level=1)
    
    # We use jinja loops to iterate over hydrated bullets, grouped by parent_id if needed.
    # For a basic template, we'll just list the bullets.
    # Ideally, we structure the context for the template to group bullets by job.
    doc.add_paragraph("{% for exp in experiences %}")
    doc.add_heading("{{ exp.company }} - {{ exp.role }}", level=2)
    doc.add_paragraph("{{ exp.start_date }} - {{ exp.end_date }}")
    doc.add_paragraph("{% for bullet in exp.bullets %}")
    doc.add_paragraph("• {{ bullet.text }}")
    doc.add_paragraph("{% endfor %}")
    doc.add_paragraph("{% endfor %}")

    doc.add_heading("Skills", level=1)
    doc.add_paragraph("Languages: {{ skills.languages | join(', ') }}")
    doc.add_paragraph("Frameworks: {{ skills.frameworks | join(', ') }}")
    doc.add_paragraph("Tools: {{ skills.tools | join(', ') }}")

    doc.save(template_path)

def generate_docx(tailored_resume: dict, kb: dict, output_path: str, template_path: str = "templates/resume_template.docx"):
    """
    Renders the tailored resume into a .docx file using a template.
    """
    if not os.path.exists(template_path):
        create_default_template(template_path)

    # Prepare context for the template
    context = {
        "personal": kb.get("personal", {}),
        "summary": tailored_resume.get("summary", ""),
        "skills": kb.get("skills", {}),
        "experiences": []
    }

    # Group hydrated bullets by their parent (work_history or project)
    hydrated_bullets = tailored_resume.get("hydrated_bullets", [])
    work_histories = {w["id"]: w for w in kb.get("work_history", [])}
    projects = {p["id"]: p for p in kb.get("projects", [])}

    exp_map = {}
    for bullet in hydrated_bullets:
        pid = bullet.get("parent_id")
        if pid not in exp_map:
            # Figure out if it's a job or project
            parent = work_histories.get(pid) or projects.get(pid)
            if parent:
                exp_map[pid] = {
                    "company": parent.get("company") or parent.get("name"),
                    "role": parent.get("role") or parent.get("tagline"),
                    "start_date": parent.get("start_date", ""),
                    "end_date": parent.get("end_date", ""),
                    "bullets": []
                }
        if pid in exp_map:
            exp_map[pid]["bullets"].append(bullet)

    context["experiences"] = list(exp_map.values())

    # Render template
    tpl = DocxTemplate(template_path)
    tpl.render(context)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    tpl.save(output_path)
    return output_path

def generate_pdf(docx_path: str, pdf_path: str) -> bool:
    """
    Attempts to convert the .docx to .pdf using docx2pdf (requires MS Word on Windows).
    If it fails, tries pypandoc (requires Pandoc).
    """
    import platform
    
    # Try docx2pdf first (best quality if MS Word is installed on Windows/Mac)
    if platform.system() in ["Windows", "Darwin"]:
        try:
            from docx2pdf import convert
            convert(docx_path, pdf_path)
            return True
        except Exception as e:
            print(f"docx2pdf failed: {e}. Trying fallback...")
            
    # Fallback to pypandoc
    try:
        import pypandoc
        pypandoc.convert_file(docx_path, 'pdf', outputfile=pdf_path)
        return True
    except Exception as e:
        print(f"pypandoc failed: {e}. Please ensure Pandoc and a PDF engine (like pdflatex) are installed.")
        return False
