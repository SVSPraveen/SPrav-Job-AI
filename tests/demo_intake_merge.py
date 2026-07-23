"""
tests/demo_intake_merge.py — Phase 0 Integration Demo
======================================================
Simulates a full Phase 0 run without needing a real PDF or internet:

  - Two "source" intermediates (mirroring what parse_resume and fetch_github would produce)
  - One "source" with a conflicting date (mirroring what parse_linkedin_export produces)
  - One manual entry with a cert

Runs the full merge and prints:
  1. The merged me.json (pretty printed)
  2. needs_detail — bullets missing metrics
  3. pending_conflicts — fields where sources disagreed

Run with:
    python tests/demo_intake_merge.py
"""
import json
import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from engine.kb_merger import merge

# ── Synthetic sources (what the real parse functions would return) ─────────────

RESUME_SOURCE = {
    "source": "resume_pdf",
    "personal": {
        "name": "Priya Sharma",
        "email": "priya@example.com",
        "phone": "+91-9876543210",
        "linkedin": "https://linkedin.com/in/priyasharma",
        "github": "https://github.com/priyasharma",
        "location": "Bengaluru, India",
        "summary": "Backend engineer with 4 years in Python and distributed systems.",
    },
    "work_history": [
        {
            "id": "work_acme_corp",
            "company": "Acme Corp",
            "role": "Senior Software Engineer",
            "type": "full_time",
            "start_date": "2021-06",
            "end_date": "Present",
            "in_progress": True,
            "last_reviewed": "2025-07-01",
            "bullets": [
                {
                    "id": "bullet_acme_1",
                    "text": "Led migration of monolithic billing service to microservices",
                    "metric_verified": "self_reported",
                    "ats_keywords": ["microservices", "Python"],
                    "themes": ["Architecture"],
                },
                {
                    "id": "bullet_acme_2",
                    "text": "Reduced API latency by 72% by introducing Redis caching",
                    "metric_verified": "verified",
                    "ats_keywords": ["Redis", "API", "performance"],
                    "themes": ["Performance"],
                },
            ],
        },
        {
            "id": "work_startup_xyz",
            "company": "Startup XYZ",
            "role": "Software Engineer",
            "type": "full_time",
            "start_date": "2019-07",
            "end_date": "2021-05",
            "in_progress": False,
            "last_reviewed": "2025-07-01",
            "bullets": [
                {
                    "id": "bullet_xyz_1",
                    "text": "Built REST API for the core product",   # no metric — should be flagged
                    "metric_verified": "self_reported",
                    "ats_keywords": ["REST API"],
                    "themes": ["Backend"],
                },
                {
                    "id": "bullet_xyz_2",
                    "text": "Improved database performance significantly",  # vague — should be flagged
                    "metric_verified": "self_reported",
                    "ats_keywords": ["PostgreSQL"],
                    "themes": ["Database"],
                },
            ],
        },
    ],
    "education": [
        {
            "id": "edu_bits",
            "institution": "BITS Pilani",
            "degree": "B.E. Computer Science",
            "year": "2019",
            "cgpa": "9.1/10",
        }
    ],
    "certifications": [],
    "skills": {
        "languages": ["Python", "Go", "SQL"],
        "frameworks": ["FastAPI", "Django", "gRPC"],
        "tools": ["Docker", "Kubernetes", "Redis", "PostgreSQL"],
    },
    "github_projects": [],
    "portfolio_projects": [],
}

# LinkedIn CSV export — same Startup XYZ job but with a DIFFERENT end date → triggers conflict
LINKEDIN_SOURCE = {
    "source": "linkedin_export",
    "personal": {
        "name": "Priya Sharma",
        "email": "priya@example.com",
    },
    "work_history": [
        {
            "id": "work_startup_xyz_li",
            "company": "Startup XYZ",
            "role": "Software Engineer",
            "type": "full_time",
            "start_date": "2019-07",
            "end_date": "2021-06",   # <-- Different! Resume says 2021-05
            "in_progress": False,
            "last_reviewed": "2025-07-01",
            "bullets": [],
            "_source": "linkedin",
        },
    ],
    "education": [],
    "certifications": [
        {
            "id": "cert_aws_saa",
            "name": "AWS Solutions Architect Associate",
            "issuer": "Amazon Web Services",
            "date_earned": "2023-03",
            "expires": "2026-03",
            "credential_id": "ABC123XYZ",
            "url": "https://aws.amazon.com/verify/ABC123XYZ",
            "last_reviewed": "2025-07-01",
            "_source": "linkedin",
        }
    ],
    "skills": {
        "linkedin_skills": ["Microservices", "System Design", "Python", "AWS"]
    },
    "github_projects": [],
    "portfolio_projects": [],
}

