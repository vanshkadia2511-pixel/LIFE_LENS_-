"""
LifeLens Ω — Cryptographic Privacy & Identifier Hashing
Product Principle P5 & Implementation Plan §38, §72

Provides:
- Salted HMAC-SHA256 hashing for stored identifiers (emails, phones, applicant IDs)
- Constant-time hash verification via hmac.compare_digest
- Visual masking for UI provenance views (e.g. j***e@company.com)
- Zero plain-text persistence of sensitive identifiers
"""
from __future__ import annotations
import hashlib
import hmac
import os
import re
from typing import Optional


DEFAULT_FALLBACK_SALT = "lifelens_omega_default_crypto_salt_2026_secured"


def get_salt() -> str:
    """Retrieve cryptographic salt from environment or safe development fallback."""
    return os.getenv("LIFELENS_HMAC_SALT") or os.getenv("SECRET_KEY") or DEFAULT_FALLBACK_SALT


def hash_identifier(raw_value: str, salt: Optional[str] = None) -> str:
    """
    Computes a salted HMAC-SHA256 digest of any raw identifier.
    Normalizes input by stripping whitespace and lowering case.
    """
    if not raw_value:
        return ""
    normalized = raw_value.strip().lower().encode("utf-8")
    salt_bytes = (salt or get_salt()).encode("utf-8")
    return hmac.new(salt_bytes, normalized, hashlib.sha256).hexdigest()


def hash_email(email: str, salt: Optional[str] = None) -> str:
    """Hashes recruiter or applicant email using salted HMAC-SHA256."""
    return hash_identifier(email, salt)


def hash_phone(phone: str, salt: Optional[str] = None) -> str:
    """Hashes phone number after stripping non-digit characters and domestic trunk zeros (preserving leading +)."""
    if not phone:
        return ""
    without_trunk = re.sub(r"\(0\)", "", phone)
    cleaned = re.sub(r"[^\d+]", "", without_trunk)
    return hash_identifier(cleaned, salt)


def verify_identifier_hash(raw_value: str, expected_hash: str, salt: Optional[str] = None) -> bool:
    """Constant-time verification of raw identifier against stored salted hash."""
    computed_hash = hash_identifier(raw_value, salt)
    return hmac.compare_digest(computed_hash, expected_hash)


def mask_email(email: str) -> str:
    """
    Masks an email for user-facing provenance displays without revealing full PII.
    Example: 'recruiter.contact@google.com' -> 'r***t@google.com'
    """
    if not email or "@" not in email:
        return email or ""
    local_part, domain = email.split("@", 1)
    if len(local_part) <= 2:
        masked_local = f"{local_part[0]}***"
    else:
        masked_local = f"{local_part[0]}***{local_part[-1]}"
    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """
    Masks a phone number for user-facing provenance displays.
    Example: '+44 7911 123456' -> '+44 *** *** 3456'
    """
    if not phone:
        return ""
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 4:
        return "***"
    prefix = "+" if phone.startswith("+") else ""
    return f"{prefix}*** *** {digits[-4:]}"
