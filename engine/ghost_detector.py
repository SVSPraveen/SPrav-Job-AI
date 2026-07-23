import re
import json
from engine.llm_provider import generate


def detect_ghost_job(description: str, location: str) -> tuple[bool, str]:
    """
    Ghost Job and Scam Detector (Block G Legitimacy Check).
    Combines fast zero-token regex checks with a deep semantic forensics pass
    using the Magnum-v4:9b model for disguised toxic culture patterns.
    Returns: (is_ghost_or_scam: bool, reason: str)
    """
    desc_lower = description.lower()
    loc_lower = location.lower()
    flags = []

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
