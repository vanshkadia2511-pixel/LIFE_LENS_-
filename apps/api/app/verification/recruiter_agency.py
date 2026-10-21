"""
LifeLens Ω — Authorized Third-Party Recruiter & Agency Registry
Solves Architecture Issue A5 (§16.1, §26)

Legitimate headhunters and recruitment firms (e.g. Michael Page, Robert Half, Hays)
routinely hire on behalf of client corporations using their own agency domains.
This module verifies recognized agency domains and provides exception handling
to prevent false positive domain mismatch flags (SIG_DOMAIN_MISMATCH).
"""
from __future__ import annotations
from typing import Dict, Optional
import urllib.parse
import re


RECOGNIZED_AGENCIES: Dict[str, Dict[str, str]] = {
    # UK / Europe
    "michaelpage.com": {"name": "Michael Page", "type": "RECRUITMENT_AGENCY", "country": "GB"},
    "michaelpage.co.uk": {"name": "Michael Page UK", "type": "RECRUITMENT_AGENCY", "country": "GB"},
    "pagepersonnel.co.uk": {"name": "Page Personnel", "type": "RECRUITMENT_AGENCY", "country": "GB"},
    "roberthalf.com": {"name": "Robert Half", "type": "STAFFING_AGENCY", "country": "US"},
    "roberthalf.co.uk": {"name": "Robert Half UK", "type": "STAFFING_AGENCY", "country": "GB"},
    "hays.com": {"name": "Hays Specialist Recruitment", "type": "RECRUITMENT_AGENCY", "country": "GB"},
    "hays.co.uk": {"name": "Hays UK", "type": "RECRUITMENT_AGENCY", "country": "GB"},
    "adecco.com": {"name": "The Adecco Group", "type": "STAFFING_AGENCY", "country": "CH"},
    "adecco.co.uk": {"name": "Adecco UK", "type": "STAFFING_AGENCY", "country": "GB"},
    "randstad.com": {"name": "Randstad N.V.", "type": "STAFFING_AGENCY", "country": "NL"},
    "randstad.co.uk": {"name": "Randstad UK", "type": "STAFFING_AGENCY", "country": "GB"},
    "reed.co.uk": {"name": "Reed Specialist Recruitment", "type": "RECRUITMENT_AGENCY", "country": "GB"},

    # Global / US
    "kornferry.com": {"name": "Korn Ferry", "type": "EXECUTIVE_SEARCH", "country": "US"},
    "manpowergroup.com": {"name": "ManpowerGroup", "type": "STAFFING_AGENCY", "country": "US"},
    "heidrick.com": {"name": "Heidrick & Struggles", "type": "EXECUTIVE_SEARCH", "country": "US"},
    "spencerstuart.com": {"name": "Spencer Stuart", "type": "EXECUTIVE_SEARCH", "country": "US"},
    "allegisgroup.com": {"name": "Allegis Group / TEKsystems", "type": "STAFFING_AGENCY", "country": "US"},
    "teksystems.com": {"name": "TEKsystems", "type": "STAFFING_AGENCY", "country": "US"},
    "aerotek.com": {"name": "Aerotek", "type": "STAFFING_AGENCY", "country": "US"},

    # India / APAC
    "teamlease.com": {"name": "TeamLease Services", "type": "STAFFING_AGENCY", "country": "IN"},
    "quesscorp.com": {"name": "Quess Corp", "type": "STAFFING_AGENCY", "country": "IN"},
    "abcconsultants.in": {"name": "ABC Consultants", "type": "EXECUTIVE_SEARCH", "country": "IN"},
}


def extract_domain_from_email_or_url(input_str: str) -> str:
    """Extract clean domain name from email or url."""
    if not input_str:
        return ""
    text = input_str.strip().lower()
    if "@" in text:
        return text.split("@")[-1].strip()
    if "://" in text:
        parsed = urllib.parse.urlparse(text)
        netloc = parsed.netloc or parsed.path
        return re.sub(r"^www\.", "", netloc.split(":")[0])
    return re.sub(r"^www\.", "", text.split("/")[0])


def is_recognized_agency_domain(domain_or_email: str) -> bool:
    """Check if domain or email belongs to a recognized recruitment/staffing agency."""
    domain = extract_domain_from_email_or_url(domain_or_email)
    if not domain:
        return False
    if domain in RECOGNIZED_AGENCIES:
        return True
    # Subdomain check (e.g., jobs.roberthalf.com)
    for agency_domain in RECOGNIZED_AGENCIES:
        if domain.endswith("." + agency_domain):
            return True
    return False


def get_agency_info(domain_or_email: str) -> Optional[Dict[str, str]]:
    """Retrieve metadata about the recognized staffing/recruitment agency."""
    domain = extract_domain_from_email_or_url(domain_or_email)
    if not domain:
        return None
    if domain in RECOGNIZED_AGENCIES:
        return RECOGNIZED_AGENCIES[domain]
    for agency_domain, info in RECOGNIZED_AGENCIES.items():
        if domain.endswith("." + agency_domain):
            return info
    return None
