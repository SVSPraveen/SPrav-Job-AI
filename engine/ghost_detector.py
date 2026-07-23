import re
import json
import os
from engine.llm_provider import generate

# ─── Known Ed-Tech & Fake Recruitment Company Blacklist ───────────────────────
# These companies are well-documented to post fake "We're Hiring!" social posts
# that are either lead-gen for their own courses or mass-resume harvesting.

EDTECH_SCAM_COMPANIES = {
    "upgrad", "unacademy", "byju", "byjus", "great learning", "simplilearn",
    "skillsoft", "coursera business", "udemy for business", "intellipaat",
    "edureka", "jigsaw academy", "imarticus", "henrys academy", "masai school",
    "coding ninjas", "newton school", "scalar", "scaler", "lambdatest academy",
    "almabetter", "learnbay", "upgrade", "prepinsta",
}

# Phrases that appear in LinkedIn posts from fake HR/CEO "social recruiting" scams
FAKE_SOCIAL_RECRUITING_SIGNALS = [
    "comment yes if interested",
    "comment 'interested'",
    "drop your resume in comments",
    "dm me your cv",
    "dm me your resume",
    "dm me if interested",
    "limited seats",
    "batch starting",
    "next batch",
    "enroll now",
    "join our free webinar",
    "guaranteed placement",
    "100% placement",
    "placement guarantee",
    "course fee",
    "training fee",
    "pay after placement",
    "pay after job",
    "income share agreement",
    "isa model",
    "upskill to get hired",
    "get certified",
    "apply through our portal after completing",
    "whatsapp your resume",
    "share this post to apply",
    "repost to apply",
    "like and comment to apply",
]

# Suspicious title patterns that are almost never real SDE/tech roles
FAKE_TITLE_PATTERNS = [
    r"business development (executive|associate|intern)",
    r"sales (executive|associate|intern|officer)",
    r"telecaller",
    r"insurance (advisor|agent|associate)",
    r"financial advisor",
    r"mlm",
    r"multi.level marketing",
    r"network marketing",
    r"direct selling",
    r"field sales",
]


