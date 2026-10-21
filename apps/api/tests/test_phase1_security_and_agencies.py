"""
LifeLens Ω — Phase 1 Security, Privacy (P5), and Recruiter Agency Tests (Issue A5)
"""
import pytest
import os
import hmac
import hashlib

from apps.api.app.security.privacy import (
    hash_identifier,
    hash_email,
    hash_phone,
    verify_identifier_hash,
    mask_email,
    mask_phone,
    get_salt,
)
from apps.api.app.verification.recruiter_agency import (
    is_recognized_agency_domain,
    get_agency_info,
    extract_domain_from_email_or_url,
)
from apps.api.app.verification.domain import DomainVerifier, DomainMatchStatus


# ============================================================================
# P5 — Salted HMAC-SHA256 Cryptographic Privacy Tests
# ============================================================================

def test_salted_hmac_identifier_hashing():
    salt = "test_custom_salt_value_123"
    raw_email = "Recruiter.Name@Company.com "

    hashed1 = hash_identifier(raw_email, salt=salt)
    hashed2 = hash_identifier("recruiter.name@company.com", salt=salt)

    # Normalization (trimming, lowercase) must produce identical hash
    assert hashed1 == hashed2
    assert len(hashed1) == 64  # SHA-256 hex string length

    # Different salt must yield completely different hash
    hashed_diff_salt = hash_identifier(raw_email, salt="different_salt")
    assert hashed1 != hashed_diff_salt


def test_hash_phone_normalization():
    phone1 = "+44 (0) 7911 123456"
    phone2 = "+447911123456"

    # Both normalized to +447911123456
    assert hash_phone(phone1) == hash_phone(phone2)


def test_verify_identifier_hash_constant_time():
    raw = "confidential_applicant_id"
    expected = hash_identifier(raw)

    assert verify_identifier_hash(raw, expected) is True
    assert verify_identifier_hash("wrong_id", expected) is False


def test_mask_email():
    assert mask_email("recruiter.smith@enterprise.com") == "r***h@enterprise.com"
    assert mask_email("hr@domain.co.uk") == "h***@domain.co.uk"
    assert mask_email("") == ""
    assert mask_email("invalid-email") == "invalid-email"


def test_mask_phone():
    assert mask_phone("+44 7911 123456") == "+*** *** 3456"
    assert mask_phone("9876543210") == "*** *** 3210"
    assert mask_phone("") == ""


# ============================================================================
# Issue A5 — Recruiter Agency Exception & Domain Handling Tests
# ============================================================================

def test_extract_domain_from_email_or_url():
    assert extract_domain_from_email_or_url("john@michaelpage.co.uk") == "michaelpage.co.uk"
    assert extract_domain_from_email_or_url("https://www.roberthalf.com/jobs") == "roberthalf.com"
    assert extract_domain_from_email_or_url("hays.com/search") == "hays.com"


def test_is_recognized_agency_domain():
    assert is_recognized_agency_domain("sarah@michaelpage.co.uk") is True
    assert is_recognized_agency_domain("recruiter@roberthalf.com") is True
    assert is_recognized_agency_domain("careers@hays.com") is True
    assert is_recognized_agency_domain("jobs.kornferry.com") is True

    # Generic company / free mail are not staffing agencies
    assert is_recognized_agency_domain("recruiter@google.com") is False
    assert is_recognized_agency_domain("scam@gmail.com") is False


def test_get_agency_info():
    info = get_agency_info("sarah@michaelpage.co.uk")
    assert info is not None
    assert info["name"] == "Michael Page UK"
    assert info["type"] == "RECRUITMENT_AGENCY"


def test_domain_verifier_recognizes_third_party_agency():
    verifier = DomainVerifier()

    # Recruiter from Michael Page hiring for DeepMind
    res = verifier.compare(
        official_website="https://deepmind.google",
        recruiter_email="sarah.consultant@michaelpage.co.uk",
    )

    # Must be categorized as THIRD_PARTY_AGENCY with 0.0 signal strength (not MISMATCH)
    assert res.domain_match_status == DomainMatchStatus.THIRD_PARTY_AGENCY
    assert res.signal_strength == 0.0
    assert "Michael Page UK" in res.mismatch_description
    assert "Third-party recruiter verified" in res.mismatch_description
