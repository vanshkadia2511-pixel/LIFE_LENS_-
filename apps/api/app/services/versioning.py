"""
LifeLens Ω — Model/Rule Versioning (§73)

Every assessment must be tagged with:
    cect_version
    risk_config_version
    extraction_version
    adapter_version
    source_version

This enables reproducibility: given a request_id + version set,
the exact assessment can be replicated.
"""
from __future__ import annotations

from dataclasses import dataclass


# ─────────────────────────────────────────────────────────────
# Component versions — bump these when logic changes
# ─────────────────────────────────────────────────────────────

CECT_VERSION = "0.2.0"
RISK_CONFIG_VERSION = "0.3.2"
EXTRACTION_VERSION = "0.2.1"
ADAPTER_VERSION = "0.1.0"
SOURCE_VERSION = "0.1.0"
THREAT_INTEL_VERSION = "0.1.0"
TRAJECTORY_VERSION = "0.2.0"

# Kill-switch registry: each entry can disable a specific rule or adapter
# Without restarting the entire service (§75).
# Format: { "feature_key": True }   →  feature is ACTIVE
#          { "feature_key": False }  →  feature is DISABLED
KILL_SWITCHES: dict[str, bool] = {
    # Verification adapters
    "adapter.companies_house": True,
    "adapter.us_sec": True,
    "adapter.india_mca": True,
    "adapter.uae_ner": True,
    "adapter.domain": True,
    # CECT rules
    "rule.coherence": True,
    "rule.evidence_independence": True,
    "rule.consistency": True,
    "rule.trajectory": True,
    # Phase 2 features
    "feature.trust_graph": True,
    "feature.behavioral_baseline": True,
    "feature.community_threat_intelligence": True,
    "feature.trust_trajectory": True,
    # Risk/risk signals
    "risk.salary_signal": True,
    "risk.urgency_signal": True,
    "risk.payment_signal": True,
}


def is_feature_enabled(feature_key: str) -> bool:
    """§75: Check whether a specific rule/adapter/feature is currently enabled."""
    return KILL_SWITCHES.get(feature_key, True)


def disable_feature(feature_key: str) -> bool:
    """§75: Disable a specific rule/adapter/feature at runtime."""
    if feature_key in KILL_SWITCHES:
        KILL_SWITCHES[feature_key] = False
        try:
            from .metrics import metrics_service
            metrics_service.set_kill_switch_metric(feature_key, False)
        except Exception:
            pass
        return True
    return False


def enable_feature(feature_key: str) -> bool:
    """§75: Re-enable a previously disabled feature at runtime."""
    if feature_key in KILL_SWITCHES:
        KILL_SWITCHES[feature_key] = True
        try:
            from .metrics import metrics_service
            metrics_service.set_kill_switch_metric(feature_key, True)
        except Exception:
            pass
        return True
    return False


def list_kill_switches() -> dict[str, bool]:
    """Return current state of all kill switches."""
    return dict(KILL_SWITCHES)


@dataclass
class VersionManifest:
    """§73: Full version manifest attached to every assessment for reproducibility."""
    cect_version: str = CECT_VERSION
    risk_config_version: str = RISK_CONFIG_VERSION
    extraction_version: str = EXTRACTION_VERSION
    adapter_version: str = ADAPTER_VERSION
    source_version: str = SOURCE_VERSION
    threat_intel_version: str = THREAT_INTEL_VERSION
    trajectory_version: str = TRAJECTORY_VERSION

    def to_dict(self) -> dict:
        return {
            "cect_version": self.cect_version,
            "risk_config_version": self.risk_config_version,
            "extraction_version": self.extraction_version,
            "adapter_version": self.adapter_version,
            "source_version": self.source_version,
            "threat_intel_version": self.threat_intel_version,
            "trajectory_version": self.trajectory_version,
        }


# Singleton manifest for production use
CURRENT_VERSION_MANIFEST = VersionManifest()
