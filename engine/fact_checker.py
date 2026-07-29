import re
from engine.skill_analyzer import load_user_kb_text

# ─────────────────────────────────────────────────────────────────────────────
# Metric extraction
# ─────────────────────────────────────────────────────────────────────────────

def extract_metric_claims(text: str) -> set:
    """Extracts and normalizes numbers from text to prevent false positives from formatting."""
    # Pre-process text: convert 'percent' to '%', remove commas in numbers
    text = re.sub(r'(?i)\bpercent\b', '%', text)
    text = re.sub(r'(?<=\d),(?=\d{3})', '', text)
    
    # Extract numbers with optional decimals and optional suffixes (K, M, B)
    # \d+(?:\.\d+)?(?:[kKmMbB])?
    pattern = r'\b\d+(?:\.\d+)?(?:[kKmMbB]\b)?'
    
    claims = set()
    for match in re.finditer(pattern, text):
        raw = match.group(0).lower()
        multiplier = 1.0
        if raw.endswith('k'):
            multiplier = 1000.0
            raw = raw[:-1]
        elif raw.endswith('m'):
            multiplier = 1000000.0
            raw = raw[:-1]
        elif raw.endswith('b'):
            multiplier = 1000000000.0
            raw = raw[:-1]
            
        try:
            val = float(raw) * multiplier
            claims.add(val)
        except ValueError:
            pass
            
    return claims


# ─────────────────────────────────────────────────────────────────────────────
# Fact verification
# ─────────────────────────────────────────────────────────────────────────────

def verify_resume_facts(
    latex_content: str,
    intent: str = "human_review",
) -> tuple[bool, list]:
    """
    Verifies that the generated resume doesn't contain invented metrics.

    Args:
        latex_content: The HTML/text content of the generated resume.
        intent:        "auto_apply"    — zero-tolerance; any invented claim is an
                                         immediate failure. No retry will be issued
                                         by the graph router; the job downgrades to
                                         Human Apply Queue.
                       "human_review"  — existing behaviour; returns the failure
                                         signal and the graph router retries up to
                                         2 times before giving up.

    Returns:
        (is_passed: bool, invented_claims: list[str])
        invented_claims is empty when is_passed is True.
    """
    # 1. Extract all metric claims from the generated resume
    generated_claims = extract_metric_claims(latex_content)

    # 2. Extract all metric claims from the user's original Knowledge Base
    user_text = load_user_kb_text()
    allowed_claims = extract_metric_claims(user_text)

    invented = [c for c in generated_claims if c not in allowed_claims]

    if invented:
        if intent == "auto_apply":
            print(
                f"[FactChecker] AUTO-APPLY ZERO-TOLERANCE FAIL: {len(invented)} "
                f"invented claim(s) detected: {invented}. "
                "Downgrading to Human Apply Queue — no retry."
            )
        else:
            print(
                f"[FactChecker] HUMAN-REVIEW PATH FAIL: {len(invented)} "
                f"invented claim(s): {invented}. Retry will be issued."
            )
        return False, invented

    print(f"[FactChecker] PASS ({intent}): no hallucinated metrics detected.")
    return True, []
