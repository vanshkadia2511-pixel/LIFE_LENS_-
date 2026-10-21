"""
LifeLens Ω — Risk Engine
Implementation Plan §16, §17, §18, §19, §20

Features:
- Configurable signals loaded from YAML (§16.1)
- RiskSignal generation (§17)
- Risk calculation with severity, reliability, evidence strength (§18)
- Distinct RiskLevel (LOW, MEDIUM, HIGH, CRITICAL) (§19)
- Confidence calculated separately from Risk (§20)
- Provenance linked to Evidence ledger (§13)
"""
from __future__ import annotations
import os
import yaml
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..models.signal import RiskSignal, Severity
from ..models.claim import Claim, ClaimType
from ..models.evidence import Evidence, SourceStatus
from ..models.entity import Entity, VerificationStatus
from ..models.assessment import CECTAssessment
from ..models.request import VerificationRequest

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent / "signals_config.yaml"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class RiskAssessmentResult:
    """
    Combined result from the Risk Engine.
    §18, §19, §20 of the implementation plan.
    """
    risk_level: RiskLevel
    risk_score: float                   # 0.0 – 1.0 (calibrated aggregate)
    confidence: float                   # 0.0 – 1.0 (separate from risk score)
    signals: List[RiskSignal] = field(default_factory=list)
    primary_concerns: List[str] = field(default_factory=list)
    mitigating_factors: List[str] = field(default_factory=list)
    config_version: str = "0.1.0"


