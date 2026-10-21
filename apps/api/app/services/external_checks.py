"""
LifeLens Ω — External API Checks Service
Integrates WHOIS/RDAP (domain age, registrar) and PhishTank (URL reputation).
Both checks are optional/graceful — missing keys fall back to free-tier APIs.

External APIs:
  - RDAP: https://rdap.org (free, no key)
  - WhoisXML API: https://www.whoisxmlapi.com (optional key → WHOIS_API_KEY)
  - PhishTank: https://www.phishtank.com (optional key → PHISHTANK_API_KEY)
"""
from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger("lifelens.external_checks")

_TIMEOUT = 10
_WHOIS_API_KEY = os.getenv("WHOIS_API_KEY", "")
_PHISHTANK_KEY = os.getenv("PHISHTANK_API_KEY", "")


# ── WHOIS / RDAP ─────────────────────────────────────────────────────────────

def check_domain_whois(domain: str) -> dict[str, Any]:
    """
    Returns WHOIS/RDAP data for a domain.
    Tries WhoisXML API if key present, falls back to free RDAP.
    Never raises — always returns a result dict with 'source' and 'error' keys.
    """
    domain = domain.strip().lower().removeprefix("www.")
    result: dict[str, Any] = {
        "domain": domain,
        "source": None,
        "creation_date": None,
        "expiry_date": None,
        "registrar": None,
        "registrant_country": None,
        "domain_age_days": None,
        "is_new_domain": None,      # True if < 180 days old
        "privacy_protected": None,
        "status": None,
        "error": None,
    }

    # --- Prefer WhoisXML API if key is set ---
    if _WHOIS_API_KEY:
        try:
            resp = httpx.get(
                "https://www.whoisxmlapi.com/whoisserver/WhoisService",
                params={
                    "apiKey": _WHOIS_API_KEY,
                    "domainName": domain,
                    "outputFormat": "JSON",
                },
                timeout=_TIMEOUT,
            )
            if resp.status_code == 200:
                data = resp.json().get("WhoisRecord", {})
                result["source"] = "WhoisXML"
                result["registrar"] = data.get("registrarName")
                result["registrant_country"] = (
                    data.get("registrant", {}).get("country")
                    or data.get("registryData", {}).get("registrant", {}).get("country")
                )
                created = data.get("createdDate") or data.get("registryData", {}).get("createdDate")
                expires = data.get("expiresDate") or data.get("registryData", {}).get("expiresDate")
                result["creation_date"] = created
                result["expiry_date"] = expires
                result["status"] = data.get("status")
                if created:
                    try:
                        dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                        age = (datetime.now(timezone.utc) - dt).days
                        result["domain_age_days"] = age
                        result["is_new_domain"] = age < 180
                    except Exception:  # noqa: BLE001
                        pass
                return result
        except Exception as exc:  # noqa: BLE001
            logger.warning("WhoisXML error for %s: %s — falling back to RDAP", domain, exc)

    # --- Free RDAP fallback ---
    try:
        resp = httpx.get(
            f"https://rdap.org/domain/{domain}",
            timeout=_TIMEOUT,
            headers={"Accept": "application/rdap+json"},
            follow_redirects=True,
        )
        if resp.status_code == 200:
            data = resp.json()
            result["source"] = "RDAP (rdap.org)"
            result["status"] = " | ".join(data.get("status", []))
            events = {e["eventAction"]: e["eventDate"] for e in data.get("events", [])}
            created = events.get("registration")
            result["creation_date"] = created
            result["expiry_date"] = events.get("expiration")
            # Registrar from entities
            for ent in data.get("entities", []):
                roles = ent.get("roles", [])
                if "registrar" in roles:
                    vcards = ent.get("vcardArray", [[], []])[1]
                    for field in vcards:
                        if field[0] == "fn":
                            result["registrar"] = field[3]
                            break
            if created:
                try:
                    dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    age = (datetime.now(timezone.utc) - dt).days
                    result["domain_age_days"] = age
                    result["is_new_domain"] = age < 180
                except Exception:  # noqa: BLE001
                    pass
        elif resp.status_code == 404:
            result["error"] = f"Domain '{domain}' not found in RDAP."
        else:
            result["error"] = f"RDAP returned HTTP {resp.status_code}"
    except httpx.TimeoutException:
        result["error"] = "RDAP request timed out."
    except Exception as exc:  # noqa: BLE001
        result["error"] = f"RDAP lookup failed: {exc}"

    return result


# ── PhishTank ─────────────────────────────────────────────────────────────────

def check_phishtank(url: str) -> dict[str, Any]:
    """
    Checks a URL against PhishTank's database.
    Returns dict with keys: in_database, valid, verified, phish_detail_url, error.
    """
    result: dict[str, Any] = {
        "url": url,
        "in_database": None,
        "is_phishing": None,
        "verified": None,
        "phish_detail_url": None,
        "source": "PhishTank",
        "error": None,
    }

    url_hash = hashlib.md5(url.encode()).hexdigest()  # noqa: S324
    params: dict[str, str] = {
        "url": url,
        "format": "json",
        "url_hash": url_hash,
    }
    if _PHISHTANK_KEY:
        params["app_key"] = _PHISHTANK_KEY

    try:
        resp = httpx.post(
            "https://checkurl.phishtank.com/checkurl/",
            data=params,
            headers={"User-Agent": "LifeLensOmega/2.0"},
            timeout=_TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json().get("results", {})
            result["in_database"] = data.get("in_database", False)
            result["is_phishing"] = data.get("valid", False) and data.get("in_database", False)
            result["verified"] = data.get("verified", False)
            result["phish_detail_url"] = data.get("phish_detail_url")
        else:
            result["error"] = f"PhishTank returned HTTP {resp.status_code}"
    except httpx.TimeoutException:
        result["error"] = "PhishTank request timed out."
    except Exception as exc:  # noqa: BLE001
        result["error"] = f"PhishTank lookup failed: {exc}"

    return result


# ── Unified enrichment ────────────────────────────────────────────────────────

def enrich_job_verification(
    company_website: str | None = None,
    recruiter_email: str | None = None,
) -> dict[str, Any]:
    """
    Run WHOIS checks on company_website and recruiter_email domain.
    Returns enriched dict for inclusion in API responses.
    """
    from ..services.normalizer import extract_domain

    enrichment: dict[str, Any] = {
        "company_domain_whois": None,
        "recruiter_domain_whois": None,
    }

    if company_website:
        domain = extract_domain(company_website)
        if domain:
            enrichment["company_domain_whois"] = check_domain_whois(domain)

    if recruiter_email:
        domain = extract_domain(recruiter_email)
        if domain:
            enrichment["recruiter_domain_whois"] = check_domain_whois(domain)

    return enrichment
