"""
LifeLens Ω — Phase H: WhatsApp Business Platform Forward-to-Verify Service
Meta Cloud API Webhook integration for user-initiated message forwards.
Compliance & Terms:
- Validates X-Hub-Signature-256 (HMAC-SHA256)
- User-initiated forwards only (Never sends unsolicited outbound messages)
- 24-hour Customer Service Window compliant (Zero marketing template fees)
- Zero persistence of victim messages once evidence card is generated
"""
from __future__ import annotations
import hmac
import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple

from .telegram_bot import EvidenceCard
from apps.api.app.detectors.digital_arrest_pack import DigitalArrestPatternPack
from apps.api.app.detectors.quishing_upi_loan_checker import UPICollectExplainer


@dataclass
class MetaPolicyDetails:
    terms_check: str = "COMPLIANT"
    conversation_type: str = "SERVICE_CONVERSATION"  # User-initiated, non-marketing
    pricing_category: str = "Zero cost within standard 24h customer service window (1,000 free/mo)"
    opt_in_policy: str = "Strictly inbound/user-initiated forwards. Zero unsolicited outbound messaging."


class WhatsAppVerifyBot:
    """
    Handles user-forwarded WhatsApp messages via Meta Cloud API webhooks.
    """

    def __init__(
        self,
        app_secret: str = "lifelens_meta_app_secret_abc123",
        verify_token: str = "lifelens_meta_verify_token_xyz",
        rate_limit_per_minute: int = 5,
    ) -> None:
        self.app_secret = app_secret
        self.verify_token = verify_token
        self.rate_limit_per_minute = rate_limit_per_minute
        self._rate_limits: Dict[str, List[float]] = {}
        self.digital_arrest_pack = DigitalArrestPatternPack()
        self.upi_explainer = UPICollectExplainer()

    def verify_webhook_hub_signature(self, raw_body_bytes: bytes, signature_header: Optional[str]) -> bool:
        """
        Validates X-Hub-Signature-256: sha256=<HMAC-SHA256(app_secret, raw_body)>.
        """
        if not signature_header or not signature_header.startswith("sha256="):
            return False

        expected_hash = hmac.new(
            self.app_secret.encode("utf-8"),
            raw_body_bytes,
            hashlib.sha256,
        ).hexdigest()

        provided_hash = signature_header[7:]
        return hmac.compare_digest(expected_hash, provided_hash)

    def verify_webhook_subscription(self, mode: Optional[str], token: Optional[str], challenge: Optional[str]) -> Optional[str]:
        """Handles Meta GET subscription handshake."""
        if mode == "subscribe" and token == self.verify_token:
            return challenge
        return None

    def is_rate_limited(self, sender_phone_raw: str) -> bool:
        now = time.time()
        # Salted hash phone number
        phone_hash = hashlib.sha256(f"{sender_phone_raw}_salt_wa".encode("utf-8")).hexdigest()[:16]
        timestamps = self._rate_limits.get(phone_hash, [])
        valid = [t for t in timestamps if now - t < 60.0]

        if len(valid) >= self.rate_limit_per_minute:
            self._rate_limits[phone_hash] = valid
            return True

        valid.append(now)
        self._rate_limits[phone_hash] = valid
        return False

    def process_incoming_forward(
        self,
        payload: Dict[str, Any],
        consent_given: bool = True,
    ) -> Tuple[bool, Optional[EvidenceCard], str]:
        """
        Processes WhatsApp webhook payload from user.
        Discards raw text immediately after generating Evidence Card.
        """
        entries = payload.get("entry", [])
        if not entries:
            return False, None, "Invalid Meta payload format."

        changes = entries[0].get("changes", [])
        if not changes:
            return False, None, "No changes in payload."

        value = changes[0].get("value", {})
        messages = value.get("messages", [])
        if not messages:
            return False, None, "No messages present (likely delivery receipt or status update)."

        msg = messages[0]
        sender_id = msg.get("from", "unknown")

        if self.is_rate_limited(sender_id):
            return False, None, "Rate limit exceeded. Please wait a minute before forwarding more messages."

        if not consent_given:
            return False, None, "Consent required before analysis."

        msg_type = msg.get("type", "")
        text = ""
        if msg_type == "text":
            text = msg.get("text", {}).get("body", "")
        elif msg_type == "image":
            text = msg.get("image", {}).get("caption", "")

        if not text:
            return False, None, "No text or caption provided in forwarded WhatsApp message."

        # Generate Evidence Card
        card = self._evaluate_text_to_card(text)

        # Sever references (zero retention)
        del text
        del payload

        return True, card, "Evidence card generated successfully."

    def _evaluate_text_to_card(self, text: str) -> EvidenceCard:
        findings: List[str] = []
        actions: List[str] = []
        verdict = "Verification step completed"
        stamp = "[VERIFIED-STEP]"
        note = "No known coercive intimidation patterns found in forwarded WhatsApp message."

        da_res = self.digital_arrest_pack.evaluate_text(text)
        if da_res.is_flagged:
            verdict = "Request looks high-risk"
            stamp = "[HIGH-RISK]"
            findings.extend(da_res.matched_patterns)
            actions.append("1. Hang up immediately: Official police never call over WhatsApp.")
            actions.append("2. Digital arrests have no legal validity in India.")
            actions.append("3. Call 1930 Cyber Fraud Helpline.")
            note = da_res.law_enforcement_note

        upi_res = self.upi_explainer.analyze_request(text)
        if upi_res.is_deceptive:
            verdict = "Request looks high-risk"
            stamp = "[HIGH-RISK]"
            findings.append("Deceptive UPI Collect Request: PIN input requested to receive funds.")
            actions.append("1. Do not enter PIN. Entering PIN always DEDUCTS money.")
            actions.append("2. Decline the collect request.")
            note = upi_res.educational_warning

        return EvidenceCard(
            verdict=verdict,
            stamp_code=stamp,
            key_findings=findings or ["No high-urgency financial or arrest coercion detected."],
            immediate_actions=actions or ["Corroborate sender identity through an out-of-band channel."],
            educational_note=note,
        )

    def get_meta_policy_details(self) -> MetaPolicyDetails:
        return MetaPolicyDetails()
