"""
LifeLens Ω — Local-First Behavioral Baseline Engine (Phase 2)
Implementation Plan §32

Optional, privacy-preserving local behavioral baseline engine.
Tracks interaction cadence, domain variance, and financial transaction requests
without storing raw conversation text or personal data.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class InteractionEvent:
    event_type: str  # OFFER_RECEIVED | INTERVIEW_SCHEDULED | PAYMENT_REQUESTED | DOCUMENT_REQUESTED
    sender_domain: Optional[str] = None
    urgency_level: str = "NORMAL"  # NORMAL | HIGH | EXTREME
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class LocalBehavioralBaseline:
    """
    Phase 2 Local-First Behavioral Baseline (§32).
    Tracks user interaction statistics locally on device / isolated session.
    Calculates anomaly & friction scores without storing message content.
    """

    def __init__(self, user_id: str = "default_local_user") -> None:
        self.user_id = user_id
        self._history: List[InteractionEvent] = []
        self._known_domains: Set[str] = set()

    def record_interaction(self, event_type: str, domain: Optional[str] = None, urgency: str = "NORMAL") -> None:
        ev = InteractionEvent(
            event_type=event_type,
            sender_domain=domain,
            urgency_level=urgency,
        )
        self._history.append(ev)
        if domain:
            self._known_domains.add(domain.lower().strip())

    def evaluate_drift(self, new_event_type: str, domain: Optional[str] = None, urgency: str = "NORMAL") -> dict:
        total = len(self._history)
        if total == 0:
            return {
                "anomaly_detected": False,
                "confidence": 0.5,
                "reason": "Cold start: insufficient baseline history.",
                "friction_recommendation": "STANDARD_VERIFICATION",
            }

        # Check domain novelty
        is_new_domain = False
        if domain and domain.lower().strip() not in self._known_domains:
            is_new_domain = True

        # Check early payment request anomaly
        is_premature_payment = (
            new_event_type == "PAYMENT_REQUESTED" and total < 3
        )

        anomaly = is_new_domain and (urgency in ("HIGH", "EXTREME") or is_premature_payment)

        reason = "Normal interaction flow within historical parameters."
        friction = "NONE"
        if is_premature_payment:
            reason = "Payment requested early in interaction sequence without prior established process."
            friction = "MAXIMUM_FRICTION"
        elif anomaly:
            reason = "Unusual combination of high-urgency message and unknown sender domain."
            friction = "HIGH_FRICTION"

        return {
            "anomaly_detected": anomaly or is_premature_payment,
            "confidence": 0.85 if total > 5 else 0.65,
            "reason": reason,
            "friction_recommendation": friction,
            "history_size": total,
        }

    def reset_baseline(self) -> None:
        """Reset local baseline data (§32 privacy requirements)."""
        self._history.clear()
        self._known_domains.clear()
        logger.info("Local behavioral baseline reset for user %s", self.user_id)
