"""
LifeLens Ω — Regression Test Suite
Implementation Plan §69 — Each bug that reaches production testing becomes a permanent regression case.

Tests correspond to entries in datasets/evaluation/regression/regression_cases.json
"""
import json
from pathlib import Path

import pytest

from apps.api.app.models.request import VerificationRequest
from apps.api.app.services.verification_service import VerificationService
from apps.api.app.risk.engine import RiskLevel

ROOT = Path(__file__).resolve().parent.parent

REGRESSION_FILE = ROOT / "datasets" / "evaluation" / "regression" / "regression_cases.json"


def load_regression_cases():
    with open(REGRESSION_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


CASES = load_regression_cases()
LEVEL_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


def _build_request(scenario: dict) -> VerificationRequest:
    return VerificationRequest(
        request_id=scenario["id"],
        created_at=None,
        job_title=scenario.get("job_title"),
        company_name=scenario.get("company_name"),
        company_website=scenario.get("company_website"),
        recruiter_name=scenario.get("recruiter_name"),
        recruiter_email=scenario.get("recruiter_email"),
        claimed_country=scenario.get("claimed_country", "GB"),
        job_description=scenario.get("job_description"),
    )


@pytest.fixture(scope="module")
def service():
    return VerificationService()


class TestRegressions:
    """
    REG-001 — BUG-001: Recognized third-party agency triggers false positive
    Fix: Issue A5 suppresses SIG_DOMAIN_MISMATCH for recognized agencies (§16.1, §26)
    """
    def test_REG001_recognized_agency_no_high_false_positive(self, service):
        case = next(c for c in CASES if c["regression_id"] == "REG-001")
        req = _build_request(case["scenario"])
        resp = service.process_verification(req)
        actual_level = resp.risk_assessment.risk_level.value
        max_allowed = case.get("expected_risk_max", "MEDIUM")
        assert LEVEL_ORDER[actual_level] <= LEVEL_ORDER[max_allowed], (
            f"REG-001 REGRESSION: Hays-agency job got {actual_level} — "
            f"must be ≤ {max_allowed}. Domain mismatch signal must be suppressed."
        )

    """
    REG-002 — BUG-002: UNAVAILABLE source status incorrectly converted to FRAUD
    Fix: UNAVAILABLE = inconclusive, not negative; risk must not reach CRITICAL
    """
    def test_REG002_api_failure_not_fraud(self, service):
        case = next(c for c in CASES if c["regression_id"] == "REG-002")
        req = _build_request(case["scenario"])
        resp = service.process_verification(req)
        actual_level = resp.risk_assessment.risk_level.value
        max_allowed = case.get("expected_risk_max", "MEDIUM")
        assert LEVEL_ORDER[actual_level] <= LEVEL_ORDER[max_allowed], (
            f"REG-002 REGRESSION: API unavailability produced {actual_level} — "
            f"must not exceed {max_allowed}. UNAVAILABLE ≠ FRAUD."
        )

    """
    REG-003 — BUG-003: New company with weak web presence incorrectly rated CRITICAL
    Fix: Absence of registry data is a MEDIUM signal at most, not a CRITICAL flag
    """
    def test_REG003_new_company_not_critical(self, service):
        case = next(c for c in CASES if c["regression_id"] == "REG-003")
        req = _build_request(case["scenario"])
        resp = service.process_verification(req)
        actual_level = resp.risk_assessment.risk_level.value
        max_allowed = case.get("expected_risk_max", "MEDIUM")
        assert LEVEL_ORDER[actual_level] <= LEVEL_ORDER[max_allowed], (
            f"REG-003 REGRESSION: New company without registry data got {actual_level} — "
            f"must not exceed {max_allowed}. Missing data is not proof of fraud."
        )

    """
    REG-004 — BUG-004: PAYMENT_REQUEST signal missing for obfuscated fee language
    Fix: Semantic pattern matching extended to detect 'compliance transfer', 'training deposit', 'hardware bond'
    """
    def test_REG004_obfuscated_payment_detected(self, service):
        case = next(c for c in CASES if c["regression_id"] == "REG-004")
        req = _build_request(case["scenario"])
        resp = service.process_verification(req)
        actual_level = resp.risk_assessment.risk_level.value
        min_required = case.get("expected_risk_min", "HIGH")
        assert LEVEL_ORDER[actual_level] >= LEVEL_ORDER[min_required], (
            f"REG-004 REGRESSION: Obfuscated payment request got {actual_level} — "
            f"must be ≥ {min_required}. Semantic PAYMENT extraction must detect evasive language."
        )
        # Also verify a PAYMENT-related signal is present
        signal_categories = [s.category for s in resp.risk_assessment.signals]
        assert any("PAYMENT" in cat.upper() or "FEE" in cat.upper() for cat in signal_categories), (
            f"REG-004 REGRESSION: No PAYMENT signal detected. Signals: {signal_categories}"
        )

    """
    REG-005 — BUG-005: AuditEventDB.metadata conflict with SQLAlchemy reserved attribute
    Fix: Renamed to event_metadata. End-to-end persistence and retrieval must succeed.
    """
    def test_REG005_db_persistence_no_attribute_error(self, service):
        case = next(c for c in CASES if c["regression_id"] == "REG-005")
        req = _build_request(case["scenario"])
        # Must not raise AttributeError from metadata field collision
        try:
            resp = service.process_verification(req)
        except AttributeError as exc:
            pytest.fail(
                f"REG-005 REGRESSION: SQLAlchemy AttributeError detected — "
                f"metadata field collision has returned: {exc}"
            )
        # Response should be valid
        assert resp.request_id is not None
        actual_level = resp.risk_assessment.risk_level.value
        max_allowed = case.get("expected_risk_max", "MEDIUM")
        assert LEVEL_ORDER[actual_level] <= LEVEL_ORDER[max_allowed], (
            f"REG-005: DeepMind pipeline got {actual_level}, expected ≤ {max_allowed}"
        )
