"""
LifeLens Ω — Verification Orchestrator
Implementation Plan §59, §42

Orchestrates:
  1. Entity normalization (§29)
  2. Company lookup via adapter (§59)
  3. Domain comparison (§26)
  4. Evidence ledger construction (§13)
  5. Source provenance + timestamping
  6. Failure handling (§25)
  7. Cache (ASSUMPTION: simple in-process dict cache — Phase 1 minimum)

Returns: list[Evidence] ready for the CECT engine.
"""
from __future__ import annotations
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from ..models.entity import Entity, VerificationStatus
from ..models.evidence import Evidence, SourceStatus
from ..models.request import VerificationRequest
from ..services.normalizer import normalize_company_name, extract_domain
from .adapter import VerificationResult
from .companies_house import CompaniesHouseAdapter
from .us_sec import USSecAdapter
from .india_mca import IndiaMcaAdapter
from .uae_ner import UaeNerAdapter
from .domain import DomainVerifier, DomainMatchStatus
from .circuit_breaker import CircuitBreaker, CircuitBreakerOpenException

logger = logging.getLogger(__name__)


class VerificationOrchestrator:
    """
    Orchestrates all Phase-1 verification steps for a VerificationRequest.
    §59 of the implementation plan.
    """

    def __init__(self) -> None:
        self._registry_adapters = [
            CompaniesHouseAdapter(),
            USSecAdapter(),
            IndiaMcaAdapter(),
            UaeNerAdapter(),
        ]
        self._domain_verifier = DomainVerifier()
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}

    def get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        if service_name not in self._circuit_breakers:
            self._circuit_breakers[service_name] = CircuitBreaker(service_name)
        return self._circuit_breakers[service_name]

    def verify(
        self,
        request: VerificationRequest,
        entities: List[Entity],
        claims: Optional[List[Claim]] = None,
    ) -> List[Evidence]:
        """Convenience method accepting entities and claims lists."""
        company_entity = next((e for e in entities if e.entity_type == "COMPANY"), None)
        if not company_entity:
            company_entity = entities[0] if entities else Entity()
        return self.run(request, company_entity)

    def run(
        self, request: VerificationRequest, company_entity: Entity
    ) -> List[Evidence]:
        """
        Run the full Phase-1 verification pipeline.
        Returns a list of Evidence objects for the evidence ledger (§13).
        """
        evidence_list: List[Evidence] = []

        # ---------------------------------------------------------------
        # 1. Company registry lookup
        # ---------------------------------------------------------------
        country = request.claimed_country or ""
        adapter = self._select_adapter(country)
        if adapter:
            company_name = request.company_name or ""
            cb = self.get_circuit_breaker(adapter.name)
            cache_key = f"{adapter.name}|{normalize_company_name(company_name)}"
            result = cb.get_cached(cache_key)

            if result is None:
                try:
                    result = cb.call(adapter.verify_company, company_name)
                    cb.set_cache(cache_key, result)
                except CircuitBreakerOpenException as cbe:
                    logger.warning("Circuit breaker OPEN for adapter %s: %s", adapter.name, cbe)
                    result = VerificationResult(
                        adapter_name=adapter.name,
                        query=company_name,
                        source=getattr(adapter, "source_name", adapter.name),
                        status=SourceStatus.UNAVAILABLE,
                        found=False,
                    )
                except Exception as exc:
                    logger.warning("Adapter %s call failed: %s", adapter.name, exc)
                    result = VerificationResult(
                        adapter_name=adapter.name,
                        query=company_name,
                        source=getattr(adapter, "source_name", adapter.name),
                        status=SourceStatus.UNAVAILABLE,
                        found=False,
                    )

            evidence_list.append(self._registry_result_to_evidence(result, company_name))

            # Update entity status
            self._update_entity_from_registry(company_entity, result)
        else:
            # No adapter for this country — document it transparently
            evidence_list.append(Evidence(
                evidence_id=str(uuid.uuid4()),
                source_type="REGISTRY",
                source_name="No registry adapter available",
                observed_value=(
                    f"No authoritative company registry adapter is available "
                    f"for country: '{country or 'unspecified'}'. "
                    f"This does NOT indicate fraud — it means verification is limited."
                ),
                captured_at=datetime.now(timezone.utc),
                source_authority=0.0,
                source_independence=1.0,
                user_verifiable=False,
                evidence_strength=0.0,
                source_status=SourceStatus.NOT_APPLICABLE,
            ))

        # ---------------------------------------------------------------
        # 2. Domain comparison (§26)
        # ---------------------------------------------------------------
        domain_result = self._domain_verifier.compare(
            official_website=request.company_website,
            recruiter_email=request.recruiter_email,
            job_posting_url=None,
        )

        official_domain = extract_domain(request.company_website)
        https_status = (
            self._domain_verifier.check_https(request.company_website)
            if request.company_website else None
        )

        evidence_list.append(Evidence(
            evidence_id=str(uuid.uuid4()),
            source_type="DOMAIN",
            source_name="Domain Comparison Engine",
            source_url=request.company_website,
            observed_value=domain_result.mismatch_description,
            captured_at=datetime.now(timezone.utc),
            source_authority=0.7,
            source_independence=1.0,  # automated check — independent of recruiter
            user_verifiable=True,
            verification_path=(
                f"You can verify the official company domain at: {request.company_website}"
                if request.company_website else None
            ),
            evidence_strength=1.0 - domain_result.signal_strength,
            source_status=(
                SourceStatus.AVAILABLE
                if domain_result.domain_match_status != DomainMatchStatus.INSUFFICIENT_DATA
                else SourceStatus.NOT_APPLICABLE
            ),
        ))

        return evidence_list

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _select_adapter(self, country: str):
        """Select the first adapter that supports the given country."""
        for adapter in self._registry_adapters:
            if adapter.supports(country):
                return adapter
        return None

    def _registry_result_to_evidence(
        self, result: VerificationResult, queried_name: str
    ) -> Evidence:
        """Convert a VerificationResult to an Evidence object."""
        if result.found:
            status = result.result_data.get("company_status", "unknown")
            observed = (
                f"Company '{result.result_data.get('company_name', queried_name)}' "
                f"found in {result.source}. "
                f"Status: {status}. "
                f"Company number: {result.result_data.get('company_number', 'N/A')}."
            )
            strength = 0.9 if status == "active" else 0.5
        elif result.error_type == "NOT_FOUND":
            observed = (
                f"Company '{queried_name}' was not found in {result.source}. "
                f"This is a risk signal — the company may not be registered, "
                f"or may be registered in a different country/registry."
            )
            strength = 0.1
        else:
            # Technical failure — do NOT accuse (§25)
            observed = (
                f"Company verification could not be completed. "
                f"Reason: {result.error or 'source unavailable'}. "
                f"This does NOT indicate fraud — it means the registry was temporarily unreachable."
            )
            strength = 0.0

        simulated = getattr(result, "is_simulated", False)
        final_strength = 0.0 if simulated else (strength * result.confidence if result.found else strength)

        return Evidence(
            evidence_id=str(uuid.uuid4()),
            source_type="REGISTRY",
            source_name=result.source,
            source_url=result.source_url,
            observed_value=observed,
            captured_at=result.timestamp,
            source_authority=0.0 if simulated else 0.95,         # simulated mock carries zero authority
            source_independence=0.0 if simulated else 1.0,
            user_verifiable=True,
            verification_path=result.verification_path,
            evidence_strength=final_strength,
            is_simulated=simulated,
            source_status=result.status,
        )

    def _update_entity_from_registry(
        self, entity: Entity, result: VerificationResult
    ) -> None:
        """Update entity verification_status based on registry result."""
        simulated = getattr(result, "is_simulated", False)
        if simulated:
            # Deterministic mocks/fallbacks do not grant genuine verified status
            entity.verification_status = VerificationStatus.UNKNOWN
            entity.verification_confidence = 0.0
            return

        if result.found:
            status = result.result_data.get("company_status", "unknown")
            if status == "active":
                entity.verification_status = VerificationStatus.VERIFIED
                entity.verification_confidence = result.confidence
            elif status in ("dissolved", "liquidation", "administration"):
                entity.verification_status = VerificationStatus.CONTRADICTED
                entity.verification_confidence = result.confidence
            else:
                entity.verification_status = VerificationStatus.PARTIALLY_VERIFIED
                entity.verification_confidence = result.confidence * 0.5
        elif result.error_type == "NOT_FOUND":
            entity.verification_status = VerificationStatus.UNKNOWN
            entity.verification_confidence = 0.0
        else:
            # Technical failure: UNAVAILABLE — not fraud (§10, §25)
            entity.verification_status = VerificationStatus.UNAVAILABLE
            entity.verification_confidence = 0.0
