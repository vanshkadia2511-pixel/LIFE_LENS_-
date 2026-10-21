"""
LifeLens Ω — Verification Service Orchestrator
Implementation Plan §5, §6, §58, §59, §60

Integrates the end-to-end LifeLens Ω pipeline:
1. Normalization & Entity/Claim Extraction (§28, §29)
2. External & Authoritative Verification (§23, §24, §26)
3. CECT Reasoning Engine (§14, §15, §42)
4. Risk & Confidence Engine (§16–§20)
5. Explanation Engine (§21, §22)
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from ..models.request import VerificationRequest
from ..models.entity import Entity
from ..models.claim import Claim
from ..models.evidence import Evidence
from ..models.assessment import CECTAssessment
from ..services.extractor import ClaimExtractor
from ..services.normalizer import normalize_company_name, extract_domain
from ..verification.orchestrator import VerificationOrchestrator
from ..cect.engine import CECTEngine
from ..risk.engine import RiskEngine, RiskAssessmentResult
from ..explanations.engine import ExplanationEngine, ExplanationReport

logger = logging.getLogger(__name__)


@dataclass
class VerificationResponse:
    """
    Complete response returned by the verification pipeline.
    """
    request_id: str
    processed_at: datetime
    entities: List[Entity]
    claims: List[Claim]
    evidence_ledger: List[Evidence]
    cect_assessment: CECTAssessment
    risk_assessment: RiskAssessmentResult
    explanation: ExplanationReport


class VerificationService:
    """
    Unified high-level verification service.
    """

    def __init__(
        self,
        extractor: Optional[ClaimExtractor] = None,
        orchestrator: Optional[VerificationOrchestrator] = None,
        cect_engine: Optional[CECTEngine] = None,
        risk_engine: Optional[RiskEngine] = None,
        explanation_engine: Optional[ExplanationEngine] = None,
    ) -> None:
        self.extractor = extractor or ClaimExtractor()
        self.orchestrator = orchestrator or VerificationOrchestrator()
        self.cect_engine = cect_engine or CECTEngine()
        self.risk_engine = risk_engine or RiskEngine()
        self.explanation_engine = explanation_engine or ExplanationEngine()

    def process_verification(self, request: VerificationRequest) -> VerificationResponse:
        """
        Runs the full verification pipeline for a user request.
        """
        logger.info("Starting verification for request %s (Company: %s, Title: %s)",
                    request.request_id, request.company_name, request.job_title)

        # 1. Extraction: entities + claims (§28, §58)
        entities = self.extractor.extract_entities(request)
        claims = self.extractor.extract_claims(request, entities[0] if entities else Entity())

        # 2. External & Registry Verification (§59) -> produces Evidence Ledger
        evidence_list = self.orchestrator.verify(request, entities, claims)

        # 3. CECT Reasoning Engine (§14, §15, §42)
        cect_assessment = self.cect_engine.analyze(
            request=request,
            claims=claims,
            entities=entities,
            evidence_list=evidence_list,
        )

        # 4. Risk & Confidence Engine (§16–§20)
        risk_assessment = self.risk_engine.evaluate(
            request=request,
            claims=claims,
            entities=entities,
            evidence_list=evidence_list,
            cect_assessment=cect_assessment,
        )

        # 5. Explanation Engine (§21, §22)
        explanation = self.explanation_engine.generate_explanation(
            request=request,
            claims=claims,
            entities=entities,
            evidence_list=evidence_list,
            cect_assessment=cect_assessment,
            risk_result=risk_assessment,
        )

        return VerificationResponse(
            request_id=request.request_id,
            processed_at=datetime.now(timezone.utc),
            entities=entities,
            claims=claims,
            evidence_ledger=evidence_list,
            cect_assessment=cect_assessment,
            risk_assessment=risk_assessment,
            explanation=explanation,
        )
