"""
LifeLens Ω — Phase 5: Unified Multi-Modal CECT Reasoner
Implements §100 (Final Unified Architecture), §101 (Mental Model), §104 (Product Definition)

Sequences reasoning through the canonical 10-step LifeLens Ω flow:
1. WHO? (Identity & Entity Normalization)
2. WHAT ARE THEY CLAIMING? (Claim Extraction)
3. WHAT EVIDENCE SUPPORTS IT? (Multi-source authoritative lookup)
4. IS THAT EVIDENCE INDEPENDENT? (Evidence Independence Scoring)
5. DO THE DETAILS AGREE? (Cross-source Coherence & Consistency)
6. IS THE INTERACTION ESCALATING? (Trust Trajectory & Meeting Alerts)
7. HOW STRONG IS THE EVIDENCE? (Evidence Ledger Strength)
8. WHAT IS THE RISK? (Risk Engine with Signal Reliability)
9. HOW CONFIDENT ARE WE? (Data Completeness & Confidence Scoring)
10. WHAT CAN THE USER VERIFY NEXT? (Explanatory safe path empowerment)
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import logging

from apps.api.app.models.request import VerificationRequest
from apps.api.app.services.verification_service import VerificationService
from apps.api.app.services.trust_graph import TrustGraphService
from apps.api.app.services.community_threat_intelligence import CommunityThreatIntelligenceService
from apps.api.app.services.meeting_shield import MeetingShieldOrchestrator
from apps.api.app.risk.engine import RiskLevel, RiskAssessmentResult

logger = logging.getLogger(__name__)


@dataclass
class UnifiedTrustVerdict:
    request_id: str
    evaluated_at: datetime
    mental_model_steps: Dict[str, Any]
    overall_risk_level: RiskLevel
    overall_confidence: float
    cect_scores: Dict[str, float]
    primary_concerns: List[str]
    supporting_evidence_count: int
    independent_evidence_ratio: float
    interaction_trajectory_status: str
    media_authenticity_status: Optional[str]
    threat_intel_match: bool
    safe_verification_next_steps: List[str]
    empowerment_guidance: str
    overall_risk_score: float = 0.0


class UnifiedCECTReasoner:
    """
    Unified Multi-modal trust reasoning engine orchestrating all LifeLens Ω modules
    into a single unified pipeline.
    """

    def __init__(
        self,
        verification_service: Optional[VerificationService] = None,
        trust_graph: Optional[TrustGraphService] = None,
        threat_intel: Optional[CommunityThreatIntelligenceService] = None,
        meeting_shield: Optional[MeetingShieldOrchestrator] = None,
    ) -> None:
        self.verif_service = verification_service or VerificationService()
        self.trust_graph = trust_graph or TrustGraphService()
        self.threat_intel = threat_intel or CommunityThreatIntelligenceService()
        self.meeting_shield = meeting_shield or MeetingShieldOrchestrator()

    def evaluate_holistic_interaction(
        self,
        request: VerificationRequest,
        meeting_session_id: Optional[str] = None,
        interaction_sequence: Optional[List[Dict[str, Any]]] = None,
    ) -> UnifiedTrustVerdict:
        """Executes the full 10-step LifeLens Ω Mental Model (§101)."""
        now = datetime.now(timezone.utc)
        
        # 1. Base Verification & CECT reasoning
        base_result = self.verif_service.process_verification(request)
        cect = base_result.cect_assessment
        risk = base_result.risk_assessment
        explanation = base_result.explanation

        # 2. Check Community Threat Intelligence (§94 Phase 3)
        threat_match = False
        threat_details = []
        company_entity = next((e for e in base_result.entities if e.entity_type == "COMPANY"), None)
        recruiter_entity = next((e for e in base_result.entities if e.entity_type == "RECRUITER"), None)

        if request.company_website:
            domain_matches = self.threat_intel.check_domain(request.company_website)
            if domain_matches:
                threat_match = True
                threat_details.append(f"Domain matched community threat patterns ({len(domain_matches)} active patterns)")
        
        signal_patterns = self.threat_intel.check_signals(
            has_upfront_fee="fee" in (request.job_description or "").lower() or "payment" in (request.job_description or "").lower(),
            domain_mismatch=bool(request.recruiter_email and request.company_website and request.recruiter_email.split("@")[-1].lower() not in request.company_website.lower()),
            unverifiable_identity=not bool(recruiter_entity),
            urgency_detected="urgent" in (request.job_description or "").lower() or "immediate" in (request.job_description or "").lower(),
        )
        if signal_patterns:
            threat_match = True
            for sp in signal_patterns:
                threat_details.append(f"Matched threat pattern {sp.pattern_id}: {sp.description}")


        # 3. Check Live Meeting Shield Signals if session linked (§94 Phase 4)
        media_status = None
        if meeting_session_id:
            session = self.meeting_shield.get_session(meeting_session_id)
            if session:
                if len(session.alerts) > 0:
                    media_status = f"ALERTS_ACTIVE ({len(session.alerts)} synthetic anomalies detected)"
                else:
                    media_status = f"CLEAN (Inspected {session.total_audio_chunks} audio, {session.total_video_chunks} video chunks)"

        # 4. Synthesize Trajectory & Composite Risk
        concerns = list(risk.primary_concerns)
        if threat_match:
            concerns.extend(threat_details)
            if risk.risk_level == RiskLevel.LOW:
                risk.risk_level = RiskLevel.MEDIUM

        # Rule B Enforcement: Media forensics (face/voice) is a LOW-WEIGHT signal with a hard cap
        # on its contribution to the final risk (max +0.15). It must never be the sole basis for a HIGH/CRITICAL result.
        MAX_MEDIA_RISK_BOOST = 0.15
        if media_status and "ALERTS_ACTIVE" in media_status:
            concerns.append("Live audio/video stream shows synthetic deepfake artifacts")
            # Cap risk score contribution
            risk.risk_score = min(1.0, round(risk.risk_score + MAX_MEDIA_RISK_BOOST, 3))
            # Rule B: Media signals alone can NEVER escalate to HIGH or CRITICAL
            if risk.risk_level == RiskLevel.LOW and risk.risk_score >= 0.40:
                risk.risk_level = RiskLevel.MEDIUM

        # 5. Build canonical 10-step mental model representation
        evidence_items = base_result.evidence_ledger
        avg_strength = sum(e.evidence_strength for e in evidence_items) / max(1, len(evidence_items))

        traj_score = cect.trajectory_score
        traj_state = "STABLE_LOW_RISK" if traj_score >= 0.75 else ("MODERATE_ESCALATION" if traj_score >= 0.45 else "HIGH_RISK_ESCALATION")

        mental_model = {
            "step_1_who": {
                "claimed_company": request.company_name,
                "claimed_recruiter": request.recruiter_name,
                "normalized_identity": company_entity.claimed_name if company_entity else request.company_name,
            },
            "step_2_claims": [c.claim_text for c in base_result.claims],
            "step_3_evidence_sources": [e.source_name for e in evidence_items],
            "step_4_evidence_independence_score": cect.evidence_independence_score,
            "step_5_details_agreement": {
                "coherence_score": cect.coherence_score,
                "consistency_score": cect.consistency_score,
            },
            "step_6_escalation_trajectory": {
                "trajectory_score": cect.trajectory_score,
                "trajectory_state": traj_state,
            },
            "step_7_evidence_strength": round(avg_strength, 2),
            "step_8_risk_level": risk.risk_level.value,
            "step_9_confidence": risk.confidence,
            "step_10_verification_actions": explanation.recommended_next_steps,
        }

        # Safe empowerment guidance (§104)
        if risk.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            empowerment = (
                "Verification indicates significant evidence gaps or contradictions. "
                "Do not submit payment, personal IDs, or wire funds. Independently contact the company via its official published registry contacts."
            )
        elif risk.risk_level == RiskLevel.MEDIUM:
            empowerment = (
                "Some claims are partially verified, but additional independent verification is recommended before proceeding with sensitive steps."
            )
        else:
            empowerment = (
                "Claims are consistent with independent public registry records. Standard caution still applies."
            )

        indep_ratio = cect.evidence_independence_score

        return UnifiedTrustVerdict(
            request_id=request.request_id,
            evaluated_at=now,
            mental_model_steps=mental_model,
            overall_risk_level=risk.risk_level,
            overall_confidence=risk.confidence,
            overall_risk_score=risk.risk_score,
            cect_scores={
                "coherence": cect.coherence_score,
                "evidence_independence": cect.evidence_independence_score,
                "consistency": cect.consistency_score,
                "trajectory": cect.trajectory_score,
            },
            primary_concerns=concerns,
            supporting_evidence_count=len(evidence_items),
            independent_evidence_ratio=indep_ratio,
            interaction_trajectory_status=traj_state,
            media_authenticity_status=media_status,
            threat_intel_match=threat_match,
            safe_verification_next_steps=explanation.recommended_next_steps,
            empowerment_guidance=empowerment,
        )


