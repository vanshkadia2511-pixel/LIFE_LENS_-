"""
LifeLens Ω — Entity Normalizer
Implementation Plan §29

Normalizes:
  - Currency
  - Country
  - Organization names
  - URLs
  - Email domains
  - Phone numbers
  - Job titles
"""
from __future__ import annotations
import re
import unicodedata
from urllib.parse import urlparse
from typing import Optional


# ---------------------------------------------------------------------------
# Company name normalization (§29)
# ---------------------------------------------------------------------------

_COMPANY_SUFFIXES = [
    r"\bltd\.?\b", r"\blimited\b", r"\bplc\b", r"\binc\.?\b",
    r"\bcorp\.?\b", r"\bcorporation\b", r"\bllc\b", r"\bllp\b",
    r"\bgmbh\b", r"\bag\b", r"\bsrl\b", r"\bpvt\.?\b", r"\bprivate\b",
]


def normalize_company_name(name: Optional[str]) -> Optional[str]:
    """
    Normalize a company name for comparison.
    Lower-case, strip legal suffixes, strip punctuation, collapse whitespace.
    """
    if not name:
        return None
    n = name.strip().lower()
    n = unicodedata.normalize("NFKD", n)
    n = n.encode("ascii", "ignore").decode("ascii")
    for suffix in _COMPANY_SUFFIXES:
        n = re.sub(suffix, "", n, flags=re.IGNORECASE)
    n = re.sub(r"[^\w\s]", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n


# ---------------------------------------------------------------------------
# Email domain normalization (§29)
# ---------------------------------------------------------------------------

def normalize_email_domain(email: Optional[str]) -> Optional[str]:
    """Extract and normalize the domain from an email address."""
    if not email or "@" not in email:
        return None
    return email.split("@")[-1].strip().lower()


# ---------------------------------------------------------------------------
# URL normalization (§27, §29)
# ---------------------------------------------------------------------------

def normalize_url(url: Optional[str]) -> Optional[str]:
    """Normalize a URL: strip scheme, www prefix, trailing slash."""
    if not url:
        return None
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    domain = re.sub(r"^www\.", "", domain)
    if not domain or "." not in domain:
        return None
    return domain


def extract_domain(url_or_email: Optional[str]) -> Optional[str]:
    """
    Extract the root domain from either a URL or an email address.
    Used for domain comparison (§26).
    """
    if not url_or_email:
        return None
    if "@" in url_or_email:
        domain = normalize_email_domain(url_or_email)
        return domain if (domain and "." in domain) else None
    return normalize_url(url_or_email)



# ---------------------------------------------------------------------------
# Country normalization (§29)
# ---------------------------------------------------------------------------

_COUNTRY_ALIASES: dict[str, str] = {
    "uk": "united kingdom",
    "u.k.": "united kingdom",
    "gb": "united kingdom",
    "us": "united states",
    "u.s.": "united states",
    "usa": "united states",
    "uae": "united arab emirates",
}


def normalize_country(country: Optional[str]) -> Optional[str]:
    if not country:
        return None
    c = country.strip().lower()
    return _COUNTRY_ALIASES.get(c, c)


# ---------------------------------------------------------------------------
# Phone normalization (§29) — strip non-digits for comparison
# ---------------------------------------------------------------------------

def normalize_phone(phone: Optional[str]) -> Optional[str]:
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone)
    return digits if digits else None