def _load_company_blacklist() -> set:
    """Loads user-managed blacklist.txt of banned company names."""
    blacklist_path = "blacklist.txt"
    result = set()
    if os.path.exists(blacklist_path):
        with open(blacklist_path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip().lower()
                if stripped and not stripped.startswith("#"):
                    result.add(stripped)
    return result


def detect_ghost_job(description: str, location: str, company: str = "", title: str = "") -> tuple[bool, str]:
    """
    Ghost Job and Scam Detector (Block G Legitimacy Check).
    Combines fast zero-token regex checks with a deep semantic forensics pass
    using the Magnum-v4:9b model for disguised toxic culture patterns.
    Returns: (is_ghost_or_scam: bool, reason: str)
    """
    desc_lower = description.lower()
    loc_lower = location.lower()
    company_lower = company.lower().strip()
    title_lower = title.lower().strip()
    flags = []

    # ── Gate 0: User-managed company blacklist ───────────────────────────────
    user_blacklist = _load_company_blacklist()
    if company_lower and company_lower in user_blacklist:
        return True, f"Company blacklisted by user: '{company}'"

    # ── Gate 0.25: Known Ed-Tech Scam Companies ──────────────────────────────
    # Ed-tech companies post fake "We're Hiring!" posts to harvest resumes and
    # funnel applicants into paid courses. Never auto-apply to them.
    for edtech in EDTECH_SCAM_COMPANIES:
        if edtech in company_lower:
            return True, (
                f"Ed-Tech Company Blocked: '{company}' is a known ed-tech that posts "
                "fake job listings to harvest resumes and sell courses"
            )

    # ── Gate 0.5: Fake Social Recruiting Signals ─────────────────────────────
    # Catches LinkedIn "HR/CEO" posts that are actually course funnels or scams.
    for signal in FAKE_SOCIAL_RECRUITING_SIGNALS:
        if signal in desc_lower:
            return True, (
                f"Fake Social Recruiting Detected: '{signal}' — this looks like a "
                "LinkedIn lead-gen post, not a real job opening"
            )

    # ── Gate 0.75: Fake Job Title Patterns ───────────────────────────────────
    # Filters out sales/BD/MLM roles disguised as tech jobs, often posted by
    # insurance agencies and ed-tech companies targeting fresh graduates.
    for pattern in FAKE_TITLE_PATTERNS:
        if re.search(pattern, title_lower):
            return True, (
                f"Suspicious Title Pattern: '{title}' matches a known non-tech "
                "disguised role (sales, MLM, insurance, or telecalling)"
            )

    # 1. Jurisdiction Mismatch (Copy-paste template error)
    is_non_us = any(k in loc_lower for k in ["canada", "uk ", "united kingdom", "europe"])
    has_us_benefits = any(k in desc_lower for k in ["401(k)", "401k", "w-2", "w2 employment"])
    if is_non_us and has_us_benefits:
        flags.append("Jurisdiction Mismatch (US benefits listed in non-US role — likely a copy-paste ghost template)")

    # 2. Evergreen / Pipeline Roles (collect resumes indefinitely, not hiring now)
    for marker in ["pipeline role", "evergreen", "ongoing basis", "rolling basis", "always looking for", "continuous hiring"]:
        if marker in desc_lower:
            flags.append(f"Evergreen/Pipeline Role Marker: '{marker}'")

    # 3. Scam / Data Harvesting Markers
    for marker in ["pay for training", "investment required", "wire transfer", "payment for equipment", "send a check", "deposit required"]:
        if marker in desc_lower:
            flags.append(f"High-Risk Scam Marker: '{marker}'")

    # 4. Buzzword Soup (Scope / Infrastructure Mismatch)
    buzzwords = ["drive transformation", "paradigm shift", "synergy", "digital transformation", "disrupt the industry"]
    if sum(1 for w in buzzwords if w in desc_lower) >= 3:
        flags.append("Extreme Buzzword Density (Potential Scope Mismatch)")

    # 5. Staffing Agency / Body Shop Markers
    for marker in ["w2 contract", "corp-to-corp", "c2c", "c2h", "contract to hire",
                   "staffing agency", "we are hiring on behalf", "client of ours",
                   "our client is looking", "placed with our client", "contingency basis",
                   "third-party staffing", "consulting firm"]:
        if marker in desc_lower:
            flags.append(f"Staffing Agency/Body-Shop Marker: '{marker}' — role may be underpaid or misrepresented")
            break  # One flag is enough, don't spam

    # 6. Deep Semantic Toxic Culture Forensics (Magnum-v4:9b)
    # This catches disguised patterns like "cross-functional autonomy" = understaffed
    forensic_prompt = f"""You are a corporate psychological forensic analyst.
Analyze this job description for subtle markers of extreme burnout culture, toxic management, or boundary-less work environments.
Look past positive phrasing (e.g., 'cross-functional autonomy' = understaffed, 'fast-paced' = no work-life balance).
Job Description: {description}

Output ONLY valid JSON with this exact schema:
{{
  "is_toxic": <true or false>,
  "reason": "<string: brief explanation if toxic, empty string if healthy>"
}}"""

    try:
        raw_response = generate(forensic_prompt, use_case="toxic_forensics")
        json_match = re.search(r"\{.*?\}", raw_response, re.DOTALL)
        if json_match:
            analysis = json.loads(json_match.group(0))
            if analysis.get("is_toxic"):
                flags.append(f"Semantic Toxic Culture Detected: {analysis.get('reason', 'No reason given')}")
    except Exception as e:
        print(f"[GhostDetector] Semantic analysis failed, using regex results only: {e}")

    if flags:
        return True, " | ".join(flags)

    return False, ""
