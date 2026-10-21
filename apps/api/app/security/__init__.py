"""
LifeLens Ω — Security Module
Implementation Plan §36, §38
"""
from .ssrf import SSRFShield, SSRFValidationResult
from .privacy import (
    get_salt,
    hash_identifier,
    hash_email,
    hash_phone,
    verify_identifier_hash,
    mask_email,
    mask_phone,
)

__all__ = [
    "SSRFShield",
    "SSRFValidationResult",
    "get_salt",
    "hash_identifier",
    "hash_email",
    "hash_phone",
    "verify_identifier_hash",
    "mask_email",
    "mask_phone",
]
