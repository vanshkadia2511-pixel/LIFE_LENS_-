"""
LifeLens Ω — Phase 3: Media Authenticity Provider Abstraction (§99, §80)

Phase 3 introduces audio/video authenticity analysis for real-time meeting alerts.
This module defines the provider abstraction as specified in §99.

Architecture (§80):
    Desktop Agent
          ↓
    Screen / Audio Capture
          ↓
    Consent Gate
          ↓
    Third-Party Detection API  ← this abstraction layer
          ↓
    Authenticity Signals
          ↓
    LifeLens Evidence Layer
          ↓
    Risk + Explanation
          ↓
    User Alert

Design rule: Do NOT train a custom deepfake model. Use provider abstraction
so providers can be swapped without rewriting LifeLens (§99).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Core enums and result types
# ─────────────────────────────────────────────────────────────

class AuthenticitySignal(str, Enum):
    """Possible authenticity signals for media content."""
    AUTHENTIC = "AUTHENTIC"
    LIKELY_AUTHENTIC = "LIKELY_AUTHENTIC"
    UNCERTAIN = "UNCERTAIN"
    INCONCLUSIVE = "INCONCLUSIVE"
    LIKELY_SYNTHETIC = "LIKELY_SYNTHETIC"
    SYNTHETIC = "SYNTHETIC"
    UNAVAILABLE = "UNAVAILABLE"           # Provider could not process this content


class MediaType(str, Enum):
    """Types of media that can be analyzed."""
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    IMAGE = "IMAGE"
    SCREEN_CAPTURE = "SCREEN_CAPTURE"


@dataclass
class AuthenticityResult:
    """
    §99: Standardized output from any MediaAuthenticityProvider.

    This is the evidence payload fed into LifeLens's risk engine.
    A provider that returns UNAVAILABLE does NOT cause a verdict;
    it reduces confidence — consistent with §25 Failure Handling.
    """
    media_type: MediaType
    signal: AuthenticitySignal
    confidence: float                    # 0.0 – 1.0
    provider_name: str
    provider_version: str
    analysis_latency_ms: float
    indicators: List[str] = field(default_factory=list)   # human-readable signals
    raw_scores: Dict[str, float] = field(default_factory=dict)
    analyzed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    consent_verified: bool = False       # §35: Consent must be confirmed before analysis
    error_message: Optional[str] = None

    def to_evidence_dict(self) -> dict:
        """
        Convert to the evidence format consumed by LifeLens's evidence ledger.
        """
        return {
            "source_type": "MEDIA_AUTHENTICITY_PROVIDER",
            "source_name": self.provider_name,
            "source_authority": 0.75,   # Third-party providers: moderate authority
            "source_independence": 0.90,
            "media_type": self.media_type.value,
            "signal": self.signal.value,
            "confidence": self.confidence,
            "indicators": self.indicators,
            "provider_version": self.provider_version,
            "analyzed_at": self.analyzed_at.isoformat(),
            "user_verifiable": False,    # User cannot independently re-check this
            "consent_verified": self.consent_verified,
        }

    @property
    def is_high_risk(self) -> bool:
        return self.signal in (AuthenticitySignal.LIKELY_SYNTHETIC, AuthenticitySignal.SYNTHETIC)

    @property
    def is_available(self) -> bool:
        return self.signal != AuthenticitySignal.UNAVAILABLE


@dataclass
class MediaCapture:
    """
    §80: Represents a media capture submitted for authenticity analysis.
    Includes a consent gate — analysis is refused if consent is not given.
    """
    media_type: MediaType
    content_bytes: Optional[bytes] = None   # raw media bytes (video/audio frame)
    content_url: Optional[str] = None       # URL to media (if stored)
    duration_seconds: Optional[float] = None
    capture_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    user_consented: bool = False            # §35: Must be True before any analysis


# ─────────────────────────────────────────────────────────────
# §99: Provider Protocol
# ─────────────────────────────────────────────────────────────

@runtime_checkable
class MediaAuthenticityProvider(Protocol):
    """
    §99: Protocol for media authenticity providers.

    Any deepfake/audio detection service implements this protocol.
    Providers can be replaced without rewriting LifeLens.

    Example implementations:
        - HiveModeration (commercial)
        - DeepWare (open source)
        - Azure AI Content Safety
        - Local ONNX model wrapper
    """

    @property
    def provider_name(self) -> str:
        """Return the provider's human-readable name."""
        ...

    @property
    def provider_version(self) -> str:
        """Return the provider's semantic version."""
        ...

    def capabilities(self) -> Dict[str, bool]:
        """
        Return a dict of which media types this provider can analyze.
        Example: {"video": True, "audio": True, "image": False}
        """
        ...

    def analyze_video(self, capture: MediaCapture) -> AuthenticityResult:
        """
        Analyze a video capture for synthetic manipulation.
        Must check consent gate before processing.
        """
        ...

    def analyze_audio(self, capture: MediaCapture) -> AuthenticityResult:
        """
        Analyze an audio capture for voice cloning / synthesis indicators.
        Must check consent gate before processing.
        """
        ...

    def analyze_image(self, capture: MediaCapture) -> AuthenticityResult:
        """
        Analyze a still image for AI generation or manipulation.
        Must check consent gate before processing.
        """
        ...


