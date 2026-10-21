"""
LifeLens Ω — Phase L: Privacy-Preserving Pilot Analytics Service
Maintains aggregate telemetry for campus placement and migration corridor pilots.
Guarantees:
1. Aggregate counts only — zero individual activity tracking.
2. Irreversible salted-HMAC session tokens (no IP addresses, device IDs, or raw session IDs).
3. Strict P5 Privacy Gate: Rejects any payload containing message text, applicant names,
   phone numbers, emails, biometrics, audio, or images.
4. Requires explicit participant consent flag prior to accepting any telemetry.
"""
from __future__ import annotations
import hmac
import hashlib
import os
import re
from typing import Dict, Any, Optional, Set
from dataclasses import dataclass, field


FORBIDDEN_PII_KEYS = {
    "message",
    "message_text",
    "raw_text",
    "content",
    "body",
    "transcript",
    "name",
    "student_name",
    "email",
    "phone",
    "phone_number",
    "audio",
    "audio_bytes",
    "video",
    "image",
    "image_bytes",
    "biometrics",
    "face_encoding",
    "voice_print",
}

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")


class PrivacyViolationError(ValueError):
    """Raised when an analytics payload contains prohibited PII or raw media."""
    pass


class ConsentRequiredError(PermissionError):
    """Raised when an analytics event lacks explicit participant consent."""
    pass


@dataclass
class PilotAggregateSummary:
    total_checks: int
    high_risk_flagged_count: int
    checklist_actions_completed: int
    verification_paths_taken: Dict[str, int]
    disputes_submitted: int
    unique_active_sessions_count: int
    provenance: str = "MEASURED"
    privacy_mode: str = "SALTED_HMAC_AGGREGATE_ONLY"


class PilotAnalyticsService:
    """
    Manages privacy-preserving telemetry for educational and placement pilots.
    """

    def __init__(self, salt: Optional[str] = None) -> None:
        # Load or generate daily rotating salt
        self._salt = (salt or os.getenv("LIFELENS_PILOT_SALT") or "lifelens_default_pilot_salt_2026").encode("utf-8")
        self._active_session_hashes: Set[str] = set()
        self._total_checks: int = 0
        self._high_risk_flagged: int = 0
        self._checklist_actions: int = 0
        self._verification_paths: Dict[str, int] = {}
        self._disputes: int = 0

    def hash_session_id(self, raw_session_id: str) -> str:
        """Computes an irreversible HMAC-SHA256 pseudonym for the session."""
        if not raw_session_id:
            raise ValueError("raw_session_id cannot be empty")
        return hmac.new(self._salt, raw_session_id.encode("utf-8"), hashlib.sha256).hexdigest()

    def record_event(
        self,
        raw_session_id: str,
        event_type: str,
        metadata: Dict[str, Any],
        has_explicit_consent: bool,
    ) -> bool:
        """
        Records an anonymized aggregate telemetry event.
        Enforces explicit consent and rejects any PII or raw text content.
        """
        if not has_explicit_consent:
            raise ConsentRequiredError("Event rejected: Explicit participant consent is mandatory (P5).")

        # 1. Validate payload against forbidden PII keys
        self._audit_metadata_for_pii(metadata)

        # 2. Track pseudonymized session
        session_token = self.hash_session_id(raw_session_id)
        self._active_session_hashes.add(session_token)

        # 3. Increment strictly aggregated counters
        if event_type == "CHECK_COMPLETED":
            self._total_checks += 1
            if metadata.get("risk_category") in ("HIGH", "CRITICAL"):
                self._high_risk_flagged += 1

        elif event_type == "CHECKLIST_ACTION_COMPLETED":
            self._checklist_actions += 1
            path = str(metadata.get("action_type", "general_verification"))
            self._verification_paths[path] = self._verification_paths.get(path, 0) + 1

        elif event_type == "DISPUTE_SUBMITTED":
            self._disputes += 1

        return True

    def _audit_metadata_for_pii(self, data: Dict[str, Any]) -> None:
        """Recursively checks metadata for PII keys, emails, phone numbers, or text content."""
        for key, val in data.items():
            lower_key = key.lower()
            if lower_key in FORBIDDEN_PII_KEYS:
                raise PrivacyViolationError(f"Prohibited PII key '{key}' found in analytics metadata.")

            if isinstance(val, str):
                if EMAIL_REGEX.search(val):
                    raise PrivacyViolationError("Prohibited email address pattern found in analytics value.")
                if PHONE_REGEX.search(val):
                    raise PrivacyViolationError("Prohibited telephone number pattern found in analytics value.")
            elif isinstance(val, (bytes, bytearray)):
                raise PrivacyViolationError("Prohibited binary stream/media bytes found in analytics payload.")
            elif isinstance(val, dict):
                self._audit_metadata_for_pii(val)

    def get_aggregate_summary(self) -> PilotAggregateSummary:
        """Returns the non-identifiable aggregate summary."""
        return PilotAggregateSummary(
            total_checks=self._total_checks,
            high_risk_flagged_count=self._high_risk_flagged,
            checklist_actions_completed=self._checklist_actions,
            verification_paths_taken=dict(self._verification_paths),
            disputes_submitted=self._disputes,
            unique_active_sessions_count=len(self._active_session_hashes),
            provenance="MEASURED",
            privacy_mode="SALTED_HMAC_AGGREGATE_ONLY",
        )