# GitHub source — two original repos
GITHUB_SOURCE = {
    "source": "github",
    "personal": {"github": "https://github.com/priyasharma"},
    "work_history": [],
    "education": [],
    "certifications": [],
    "skills": {},
    "github_projects": [
        {
            "id": "gh_sprav_pipeline",
            "name": "sprav-pipeline",
            "description": "Autonomous job application pipeline using local LLMs",
            "readme_summary": "A multi-model MoE pipeline for resume tailoring and job discovery...",
            "tech_stack": ["Python"],
            "topics": ["llm", "fastapi", "automation"],
            "stars": 18,
            "last_commit_date": "2025-07-15",
            "user_commit_count": 134,
            "url": "https://github.com/priyasharma/sprav-pipeline",
            "is_fork": False,
        },
        {
            "id": "gh_redis_cache_lib",
            "name": "redis-cache-lib",
            "description": "Typed Redis caching wrapper for FastAPI",
            "readme_summary": "Drop-in caching layer for FastAPI endpoints using Redis...",
            "tech_stack": ["Python"],
            "topics": ["redis", "fastapi", "caching"],
            "stars": 7,
            "last_commit_date": "2024-11-02",
            "user_commit_count": 46,
            "url": "https://github.com/priyasharma/redis-cache-lib",
            "is_fork": False,
        },
    ],
    "portfolio_projects": [],
}

# Manual cert entry
MANUAL_SOURCE = {
    "source": "manual",
    "personal": {},
    "work_history": [],
    "education": [],
    "certifications": [
        {
            "id": "cert_cka",
            "name": "Certified Kubernetes Administrator (CKA)",
            "issuer": "Cloud Native Computing Foundation",
            "date_earned": "2024-08",
            "expires": "2027-08",
            "credential_id": "CKA-2024-0055",
            "url": "https://training.linuxfoundation.org/certification/certified-kubernetes-administrator-cka/",
            "last_reviewed": "2025-07-01",
        }
    ],
    "skills": {},
    "github_projects": [],
    "portfolio_projects": [],
}


def run_demo():
    # Use a temp directory as the KB path so we don't overwrite the real me.json
    tmpdir = tempfile.mkdtemp()
    demo_kb_path = os.path.join(tmpdir, "demo_me.json")
    demo_history_dir = os.path.join(tmpdir, "history")

    print("=" * 70)
    print("  Phase 0 — Intake Merge Demo")
    print("  Sources: resume_pdf, linkedin_export, github, manual")
    print("=" * 70)

    # Monkey-patch HISTORY_DIR to point to temp dir
    import engine.kb_merger as km
    original_history = km.HISTORY_DIR
    km.HISTORY_DIR = demo_history_dir

    sources = [RESUME_SOURCE, LINKEDIN_SOURCE, GITHUB_SOURCE, MANUAL_SOURCE]
    result = merge(sources, kb_path=demo_kb_path)

    km.HISTORY_DIR = original_history  # Restore

    # ── Print merged summary ──────────────────────────────────────────────────
    print("\n[+] Merged Knowledge Base (me.json):")
    print("-" * 70)
    # Print everything except github_projects README (too noisy)
    display = dict(result)
    display["github_projects"] = [
        {k: v for k, v in p.items() if k != "readme_summary"}
        for p in result.get("github_projects", [])
    ]
    print(json.dumps(display, indent=2, ensure_ascii=False))

    # ── Print needs_detail ────────────────────────────────────────────────────
    print("\n[!] needs_detail -- Bullets flagged for missing metrics:")
    print("-" * 70)
    needs = result.get("needs_detail", [])
    if needs:
        for nd in needs:
            print(f"  [{nd['bullet_id']}] @ {nd['parent_role']} / {nd['parent_company']}")
            print(f"  Current: \"{nd['current_text']}\"")
            print(f"  Prompt: {nd['prompt']}")
            print()
    else:
        print("  [OK] No missing metrics detected.")

    # ── Print pending_conflicts ───────────────────────────────────────────────
    print("\n[!] pending_conflicts -- Fields where sources disagreed:")
    print("-" * 70)
    conflicts = result.get("pending_conflicts", [])
    if conflicts:
        for c in conflicts:
            print(f"  Field: {c['field']}")
            for v in c["values"]:
                print(f"    [{v['source']}] -> \"{v['value']}\"")
            print()
    else:
        print("  [OK] No conflicts detected.")

    # ── Summary stats ─────────────────────────────────────────────────────────
    print("=" * 70)
    print(f"  Roles merged:         {len(result.get('work_history', []))}")
    print(f"  GitHub projects:      {len(result.get('github_projects', []))}")
    print(f"  Certifications:       {len(result.get('certifications', []))}")
    print(f"  Skills categories:    {list(result.get('skills', {}).keys())}")
    print(f"  Bullets needing #:    {len(needs)}")
    print(f"  Conflicts to resolve: {len(conflicts)}")
    print("=" * 70)

    shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    run_demo()