# ─────────────────────────────────────────────────────────────
# Stub / fallback provider (no external service)
# ─────────────────────────────────────────────────────────────

class UnavailableProvider:
    """
    §25 Failure Handling: A stub provider that always returns UNAVAILABLE.

    Used when:
    - No third-party API key is configured.
    - Provider is disabled via kill switch.
    - Provider is unavailable.

    UNAVAILABLE != FRAUD. The system must not penalize users when a
    provider is simply not configured.
    """
    provider_name: str = "UnavailableStub"
    provider_version: str = "0.0.0"

    def capabilities(self) -> Dict[str, bool]:
        return {"video": False, "audio": False, "image": False}

    def _unavailable(self, media_type: MediaType, reason: str) -> AuthenticityResult:
        return AuthenticityResult(
            media_type=media_type,
            signal=AuthenticitySignal.UNAVAILABLE,
            confidence=0.0,
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            analysis_latency_ms=0.0,
            error_message=reason,
            consent_verified=False,
        )

    def analyze_video(self, capture: MediaCapture) -> AuthenticityResult:
        return self._unavailable(MediaType.VIDEO, "No video authenticity provider configured.")

    def analyze_audio(self, capture: MediaCapture) -> AuthenticityResult:
        return self._unavailable(MediaType.AUDIO, "No audio authenticity provider configured.")

    def analyze_image(self, capture: MediaCapture) -> AuthenticityResult:
        return self._unavailable(MediaType.IMAGE, "No image authenticity provider configured.")


# ─────────────────────────────────────────────────────────────
# Mock provider for testing and demo
# ─────────────────────────────────────────────────────────────

