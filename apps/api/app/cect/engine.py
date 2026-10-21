"""
LifeLens Ω — CECT Pipeline Engine
Implementation Plan §42, §60

Pipeline order (§42, §60):
  Raw Job / Recruiter Data
    → Normalization
    → Claim Extraction
    → Evidence Collection
    → Evidence Source Classification
    → Coherence Analysis         (C)
    → Evidence Independence      (E)
    → Consistency Analysis       (C2)
    → Trajectory Analysis        (T)
    → CECT Assessment
    → Risk Engine
    → Confidence Engine
    → Explanation Engine

Implementation order (§60): Coherence → Evidence Indep. → Consistency → Trajectory
Do NOT build an advanced ML model before the deterministic layer works (§60).
"""
from __future__ import annotations
import logging
import uuid
from typing import List

from ..models.assessment import CECTAssessment
from ..models.claim import Claim
from ..models.entity import Entity
from ..models.evidence import Evidence
from ..models.request import VerificationRequest
from .coherence import CoherenceEngine
from .independence import EvidenceIndependenceEngine
from .consistency import ConsistencyEngine
from .trajectory import TrajectoryEngine

logger = logging.getLogger(__name__)

CECT_VERSION = "0.1.0"


class CECTEngine:
    """
    CECT reasoning pipeline orchestrator.
    §42 of the implementation plan.

    Runs in order: C → E → C → T (§60).
    """

    def __init__(self) -> None:
        self._coherence = CoherenceEngine()
        self._independence = EvidenceIndependenceEngine()
        self._consistency = ConsistencyEngine()
        self._trajectory = TrajectoryEngine()

    def analyze(
        self,
        request: VerificationRequest,
        claims: List[Claim],
        entities: List[Entity],
        evidence_list: List[Evidence],
    ) -> CECTAssessment:
        """
        Run the full CECT analysis.
        Returns a CECTAssessment (§15).
        """
        company_entity = next(
            (e for e in entities if e.entity_type == "COMPANY"),
            entities[0] if entities else Entity(),
        )

        # ---------------------------------------------------------------
        # C — Coherence (§43–44)
        # ---------------------------------------------------------------
        coherence_result = self._coherence.analyze(claims, entities)
        logger.info("CECT Coherence score: %.3f", coherence_result.score)

        # ---------------------------------------------------------------
        # E — Evidence Independence (§45)
        # ---------------------------------------------------------------
        independence_result = self._independence.analyze(evidence_list)
        logger.info("CECT Evidence Independence score: %.3f", independence_result.score)

        # ---------------------------------------------------------------
        # C — Consistency (§46)
        # ---------------------------------------------------------------
        consistency_result = self._consistency.analyze(request, company_entity, evidence_list)
        logger.info("CECT Consistency score: %.3f", consistency_result.score)

        # ---------------------------------------------------------------
        # T — Trajectory (§47)
        # ---------------------------------------------------------------
        trajectory_result = self._trajectory.analyze(claims)
        logger.info("CECT Trajectory score: %.3f", trajectory_result.score)

        # ---------------------------------------------------------------
        # Confidence (§20) — separate from risk, based on evidence completeness
        # ---------------------------------------------------------------
        available_evidence = [
            e for e in evidence_list
            if e.source_status.value not in ("UNAVAILABLE", "NOT_APPLICABLE")
        ]
        evidence_completeness = min(1.0, len(available_evidence) / max(1, len(evidence_list)))
        data_quality = (
            (consistency_result.score + independence_result.score) / 2
        ) if evidence_list else 0.0
        confidence = round((evidence_completeness * 0.5 + data_quality * 0.5), 3)

        # ---------------------------------------------------------------
        # Aggregate findings
        # ---------------------------------------------------------------
        all_findings: List[str] = (
            coherence_result.findings
            + independence_result.findings
            + consistency_result.findings
            + trajectory_result.findings
        )

        supporting_ids = independence_result.high_independence_evidence_ids
        contradicting_ids = independence_result.low_independence_evidence_ids

        return CECTAssessment(
            coherence_score=coherence_result.score,
            evidence_independence_score=independence_result.score,
            consistency_score=consistency_result.score,
            trajectory_score=trajectory_result.score,
            confidence=confidence,
            findings=all_findings,
            supporting_evidence_ids=supporting_ids,
            contradicting_evidence_ids=contradicting_ids,
        )
