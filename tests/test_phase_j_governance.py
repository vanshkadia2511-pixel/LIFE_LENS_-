"""
LifeLens Ω — Phase J: Trust & Governance Test Suite
Tests for:
1. Dispute and Right-of-Reply with DNS TXT & Company Email Proof-of-Control
2. Anti-Abuse Protection (Scammers cannot clear flags without domain control)
3. Calibration Reporting and Expected Calibration Error (ECE) labeled MEASURED
4. Drift Canary Set evaluation and recall alerting (Threshold labeled TARGET)
5. Public Transparency Report (MEASURED vs TARGET, known limits, unverified hypotheses)
6. Phase J REST API Endpoints Integration
"""
import pytest
from fastapi.testclient import TestClient

from apps.api.app.main import app
from apps.api.app.models.dispute import (
    DisputeRequest,
    DisputeStatus,
    ProofOfControlMethod,
)
from apps.api.app.services.governance.dispute_service import DisputeService
from apps.api.app.services.governance.calibration_reporter import (
    CalibrationReportService,
    SignalGroupCalibration,
)
from apps.api.app.services.governance.drift_canary import (
    DriftCanaryService,
    CanaryPhrase,
)
from apps.api.app.services.governance.transparency_service import (
    TransparencyReportService,
)

client = TestClient(app)


# ── 1. Dispute & Proof-of-Control Tests ────────────────────────────────────────

def test_dispute_submission_and_proof_of_control_dns_txt():
    """Verify right-of-reply workflow: DNS TXT proof challenge and ledger recording."""
    service = DisputeService()

    # 1. Recruiter files dispute for legitimate company flagged erroneously
    req = service.submit_dispute(
        target_entity_domain="verified-recruiting-corp.com",
        contestant_name="Jane Doe",
        contestant_email="hr@verified-recruiting-corp.com",
        reason_for_contest="Legitimate agency flagged due to third-party domain forwarding.",
        proof_method=ProofOfControlMethod.DNS_TXT_RECORD,
    )

    assert req.status == DisputeStatus.DISPUTED_UNDER_REVIEW
    assert service.get_entity_dispute_state("verified-recruiting-corp.com") == "DISPUTED"
    assert "_lifelens-challenge." in req.dns_txt_record_name
    assert "lifelens-verification=" in req.dns_txt_expected_value
    assert "TARGET: 48 business hours" in req.review_time_target

    # 2. Submitting incorrect challenge token fails (Adverse flag remains active)
    fail_res = service.verify_proof_of_control(req.dispute_id, "WRONG_TOKEN_VALUE")
    assert fail_res.proof_verified is False
    assert fail_res.finding_modified is False
    assert fail_res.status == DisputeStatus.REJECTED_PROOF_FAILED
    assert "ABUSE PROTECTION TRIGGERED" in fail_res.explanation

    # 3. Submitting verified DNS token succeeds (Finding modified under right-of-reply)
    success_res = service.verify_proof_of_control(req.dispute_id, req.dns_txt_expected_value)
    assert success_res.proof_verified is True
    assert success_res.finding_modified is True
    assert success_res.status == DisputeStatus.PROOF_VERIFIED_RESOLVED
    assert len(success_res.ledger_entry_hash) == 64


def test_dispute_corporate_email_domain_mismatch_abuse_protection():
    """Verify abuse protection blocks scammer attempting to contest with unrelated email."""
    service = DisputeService()

    # Attacker tries to contest microsoft.com flag using attacker@mail-shell.xyz
    bad_req = service.submit_dispute(
        target_entity_domain="microsoft.com",
        contestant_name="Scammer",
        contestant_email="attacker@mail-shell.xyz",
        reason_for_contest="Clear this flag now",
        proof_method=ProofOfControlMethod.COMPANY_DOMAIN_EMAIL,
    )

    # Must be immediately rejected
    assert bad_req.status == DisputeStatus.REJECTED_PROOF_FAILED

    # Legitimate recruiter with matching email domain succeeds in receiving verification code
    good_req = service.submit_dispute(
        target_entity_domain="microsoft.com",
        contestant_name="Alice Recruiter",
        contestant_email="alice@microsoft.com",
        reason_for_contest="Legitimate recruiter communication",
        proof_method=ProofOfControlMethod.COMPANY_DOMAIN_EMAIL,
    )
    assert good_req.status == DisputeStatus.DISPUTED_UNDER_REVIEW
    assert good_req.email_verification_code.startswith("CODE_")

    # Verify code succeeds
    res = service.verify_proof_of_control(good_req.dispute_id, good_req.email_verification_code)
    assert res.proof_verified is True
    assert res.finding_modified is True


# ── 2. Calibration & ECE Tests ────────────────────────────────────────────────

def test_calibration_ece_calculation_and_signal_group_reports():
    """Verify ECE calculation and MEASURED signal group calibration reporting."""
    service = CalibrationReportService()

    # 1. Unit test ECE mathematical calculation
    confs = [0.95, 0.90, 0.85, 0.80, 0.20, 0.10]
    labels = [1, 1, 1, 1, 0, 0]
    ece, bins = service.calculate_ece(confs, labels, num_bins=5)
    assert 0.0 <= ece <= 0.15
    assert len(bins) > 0

    # 2. Comprehensive report
    groups = service.get_comprehensive_calibration_report()
    assert len(groups) >= 4

    for g in groups:
        assert g.metric_provenance == "MEASURED"
        assert g.expected_calibration_error >= 0.0
        assert g.sample_size >= 500

    # Assert media forensics openly discloses in-the-wild degradation
    media_g = next(g for g in groups if "Media Forensics" in g.signal_group_name)
    assert media_g.expected_calibration_error == 0.142
    assert "Rule B" in media_g.in_the_wild_caveat