class MockDeepfakeDetectionProvider:
    """
    §87 Demo Scenario: A deterministic mock provider for testing and demonstrations.

    Returns configurable results based on content patterns in the media URL or bytes.
    NOT for production use.
    """
    provider_name: str = "MockDetector"
    provider_version: str = "0.1.0"

    def capabilities(self) -> Dict[str, bool]:
        return {"video": True, "audio": True, "image": True}

    def _check_consent(self, capture: MediaCapture, media_type: MediaType) -> Optional[AuthenticityResult]:
        """§35: Reject analysis if user has not consented."""
        if not capture.user_consented:
            logger.warning("Media analysis refused: user consent not given (§35).")
            return AuthenticityResult(
                media_type=media_type,
                signal=AuthenticitySignal.UNAVAILABLE,
                confidence=0.0,
                provider_name=self.provider_name,
                provider_version=self.provider_version,
                analysis_latency_ms=0.0,
                error_message="User consent not provided. Analysis refused per §35.",
                consent_verified=False,
            )
        return None

    def analyze_video(self, capture: MediaCapture) -> AuthenticityResult:
        if r := self._check_consent(capture, MediaType.VIDEO):
            return r
        # Demo logic: URL containing 'deepfake' triggers SYNTHETIC signal
        url = capture.content_url or ""
        if "borderline" in url.lower() or "inconclusive" in url.lower() or "compressed" in url.lower():
            return AuthenticityResult(
                media_type=MediaType.VIDEO,
                signal=AuthenticitySignal.INCONCLUSIVE,
                confidence=0.50,
                provider_name=self.provider_name,
                provider_version=self.provider_version,
                analysis_latency_ms=210.0,
                indicators=["Inconclusive: media compression artifacts within natural recording variance."],
                raw_scores={"face_authenticity": 0.52, "lip_sync": 0.49, "texture": 0.50},
                consent_verified=True,
            )
        if "deepfake" in url.lower() or "fake" in url.lower():
            return AuthenticityResult(
                media_type=MediaType.VIDEO,
                signal=AuthenticitySignal.LIKELY_SYNTHETIC,
                confidence=0.82,
                provider_name=self.provider_name,
                provider_version=self.provider_version,
                analysis_latency_ms=350.0,
                indicators=[
                    "Facial landmark inconsistency detected in frames 12–45.",
                    "Lip sync artifacts inconsistent with natural speech rhythm.",
                    "Compression pattern anomaly in background regions.",
                ],
                raw_scores={"face_authenticity": 0.18, "lip_sync": 0.23, "texture": 0.31},
                consent_verified=True,
            )
        return AuthenticityResult(
            media_type=MediaType.VIDEO,
            signal=AuthenticitySignal.LIKELY_AUTHENTIC,
            confidence=0.78,
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            analysis_latency_ms=280.0,
            indicators=["No significant authenticity concerns detected."],
            raw_scores={"face_authenticity": 0.89, "lip_sync": 0.85, "texture": 0.91},
            consent_verified=True,
        )

    def analyze_audio(self, capture: MediaCapture) -> AuthenticityResult:
        if r := self._check_consent(capture, MediaType.AUDIO):
            return r
        url = capture.content_url or ""
        if "clone" in url.lower() or "synthetic" in url.lower():
            return AuthenticityResult(
                media_type=MediaType.AUDIO,
                signal=AuthenticitySignal.LIKELY_SYNTHETIC,
                confidence=0.75,
                provider_name=self.provider_name,
                provider_version=self.provider_version,
                analysis_latency_ms=180.0,
                indicators=[
                    "Voice spectral pattern inconsistent with natural human phonation.",
                    "Prosody patterns suggest text-to-speech synthesis.",
                ],
                raw_scores={"voice_naturalness": 0.21, "prosody": 0.19},
                consent_verified=True,
            )
        return AuthenticityResult(
            media_type=MediaType.AUDIO,
            signal=AuthenticitySignal.LIKELY_AUTHENTIC,
            confidence=0.80,
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            analysis_latency_ms=150.0,
            indicators=["Audio appears consistent with natural human speech."],
            raw_scores={"voice_naturalness": 0.88, "prosody": 0.84},
            consent_verified=True,
        )

    def analyze_image(self, capture: MediaCapture) -> AuthenticityResult:
        if r := self._check_consent(capture, MediaType.IMAGE):
            return r
        return AuthenticityResult(
            media_type=MediaType.IMAGE,
            signal=AuthenticitySignal.UNCERTAIN,
            confidence=0.55,
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            analysis_latency_ms=120.0,
            indicators=["Image analysis inconclusive — insufficient metadata for determination."],
            raw_scores={"gan_score": 0.45},
            consent_verified=True,
        )


# ─────────────────────────────────────────────────────────────
# §80: Media Authenticity Orchestrator
# ─────────────────────────────────────────────────────────────

