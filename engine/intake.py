"""
engine/intake.py — Phase 0 Intake Pipeline
==========================================
Parses real-world sources (resume PDF/DOCX, GitHub API, LinkedIn CSV export,
portfolio website, manual entries) into a common intermediate dict structure
that kb_merger.py then merges into knowledge_base/me.json.

Intermediate structure (returned by every parse_* function):
{
    "source": "<name of source, e.g. 'resume_pdf'>",
    "personal":       {...},          # contact info
    "work_history":   [...],          # list of role dicts
    "education":      [...],
    "certifications": [...],
    "skills":         {...},          # {category: [items]}
    "github_projects": [...],         # only from fetch_github
    "portfolio_projects": [...],      # only from parse_portfolio
}

All functions return this structure even if partially filled.
No XYZ rewriting happens here — that is the tailoring engine's job.
"""

import csv
import io
import json
import os
import re
import uuid
import zipfile
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_id(prefix: str, text: str = "") -> str:
    """Generates a deterministic-ish slug ID from a prefix + text."""
    slug = re.sub(r"[^a-z0-9]", "_", text.lower())[:30].strip("_")
    return f"{prefix}_{slug}" if slug else f"{prefix}_{uuid.uuid4().hex[:8]}"


def _extract_text_from_pdf(file_path: str) -> str:
    """Uses pdfplumber for layout-aware text extraction (handles multi-column)."""
    try:
        import pdfplumber
        pages = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text(x_tolerance=2, y_tolerance=3)
                if text:
                    pages.append(text)
        return "\n\n".join(pages)
    except ImportError:
        # Fallback to PyPDF2 if pdfplumber somehow isn't installed
        import PyPDF2
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            return "\n".join(p.extract_text() or "" for p in reader.pages)


def _extract_text_from_docx(file_path: str) -> str:
    from docx import Document
    doc = Document(file_path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _call_extraction_llm(text: str) -> dict:
    """
    Calls qwen2.5:7b-instruct (the extraction model already in the MoE routing)
    to parse raw resume text into structured JSON.
    """
    from engine.llm_provider import generate

    prompt = f"""You are a structured data extraction engine. Parse the following resume text and extract every piece of information into this exact JSON schema. Output ONLY valid JSON with no markdown, no explanation.

Schema:
{{
  "personal": {{
    "name": "",
    "email": "",
    "phone": "",
    "linkedin": "",
    "github": "",
    "portfolio": "",
    "location": "",
    "summary": ""
  }},
  "work_history": [
    {{
      "company": "",
      "role": "",
      "type": "full_time",
      "start_date": "",
      "end_date": "",
      "bullets": ["<raw bullet text>"]
    }}
  ],
  "education": [
    {{
      "institution": "",
      "degree": "",
      "year": "",
      "cgpa": ""
    }}
  ],
  "certifications": [
    {{
      "name": "",
      "issuer": "",
      "date_earned": "",
      "expires": null
    }}
  ],
  "skills": {{
    "languages": [],
    "frameworks": [],
    "tools": [],
    "soft_skills": []
  }}
}}

Rules:
- type is one of: full_time, internship, freelance, contract — infer from context
- If a field is not present in the resume, use "" or [] or null
- Dates should be YYYY-MM-DD if possible, or YYYY if only year is known
- Do NOT invent or infer facts not explicitly in the text

Resume Text:
{text[:8000]}
"""
    raw = generate(prompt, use_case="extraction")

    # Strip markdown fences if present
    raw = raw.strip()
    match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, re.DOTALL)
    if match:
        raw = match.group(1)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Return empty scaffold on parse failure
        return {
            "personal": {}, "work_history": [], "education": [],
            "certifications": [], "skills": {}
        }


