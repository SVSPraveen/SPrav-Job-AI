import os
from engine.llm_provider import generate

def generate_negotiation_script(company: str, role: str, offer_salary: str, target_salary: str, competing: str, discount: str) -> str:
    prompt = f"""You are an elite, psychological Salary Negotiator AI from the SPrav architecture.
The user just received a job offer, but it is below their target.

Company: {company}
Role: {role}
Offered Salary: {offer_salary}
Target Salary: {target_salary}
Competing Offers: {competing}
Geographic Discount Applied: {discount}

Draft a highly professional, strategic, and polite negotiation email to the Recruiter or Hiring Manager.
- Use psychological leverage (e.g. excitement to join, but financial hurdle).
- If there are competing offers, leverage them gracefully.
- If they applied a geographic discount, push back professionally by emphasizing the value of output, not ZIP code.
- Do NOT sound aggressive. Sound highly valuable and in-demand.

Output ONLY the email draft in Markdown.
"""
    from engine.fact_checker import extract_metric_claims
    source_metrics = extract_metric_claims(f"{offer_salary} {target_salary} {competing}")
    
    attempts = 0
    max_attempts = 2
    email_draft = ""
    
    while attempts < max_attempts:
        attempts += 1
        email_draft = generate(prompt, use_case="resume_tailoring")
        
        draft_metrics = extract_metric_claims(email_draft)
        invented = draft_metrics - source_metrics
        
        if not invented:
            return email_draft
            
        print(f"[Negotiator FactChecker] Hallucinated financial metrics on attempt {attempts}: {invented}")
        if attempts < max_attempts:
            prompt += f"\n\n[SYSTEM ERROR]: You hallucinated these numbers: {invented}. You must NOT invent any numbers. Only use exactly what was provided."
        else:
            return f"ERROR: Could not generate a verified negotiation script — retry manually or draft this section yourself.\nHallucinated figures: {invented}\nReal source numbers: {source_metrics}"
    
    return email_draft

def run_negotiator():
    print("=========================================")
    print("      SPrav AI Salary Negotiator         ")
    print("=========================================")
    print("Enter the details of your offer below.\n")
    
    company = input("Company Name: ")
    role = input("Role/Title: ")
    offer_salary = input("Offered Base Salary (e.g. 120k): ")
    target_salary = input("Your Target Base Salary (e.g. 140k): ")
    competing = input("Do you have competing offers? (Yes/No/Details): ")
    discount = input("Are they applying a geographic/remote pay discount? (Yes/No): ")
    
    print("\n[Negotiator] Analyzing leverage and drafting strategy...\n")
    email_draft = generate_negotiation_script(company, role, offer_salary, target_salary, competing, discount)
    
    print("=========================================")
    print("          NEGOTIATION SCRIPT             ")
    print("=========================================")
    print(email_draft)
    print("=========================================\n")
    print("Good luck. Hold the line.")

if __name__ == "__main__":
    run_negotiator()
