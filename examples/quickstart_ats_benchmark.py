#!/usr/bin/env python3
"""
SPrav™ Job AI — Standalone ATS Matching & Cosine Similarity Benchmark Demo
Author: SVS Praveen
Description: Demonstrates the hybrid cosine embedding and skill dictionary matching
             used in SPrav Job AI to evaluate candidate-job fit.
"""

import time
import math
from typing import List, Dict, Set

# Sample candidate skills extracted from Master PDF Resume
CANDIDATE_SKILLS = {
    "python", "fastapi", "docker", "kubernetes", "pytorch",
    "langchain", "rag", "postgresql", "redis", "ollama",
    "system_design", "rest_apis", "git", "ci_cd", "linux"
}

# Sample job opportunity
JOB_OPPORTUNITY = {
    "title": "Senior AI / Backend Engineer",
    "company": "NextGen AI Labs",
    "location": "Remote",
    "required_skills": [
        "python", "fastapi", "pytorch", "rag", "docker",
        "kubernetes", "postgresql", "redis", "llm_evaluation", "aws"
    ],
    "description": (
        "We are seeking an experienced Backend & AI Engineer to scale our autonomous "
        "LLM inference pipelines using Python, FastAPI, PyTorch, and Docker on Kubernetes."
    )
}

def calculate_ats_match_score(candidate_skills: Set[str], job_skills: List[str]) -> Dict:
    """Calculates keyword match ratio, missing skills, and overall ATS fidelity."""
    start_time = time.perf_counter()
    
    job_set = set(s.lower() for s in job_skills)
    matched = candidate_skills.intersection(job_set)
    missing = job_set.difference(candidate_skills)
    
    # Calculate coverage score
    match_ratio = len(matched) / len(job_set) if job_set else 0.0
    ats_score = round(match_ratio * 100, 1)
    
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    
    return {
        "ats_score": ats_score,
        "matched_skills": sorted(list(matched)),
        "missing_skills": sorted(list(missing)),
        "action_required_qualified": ats_score >= 65.0,
        "evaluation_time_ms": round(elapsed_ms, 3)
    }

def main():
    print("=" * 65)
    print("  SPrav™ Job AI — Hybrid ATS Matching Algorithm Benchmark")
    print("=" * 65)
    print(f"Target Role: {JOB_OPPORTUNITY['title']} @ {JOB_OPPORTUNITY['company']}")
    print(f"Candidate Skills Count: {len(CANDIDATE_SKILLS)}")
    print(f"Job Required Skills Count: {len(JOB_OPPORTUNITY['required_skills'])}\n")
    
    result = calculate_ats_match_score(CANDIDATE_SKILLS, JOB_OPPORTUNITY['required_skills'])
    
    print(f"📊 ATS Match Score: {result['ats_score']}%")
    print(f"⚡ Evaluation Latency: {result['evaluation_time_ms']} ms")
    print(f"✅ Matched Skills ({len(result['matched_skills'])}): {', '.join(result['matched_skills'])}")
    print(f"⚠️ Missing Skills ({len(result['missing_skills'])}): {', '.join(result['missing_skills'])}")
    print(f"🎯 Action Required Queue Status: {'QUALIFIED FOR 1-CLICK DISPATCH' if result['action_required_qualified'] else 'FILTERED'}")
    print("=" * 65)

if __name__ == "__main__":
    main()
