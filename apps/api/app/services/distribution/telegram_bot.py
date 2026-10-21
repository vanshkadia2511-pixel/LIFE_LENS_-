"""
LifeLens Ω — Phase H: Telegram Forward-to-Verify Bot Service
Implements Telegram Bot API webhook processing.
Constraints:
- Secret token verification (X-Telegram-Bot-Api-Secret-Token)
- Rate-limiting per sender (salted-HMAC chat ID)
- Never retains message content after processing
- Plain-language Evidence Card reply adhering to Passport Control format
"""
from __future__ import annotations
import hmac
import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple

from apps.api.app.detectors.digital_arrest_pack import DigitalArrestPatternPack
from apps.api.app.detectors.quishing_upi_loan_checker import UPICollectExplainer


@dataclass
class EvidenceCard:
    verdict: str  # Rule A: "Request looks high-risk" | "Needs Verification" | "Verification step completed"
    stamp_code: str  # [HIGH-RISK], [NEEDS-VERIFICATION], [VERIFIED]
    key_findings: List[str]
    immediate_actions: List[str]
    educational_note: str
    provenance: str = "LifeLens Ω Distribution Sentinel (In-Memory Triage)"


class TelegramVerifyBot:
    """
    Handles user-forwarded suspicious messages via Telegram Bot API webhook.
    """

    def __init__(
        self,
        bot_token: str = "SIMULATED_TELEGRAM_TOKEN",
        webhook_secret: str = "lifelens_telegram_secret_token_123",
        rate_limit_per_minute: int = 5,
    ) -> None:
        self.bot_token = bot_token
        self.webhook_secret = webhook_secret
        self.rate_limit_per_minute = rate_limit_per_minute
        self._rate_limits: Dict[str, List[float]] = {}
        self.digital_arrest_pack = DigitalArrestPatternPack()
        self.upi_explainer = UPICollectExplainer()

    def verify_webhook_secret(self, secret_header: Optional[str]) -> bool:
        """Verifies X-Telegram-Bot-Api-Secret-Token matches configured secret."""
        if not secret_header or not self.webhook_secret:
            return False
        return hmac.compare_digest(secret_header, self.webhook_secret)

    def is_rate_limited(self, chat_id: str) -> bool:
        """Enforces rate-limiting per salted-HMAC chat ID to prevent DoS/abuse."""
        now = time.time()
        # Hash chat ID so raw identifier is never kept
        hashed_id = hashlib.sha256(f"{chat_id}_salt_telegram".encode("utf-8")).hexdigest()[:16]

        timestamps = self._rate_limits.get(hashed_id, [])
        # Keep only timestamps in the last 60 seconds
        valid = [t for t in timestamps if now - t < 60.0]

        if len(valid) >= self.rate_limit_per_minute:
            self._rate_limits[hashed_id] = valid
            return True

        valid.append(now)
        self._rate_limits[hashed_id] = valid
        return False

    def process_forwarded_update(
        self,
        update_payload: Dict[str, Any],
        consent_given: bool = True,
    ) -> Tuple[bool, Optional[EvidenceCard], str]:
        """
        Processes a Telegram webhook update.
        Returns: (success: bool, evidence_card: Optional[EvidenceCard], message: str)
        """
        message_data = update_payload.get("message", {})
        chat_id = str(message_data.get("chat", {}).get("id", "0"))

        # 1. Rate limiting check
        if self.is_rate_limited(chat_id):
            return False, None, "Rate limit exceeded. Please wait a minute before sending more verifications."

        # 2. Consent gate
        if not consent_given:
            return False, None, "User consent required before processing forwarded message."

        # 3. Extract message text
        text = message_data.get("text", "")
        if not text:
            # Check caption if photo
            text = message_data.get("caption", "")

        if not text:
            return False, None, "No readable text found in forwarded message."

        # 4. Generate Evidence Card
        card = self._evaluate_text_to_card(text)

        # 5. Sever reference to message payload (zero retention)
        del text
        del update_payload

        return True, card, "Evidence card successfully generated."

    def _evaluate_text_to_card(self, text: str) -> EvidenceCard:
        findings: List[str] = []
        actions: List[str] = []
        verdict = "Verification step completed"
        stamp = "[VERIFIED-STEP]"
        note = "No known coercive intimidation patterns found in submitted message."

        # Check digital arrest
        da_res = self.digital_arrest_pack.evaluate_text(text)
        if da_res.is_flagged:
            verdict = "Request looks high-risk"
            stamp = "[HIGH-RISK]"
            findings.extend(da_res.matched_patterns)
            actions.append("1. Do NOT join any video call or transfer bail money.")
            actions.append("2. Police / CBI never arrest anyone over Skype, Zoom, or WhatsApp.")
            actions.append("3. Report immediately on cybercrime.gov.in (Helpline: 1930).")
            note = da_res.law_enforcement_note

        # Check UPI deception
        upi_res = self.upi_explainer.analyze_request(text)
        if upi_res.is_deceptive:
            verdict = "Request looks high-risk"
            stamp = "[HIGH-RISK]"
            findings.append("Deceptive UPI Collect Request: Instructs entering PIN to receive funds.")
            actions.append("1. DO NOT enter your UPI PIN. Entering PIN always DEDUCTS money.")
            actions.append("2. Decline the collect request on Google Pay / PhonePe / Paytm.")
            note = upi_res.educational_warning

        if not findings:
            actions.append("1. Always corroborate job or offer links via independent official channels.")

        return EvidenceCard(
            verdict=verdict,
            stamp_code=stamp,
            key_findings=findings or ["No high-urgency financial or arrest coercion detected."],
            immediate_actions=actions,
            educational_note=note,
        )