class RiskEngine:
    """
    Evaluates risk signals and computes calibrated risk and confidence.
    §16–§20 of the master plan.
    """

    def __init__(self, config_file: Optional[Path] = None) -> None:
        self.config_path = config_file or CONFIG_PATH
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Loads signals configuration from YAML."""
        if not self.config_path.exists():
            logger.warning("Signals config file not found at %s. Using default signals.", self.config_path)
            return {"version": "0.1.0", "signals": {}}
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {"version": "0.1.0", "signals": {}}
        except Exception as e:
            logger.error("Error reading signals config: %s", e)
            return {"version": "0.1.0", "signals": {}}

    def evaluate(
        self,
        request: VerificationRequest,
        claims: List[Claim],
        entities: List[Entity],
        evidence_list: List[Evidence],
        cect_assessment: CECTAssessment,
    ) -> RiskAssessmentResult:
        """
        Executes risk evaluation pipeline.
        Returns RiskAssessmentResult.
        """
        signals: List[RiskSignal] = []
        mitigating_factors: List[str] = []
        signal_configs = self.config.get("signals", {})
        config_version = self.config.get("version", "0.1.0")

        # -------------------------------------------------------------
        # 1. Company Identity Signals
        # -------------------------------------------------------------
        company_entity = next((e for e in entities if e.entity_type == "COMPANY"), None)
        if company_entity:
            if company_entity.verification_status == VerificationStatus.CONTRADICTED:
                cfg = signal_configs.get("company_dissolved", {})
                signals.append(RiskSignal(
                    signal_id=f"sig-comp-dissolved-{len(signals)+1}",
                    category=cfg.get("category", "COMPANY_IDENTITY"),
                    description=cfg.get("description", "Company is listed as dissolved/inactive in registry."),
                    severity=Severity.HIGH,
                    reliability=0.95,
                    evidence_ids=[e.evidence_id for e in evidence_list if e.source_type == "BUSINESS_REGISTRY"],
                    detected_by="RiskEngine.CompanyCheck"
                ))
            elif company_entity.verification_status == VerificationStatus.UNKNOWN:
                cfg = signal_configs.get("company_not_found", {})
                signals.append(RiskSignal(
                    signal_id=f"sig-comp-notfound-{len(signals)+1}",
                    category=cfg.get("category", "COMPANY_IDENTITY"),
                    description=cfg.get("description", "Company could not be found in authoritative registry."),
                    severity=Severity.HIGH,
                    reliability=0.85,
                    evidence_ids=[e.evidence_id for e in evidence_list if e.source_type == "BUSINESS_REGISTRY"],
                    detected_by="RiskEngine.CompanyCheck"
                ))
            elif company_entity.verification_status == VerificationStatus.VERIFIED:
                mitigating_factors.append("Company is officially registered in authoritative government registry.")

        # -------------------------------------------------------------
        # 2. Domain & Email Mismatch Signals
        # -------------------------------------------------------------
        domain_evidence = [e for e in evidence_list if e.source_type in ("DOMAIN", "DOMAIN_REGISTRY")]
        for dev in domain_evidence:
            obs = dev.observed_value or ""
            if "not a domain mismatch" in obs.lower() or "staffing agency" in obs.lower() or "recruitment agency" in obs.lower():
                mitigating_factors.append(obs)
            elif "MISMATCH" in obs or "does not match" in obs:
                cfg = signal_configs.get("official_domain_mismatch", {})
                signals.append(RiskSignal(
                    signal_id=f"sig-domain-mismatch-{len(signals)+1}",
                    category=cfg.get("category", "DOMAIN"),
                    description=cfg.get("description", "Recruiter email domain does not match official domain."),
                    severity=Severity.MEDIUM,
                    reliability=0.90,
                    evidence_ids=[dev.evidence_id],
                    detected_by="RiskEngine.DomainCheck"
                ))
            elif "MATCH" in obs or "matches the official" in obs:
                mitigating_factors.append("Recruiter email domain matches the official company domain.")

        # -------------------------------------------------------------
        # 3. High-Risk Claim Signals (Payment, Documents, Urgency, Off-Platform)
        # -------------------------------------------------------------
        for claim in claims:
            if claim.claim_type == ClaimType.PAYMENT:
                cfg = signal_configs.get("upfront_payment_request", {})
                signals.append(RiskSignal(
                    signal_id=f"sig-payment-{len(signals)+1}",
                    category=cfg.get("category", "PAYMENT"),
                    description=cfg.get("description", "Request for upfront payment, training fee, or deposit."),
                    severity=Severity.CRITICAL,
                    reliability=0.95,
                    evidence_ids=claim.supporting_evidence_ids,
                    detected_by="RiskEngine.ClaimAnalysis"
                ))
            elif claim.claim_type == ClaimType.DOCUMENT:
                cfg = signal_configs.get("sensitive_document_request", {})
                signals.append(RiskSignal(
                    signal_id=f"sig-doc-{len(signals)+1}",
                    category=cfg.get("category", "TRAJECTORY"),
                    description=cfg.get("description", "Recruiter is requesting sensitive personal documents."),
                    severity=Severity.HIGH,
                    reliability=0.85,
                    evidence_ids=claim.supporting_evidence_ids,
                    detected_by="RiskEngine.ClaimAnalysis"
                ))
            elif claim.claim_type == ClaimType.URGENCY:
                cfg = signal_configs.get("urgency_pressure", {})
                signals.append(RiskSignal(
                    signal_id=f"sig-urgency-{len(signals)+1}",
                    category=cfg.get("category", "TRAJECTORY"),
                    description=cfg.get("description", "High urgency or pressure to act quickly without review."),
                    severity=Severity.MEDIUM,
                    reliability=0.80,
                    evidence_ids=claim.supporting_evidence_ids,
                    detected_by="RiskEngine.ClaimAnalysis"
                ))
            elif claim.claim_type == ClaimType.CONTACT:
                if any(kw in claim.claim_text.lower() for kw in ["telegram", "whatsapp", "move to", "off-platform", "personal email"]):
                    cfg = signal_configs.get("off_platform_move", {})
                    signals.append(RiskSignal(
                        signal_id=f"sig-offplatform-{len(signals)+1}",
                        category=cfg.get("category", "TRAJECTORY"),
                        description=cfg.get("description", "Recruiter asking to move communication off official platform."),
                        severity=Severity.MEDIUM,
                        reliability=0.80,
                        evidence_ids=claim.supporting_evidence_ids,
                        detected_by="RiskEngine.ClaimAnalysis"
                    ))
            elif claim.claim_type == ClaimType.VISA:
                if claim.verification_status == VerificationStatus.UNKNOWN:
                    cfg = signal_configs.get("visa_claim_unverified", {})
                    signals.append(RiskSignal(
                        signal_id=f"sig-visa-unverified-{len(signals)+1}",
                        category=cfg.get("category", "VISA"),
                        description=cfg.get("description", "Foreign visa sponsorship claimed without authoritative backing."),
                        severity=Severity.MEDIUM,
                        reliability=0.75,
                        evidence_ids=claim.supporting_evidence_ids,
                        detected_by="RiskEngine.ClaimAnalysis"
                    ))

        # -------------------------------------------------------------
        # 4. Risk Score Calculation (§18)
        # -------------------------------------------------------------
        # Severity weights: CRITICAL=0.45, HIGH=0.25, MEDIUM=0.12, LOW=0.04
        severity_multiplier = {
            Severity.CRITICAL: 0.45,
            Severity.HIGH: 0.25,
            Severity.MEDIUM: 0.12,
            Severity.LOW: 0.04,
        }

        total_risk_contribution = 0.0
        for s in signals:
            mult = severity_multiplier.get(s.severity, 0.10)
            # Risk = Severity * Reliability
            total_risk_contribution += mult * s.reliability

        # Factor in CECT inconsistency / lack of evidence independence
        cect_risk_penalty = (1.0 - cect_assessment.coherence_score) * 0.15 + \
                            (1.0 - cect_assessment.consistency_score) * 0.20 + \
                            (1.0 - cect_assessment.evidence_independence_score) * 0.10 + \
                            (1.0 - cect_assessment.trajectory_score) * 0.15

        raw_risk = total_risk_contribution + cect_risk_penalty
        risk_score = min(1.0, max(0.0, round(raw_risk, 3)))

        # -------------------------------------------------------------
        # 5. Risk Level Mapping (§19)
        # -------------------------------------------------------------
        has_critical_signal = any(s.severity == Severity.CRITICAL for s in signals)
        has_high_signal = any(s.severity == Severity.HIGH for s in signals)
        has_medium_signal = any(s.severity == Severity.MEDIUM for s in signals)

        if has_critical_signal or risk_score >= 0.70:
            risk_level = RiskLevel.CRITICAL if (has_critical_signal or risk_score >= 0.85) else RiskLevel.HIGH
        elif has_high_signal or risk_score >= 0.45:
            risk_level = RiskLevel.HIGH
        elif has_medium_signal or risk_score >= 0.20:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        # -------------------------------------------------------------
        # 6. Confidence (§20)
        # -------------------------------------------------------------
        # Computed from CECT confidence and completeness of evidence
        confidence = cect_assessment.confidence

        # -------------------------------------------------------------
        # 7. Primary Concerns
        # -------------------------------------------------------------
        primary_concerns = [s.description for s in signals]
        if not primary_concerns and risk_score < 0.3:
            primary_concerns.append("No critical risk patterns or unverified claims detected.")

        return RiskAssessmentResult(
            risk_level=risk_level,
            risk_score=risk_score,
            confidence=confidence,
            signals=signals,
            primary_concerns=primary_concerns,
            mitigating_factors=mitigating_factors,
            config_version=config_version,
        )