def _normalise_work_history(raw_entries: list, source: str) -> list:
    """Converts raw work history dicts into the full schema format with bullet IDs."""
    result = []
    for entry in raw_entries:
        company = entry.get("company", "").strip()
        role = entry.get("role", "").strip()
        if not company:
            continue
        entry_id = _make_id("work", company)
        bullets = []
        for i, raw_bullet in enumerate(entry.get("bullets", [])):
            text = raw_bullet.strip() if isinstance(raw_bullet, str) else ""
            if not text:
                continue
            bullet_id = _make_id("bullet", f"{company}_{i}")
            bullets.append({
                "id": bullet_id,
                "text": text,
                "metric_verified": "self_reported",
                "ats_keywords": [],
                "themes": [],
                "last_reviewed": datetime.now().strftime("%Y-%m-%d"),
                "_source": source,
            })
        result.append({
            "id": entry_id,
            "company": company,
            "role": role,
            "type": entry.get("type", "full_time"),
            "start_date": entry.get("start_date", ""),
            "end_date": entry.get("end_date", ""),
            "in_progress": entry.get("end_date", "").lower() in ("present", "current", ""),
            "last_reviewed": datetime.now().strftime("%Y-%m-%d"),
            "bullets": bullets,
            "_source": source,
        })
    return result


# ─────────────────────────────────────────────────────────────────────────────
# 1. parse_resume — PDF or DOCX
# ─────────────────────────────────────────────────────────────────────────────