class MediaAuthenticityOrchestrator:
    """
    §80: Orchestrates the media authenticity analysis pipeline.

    Desktop Agent → Screen/Audio Capture → Consent Gate
      → Provider → Authenticity Signals → Evidence Layer → Risk + Explanation → Alert
    """

    def __init__(self, provider: Optional[object] = None) -> None:
        self._provider = provider or UnavailableProvider()

    def analyze(self, capture: MediaCapture) -> AuthenticityResult:
        """
        Route a media capture to the appropriate provider method.
        Enforces consent gate (§35) before any analysis.
        """
        if not capture.user_consented:
            logger.warning("MediaAuthenticityOrchestrator: Analysis refused — no user consent.")
            return AuthenticityResult(
                media_type=capture.media_type,
                signal=AuthenticitySignal.UNAVAILABLE,
                confidence=0.0,
                provider_name="orchestrator",
                provider_version="0.3.0",
                analysis_latency_ms=0.0,
                error_message="User consent is required before media analysis (§35).",
                consent_verified=False,
            )

        caps = self._provider.capabilities()
        if capture.media_type == MediaType.VIDEO:
            if not caps.get("video", False):
                return self._not_capable(capture.media_type)
            return self._provider.analyze_video(capture)
        elif capture.media_type in (MediaType.AUDIO,):
            if not caps.get("audio", False):
                return self._not_capable(capture.media_type)
            return self._provider.analyze_audio(capture)
        elif capture.media_type == MediaType.IMAGE:
            if not caps.get("image", False):
                return self._not_capable(capture.media_type)
            return self._provider.analyze_image(capture)
        else:
            return self._not_capable(capture.media_type)

    def _not_capable(self, media_type: MediaType) -> AuthenticityResult:
        return AuthenticityResult(
            media_type=media_type,
            signal=AuthenticitySignal.UNAVAILABLE,
            confidence=0.0,
            provider_name=self._provider.provider_name,
            provider_version=self._provider.provider_version,
            analysis_latency_ms=0.0,
            error_message=f"Provider '{self._provider.provider_name}' does not support {media_type.value} analysis.",
        )

    def get_risk_boost(self, result: AuthenticityResult) -> float:
        """
        Convert a media authenticity result into a risk score boost for the CECT engine.
        UNAVAILABLE = 0.0 boost (§25 Failure Handling — not penalized).
        """
        if not result.is_available:
            return 0.0
        boosts = {
            AuthenticitySignal.SYNTHETIC: 0.15,
            AuthenticitySignal.LIKELY_SYNTHETIC: 0.10,
            AuthenticitySignal.UNCERTAIN: 0.04,
            AuthenticitySignal.INCONCLUSIVE: 0.02,
            AuthenticitySignal.LIKELY_AUTHENTIC: 0.0,
            AuthenticitySignal.AUTHENTIC: 0.0,
        }
        base_boost = boosts.get(result.signal, 0.0)
        # Rule B hard cap: media signals alone cannot boost risk above 0.15
        return round(min(0.15, base_boost * result.confidence), 3)


def compute_expected_calibration_error(
    confidences: List[float], labels: List[int], n_bins: int = 10
) -> float:
    """
    Computes the Expected Calibration Error (ECE) across confidence bins.
    ECE = sum_{m=1}^M (|B_m| / N) * |acc(B_m) - conf(B_m)|
    """
    if not confidences or not labels or len(confidences) != len(labels):
        return 0.0

    n = len(confidences)
    bin_boundaries = [i / n_bins for i in range(n_bins + 1)]
    ece = 0.0

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]

        # In-bin indices
        bin_indices = [
            idx for idx, c in enumerate(confidences)
            if (bin_lower <= c < bin_upper) or (i == n_bins - 1 and bin_lower <= c <= bin_upper)
        ]

        if not bin_indices:
            continue

        bin_size = len(bin_indices)
        bin_conf = sum(confidences[idx] for idx in bin_indices) / bin_size
        bin_acc = sum(labels[idx] for idx in bin_indices) / bin_size

        ece += (bin_size / n) * abs(bin_acc - bin_conf)

    return round(ece, 4)


class ReferenceEnrollmentPolicy:
    """
    §Rule D / Phase E: Policy governing real person reference biometric enrollment.
    Default status: NOT BUILT.
    Enrollment of a real person's voice/face is opt-in, stored only as salted-HMAC
    protected templates, and requires explicit written privacy review approval.
    """
    is_built: bool = False
    status: str = "NOT_BUILT"
    governance_rule: str = (
        "Requires explicit approved written privacy review and individual opt-in. "
        "Templates must be salted-HMAC only with zero raw biometric storage (§Rule D)."
    )

    def enroll_biometric_template(self, subject_id: str, sample_bytes: bytes) -> str:
        raise NotImplementedError(
            "Biometric enrollment is NOT BUILT by default (§Rule D, Phase E). "
            "Requires approved written privacy review."
        )