# ── 3. Drift Canary Set Tests ─────────────────────────────────────────────────

def test_drift_canary_evaluation_and_recall_alerting():
    """Verify drift canary set evaluates novel scam phrasings and alerts on recall drops."""
    service = DriftCanaryService(target_threshold=0.85)

    # 1. Run default canary set
    result = service.run_canary_evaluation()
    assert result.total_canaries >= 10
    assert result.measured_recall >= 0.85  # Default detectors should catch our canaries
    assert result.target_threshold == 0.85
    assert result.alert_triggered is False

    # 2. Simulate drift with novel unhandled phrases to trigger alert
    novel_unhandled_canaries = [
        CanaryPhrase("DRIFT_01", "Novel", "Completely unobtrusive benign text 1", "UNKNOWN", "English"),
        CanaryPhrase("DRIFT_02", "Novel", "Completely unobtrusive benign text 2", "UNKNOWN", "English"),
        CanaryPhrase("DRIFT_03", "Novel", "Completely unobtrusive benign text 3", "UNKNOWN", "English"),
    ]
    drift_result = service.run_canary_evaluation(novel_unhandled_canaries)
    assert drift_result.measured_recall < 0.85
    assert drift_result.alert_triggered is True  # Alert fired for SRE sentinel


# ── 4. Public Transparency Report Tests ───────────────────────────────────────

def test_transparency_report_metrics_and_unverified_hypotheses():
    """Verify transparency report clearly contrasts MEASURED vs TARGET and notes unverified hypotheses."""
    service = TransparencyReportService()
    report = service.get_transparency_report()

    # 1. Check metric provenance labels
    for m in report.metrics_comparison:
        assert "TARGET" in m.target_value
        assert "MEASURED" in m.measured_value or "Operational target" in m.measured_value
        assert len(m.dataset_and_split) > 0

    # 2. Check limitations
    assert any("Media Forensics" in l["subsystem"] for l in report.known_limitations)
    assert any("E2EE Calls" in l["subsystem"] for l in report.known_limitations)

    # 3. Check unverified hypotheses
    hyp_ids = {h["hypothesis_id"] for h in report.unverified_hypotheses}
    assert {"HYP_01", "HYP_02"}.issubset(hyp_ids)
    assert any("UNVERIFIED" in h["status"] for h in report.unverified_hypotheses)


# ── 5. Phase J REST API Endpoints Integration ──────────────────────────────────

def test_phase_j_api_endpoints():
    """Integration test for Phase J governance REST endpoints."""
    # 1. Dispute submit endpoint
    resp_sub = client.post(
        "/api/v1/governance/dispute/submit",
        json={
            "target_entity_domain": "corp-jobs.com",
            "contestant_name": "Bob HR",
            "contestant_email": "bob@corp-jobs.com",
            "reason_for_contest": "Verified career portal",
            "proof_method": "COMPANY_DOMAIN_EMAIL",
        },
    )
    assert resp_sub.status_code == 200
    data_sub = resp_sub.json()
    assert data_sub["status"] == "DISPUTED_UNDER_REVIEW"
    assert "CODE_" in data_sub["email_verification_code"]

    # 2. Dispute verify-proof endpoint
    disp_id = data_sub["dispute_id"]
    code = data_sub["email_verification_code"]
    resp_ver = client.post(
        "/api/v1/governance/dispute/verify-proof",
        json={"dispute_id": disp_id, "submitted_proof_token": code},
    )
    assert resp_ver.status_code == 200
    data_ver = resp_ver.json()
    assert data_ver["proof_verified"] is True
    assert data_ver["finding_modified"] is True

    # 3. Calibration report endpoint
    resp_cal = client.get("/api/v1/governance/calibration/report")
    assert resp_cal.status_code == 200
    assert len(resp_cal.json()["signal_groups"]) >= 4

    # 4. Drift canary run endpoint
    resp_can = client.post("/api/v1/governance/drift-canary/run")
    assert resp_can.status_code == 200
    assert resp_can.json()["target_threshold"] == 0.85

    # 5. Public transparency endpoint
    resp_trans = client.get("/api/v1/governance/transparency")
    assert resp_trans.status_code == 200
    assert len(resp_trans.json()["metrics_comparison"]) >= 6

    # 6. Pilot event endpoint (consented & privacy-safe)
    resp_pilot_event = client.post(
        "/api/v1/governance/pilot/event",
        json={
            "raw_session_id": "test_session_api_1",
            "event_type": "CHECK_COMPLETED",
            "metadata": {"risk_category": "LOW"},
            "has_explicit_consent": True,
        },
    )
    assert resp_pilot_event.status_code == 200
    assert resp_pilot_event.json()["status"] == "RECORDED"

    # 7. Pilot event endpoint rejects unconsented request (403)
    resp_pilot_unconsented = client.post(
        "/api/v1/governance/pilot/event",
        json={
            "raw_session_id": "test_session_api_2",
            "event_type": "CHECK_COMPLETED",
            "metadata": {"risk_category": "LOW"},
            "has_explicit_consent": False,
        },
    )
    assert resp_pilot_unconsented.status_code == 403

    # 8. Pilot summary endpoint
    resp_pilot_summary = client.get("/api/v1/governance/pilot/summary")
    assert resp_pilot_summary.status_code == 200
    data_summary = resp_pilot_summary.json()
    assert data_summary["total_checks"] >= 1
    assert data_summary["privacy_mode"] == "SALTED_HMAC_AGGREGATE_ONLY"
