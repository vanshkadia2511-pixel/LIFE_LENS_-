"""
LifeLens Ω — CECTAssessment
Implementation Plan §15

C = Coherence
E = Evidence Independence
C = Consistency
T = Trajectory
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class CECTAssessment:
    """
    Output of the CECT reasoning engine.
    §15 of the implementation plan.

    NOTE: confidence is separate from the individual CECT scores.
    confidence represents how complete/reliable the evidence is,
    NOT the same as risk level (§20).
    """
    coherence_score: float = 0.0            # 0.0 – 1.0
    evidence_independence_score: float = 0.0  # 0.0 – 1.0
    consistency_score: float = 0.0          # 0.0 – 1.0
    trajectory_score: float = 0.0          # 0.0 – 1.0

    confidence: float = 0.0                # overall confidence in the assessment

    findings: List[str] = field(default_factory=list)

    supporting_evidence_ids: List[str] = field(default_factory=list)
    contradicting_evidence_ids: List[str] = field(default_factory=list)
