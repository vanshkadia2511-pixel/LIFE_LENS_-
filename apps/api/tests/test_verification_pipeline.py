"""
Unit & Integration Tests for LifeLens Ω Verification Pipeline
Tests §9–§22, §58–§60 of Master Implementation Plan
"""
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from apps.api.app.models.request import VerificationRequest
from apps.api.app.services.extractor import ClaimExtractor
from apps.api.app.services.normalizer import normalize_company_name, extract_domain, normalize_url
from apps.api.app.verification.orchestrator import VerificationOrchestrator
from apps.api.app.verification.companies_house import CompaniesHouseAdapter
from apps.api.app.cect.engine import CECTEngine
from apps.api.app.risk.engine import RiskEngine, RiskLevel
from apps.api.app.explanations.engine import ExplanationEngine
from apps.api.app.services.verification_service import VerificationService
from apps.api.app.main import app

client = TestClient(app)


def test_normalizer_company_name():
    assert normalize_company_name("Acme Technologies Ltd.") == "acme technologies"
    assert normalize_company_name("Google Inc") == "google"
    assert normalize_company_name("  Vanguard Corp.  ") == "vanguard"


def test_normalizer_extract_domain():
    assert extract_domain("hr@deepmind.google") == "deepmind.google"
    assert extract_domain("https://www.example.co.uk/careers/job123") == "example.co.uk"
    assert extract_domain("invalid-domain-string") is None


def test_claim_extractor():
    extractor = ClaimExtractor()
    req = VerificationRequest(
        request_id="req-test-1",
        created_at=datetime.now(timezone.utc),
        source_platform="LinkedIn",
        job_title="Senior AI Engineer",
        job_description="Join immediately! Must pay refundable training deposit of $500. Visa sponsored.",
        company_name="Acme Tech",
        recruiter_name="Alice Recruiter",
        recruiter_email="alice@gmail.com",
    )
    entities = extractor.extract_entities(req)
    assert len(entities) >= 1
    company_entity = next(e for e in entities if e.entity_type == "COMPANY")
    assert company_entity.claimed_name == "Acme Tech"

    claims = extractor.extract_claims(req, company_entity)
    claim_types = [c.claim_type.value if hasattr(c.claim_type, "value") else c.claim_type for c in claims]
    assert "PAYMENT" in claim_types
    assert "URGENCY" in claim_types
    assert "VISA" in claim_types


def test_verification_orchestrator_mock():
    orchestrator = VerificationOrchestrator()
    req = VerificationRequest(
        request_id="req-orch-1",
        created_at=datetime.now(timezone.utc),
        source_platform="LinkedIn",
        company_name="DeepMind Technologies Limited",
        company_website="https://deepmind.google",
        recruiter_email="recruiter@deepmind.google",
    )
    extractor = ClaimExtractor()
    entities = extractor.extract_entities(req)
    claims = extractor.extract_claims(req, entities[0])
    
    evidence = orchestrator.verify(req, entities, claims)
    assert len(evidence) >= 1
    # Domain match should be detected
    domain_ev = [e for e in evidence if e.source_type == "DOMAIN"]
    assert len(domain_ev) > 0


def test_full_pipeline_legitimate_job():
    service = VerificationService()
    req = VerificationRequest(
        request_id="req-legit-1",
        created_at=datetime.now(timezone.utc),
        source_platform="LinkedIn",
        job_title="Software Engineer",
        job_description="Standard software engineering role at our London office.",
        company_name="DeepMind Technologies Limited",
        company_website="https://deepmind.google",
        recruiter_name="Official Recruiter",
        recruiter_email="recruiter@deepmind.google",
        claimed_country="GB",
    )
    response = service.process_verification(req)
    assert response.request_id == "req-legit-1"
    assert response.risk_assessment.risk_level in (RiskLevel.LOW, RiskLevel.MEDIUM)
    assert response.cect_assessment.coherence_score >= 0.5
    assert len(response.explanation.what_was_checked) > 0
    assert len(response.explanation.recommended_next_steps) > 0


def test_full_pipeline_scam_job_with_upfront_payment():
    service = VerificationService()
    req = VerificationRequest(
        request_id="req-scam-1",
        created_at=datetime.now(timezone.utc),
        source_platform="Telegram",
        job_title="Data Entry Assistant",
        job_description="Work from home! Urgent requirement, apply today. You must pay an advance registration fee of $250. Send passport copy immediately.",
        company_name="NonExistentFakeCompanyXYZ12345",
        company_website="https://fakecompany-xyz.freehosting.com",
        recruiter_name="Quick Job Recruiter",
        recruiter_email="jobsoffer999@gmail.com",
        claimed_country="GB",
    )
    response = service.process_verification(req)
    assert response.risk_assessment.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
    assert len(response.risk_assessment.signals) >= 2
    # Check that payment signal is detected
    assert any(s.category == "PAYMENT" for s in response.risk_assessment.signals)
    assert "CRITICAL" in response.explanation.summary_headline or "HIGH" in response.explanation.summary_headline


def test_api_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "lifelens-omega-api"


def test_api_verify_job_endpoint():
    payload = {
        "job_title": "Remote Analyst",
        "job_description": "Urgent joining! Send passport scan and deposit $100 processing fee to secure your slot.",
        "company_name": "Ghost Enterprises Global",
        "recruiter_email": "recruiter.fast@gmail.com",
        "claimed_country": "GB"
    }
    resp = client.post("/api/v1/verify-job", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "risk_level" in data
    assert "cect_scores" in data
    assert "explanation" in data
    assert len(data["signals"]) > 0
    assert len(data["explanation"]["evidence_cards"]) > 0


def test_api_verify_canonical_endpoint():
    payload = {
        "job_title": "Junior Python Developer",
        "job_description": "Legitimate software engineer role at DeepMind.",
        "company_name": "DeepMind Technologies Limited",
        "recruiter_email": "jobs@deepmind.google",
        "company_website": "https://deepmind.google",
        "claimed_country": "GB"
    }
    resp = client.post("/api/v1/verify", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "request_id" in data
    assert "risk_level" in data
    assert "cect_scores" in data
    assert "explanation" in data


def test_api_verifications_lifecycle_and_feedback():
    # 1. Create verification via /verifications
    payload = {
        "job_title": "Senior Security Researcher",
        "company_name": "DeepMind Technologies Limited",
        "company_website": "https://deepmind.google",
        "recruiter_email": "recruiter@deepmind.google",
        "job_description": "Standard AI safety research position.",
        "claimed_country": "GB"
    }
    create_resp = client.post("/api/v1/verifications", json=payload)
    assert create_resp.status_code == 200
    create_data = create_resp.json()
    req_id = create_data["request_id"]
    assert req_id is not None

    # 2. Retrieve verification via /verifications/{request_id}
    get_resp = client.get(f"/api/v1/verifications/{req_id}")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["request_id"] == req_id
    assert get_data["risk_level"] in ("LOW", "MEDIUM")

    # 3. Submit feedback via /feedback
    fb_payload = {
        "request_id": req_id,
        "feedback_type": "accurate",
        "comment": "Assessment was verified independently.",
        "confirmed_outcome": "LEGITIMATE"
    }
    fb_resp = client.post("/api/v1/feedback", json=fb_payload)
    assert fb_resp.status_code == 201
    fb_data = fb_resp.json()
    assert fb_data["status"] == "recorded"
    assert fb_data["request_id"] == req_id


def test_web_workspace_root_served():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "LifeLens" in resp.text
    assert "Reality Integrity" in resp.text

