"""
LifeLens Ω — Phase 2 Trust Graph, Security & Baseline Tests
Tests §32, §39, §69, §81 of Master Implementation Plan
"""
import pytest
from apps.api.app.services.trust_graph import TrustGraphService
from apps.api.app.cect.behavioral_baseline import LocalBehavioralBaseline
from apps.api.app.security import SSRFShield
from apps.api.app.repositories.db_models import create_tables, SessionLocal
from apps.api.app.repositories.repositories import VerificationRequestRepository, AuditRepository


def test_trust_graph_service():
    graph = TrustGraphService()
    res = graph.record_verification(
        company_name="Acme Corp",
        recruiter_email="hr@acme-careers-verify.com",
        domain="acme-careers-verify.com",
        is_risky=True,
    )
    assert res["total_nodes"] == 3
    assert res["total_edges"] == 2
    assert res["computed_trust_score"] < 1.0

    neighbors = graph.get_neighbors("recruiter:hr@acme-careers-verify.com")
    assert len(neighbors) == 2


def test_local_behavioral_baseline():
    baseline = LocalBehavioralBaseline(user_id="test_user")

    # Initial interaction
    eval1 = baseline.evaluate_drift("OFFER_RECEIVED", domain="techcorp.com", urgency="NORMAL")
    assert not eval1["anomaly_detected"]

    baseline.record_interaction("OFFER_RECEIVED", domain="techcorp.com", urgency="NORMAL")

    # Anomalous interaction (early payment request + unknown domain)
    eval2 = baseline.evaluate_drift("PAYMENT_REQUESTED", domain="unknown-scam.com", urgency="HIGH")
    assert eval2["anomaly_detected"]
    assert eval2["friction_recommendation"] == "MAXIMUM_FRICTION"

    baseline.reset_baseline()
    assert len(baseline._history) == 0


def test_ssrf_security_shield():
    shield = SSRFShield()

    # Public URLs should pass
    res = shield.validate_url("https://www.google.com")
    assert res.is_safe

    # Internal IPs / loopback / cloud metadata should be blocked
    res_int = shield.validate_url("http://127.0.0.1:8000")
    assert not res_int.is_safe

    res_meta = shield.validate_url("http://169.254.169.254/latest/meta-data")
    assert not res_meta.is_safe


def test_db_repositories():
    import uuid
    create_tables()
    db = SessionLocal()
    req_id = f"req-test-db-{uuid.uuid4().hex[:8]}"
    try:
        req_repo = VerificationRequestRepository(db)
        audit_repo = AuditRepository(db)

        # Create request DB record
        req_db = req_repo.create({
            "id": req_id,
            "source_platform": "LinkedIn",
            "company_name": "Test Global Inc",
            "status": "PROCESSING",
        })
        assert req_db.id == req_id

        req_repo.update_result(
            request_id=req_id,
            risk_level="HIGH",
            risk_confidence=0.90,
            cect_version="1.0.0",
            risk_config_version="1.0.0",
            extractor_version="1.0.0",
        )

        fetched = req_repo.get(req_id)
        assert fetched.status == "COMPLETE"
        assert fetched.risk_level == "HIGH"

        # Log audit event
        audit_repo.log(
            event_type="VERIFICATION_EXPLICIT",
            action="VERIFY_JOB",
            request_id=req_id,
            result="PASS",
        )
    finally:
        db.close()
