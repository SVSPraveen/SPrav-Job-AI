"""
engine/jd_extractor.py
=======================
Fetches the full Job Description text from any URL using a lightweight
requests+BeautifulSoup approach first. Falls back to Playwright for
JavaScript-heavy pages (React SPAs, etc.).

Used by the Career Page Watcher to backfill JD text for stealth listings
before they enter the scoring pipeline.
"""

import re
import requests
from bs4 import BeautifulSoup
from typing import Optional

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# CSS selectors commonly used for JD content across popular ATS/career pages
JD_SELECTORS = [
    ".job-description", ".jobDescriptionContent", ".job-desc",
    ".description__text", ".show-more-less-html__markup",
    "[class*='job-description']", "[class*='jd-desc']",
    "[class*='description']", "[data-testid='job-description']",
    "article", ".content", ".body-text", "main",
]


def _extract_text_from_html(html: str) -> str:
    """Parse HTML and return clean text from the best JD container."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove boilerplate noise
    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()

    for selector in JD_SELECTORS:
        el = soup.select_one(selector)
        if el:
            text = el.get_text(separator="\n", strip=True)
            if len(text) > 200:
                return text[:4000]

    # Last resort: full body text
    return soup.get_text(separator="\n", strip=True)[:4000]


def fetch_jd_text(url: str, timeout: int = 15) -> Optional[str]:
    """
    Fetch job description text from a URL.
    Uses requests first (fast), falls back to Playwright for JS-heavy pages.
    Returns None on failure.
    """
    if not url or not url.startswith("http"):
        return None

    # ── Fast path: plain HTTP fetch ───────────────────────────────────────────
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        text = _extract_text_from_html(resp.text)
        if len(text) > 300:
            return text
    except Exception as e:
        print(f"[JDExtractor] HTTP fetch failed ({url}): {e} — trying Playwright...")

    # ── Slow path: Playwright for SPAs ───────────────────────────────────────
    try:
        import subprocess, json, os
        extractor_js = os.path.join(
            os.path.dirname(__file__), "..", "scraper_service", "jd_extractor.js"
        )
        if not os.path.exists(extractor_js):
            return None

        result = subprocess.run(
            ["node", extractor_js, url],
            capture_output=True, text=True, timeout=30
        )
        output = result.stdout.strip()
        if output:
            data = json.loads(output)
            return data.get("text", "")
    except Exception as e:
        print(f"[JDExtractor] Playwright fallback failed ({url}): {e}")

    return None
