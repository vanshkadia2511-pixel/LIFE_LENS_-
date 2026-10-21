"""
LifeLens Ω — Simulated Mock Fallback & Zero-Weight Tests
Phase A Item 3:
Asserts that every deterministic mock/fallback:
  (a) carries source="SIMULATED"
  (b) has is_simulated=True
  (c) contributes zero evidence weight (evidence_strength == 0.0)
  (d) fails if any mock result is ever returned without the simulated tag.
"""
import pytest
from apps.api.app.verification.us_sec import USSecAdapter, _KNOWN_US_CORPORATIONS
from apps.api.app.verification.india_mca import IndiaMcaAdapter, _KNOWN_INDIAN_CORPORATIONS
from apps.api.app.verification.uae_ner import UaeNerAdapter, _KNOWN_UAE_CORPORATIONS
from apps.api.app.verification.orchestrator import VerificationOrchestrator
from apps.api.app.models.request import VerificationRequest
from apps.api.app.models.entity import Entity
from apps.api.app.cect.independence import EvidenceIndependenceEngine


def test_us_sec_offline_catalog_tagged_simulated():
    adapter = USSecAdapter()
    for company_key in _KNOWN_US_CORPORATIONS:
        result = adapter.verify_company(company_key)
        assert result.found is True
        assert result.source == "SIMULATED", (
            f"Mock US SEC result for '{company_key}' must carry source='SIMULATED', got '{result.source}'"
        )
        assert result.is_simulated is True, (
            f"Mock US SEC result for '{company_key}' must have is_simulated=True"
        )
        assert result.confidence == 0.0, (
            f"Simulated result must carry 0.0 confidence, got {result.confidence}"
        )


def test_india_mca_offline_catalog_tagged_simulated():
    adapter = IndiaMcaAdapter()
    for company_key in _KNOWN_INDIAN_CORPORATIONS:
        result = adapter.verify_company(company_key)
        assert result.found is True
        assert result.source == "SIMULATED", (
            f"Mock India MCA result for '{company_key}' must carry source='SIMULATED', got '{result.source}'"
        )
        assert result.is_simulated is True, (
            f"Mock India MCA result for '{company_key}' must have is_simulated=True"
        )
        assert result.confidence == 0.0


def test_uae_ner_offline_catalog_tagged_simulated():
    adapter = UaeNerAdapter()
    for company_key in _KNOWN_UAE_CORPORATIONS:
        result = adapter.verify_company(company_key)
        assert result.found is True
        assert result.source == "SIMULATED", (
            f"Mock UAE NER result for '{company_key}' must carry source='SIMULATED', got '{result.source}'"
        )
        assert result.is_simulated is True, (
            f"Mock UAE NER result for '{company_key}' must have is_simulated=True"
        )
        assert result.confidence == 0.0


def test_orchestrator_assigns_zero_weight_to_simulated_evidence():
    orchestrator = VerificationOrchestrator()
    # Test with Google (in US SEC offline catalog)
    req = VerificationRequest(
        request_id="test-sim-001",
        company_name="Google",
        claimed_country="US",
        company_website="https://google.com",
    )
    company_ent = Entity(entity_id="ent-001", entity_type="COMPANY", normalized_name="google")
    evidence_list = orchestrator.run(req, company_ent)

    sim_ev = next((e for e in evidence_list if e.source_name == "SIMULATED"), None)
    assert sim_ev is not None, "Expected simulated registry evidence for mock catalog lookup"
    assert sim_ev.is_simulated is True
    assert sim_ev.evidence_strength == 0.0, (
        f"Simulated evidence must have evidence_strength=0.0, got {sim_ev.evidence_strength}"
    )
    assert sim_ev.source_authority == 0.0, (
        f"Simulated evidence must have source_authority=0.0, got {sim_ev.source_authority}"
    )
    # Ensure entity was NOT marked VERIFIED from simulated evidence
    assert company_ent.verification_status.value != "VERIFIED"


def test_cect_independence_zero_weight_for_simulated():
    orchestrator = VerificationOrchestrator()
    req = VerificationRequest(
        request_id="test-sim-002",
        company_name="Infosys",
        claimed_country="IN",
        company_website="https://infosys.com",
    )
    company_ent = Entity(entity_id="ent-002", entity_type="COMPANY", normalized_name="infosys")
    evidence_list = orchestrator.run(req, company_ent)

    independence_engine = EvidenceIndependenceEngine()
    ind_result = independence_engine.analyze(evidence_list)

    # Check that any simulated evidence id is not counted as high independence
    sim_ev = next(e for e in evidence_list if e.is_simulated)
    assert sim_ev.evidence_id not in ind_result.high_independence_evidence_ids
    assert sim_ev.evidence_id in ind_result.low_independence_evidence_ids
    assert any("SIMULATED" in f for f in ind_result.findings)


def test_assertion_fails_if_mock_shown_without_tag():
    """Fails if any simulated result is created with is_simulated=False."""
    adapter = USSecAdapter()
    result = adapter.verify_company("Google")
    # Strict gate: is_simulated must be True
    assert result.is_simulated, "Mock result was returned without is_simulated=True flag"
    assert result.source == "SIMULATED", "Mock result was returned without source='SIMULATED'"
