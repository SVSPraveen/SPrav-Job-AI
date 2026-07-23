"""
engine/email_extractor.py
=========================
Extracts and validates email addresses from LinkedIn post text.
Falls back to guessing the email from the poster's name + company domain
when no email is explicitly mentioned in the post.
"""

import re
import socket
import dns.resolver  # pip install dnspython
from typing import Optional

# Common company email domain overrides — avoids generic @gmail guesses
KNOWN_DOMAINS = {
    "google": "google.com",
    "microsoft": "microsoft.com",
    "amazon": "amazon.com",
    "flipkart": "flipkart.com",
    "zepto": "zepto.team",
    "razorpay": "razorpay.com",
    "cred": "cred.club",
    "meesho": "meesho.com",
    "phonepe": "phonepe.com",
    "swiggy": "swiggy.in",
    "zomato": "zomato.com",
    "groww": "groww.in",
    "freshworks": "freshworks.com",
    "zoho": "zohocorp.com",
    "infosys": "infosys.com",
    "wipro": "wipro.com",
    "tcs": "tcs.com",
    "postman": "postman.com",
    "ola": "olacabs.com",
}

EMAIL_REGEX = re.compile(
    r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
)


def extract_from_text(text: str) -> Optional[str]:
    """Pull the first valid-looking email out of raw text."""
    matches = EMAIL_REGEX.findall(text)
    for m in matches:
        # Skip image/tracking placeholders
        if any(skip in m.lower() for skip in ['example.', 'placeholder', 'noreply', 'no-reply']):
            continue
        return m
    return None


def guess_email(poster_name: str, company: str) -> Optional[str]:
    """
    Construct a best-guess email from the poster's name and company.
    Uses known domain map; falls back to company_slug.com.
    Only returns a guess if the domain has a valid MX record.
    """
    # Clean name
    name_parts = poster_name.strip().lower().split()
    if len(name_parts) < 2:
        return None

    first = re.sub(r'[^a-z]', '', name_parts[0])
    last = re.sub(r'[^a-z]', '', name_parts[-1])

    # Find domain
    company_lower = company.lower().strip()
    domain = None
    for key, dom in KNOWN_DOMAINS.items():
        if key in company_lower:
            domain = dom
            break

    if not domain:
        # Construct from company name: "Zepto Technologies" → "zeptotechnologies.com"
        slug = re.sub(r'[^a-z]', '', company_lower)
        domain = f"{slug}.com"

    # Check MX record exists (domain is real and accepts email)
    if not _has_mx_record(domain):
        return None

    # Try most common patterns: firstname.lastname@domain.com
    return f"{first}.{last}@{domain}"


def _has_mx_record(domain: str) -> bool:
    """Returns True if the domain has a valid MX DNS record."""
    try:
        dns.resolver.resolve(domain, 'MX')
        return True
    except Exception:
        return False


def get_best_email(post_text: str, poster_name: str, company: str) -> Optional[str]:
    """
    Main entry point. Tries to extract an explicit email first,
    then falls back to a guessed email with MX validation.
    """
    explicit = extract_from_text(post_text)
    if explicit:
        return explicit

    guessed = guess_email(poster_name, company)
    return guessed
