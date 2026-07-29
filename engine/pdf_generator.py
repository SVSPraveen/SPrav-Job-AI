import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

def generate_pdf(tailored_resume: dict, kb: dict, pdf_path: str) -> bool:
    """
    Generates a 1-page PDF using ReportLab with dynamic font sizing and relevance-based truncation.
    """
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    
    # Extract data
    personal = kb.get("personal", {})
    name = personal.get("name", "")
    contact_info = f"{personal.get('email', '')} | {personal.get('phone', '')} | {personal.get('linkedin', '')} | {personal.get('github', '')}"
    summary = tailored_resume.get("summary", "")
    
    # We need to map hydrated_bullets to experiences
    hydrated_bullets = tailored_resume.get("hydrated_bullets", [])
    work_histories = {w["id"]: w for w in kb.get("work_history", [])}
    
    # We also need to get selected projects and their generated bullets
    projects = {p["id"]: p for p in kb.get("projects", [])}
    gen_proj_bullets = tailored_resume.get("generated_project_bullets", [])
    
    skills = kb.get("skills", {})
    
    # Iteratively try to fit the content by reducing font size from 11 down to 9
    # If it still overflows at 9, we drop the lowest scoring bullets.
    
    def build_flowables(font_size, bullets_to_include):
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'NameTitle',
            parent=styles['Heading1'],
            fontSize=font_size + 6,
            alignment=TA_CENTER,
            spaceAfter=4
        )
        
        contact_style = ParagraphStyle(
            'ContactInfo',
            parent=styles['Normal'],
            fontSize=font_size - 1,
            alignment=TA_CENTER,
            spaceAfter=8
        )
        
        heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=font_size + 2,
            spaceBefore=6,
            spaceAfter=4,
            borderPadding=0
        )
        
        job_title_style = ParagraphStyle(
            'JobTitle',
            parent=styles['Heading3'],
            fontSize=font_size,
            spaceBefore=4,
            spaceAfter=2,
            fontName='Helvetica-Bold'
        )
        
        normal_style = ParagraphStyle(
            'NormalBullet',
            parent=styles['Normal'],
            fontSize=font_size,
            leading=font_size + 2,
            spaceAfter=2,
            leftIndent=15,
            firstLineIndent=-10
        )
        
        elements = []
        
        # Header
        elements.append(Paragraph(name, title_style))
        elements.append(Paragraph(contact_info, contact_style))
        
        # Summary
        if summary:
            elements.append(Paragraph("<b>Summary</b>", heading_style))
            elements.append(Paragraph(summary, ParagraphStyle('Summ', parent=styles['Normal'], fontSize=font_size, leading=font_size+2)))
        
        # Experience
        exp_map = {}
        for b in bullets_to_include:
            pid = b.get("parent_id")
            if not pid: continue
            if pid not in exp_map:
                parent = work_histories.get(pid)
                if parent:
                    exp_map[pid] = {
                        "company": parent.get("company", ""),
                        "role": parent.get("role", ""),
                        "date": f"{parent.get('start_date','')} - {parent.get('end_date','')}",
                        "bullets": []
                    }
            if pid in exp_map:
                exp_map[pid]["bullets"].append(b["text"])
                
        if exp_map:
            elements.append(Paragraph("<b>Experience</b>", heading_style))
            for pid, job in exp_map.items():
                header = f"{job['company']} - {job['role']} <font color='gray'>({job['date']})</font>"
                elements.append(Paragraph(header, job_title_style))
                for text in job['bullets']:
                    elements.append(Paragraph(f"• {text}", normal_style))
                    
        # Projects
        if gen_proj_bullets:
            elements.append(Paragraph("<b>Projects</b>", heading_style))
            for pb in gen_proj_bullets:
                pid = pb.get("project_id")
                parent = projects.get(pid)
                if parent:
                    header = f"{parent.get('name', '')} <font color='gray'>({parent.get('tagline', '')})</font>"
                    elements.append(Paragraph(header, job_title_style))
                    for text in pb.get("bullets", []):
                        elements.append(Paragraph(f"• {text}", normal_style))
                        
        # Skills
        elements.append(Paragraph("<b>Skills</b>", heading_style))
        s_style = ParagraphStyle('Skills', parent=styles['Normal'], fontSize=font_size, leading=font_size+2)
        if skills.get("languages"):
            elements.append(Paragraph(f"<b>Languages:</b> {', '.join(skills['languages'])}", s_style))
        if skills.get("frameworks"):
            elements.append(Paragraph(f"<b>Frameworks:</b> {', '.join(skills['frameworks'])}", s_style))
        if skills.get("tools"):
            elements.append(Paragraph(f"<b>Tools:</b> {', '.join(skills['tools'])}", s_style))
            
        return elements

    # Trial loop for fitting
    # We will try font sizes from 11 down to 9.
    # If font size 9 still overflows, we drop bullets one by one based on relevance_score.
    
    current_bullets = list(hydrated_bullets)
    
    # Sort bullets by score ascending (lowest score first) so we can pop them from the end
    current_bullets.sort(key=lambda x: x.get("relevance_score", 1.0), reverse=False)
    
    author_name = personal.get("name", "")
    
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
        author=author_name,
        title=f"{author_name} Resume" if author_name else "Resume",
        creator="",
        producer=""
    )
    
    class StopFitting(Exception): pass
    
    best_elements = None
    try:
        while True:
            for font_size in [11, 10.5, 10, 9.5, 9]:
                elements = build_flowables(font_size, current_bullets)
                
                # Check height
                w, h = doc.pagesize
                avail_h = h - doc.topMargin - doc.bottomMargin
                
                # Render elements onto a dummy canvas to measure height
                from reportlab.pdfgen.canvas import Canvas
                dummy_c = Canvas("dummy.pdf")
                
                total_height = 0
                for el in elements:
                    el.wrap(w - doc.leftMargin - doc.rightMargin, avail_h)
                    total_height += el.height
                    
                if total_height <= avail_h:
                    best_elements = elements
                    raise StopFitting()
            
            # If we exhausted font sizes and still didn't fit, drop the lowest-scored bullet
            if current_bullets:
                dropped = current_bullets.pop(0)  # Remove the lowest relevance score
                print(f"[Formatter] Content too long. Truncating lowest-relevance bullet: {dropped.get('id')}")
            else:
                # Can't drop anymore, just build whatever is left
                best_elements = build_flowables(9, current_bullets)
                raise StopFitting()
                
    except StopFitting:
        pass
        
    if best_elements:
        try:
            doc.build(best_elements)
            return True
        except Exception as e:
            print(f"[Formatter] PDF Build Error: {e}")
            return False
    return False
