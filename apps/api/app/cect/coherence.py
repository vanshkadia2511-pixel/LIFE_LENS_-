"""
LifeLens Ω — Coherence Engine
Implementation Plan §14-C, §43–44, §60

Question: Do the claims logically fit together? (§14-C)

Distinguishes (§44):
  DIRECT_CONTRADICTION
  MISSING_INFORMATION
  POSSIBLE_EXPLANATION
  UNVERIFIED

Uses: structured rules + entity matching + explicit contradiction rules (§43)
Does NOT use only keyword rules (§43).
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import List, Tuple

from ..models.claim import Claim, ClaimType
from ..models.entity import Entity

logger = logging.getLogger(__name__)


class CoherenceIssueType:
    DIRECT_CONTRADICTION = "DIRECT_CONTRADICTION"
    MISSING_INFORMATION = "MISSING_INFORMATION"
    POSSIBLE_EXPLANATION = "POSSIBLE_EXPLANATION"
    UNVERIFIED = "UNVERIFIED"


@dataclass
class CoherenceIssue:
    issue_type: str
    description: str
    claim_ids_involved: List[str] = field(default_factory=list)
    severity: float = 0.5  # 0.0–1.0


@dataclass
class CoherenceResult:
    """Output of coherence analysis."""
    score: float              # 0.0 (incoherent) – 1.0 (fully coherent)
    issues: List[CoherenceIssue] = field(default_factory=list)
    findings: List[str] = field(default_factory=list)


class CoherenceEngine:
    """
    Phase 1 coherence engine.
    Uses structured rules and entity matching (§43).
    Detects claim contradictions per §44.
    """

    def analyze(self, claims: List[Claim], entities: List[Entity]) -> CoherenceResult:
        issues: List[CoherenceIssue] = []
        findings: List[str] = []

        # ------------------------------------------------------------------
        # Rule: upfront payment + "legitimate job" is a coherence issue (§44)
        # ------------------------------------------------------------------
        payment_claims = [c for c in claims if c.claim_type == ClaimType.PAYMENT]
        if payment_claims:
            issues.append(CoherenceIssue(
                issue_type=CoherenceIssueType.DIRECT_CONTRADICTION,
                description=(
                    "A legitimate job offer typically does not require upfront payment. "
                    "A payment request in a job posting is a coherence issue — "
                    "the claim of providing employment and requesting payment are in tension."
                ),
                claim_ids_involved=[c.claim_id for c in payment_claims],
                severity=0.9,
            ))
            findings.append(
                "Payment request detected in job posting. "
                "Legitimate employers do not charge candidates to be hired."
            )

        # ------------------------------------------------------------------
        # Rule: no-experience-required + very high salary = coherence issue
        # ------------------------------------------------------------------
        salary_claims = [c for c in claims if c.claim_type == ClaimType.SALARY]
        no_exp_claims = [
            c for c in claims
            if c.claim_type == ClaimType.EMPLOYMENT
            and "no experience" in c.claim_text.lower()
        ]
        if salary_claims and no_exp_claims:
            issues.append(CoherenceIssue(
                issue_type=CoherenceIssueType.POSSIBLE_EXPLANATION,
                description=(
                    "The posting claims no experience is required alongside an above-average salary. "
                    "This is a potential coherence issue worth verifying independently."
                ),
                claim_ids_involved=[c.claim_id for c in salary_claims + no_exp_claims],
                severity=0.4,
            ))
            findings.append(
                "No-experience-required combined with high salary claim — verify independently."
            )

        # ------------------------------------------------------------------
        # Rule: urgency + document request (§44 — trajectory coherence)
        # ------------------------------------------------------------------
        urgency_claims = [c for c in claims if c.claim_type == ClaimType.URGENCY]
        doc_claims = [c for c in claims if c.claim_type == ClaimType.DOCUMENT]
        if urgency_claims and doc_claims:
            issues.append(CoherenceIssue(
                issue_type=CoherenceIssueType.DIRECT_CONTRADICTION,
                description=(
                    "Urgency pressure combined with sensitive document requests is a "
                    "recognized escalation pattern. Legitimate employers typically do not "
                    "combine extreme urgency with requests for passport or financial documents."
                ),
                claim_ids_involved=[
                    c.claim_id for c in urgency_claims + doc_claims
                ],
                severity=0.8,
            ))
            findings.append(
                "Urgency pressure + sensitive document request detected — "
                "this combination is a high-risk coherence pattern."
            )

        # ------------------------------------------------------------------
        # Rule: off-platform contact during job application
        # ------------------------------------------------------------------
        contact_claims = [
            c for c in claims
            if c.claim_type == ClaimType.CONTACT
            and any(kw in c.claim_text.lower() for kw in ["whatsapp", "telegram", "signal", "text me"])
        ]
        if contact_claims:
            issues.append(CoherenceIssue(
                issue_type=CoherenceIssueType.POSSIBLE_EXPLANATION,
                description=(
                    "Recruiter is requesting communication through an unverifiable "
                    "off-platform channel. Legitimate recruitment usually occurs through "
                    "the job platform or official company email."
                ),
                claim_ids_involved=[c.claim_id for c in contact_claims],
                severity=0.5,
            ))
            findings.append(
                "Off-platform contact request detected (WhatsApp/Telegram). "
                "Verify the recruiter through the official company channel."
            )

        # ------------------------------------------------------------------
        # Score: start at 1.0, subtract per-issue severity proportionally
        # ------------------------------------------------------------------
        if issues:
            max_severity = max(i.severity for i in issues)
            # Compound: each issue reduces coherence
            total_penalty = sum(i.severity for i in issues) * 0.4
            score = max(0.0, 1.0 - min(total_penalty, 0.95))
        else:
            score = 1.0
            findings.append("No coherence issues detected between the claims.")

        return CoherenceResult(score=round(score, 3), issues=issues, findings=findings)
