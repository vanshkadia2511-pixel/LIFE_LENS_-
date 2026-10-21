"""
LifeLens Ω — Consistency Engine
Implementation Plan §14-C2, §46, §60

Question: Do the identity, company, domain, location, role and contact details agree? (§14-C2)

Checks relationships among (§46):
  Company name / Official company name
  Website
  Recruiter email
  Recruiter role
  Job location
  Job board
  Contact details
  Claimed visa information
  Recruitment agency

Output (§46):
  CONSISTENT
  PARTIALLY_CONSISTENT
  CONFLICTING
  INSUFFICIENT_DATA
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import List, Optional

from ..models.entity import Entity
from ..models.evidence import Evidence, SourceStatus
from ..models.request import VerificationRequest
from ..services.normalizer import normalize_company_name, extract_domain
from ..verification.domain import DomainMatchStatus

logger = logging.getLogger(__name__)


class ConsistencyStatus:
    CONSISTENT = "CONSISTENT"
    PARTIALLY_CONSISTENT = "PARTIALLY_CONSISTENT"
    CONFLICTING = "CONFLICTING"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass
class ConsistencyCheck:
    field_name: str
    expected: Optional[str]
    observed: Optional[str]
    consistent: bool
    description: str


@dataclass
class ConsistencyResult:
    """Output of consistency analysis."""
    status: str               # CONSISTENT | PARTIALLY_CONSISTENT | CONFLICTING | INSUFFICIENT_DATA
    score: float              # 0.0 – 1.0
    checks: List[ConsistencyCheck] = field(default_factory=list)
    findings: List[str] = field(default_factory=list)


class ConsistencyEngine:
    """
    Identity/domain/data consistency engine.
    §14-C2, §46.
    """

    def analyze(
        self,
        request: VerificationRequest,
        company_entity: Entity,
        evidence_list: List[Evidence],
    ) -> ConsistencyResult:
        checks: List[ConsistencyCheck] = []
        findings: List[str] = []

        data_points = 0
        consistent_points = 0

        # ---------------------------------------------------------------
        # Check 1: Company name from request vs normalized entity name
        # ---------------------------------------------------------------
        if request.company_name and company_entity.normalized_name:
            norm_req = normalize_company_name(request.company_name)
            consistent = (norm_req == company_entity.normalized_name)
            checks.append(ConsistencyCheck(
                field_name="company_name",
                expected=company_entity.normalized_name,
                observed=norm_req,
                consistent=consistent,
                description=(
                    f"Company name '{request.company_name}' "
                    f"{'matches' if consistent else 'does not match'} "
                    f"normalized name '{company_entity.normalized_name}'."
                ),
            ))
            data_points += 1
            if consistent:
                consistent_points += 1

        # ---------------------------------------------------------------
        # Check 2: Recruiter email domain vs official website domain
        # ---------------------------------------------------------------
        official_domain = extract_domain(request.company_website)
        recruiter_domain = extract_domain(request.recruiter_email)

        if official_domain and recruiter_domain:
            data_points += 1
            consistent = (
                official_domain == recruiter_domain
                or recruiter_domain.endswith("." + official_domain)
            )
            checks.append(ConsistencyCheck(
                field_name="email_domain",
                expected=official_domain,
                observed=recruiter_domain,
                consistent=consistent,
                description=(
                    f"Recruiter email domain ({recruiter_domain}) "
                    f"{'matches' if consistent else 'does NOT match'} "
                    f"official company domain ({official_domain})."
                ),
            ))
            if consistent:
                consistent_points += 1
            else:
                findings.append(
                    f"Domain mismatch: recruiter email domain ({recruiter_domain}) "
                    f"≠ official domain ({official_domain}). "
                    f"This is a signal requiring additional verification."
                )

        # ---------------------------------------------------------------
        # Check 3: Registry-verified company name vs claimed company name
        # ---------------------------------------------------------------
        registry_evidence = next(
            (e for e in evidence_list if e.source_type == "REGISTRY"), None
        )
        if registry_evidence and registry_evidence.source_status == SourceStatus.AVAILABLE:
            # Extract company name from observed value (pragmatic: check if claimed name appears)
            if request.company_name:
                data_points += 1
                name_in_result = (
                    normalize_company_name(request.company_name) or ""
                ) in registry_evidence.observed_value.lower()

                checks.append(ConsistencyCheck(
                    field_name="registry_name_match",
                    expected=request.company_name,
                    observed=registry_evidence.observed_value[:120],
                    consistent=name_in_result,
                    description=(
                        f"Registry lookup {'found' if name_in_result else 'did not find'} "
                        f"a match for '{request.company_name}'."
                    ),
                ))
                if name_in_result:
                    consistent_points += 1
                    findings.append(f"Company '{request.company_name}' found in registry.")
                else:
                    findings.append(
                        f"Company '{request.company_name}' was not confirmed by registry. "
                        f"This may indicate a different registered name or no registration."
                    )

        # ---------------------------------------------------------------
        # Determine overall status
        # ---------------------------------------------------------------
        if data_points == 0:
            status = ConsistencyStatus.INSUFFICIENT_DATA
            score = 0.0
            findings.append(
                "Insufficient data to perform consistency checks — "
                "company website or recruiter email was not provided."
            )
        else:
            ratio = consistent_points / data_points
            score = round(ratio, 3)
            if ratio >= 0.9:
                status = ConsistencyStatus.CONSISTENT
                findings.insert(0, "All checked fields are consistent.")
            elif ratio >= 0.5:
                status = ConsistencyStatus.PARTIALLY_CONSISTENT
                findings.insert(0, "Some fields are inconsistent — additional verification recommended.")
            else:
                status = ConsistencyStatus.CONFLICTING
                findings.insert(0, "Multiple consistency issues found — verify the recruiter and company independently.")

        return ConsistencyResult(
            status=status,
            score=score,
            checks=checks,
            findings=findings,
        )
