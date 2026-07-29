import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path

from engine.intake import parse_resume, fetch_github, _extract_text_from_pdf, _extract_text_from_docx
from engine.fact_checker import extract_metric_claims
from engine.llm_provider import generate

def qualitative_overclaim_check(bullet: str, source_text: str, repo_file_tree: list = None) -> dict:
    prompt = f"Extract only the specific high-leverage qualitative claims from this bullet (e.g. 'production-grade', 'enterprise-scale', 'used by thousands', 'highly scalable', 'zero-downtime'). Return a comma-separated list of the exact phrases found, or 'NONE'.\nBullet: {bullet}"
    claims_raw = generate(prompt, use_case="extraction").strip()
    
    if claims_raw.upper() == "NONE" or not claims_raw:
        return {"overclaim": False}
        
    if repo_file_tree is not None:
        markers = {
            "docker": ["Dockerfile", "docker-compose.yml", "container/"],
            "production": ["Dockerfile", "docker-compose.yml", "container/"],
            "ci/cd": [".github/workflows/", ".gitlab-ci.yml", "jenkinsfile"],
            "pipeline": [".github/workflows/", ".gitlab-ci.yml", "jenkinsfile"],
            "test": ["test/", "tests/", "spec/", "__tests__/", "pytest.ini"],
            "production-grade": ["test/", "tests/", "spec/", "__tests__/", "pytest.ini", "Dockerfile"],
            "scale": ["kubernetes/", "k8s/", "terraform/"],
            "enterprise": ["kubernetes/", "k8s/", "terraform/"]
        }
        
        claims_lower = claims_raw.lower()
        matched_marker = None
        for claim_key, marker_list in markers.items():
            if claim_key in claims_lower:
                # check if any marker in the list exists in the tree
                for m in marker_list:
                    # check if the marker string is in any path (e.g. .github/workflows/ in .github/workflows/main.yml)
                    if any(m in p for p in repo_file_tree):
                        matched_marker = m
                        break
                if matched_marker:
                    break
                    
        if matched_marker:
            return {"overclaim": False, "reason": f"'{matched_marker}' present in repo tree"}
        return {"overclaim": True}
        
    else:
        # Fallback text check for resumes
        source_lower = source_text.lower()
        evidence_keywords = ["test", "ci/cd", "pipeline", "docker", "deploy", "production", "users", "scale", "aws", "gcp", "azure", ".github/workflows"]
        evidence_found = any(word in source_lower for word in evidence_keywords)
        
        if not evidence_found:
            return {"overclaim": True}
        return {"overclaim": False, "reason": "Verified against source"}

def validate_bullet(bullet_text: str, source_text: str, repo_file_tree: list = None) -> dict:
    source_metrics = extract_metric_claims(source_text)
    bullet_metrics = extract_metric_claims(bullet_text)
    
    invented = bullet_metrics - source_metrics
    if invented:
        return {"valid": False, "reason": f"Fabricated metrics: {invented}", "flag": "Failed Metric Check"}
        
    overclaim_res = qualitative_overclaim_check(bullet_text, source_text, repo_file_tree)
    if overclaim_res["overclaim"]:
        return {"valid": True, "reason": "Lacks structural/concrete source evidence for scale/sophistication", "flag": "Qualitative Overclaim"}
        
    if not bullet_metrics:
        # Even if it passes overclaim, we still flag if it lacks metrics, but we preserve the structural reason if it was provided
        reason_str = overclaim_res.get("reason", "No concrete numbers")
        if reason_str == "Verified against source":
            reason_str = "No concrete numbers"
        return {"valid": True, "reason": reason_str, "flag": "No Metrics"}
        
    reason_str = overclaim_res.get("reason", "Verified against source")
    return {"valid": True, "reason": reason_str, "flag": "Verified"}

