import sqlite3
import os
from engine.llm_provider import generate
from engine.memory_palace import get_relevant_lessons
from engine.knowledge_graph import get_entity_context
from engine.db_utils import db_mutex

DB_PATH = "jobs.db"

def generate_strategy_report(job_id: int, company: str, title: str, job_requirements: dict, master_evidence_sheet: str, evaluation_rubric: dict = None):
    """
    Phase 4 Strategy Generator:
    First conducts a 6-Axis Deep Research profile on the company.
    Then generates a Cover Letter.
    Accepts pre-computed Block C/D rubric data to avoid redundant LLM calls.
    """
    print(f"\n[Strategy Generator] Step 1: Conducting 6-Axis Deep Research on {company}...")
    
    # Use pre-computed Block C/D data if available
    precomputed_insights = ""
    if evaluation_rubric:
        positioning = evaluation_rubric.get("positioning", {})
        compensation = evaluation_rubric.get("compensation", {})
        if positioning:
            precomputed_insights += f"""
\n## Pre-Computed Positioning Intelligence (from evaluator):
- Level Delta: {positioning.get('level_delta', 'Unknown')}
- Positioning Strategy: {positioning.get('positioning_strategy', '')}
- Downlevel Response: {positioning.get('downlevel_response', '')}"""
        if compensation:
            precomputed_insights += f"""
\n## Pre-Computed Compensation Intelligence (from evaluator):
- Company Type: {compensation.get('company_type', 'Unknown')}
- Comp Reliability: {compensation.get('comp_reliability', 'Unknown')}
- Expected Stable Cash: {compensation.get('expected_stable_cash', 'Unknown')}"""
    
    deep_research_prompt = f"""You are a Silicon Valley Business Analyst (Career-Ops Deep Mode).
Analyze the following Job Description for {company} and generate a concise 6-Axis Deep Profile:
1. Business Strategy & Market Position
2. Engineering Culture & Tech Stack
3. Competitors & Moat
4. The Candidate Angle (How the candidate specifically solves their core problems)
5. TOXIC INTERVIEW FORENSICS: Scan the tone of the JD for red flags (e.g. "fast-paced", "wear many hats", strict monitoring). Flag them and provide 2 cross-examination questions to ask the interviewer to expose bad management.
{precomputed_insights}

Job Requirements: {job_requirements}
"""
    deep_profile = generate(deep_research_prompt, use_case="hard_filter")
    print(f"[Strategy Generator] Deep Profile generated.")
    
    print(f"[Strategy Generator] Step 2: Drafting Cover Letter...")
    
    prompt = f"""You are an elite SPrav AI Agent.
The user is manually applying to the following job.
Company: {company}
Title: {title}

CRITICAL PAST LESSONS TO LEARN FROM (Retrieved via Semantic Vector Search):
{get_relevant_lessons(str(job_requirements), wing="strategy")}

TEMPORAL KNOWLEDGE GRAPH (Your History with this Company/Recruiters):
{get_entity_context(company)}

COMPANY DEEP PROFILE (6-Axis Research):
{deep_profile}

Based on the Company Deep Profile and the User's Evaluated Profile Evidence:
{master_evidence_sheet}

Draft a Strategy Report in clean Markdown containing only a Cover Letter:

### Cover Letter
Write a 3-paragraph cover letter targeting this role. Do not use generic buzzwords. Use the user's specific evidence and map it directly to the business strategy identified in the Deep Profile. Address it to the Hiring Team.
"""

    report_markdown = generate(prompt, use_case="resume_tailoring")
    
    # Prepend the Deep Profile to the final report so the user sees it in the dashboard
    final_report = f"## {company} Deep Research Profile\n\n{deep_profile}\n\n---\n\n{report_markdown}"
    
    try:
        with db_mutex:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("UPDATE jobs SET strategy_report = ? WHERE id = ?", (final_report, job_id))
            conn.commit()
            conn.close()
        print(f"[Strategy Generator] Report saved to DB for job {job_id}.")
    except Exception as e:
        print(f"[Strategy Generator] Failed to save report: {e}")
        
    return final_report

def generate_application_email(job_id: int, company: str, title: str, extracted_json: dict, master_identity: str):
    """
    Generates a formal application email for jobs that require direct email submission
    instead of an ATS portal.
    """
    print(f"\n[Strategy Generator] Drafting Direct Application Email for {company}...")
    
    prompt = f"""You are an elite SPrav AI Agent.
Draft a highly professional Application Email for the user to send directly to the founder/recruiter at {company} for the {title} role.

User Data: {master_identity}
Job Requirements: {extracted_json}

The email must:
1. Be concise (max 3 short paragraphs).
2. Directly map 1 major achievement to their core requirement.
3. Include a bulleted attachment checklist at the bottom (e.g. "Attached: 1. Resume (PDF)").
Output ONLY the email draft in Markdown.
"""

    email_draft = generate(prompt, use_case="resume_tailoring")
    
    try:
        with db_mutex:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            # Overloading strategy_report column for email drafts
            cursor.execute("UPDATE jobs SET strategy_report = ? WHERE id = ?", (f"## Direct Application Email Draft\n\n{email_draft}", job_id))
            conn.commit()
            conn.close()
    except Exception as e:
        print(f"[Strategy Generator] Failed to save application email: {e}")
        
    return email_draft

def generate_followup_email(job_id: int, company: str, title: str, days_silent: int):
    """
    Generates a structured follow-up email after 7 or 14 days of silence.
    """
    prompt = f"""Draft a professional, polite, and concise {days_silent}-day follow-up email to the recruiting team at {company} regarding the {title} application.
If this is 7 days, be very casual ("just bubbling this up").
If this is 14 days, be slightly more direct but still polite.
Do not sound desperate. Sound like a high-value candidate checking in.
Output ONLY the email text."""

    email_draft = generate(prompt, use_case="resume_tailoring")
    
    try:
        with db_mutex:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            # Append follow-up to strategy report or store it
            cursor.execute("SELECT strategy_report FROM jobs WHERE id = ?", (job_id,))
            current_report = cursor.fetchone()[0] or ""
            new_report = current_report + f"\n\n---\n\n## Automated Follow-Up Draft ({days_silent} Days)\n\n{email_draft}"
            cursor.execute("UPDATE jobs SET strategy_report = ? WHERE id = ?", (new_report, job_id))
            conn.commit()
            conn.close()
    except Exception as e:
        print(f"[Strategy Generator] Failed to save follow-up email: {e}")
