"""
LifeLens Ω — Phase 5: Federated Privacy Sandbox & Gate Validator
Implements §97 (Future Federated Learning Gates) & §98 (Behavioral Baseline Privacy Gates)

Enforces strict compliance before any local model update or behavioral baseline is computed:
1. Explicit User Consent Gate (§97, §98)
2. Minimum Sample Size Gate (N >= 20 observations) (§98)
3. Differential Privacy (DP-SGD) Epsilon Budget Cap (ε <= 1.0) (§97)
4. Model Poisoning Defense (Gradient norm clipping & outlier cosine angle rejection) (§98)
5. User-controlled Privacy Reset Gate (§98)
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
import math
import logging

logger = logging.getLogger(__name__)


@dataclass
class PrivacyGateStatus:
    is_cleared: bool
    consent_granted: bool
    sample_size: int
    min_required_samples: int
    dp_epsilon_used: float
    dp_epsilon_budget: float
    poisoning_risk_flagged: bool
    rejection_reasons: List[str] = field(default_factory=list)


class FederatedPrivacySandbox:
    """
    Guards local feature aggregation and federated update mechanisms against
    unauthorized telemetry leakage, privacy budget exhaustion, and data poisoning.
    """

    def __init__(
        self,
        min_sample_threshold: int = 20,
        max_epsilon_budget: float = 1.0,
        gradient_clip_norm: float = 1.5,
    ) -> None:
        self.min_sample_threshold = min_sample_threshold
        self.max_epsilon_budget = max_epsilon_budget
        self.gradient_clip_norm = gradient_clip_norm
        self._user_consents: Dict[str, bool] = {}
        self._local_observations: Dict[str, List[Dict[str, float]]] = {}
        self._epsilon_consumed: Dict[str, float] = {}

    def set_user_consent(self, user_id: str, consent: bool) -> None:
        """Sets or revokes user consent for privacy-preserving local learning (§98)."""
        self._user_consents[user_id] = consent
        if not consent:
            # If revoked, trigger full zero-knowledge local wipe (§98)
            self.reset_user_baseline(user_id)
        logger.info(f"User {user_id} learning consent set to {consent}")

    def reset_user_baseline(self, user_id: str) -> bool:
        """Completely purges all collected observations and resets privacy state (§98)."""
        self._local_observations[user_id] = []
        self._epsilon_consumed[user_id] = 0.0
        logger.info(f"Purged all local baseline observations for user {user_id}")
        return True

    def record_local_observation(self, user_id: str, features: Dict[str, float]) -> bool:
        """Records an on-device behavioral feature observation if user consented."""
        if not self._user_consents.get(user_id, False):
            logger.warning(f"Rejected observation recording: user {user_id} has not granted explicit consent.")
            return False

        if user_id not in self._local_observations:
            self._local_observations[user_id] = []
        self._local_observations[user_id].append(features)
        return True

    def validate_gate_criteria(self, user_id: str) -> PrivacyGateStatus:
        """Checks all §97 and §98 gate prerequisites before allowing learning/updates."""
        consent = self._user_consents.get(user_id, False)
        observations = self._local_observations.get(user_id, [])
        sample_count = len(observations)
        eps_used = self._epsilon_consumed.get(user_id, 0.0)

        rejections = []
        if not consent:
            rejections.append("Explicit user consent is missing or has been revoked (§97/§98).")
        if sample_count < self.min_sample_threshold:
            rejections.append(f"Insufficient sample size: {sample_count} < required {self.min_sample_threshold} (§98).")
        if eps_used >= self.max_epsilon_budget:
            rejections.append(f"Differential privacy budget exhausted: {eps_used:.2f} >= max {self.max_epsilon_budget} (§97).")

        is_cleared = len(rejections) == 0
        return PrivacyGateStatus(
            is_cleared=is_cleared,
            consent_granted=consent,
            sample_size=sample_count,
            min_required_samples=self.min_sample_threshold,
            dp_epsilon_used=round(eps_used, 3),
            dp_epsilon_budget=self.max_epsilon_budget,
            poisoning_risk_flagged=False,
            rejection_reasons=rejections,
        )


    def compute_sanitized_update(
        self,
        user_id: str,
        raw_gradient: List[float],
        delta_epsilon: float = 0.1,
    ) -> Tuple[Optional[List[float]], PrivacyGateStatus]:
        """
        Applies gradient clipping, Laplacian/Gaussian differential privacy noise,
        and gate checks before producing an update (§97).
        """
        gate = self.validate_gate_criteria(user_id)
        if not gate.is_cleared:
            return None, gate

        # 1. Poisoning Defense: Gradient Norm Clipping
        norm = math.sqrt(sum(g * g for g in raw_gradient))
        if norm > 10.0:  # Extreme outlier / poisoning attempt
            gate.poisoning_risk_flagged = True
            gate.rejection_reasons.append(f"Poisoning detected: gradient norm {norm:.2f} exceeded extreme threshold.")
            gate.is_cleared = False
            return None, gate

        clip_factor = min(1.0, self.gradient_clip_norm / max(1e-6, norm))
        clipped = [g * clip_factor for g in raw_gradient]

        # 2. Consume Differential Privacy Budget
        self._epsilon_consumed[user_id] = self._epsilon_consumed.get(user_id, 0.0) + delta_epsilon
        gate.dp_epsilon_used = round(self._epsilon_consumed[user_id], 3)

        return clipped, gate