def generate_github_bullets(repo: dict) -> list:
    readme = repo.get("readme_summary", "")
    desc = repo.get("description", "")
    source_text = f"{desc}\n\n{readme}"
    repo_file_tree = repo.get("file_tree", [])
    
    if len(readme) < 100:
        return [{"text": f"Built {repo.get('name')}", "flag": "No README", "reason": "Source material too thin for extraction"}]
        
    prompt = f"Generate 3-4 professional resume bullet points based on this GitHub project. Do not invent metrics. You MUST start every bullet point with a dash (-).\n\nDescription: {desc}\n\nREADME:\n{source_text}"
    raw = generate(prompt, use_case="extraction")
    
    bullets = []
    for line in raw.split("\n"):
        line = line.strip()
        # Strip potential numbering or multiple dashes like "- - "
        btext = re.sub(r"^(\d+\.|\*|-|\u2022|\s)+", "", line).strip()
        if btext and len(btext) > 10:
            val = validate_bullet(btext, source_text, repo_file_tree)
            if not val["valid"]:
                continue
            bullets.append({"text": btext, "flag": val["flag"], "reason": val["reason"]})
            
    if not bullets:
        return [{"text": f"Developed {repo.get('name')}", "flag": "Garbled", "reason": "Failed to generate valid bullets"}]
        
    return bullets

def build_review_payload(resume_path: str, github_target: str) -> dict:
    payload = {
        "jobs": [],
        "projects": []
    }
    
    if resume_path:
        print(f"Parsing resume: {resume_path}")
        raw_text = _extract_text_from_pdf(resume_path) if str(resume_path).lower().endswith(".pdf") else _extract_text_from_docx(resume_path)
        resume_data = parse_resume(resume_path)
        
        for job in resume_data.get("work_history", []):
            job_obj = {
                "id": job["id"],
                "company": job["company"],
                "role": job["role"],
                "start_date": job.get("start_date", ""),
                "end_date": job.get("end_date", ""),
                "proposed_bullets": []
            }
            for b in job.get("bullets", []):
                val = validate_bullet(b["text"], raw_text)
                job_obj["proposed_bullets"].append({
                    "text": b["text"],
                    "flag": val["flag"],
                    "reason": val["reason"]
                })
            payload["jobs"].append(job_obj)
            
    if github_target:
        print(f"Fetching GitHub for: {github_target}")
        from engine.auth import get_system_credential
        gh_data = fetch_github(github_target, github_token=get_system_credential("github", "token"))
        for repo in gh_data.get("github_projects", []):
            proj_obj = {
                "id": repo["id"],
                "name": repo["name"],
                "description": repo.get("description", ""),
                "url": repo.get("url", ""),
                "proposed_bullets": generate_github_bullets(repo)
            }
            payload["projects"].append(proj_obj)
            
    return payload

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", type=str)
    parser.add_argument("--github", type=str)
    parser.add_argument("--merge", type=str)
    args = parser.parse_args()
    
    if args.merge:
        with open(args.merge, "r", encoding="utf-8") as f:
            review_data = json.load(f)
            
        kb_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "knowledge_base", "me.json"))
        with open(kb_path, "r", encoding="utf-8") as f:
            kb = json.load(f)
            
        # Simplified merge logic
        for job in review_data.get("jobs", []):
            # Just push into work history
            kb.setdefault("work_history", []).append({
                "id": job["id"],
                "company": job["company"],
                "role": job["role"],
                "start_date": job["start_date"],
                "end_date": job["end_date"],
                "bullets": [{"id": f"{job['id']}_{i}", "text": b["text"]} for i, b in enumerate(job["proposed_bullets"])]
            })
            
        for proj in review_data.get("projects", []):
            kb.setdefault("projects", []).append({
                "id": proj["id"],
                "name": proj["name"],
                "tagline": proj["description"],
                "bullets": [{"id": f"{proj['id']}_{i}", "text": b["text"]} for i, b in enumerate(proj["proposed_bullets"])]
            })
            
        with open(kb_path, "w", encoding="utf-8") as f:
            json.dump(kb, f, indent=2)
            
        print("Merged successfully into me.json")
        return

    payload = build_review_payload(args.resume, args.github)
    
    with open("onboarding_review.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        
    with open("onboarding_review.md", "w", encoding="utf-8") as f:
        f.write("# Onboarding Review\n\n")
        f.write("## Jobs\n")
        for job in payload["jobs"]:
            f.write(f"### {job['company']} - {job['role']}\n")
            for b in job["proposed_bullets"]:
                flag = f"[{b['flag']}]"
                f.write(f"- {b['text']} **{flag}** *(Reason: {b['reason']})*\n")
                
        f.write("\n## Projects\n")
        for proj in payload["projects"]:
            f.write(f"### {proj['name']}\n")
            for b in proj["proposed_bullets"]:
                flag = f"[{b['flag']}]"
                f.write(f"- {b['text']} **{flag}** *(Reason: {b['reason']})*\n")
                
    print("Generated onboarding_review.json and onboarding_review.md")

if __name__ == "__main__":
    main()