def parse_resume(file_path: str) -> dict:
    """
    Extracts structured profile data from an existing resume PDF or DOCX.
    Uses pdfplumber for PDFs (handles multi-column layouts), python-docx for DOCX.
    Then sends raw text to qwen2.5:7b-instruct for structured extraction.
    Returns the common intermediate dict.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Resume file not found: {file_path}")

    ext = path.suffix.lower()
    if ext == ".pdf":
        raw_text = _extract_text_from_pdf(file_path)
    elif ext in (".docx", ".doc"):
        raw_text = _extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Use PDF or DOCX.")

    print(f"[Intake] Extracted {len(raw_text)} characters from {path.name}")

    extracted = _call_extraction_llm(raw_text)

    return {
        "source": "resume_pdf" if ext == ".pdf" else "resume_docx",
        "personal": extracted.get("personal", {}),
        "work_history": _normalise_work_history(extracted.get("work_history", []), "resume"),
        "education": [
            {**edu, "id": _make_id("edu", edu.get("institution", ""))}
            for edu in extracted.get("education", [])
        ],
        "certifications": [
            {
                **cert,
                "id": _make_id("cert", cert.get("name", "")),
                "last_reviewed": datetime.now().strftime("%Y-%m-%d"),
            }
            for cert in extracted.get("certifications", [])
        ],
        "skills": extracted.get("skills", {}),
        "github_projects": [],
        "portfolio_projects": [],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2. fetch_github — GitHub REST API
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_single_repo(owner: str, repo_name: str, username: str, headers: dict) -> dict | None:
    """Fetches structured data for a single repo by owner/repo_name."""
    try:
        repo_resp = requests.get(
            f"https://api.github.com/repos/{owner}/{repo_name}",
            headers=headers, timeout=10
        )
        repo_resp.raise_for_status()
        repo = repo_resp.json()
    except requests.RequestException as e:
        print(f"[Intake] GitHub: could not fetch {owner}/{repo_name}: {e}")
        return None

    if repo.get("fork"):
        return None  # Skip forks

    readme_text = ""
    try:
        readme_resp = requests.get(
            f"https://api.github.com/repos/{owner}/{repo_name}/readme",
            headers={**headers, "Accept": "application/vnd.github.raw"},
            timeout=8,
        )
        if readme_resp.status_code == 200:
            readme_text = readme_resp.text[:2000]
    except Exception:
        pass

    commit_count = 0
    try:
        commit_resp = requests.get(
            f"https://api.github.com/repos/{owner}/{repo_name}/commits?author={username}&per_page=100",
            headers=headers, timeout=8,
        )
        if commit_resp.status_code == 200:
            commit_count = len(commit_resp.json())
    except Exception:
        pass

    last_commit = repo.get("pushed_at", "")[:10] if repo.get("pushed_at") else ""

    return {
        "id": _make_id("gh", repo_name),
        "name": repo_name,
        "description": repo.get("description") or "",
        "readme_summary": readme_text.strip(),
        "tech_stack": [repo.get("language")] if repo.get("language") else [],
        "topics": repo.get("topics", []),
        "stars": repo.get("stargazers_count", 0),
        "last_commit_date": last_commit,
        "user_commit_count": commit_count,
        "url": repo.get("html_url", ""),
        "is_fork": False,
        "_source": "github",
    }


def fetch_github(username_or_repo_urls: str | list, github_token: str = None) -> dict:
    """
    Fetches public repository data from the GitHub REST API.

    Args:
        username_or_repo_urls: Either:
            - A GitHub username string → fetches all non-fork repos for that user
            - A list of github.com repo URLs → fetches only those specific repos
        github_token: Optional PAT for higher rate limits (5000/hr vs 60/hr unauth)

    Captures per repo: name, description, README, language, topics, stars,
    last commit, user commit count. Does NOT fabricate impact.
    """
    headers = {"Accept": "application/vnd.github+json"}
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    projects = []

    # ── Mode A: list of specific repo URLs ───────────────────────────────────
    if isinstance(username_or_repo_urls, list):
        # Extract owner/repo from URLs like https://github.com/owner/repo
        for url in username_or_repo_urls:
            url = url.rstrip("/")
            parts = url.replace("https://github.com/", "").split("/")
            if len(parts) < 2:
                print(f"[Intake] GitHub: skipping malformed URL: {url}")
                continue
            owner, repo_name = parts[0], parts[1]
            # Use the owner as the "username" for commit counting
            proj = _fetch_single_repo(owner, repo_name, owner, headers)
            if proj:
                projects.append(proj)

        username_for_personal = ""
        if username_or_repo_urls and "github.com" in username_or_repo_urls[0]:
            username_for_personal = username_or_repo_urls[0].replace("https://github.com/", "").split("/")[0]

    # ── Mode B: username string — fetch all repos ─────────────────────────────
    else:
        username = username_or_repo_urls.strip()
        username_for_personal = username
        repos_url = f"https://api.github.com/users/{username}/repos?per_page=50&sort=updated"
        try:
            resp = requests.get(repos_url, headers=headers, timeout=10)
            resp.raise_for_status()
            repos = resp.json()
        except requests.RequestException as e:
            print(f"[Intake] GitHub API error: {e}")
            return {
                "source": "github", "github_projects": [], "personal": {},
                "work_history": [], "education": [], "certifications": [],
                "skills": {}, "portfolio_projects": []
            }

        for repo in repos:
            if repo.get("fork"):
                continue
            proj = _fetch_single_repo(username, repo["name"], username, headers)
            if proj:
                projects.append(proj)

    print(f"[Intake] GitHub: fetched {len(projects)} original repos.")

    personal = {}
    if username_for_personal:
        personal["github"] = f"https://github.com/{username_for_personal}"

    return {
        "source": "github",
        "personal": personal,
        "work_history": [],
        "education": [],
        "certifications": [],
        "skills": {},
        "github_projects": projects,
        "portfolio_projects": [],
    }



# ─────────────────────────────────────────────────────────────────────────────

# 3. parse_linkedin_export — Official LinkedIn Data Export (ZIP of CSVs)
# ─────────────────────────────────────────────────────────────────────────────

def parse_linkedin_export(zip_path: str) -> dict:
    """
    Parses the official LinkedIn data export ZIP file.
    LinkedIn Settings → Data Privacy → Get a copy of your data → All data.
    The ZIP contains CSVs: Positions.csv, Education.csv, Skills.csv,
    Certifications.csv, Projects.csv, Profile.csv.

    This is the ToS-safe, scraping-free path. LinkedIn aggressively blocks
    scrapers, matching our existing policy of queuing LinkedIn jobs to the
    Human Apply queue instead of auto-applying.
    """
    work_history = []
    education = []
    certifications = []
    skills = {}
    portfolio_projects = []
    personal = {}

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = {n.lower(): n for n in zf.namelist()}

            def read_csv(key: str) -> list[dict]:
                """Case-insensitive CSV reader from the ZIP."""
                for zname in zf.namelist():
                    if key in zname.lower():
                        with zf.open(zname) as f:
                            reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))
                            return list(reader)
                return []

            # Profile.csv — name, email, headline
            for row in read_csv("profile.csv"):
                personal["name"] = f"{row.get('First Name', '')} {row.get('Last Name', '')}".strip()
                personal["email"] = row.get("Email Address", "")
                break

            # Positions.csv
            for row in read_csv("positions.csv"):
                company = row.get("Company Name", "").strip()
                role = row.get("Title", "").strip()
                start = row.get("Started On", "")
                end = row.get("Finished On", "")
                if not company:
                    continue
                work_history.append({
                    "id": _make_id("work", company),
                    "company": company,
                    "role": role,
                    "type": "full_time",
                    "start_date": start,
                    "end_date": end or "Present",
                    "in_progress": not bool(end),
                    "last_reviewed": datetime.now().strftime("%Y-%m-%d"),
                    "bullets": [],
                    "_source": "linkedin",
                })

            # Education.csv
            for row in read_csv("education.csv"):
                institution = row.get("School Name", "").strip()
                if not institution:
                    continue
                education.append({
                    "id": _make_id("edu", institution),
                    "institution": institution,
                    "degree": f"{row.get('Degree Name', '')} {row.get('Field Of Study', '')}".strip(),
                    "year": row.get("End Date", "")[:4],
                    "cgpa": "",
                    "_source": "linkedin",
                })

            # Skills.csv
            skill_list = [row.get("Name", "").strip() for row in read_csv("skills.csv") if row.get("Name")]
            if skill_list:
                skills["linkedin_skills"] = skill_list

            # Certifications.csv
            for row in read_csv("certifications.csv"):
                name = row.get("Name", "").strip()
                if not name:
                    continue
                certifications.append({
                    "id": _make_id("cert", name),
                    "name": name,
                    "issuer": row.get("Authority", ""),
                    "date_earned": row.get("Started On", ""),
                    "expires": row.get("Finished On") or None,
                    "credential_id": row.get("License Number", ""),
                    "url": row.get("Url", ""),
                    "last_reviewed": datetime.now().strftime("%Y-%m-%d"),
                    "_source": "linkedin",
                })

            # Projects.csv
            for row in read_csv("projects.csv"):
                title = row.get("Title", "").strip()
                if not title:
                    continue
                portfolio_projects.append({
                    "id": _make_id("proj", title),
                    "name": title,
                    "description": row.get("Description", ""),
                    "url": row.get("Url", ""),
                    "start_date": row.get("Started On", ""),
                    "end_date": row.get("Finished On", ""),
                    "tech_stack": [],
                    "confirmed": False,  # needs user review
                    "_source": "linkedin",
                })

    except zipfile.BadZipFile:
        raise ValueError(f"Not a valid ZIP file: {zip_path}")

    print(f"[Intake] LinkedIn export: {len(work_history)} roles, {len(education)} edu, "
          f"{len(certifications)} certs, {len(portfolio_projects)} projects")

    return {
        "source": "linkedin_export",
        "personal": personal,
        "work_history": work_history,
        "education": education,
        "certifications": certifications,
        "skills": skills,
        "github_projects": [],
        "portfolio_projects": portfolio_projects,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4. parse_portfolio — Portfolio website
# ─────────────────────────────────────────────────────────────────────────────

def parse_portfolio(url: str) -> dict:
    """
    Fetches and parses a portfolio website using BeautifulSoup.
    Returns project data as `confirmed: False` — every item must be
    explicitly confirmed by the user in the Onboarding wizard before
    being merged into me.json.
    """
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[Intake] Portfolio fetch failed: {e}")
        return {
            "source": "portfolio", "personal": {}, "work_history": [], "education": [],
            "certifications": [], "skills": {}, "github_projects": [], "portfolio_projects": []
        }

    soup = BeautifulSoup(resp.text, "html.parser")

    # Heuristic extraction — portfolio sites vary wildly in structure
    projects = []
    seen_titles: set[str] = set()

    # Look for common project card patterns
    selectors = [
        "article", ".project", ".card", "[data-project]",
        "section.work", ".portfolio-item", ".project-card"
    ]
    candidates = []
    for sel in selectors:
        candidates.extend(soup.select(sel))
    if not candidates:
        # Fallback: grab all headings with nearby paragraph text
        candidates = soup.find_all(["h2", "h3"])

    for el in candidates[:20]:  # cap at 20 candidates
        title = ""
        desc = ""

        heading = el.find(["h1", "h2", "h3", "h4"]) or el
        title = heading.get_text(strip=True)[:100]
        if not title or title in seen_titles:
            continue
        seen_titles.add(title)

        # Grab nearby paragraph
        sibling = el.find_next_sibling("p") or el.find("p")
        if sibling:
            desc = sibling.get_text(strip=True)[:300]

        # Try to detect tech stack from text (capitalised words)
        full_text = el.get_text(" ", strip=True)
        tech_candidates = re.findall(r"\b(React|Vue|Angular|Next\.js|Python|FastAPI|Django|Node\.js|TypeScript|JavaScript|PostgreSQL|MongoDB|Redis|Docker|Kubernetes|AWS|GCP|Azure|Go|Rust|Swift|Flutter|TensorFlow|PyTorch)\b", full_text)
        tech_stack = list(dict.fromkeys(tech_candidates))  # deduplicated, order-preserving

        projects.append({
            "id": _make_id("proj", title),
            "name": title,
            "description": desc,
            "tech_stack": tech_stack,
            "url": url,
            "confirmed": False,  # ALWAYS starts as unconfirmed
            "_source": "portfolio",
        })

    print(f"[Intake] Portfolio: extracted {len(projects)} candidate projects (all unconfirmed)")

    return {
        "source": "portfolio",
        "personal": {"portfolio": url},
        "work_history": [],
        "education": [],
        "certifications": [],
        "skills": {},
        "github_projects": [],
        "portfolio_projects": projects,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 5. manual_entries — Structured form input from UI
# ─────────────────────────────────────────────────────────────────────────────

def manual_entries(data: dict) -> dict:
    """
    Accepts structured manual entries from the Onboarding wizard's form.
    Expected `data` shape:
    {
        "freelance": [
            {"company": "Client Name", "role": "Freelance Developer",
             "start_date": "2023-01", "end_date": "2023-06",
             "bullets": ["Built X", "Reduced Y by Z%"]}
        ],
        "internships": [
            {"company": "Corp", "role": "Intern", "start_date": "...", "end_date": "...", "bullets": [...]}
        ],
        "certifications": [
            {"name": "AWS SAA", "issuer": "Amazon", "date_earned": "2024-01",
             "expires": "2027-01", "credential_id": "ABC123", "url": "https://..."}
        ]
    }
    """
    work_history = []
    for entry_type, type_key in [("freelance", "freelance"), ("internships", "internship")]:
        for entry in data.get(entry_type, []):
            normalized = _normalise_work_history(
                [{**entry, "type": type_key}], source="manual"
            )
            work_history.extend(normalized)

    certifications = []
    for cert in data.get("certifications", []):
        name = cert.get("name", "").strip()
        if not name:
            continue
        certifications.append({
            "id": _make_id("cert", name),
            "name": name,
            "issuer": cert.get("issuer", ""),
            "date_earned": cert.get("date_earned", ""),
            "expires": cert.get("expires") or None,
            "credential_id": cert.get("credential_id", ""),
            "url": cert.get("url", ""),
            "last_reviewed": datetime.now().strftime("%Y-%m-%d"),
            "_source": "manual",
        })

    return {
        "source": "manual",
        "personal": {},
        "work_history": work_history,
        "education": [],
        "certifications": certifications,
        "skills": {},
        "github_projects": [],
        "portfolio_projects": [],
    }
