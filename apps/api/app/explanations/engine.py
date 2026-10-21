"""
LifeLens Ω — Explanation Engine
Implementation Plan §21, §22

Structure of Explanation:
1. What was checked (Company, Recruiter, Domain, Job claims, Evidence)
2. What was found (Authoritative match, discrepancies, flags)
3. Why it matters (Risk reasoning, not accusation - P1, P2)
4. What could not be verified (Missing data / unverified claims)
5. Recommended next steps (Actionable, safe verification paths)
6. Evidence Provenance Cards (Source URL, snapshot, authority, independence)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from ..models.assessment import CECTAssessment
from ..models.claim import Claim
from ..models.entity import Entity, VerificationStatus
from ..models.evidence import Evidence, SourceStatus
from ..models.request import VerificationRequest
from ..risk.engine import RiskAssessmentResult, RiskLevel


@dataclass
class EvidenceCard:
    """Provenance card for user review (§3, §13)."""
    evidence_id: str
    source_name: str
    source_type: str
    observed_value: str
    source_url: Optional[str]
    source_authority: float
    source_independence: float
    user_verifiable: bool
    verification_path: Optional[str]
    captured_at: str
    is_simulated: bool = False


@dataclass
class ExplanationReport:
    """
    Standardized explanation output conforming to §21 and §22.
    """
    risk_level: RiskLevel
    confidence: float
    confidence_label: str       # HIGH, MEDIUM, LOW

    summary_headline: str

    what_was_checked: List[str] = field(default_factory=list)
    what_was_found: List[str] = field(default_factory=list)
    why_it_matters: List[str] = field(default_factory=list)
    what_could_not_be_verified: List[str] = field(default_factory=list)
    recommended_next_steps: List[str] = field(default_factory=list)

    evidence_cards: List[EvidenceCard] = field(default_factory=list)

    disclaimer: str = (
        "Important: LifeLens Ω provides independent verification signals and reasoning. "
        "A risk signal is not automatic proof of fraud. Verify independently before sending "
        "any payment, personal information, or sensitive identity documents."
    )


class ExplanationEngine:
    """
    Generates human-readable, auditable, and actionable explanations.
    §21–§22 of the master plan.
    """

    def generate_explanation(
        self,
        request: VerificationRequest,
        claims: List[Claim],
        entities: List[Entity],
        evidence_list: List[Evidence],
        cect_assessment: CECTAssessment,
        risk_result: RiskAssessmentResult,
    ) -> ExplanationReport:
        """
        Synthesizes all pipeline outputs into a structured ExplanationReport.
        """
        # 1. Confidence Label (§20)
        conf = risk_result.confidence
        if conf >= 0.75:
            conf_label = "HIGH"
        elif conf >= 0.40:
            conf_label = "MEDIUM"
        else:
            conf_label = "LOW"

        # 2. What was checked (§21)
        what_checked = [
            f"Company Identity ({request.company_name or 'Not specified'}) against official business registries",
            f"Recruiter Details ({request.recruiter_name or 'Anonymous'} / {request.recruiter_email or 'No email'})",
            f"Domain consistency between recruiter email and official web domains",
            f"Job claims ({len(claims)} key claims extracted: compensation, visa, requirements)",
            f"Independent evidence corroboration across {len(evidence_list)} sources",
        ]

        # 3. What was found (§21)
        what_found: List[str] = []
        for mf in risk_result.mitigating_factors:
            what_found.append(f"Verified: {mf}")
        for s in risk_result.signals:
            what_found.append(f"Risk Signal ({s.severity.value}): {s.description}")

        if not what_found:
            what_found.append("No obvious anomalies or contradictions found during automated checks.")

        # 4. Why it matters (§21, P2)
        why_matters: List[str] = []
        for s in risk_result.signals:
            if s.category == "COMPANY_IDENTITY":
                why_matters.append(
                    "Company identity discrepancy makes it difficult to establish whether the organization legitimately exists or operates at the claimed location."
                )
            elif s.category == "DOMAIN":
                why_matters.append(
                    "Using a generic or mismatched domain (e.g. Gmail instead of official corporate domain) prevents verifying if the recruiter actually represents the company."
                )
            elif s.category == "PAYMENT":
                why_matters.append(
                    "Legitimate employers and authorized recruitment agencies almost never charge job seekers upfront fees for placement, equipment, or training."
                )
            elif s.category == "TRAJECTORY":
                why_matters.append(
                    "Requesting sensitive identity documents or moving off-platform before an official interview/offer is a common pattern in deceptive recruitment."
                )
            elif s.category == "VISA":
                why_matters.append(
                    "Foreign work visas require official sponsorship through government immigration portals, not informal recruiter promises."
                )

        if not why_matters:
            why_matters.append("The claims and identifiers analyzed appear coherent and align with standard recruitment practices.")

        # Remove duplicates while preserving order
        why_matters = list(dict.fromkeys(why_matters))

        # 5. What could not be verified (§21)
        could_not_verify: List[str] = []
        company_entity = next((e for e in entities if e.entity_type == "COMPANY"), None)
        if company_entity and company_entity.verification_status in (VerificationStatus.UNKNOWN, VerificationStatus.UNAVAILABLE):
            could_not_verify.append("Official company registration in the target jurisdiction")
        if not request.recruiter_email or "@" not in request.recruiter_email:
            could_not_verify.append("Recruiter corporate email address (none provided)")
        
        for c in claims:
            if c.verification_status == VerificationStatus.UNKNOWN:
                could_not_verify.append(f"Independent backing for claim: '{c.claim_text}'")

        if not could_not_verify:
            could_not_verify.append("All primary submitted claims were covered by available verification checks.")

        # 6. Recommended Next Steps (§21, §22)
        next_steps: List[str] = []
        if risk_result.risk_level in (RiskLevel.CRITICAL, RiskLevel.HIGH):
            next_steps.append("DO NOT transfer funds, purchase equipment, or provide banking/passport details.")
            next_steps.append("Navigate independently to the company's verified website (not via links in message) to check careers pages.")
            next_steps.append("Contact the company's HR department directly using contact info from their verified domain.")
        elif risk_result.risk_level == RiskLevel.MEDIUM:
            next_steps.append("Request a formal email confirmation from the recruiter's official company email domain.")
            next_steps.append("Verify the specific job posting on the company's official careers portal.")
        else:
            next_steps.append("Proceed with normal review and standard recruitment process.")

        # 7. Evidence Cards (§13)
        cards: List[EvidenceCard] = []
        for ev in evidence_list:
            cards.append(EvidenceCard(
                evidence_id=ev.evidence_id,
                source_name=ev.source_name,
                source_type=ev.source_type,
                observed_value=ev.observed_value,
                source_url=ev.source_url,
                source_authority=ev.source_authority,
                source_independence=ev.source_independence,
                user_verifiable=ev.user_verifiable,
                verification_path=ev.verification_path,
                captured_at=ev.captured_at.isoformat() if hasattr(ev.captured_at, 'isoformat') else str(ev.captured_at),
                is_simulated=getattr(ev, 'is_simulated', False),
            ))

        # Headline
        if risk_result.risk_level == RiskLevel.CRITICAL:
            headline = "CRITICAL RISK: Major inconsistencies and high-risk demands detected."
        elif risk_result.risk_level == RiskLevel.HIGH:
            headline = "HIGH RISK: Key claims and recruiter identity lack independent verification."
        elif risk_result.risk_level == RiskLevel.MEDIUM:
            headline = "CAUTION: Some signals warrant additional manual verification."
        else:
            headline = "VERIFIED: Key claims and company presence are well-supported."

        return ExplanationReport(
            risk_level=risk_result.risk_level,
            confidence=risk_result.confidence,
            confidence_label=conf_label,
            summary_headline=headline,
            what_was_checked=what_checked,
            what_was_found=what_found,
            why_it_matters=why_matters,
            what_could_not_be_verified=could_not_verify,
            recommended_next_steps=next_steps,
            evidence_cards=cards,
        )
