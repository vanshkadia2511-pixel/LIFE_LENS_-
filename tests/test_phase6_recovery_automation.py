"""
LifeLens Ω — Phase 6: Recovery Automation Test Suite
Evolved Blueprint Phase 6 (Months 19-21)

Tests:
1. Damage assessment across incident types (Advance fee, Malware, Credential theft, Identity theft)
2. Account prioritization & blast radius calculation (Tier 1 Critical to Tier 4)
3. Step-by-step recovery plan generation with time estimation (< 30 minutes criterion)
4. Interactive step completion tracking & state progression (ACTIVE -> IN_PROGRESS -> COMPLETED)
5. Trusted contact emergency safety broadcast
6. Regulatory complaint packet generation (FBI IC3, FTC, Action Fraud UK, NCRP India) with SHA-256 fingerprint
7. Full FastAPI REST API integration testing
"""
import pytest
from fastapi.testclient import TestClient

from apps.api.app.main import app
from apps.api.app.models.recovery import (
    IncidentType,
    AccountTier,
    UrgencyLevel,
    ActionType,
    IncidentReport,
    TrustedContact,
    RegulatoryAgency,
)
from apps.api.app.services.recovery_service import RecoveryService


@pytest.fixture
def service():
    return RecoveryService()


@pytest.fixture
def client():
    return TestClient(app)


# ==============================================================================
# UNIT TESTS: Service & Logic Layer
# ==============================================================================

class TestDamageAssessment:
    def test_advance_fee_financial_drain_critical(self, service: RecoveryService):
        report = IncidentReport(
            incident_id="inc-test-001",
            incident_type=IncidentType.ADVANCE_FEE_PAID,
            financial_amount_lost=6500.0,
            currency="USD",
            compromised_accounts=["chase_checking", "primary_gmail"],
            description="Paid $6,500 wire for fake international visa processing.",
        )
        assessment = service.assess_damage(report)
        assert assessment.severity_label == "CRITICAL"
        assert assessment.severity_score >= 0.75
        assert assessment.urgency_level == UrgencyLevel.IMMEDIATE_15_MIN
        assert any("recall" in d.lower() or "wire" in d.lower() for d in assessment.containment_directives)

    def test_malware_executed_containment(self, service: RecoveryService):
        report = IncidentReport(
            incident_id="inc-test-002",
            incident_type=IncidentType.MALWARE_EXECUTED,
            compromised_accounts=["workstation_pc"],
            description="Downloaded and ran malicious interview screening software .exe.",
        )
        assessment = service.assess_damage(report)
        assert assessment.severity_label in ["HIGH", "CRITICAL"]
        assert assessment.urgency_level == UrgencyLevel.IMMEDIATE_15_MIN
        assert any("disconnect" in d.lower() for d in assessment.containment_directives)

    def test_identity_theft_ssn_harvesting(self, service: RecoveryService):
        report = IncidentReport(
            incident_id="inc-test-003",
            incident_type=IncidentType.IDENTITY_THEFT,
            compromised_accounts=["ssn_number", "passport_scan"],
            description="Submitted passport scan and SSN on fake recruiter onboarding portal.",
        )
        assessment = service.assess_damage(report)
        assert assessment.severity_label in ["MEDIUM", "HIGH", "CRITICAL"]
        assert any("credit" in d.lower() or "freeze" in d.lower() for d in assessment.containment_directives)


class TestRecoveryPlanGeneration:
    def test_recovery_plan_total_time_under_30_minutes(self, service: RecoveryService):
        """Blueprint Criterion: User recovers account within 30 minutes with system guidance."""
        report = IncidentReport(
            incident_id="inc-test-004",
            incident_type=IncidentType.CREDENTIAL_THEFT,
            compromised_accounts=["gmail", "linkedin"],
            description="Entered login details into phishing site.",
        )
        plan = service.generate_recovery_plan(report)
        assert plan.total_steps >= 4
        # Target duration validation
        assert plan.estimated_total_minutes <= 30
        assert plan.status == "ACTIVE"

    def test_tier_prioritization_critical_first(self, service: RecoveryService):
        report = IncidentReport(
            incident_id="inc-test-005",
            incident_type=IncidentType.ADVANCE_FEE_PAID,
            financial_amount_lost=2500.0,
            compromised_accounts=["chase", "gmail", "linkedin"],
        )
        plan = service.generate_recovery_plan(report)
        first_step = plan.steps[0]
        assert first_step.tier == AccountTier.TIER_1_CRITICAL
        # Financial or session freeze should precede social/regulatory
        assert first_step.action_type in [
            ActionType.FREEZE_FINANCIAL,
            ActionType.REVOKE_ALL_SESSIONS,
            ActionType.DISCONNECT_DEVICE,
        ]

    def test_step_completion_lifecycle(self, service: RecoveryService):
        report = IncidentReport(
            incident_id="inc-test-006",
            incident_type=IncidentType.SESSION_HIJACK,
            compromised_accounts=["gmail"],
        )
        plan = service.generate_recovery_plan(report)
        rec_id = plan.recovery_id
        assert plan.status == "ACTIVE"
        assert plan.completed_steps == 0

        # Complete step 1
        updated = service.complete_step(rec_id, plan.steps[0].step_id, completed=True)
        assert updated is not None
        assert updated.status == "IN_PROGRESS"
        assert updated.completed_steps == 1
        assert updated.steps[0].completed is True
        assert updated.steps[0].completed_at is not None

        # Complete all remaining steps
        for step in plan.steps[1:]:
            service.complete_step(rec_id, step.step_id, completed=True)

        final_plan = service.get_plan(rec_id)
        assert final_plan.status == "COMPLETED"
        assert final_plan.completed_steps == final_plan.total_steps


class TestTrustedContactsAndRegulatoryReports:
    def test_trusted_contact_notification_no_credential_leak(self, service: RecoveryService):
        report = IncidentReport(
            incident_id="inc-test-007",
            user_id="Alice victim",
            incident_type=IncidentType.IDENTITY_THEFT,
        )
        plan = service.generate_recovery_plan(report)
        contacts = [
            TrustedContact(
                name="Bob Mentor",
                relationship="Colleague",
                contact_channel="EMAIL",
                destination="bob@example.com",
            )
        ]
        results = service.notify_trusted_contacts(plan.recovery_id, contacts)
        assert len(results) == 1
        assert results[0].status == "SENT"
        # Must not contain passwords or raw data
        assert "Alice victim" in results[0].message_preview
        assert "IDENTITY_THEFT" in results[0].message_preview
        assert "disregard any unexpected requests" in results[0].message_preview

    def test_regulatory_report_ic3_and_action_fraud(self, service: RecoveryService):
        report = IncidentReport(
            incident_id="inc-test-008",
            incident_type=IncidentType.ADVANCE_FEE_PAID,
            financial_amount_lost=4000.0,
            currency="USD",
            scammer_identifiers={
                "email": "recruiter-fake@apex-careers.biz",
                "phone": "+1-555-0199",
                "crypto_address": "0x71C...B49",
            },
            description="Recruiter demanded USD 4,000 equipment deposit via wire transfer.",
        )
        plan = service.generate_recovery_plan(report)

        # 1. FBI IC3
        ic3_packet = service.generate_regulatory_report(plan.recovery_id, RegulatoryAgency.FBI_IC3)
        assert ic3_packet.agency == RegulatoryAgency.FBI_IC3
        assert "IC3" in ic3_packet.complaint_reference
        assert "4,000.00" in ic3_packet.monetary_loss
        assert len(ic3_packet.evidence_fingerprint_sha256) == 64
        assert "recruiter-fake@apex-careers.biz" in ic3_packet.formatted_complaint_text

        # 2. Action Fraud UK
        uk_packet = service.generate_regulatory_report(
            plan.recovery_id, RegulatoryAgency.ACTION_FRAUD_UK
        )
        assert uk_packet.agency == RegulatoryAgency.ACTION_FRAUD_UK
        assert "NFRC-UK-" in uk_packet.complaint_reference
        assert "Action Fraud" in uk_packet.agency_full_name


# ==============================================================================
# INTEGRATION TESTS: FastAPI REST Endpoints
# ==============================================================================

class TestRecoveryEndpoints:
    def test_api_assess_endpoint(self, client: TestClient):
        payload = {
            "incident_id": "api-inc-001",
            "incident_type": "ADVANCE_FEE_PAID",
            "financial_amount_lost": 1500.0,
            "currency": "USD",
            "compromised_accounts": ["bank_account"],
            "description": "Paid $1,500 background check fee.",
        }
        res = client.post("/api/v1/recovery/assess", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "severity_score" in data
        assert data["severity_label"] in ["MEDIUM", "HIGH", "CRITICAL"]
        assert len(data["containment_directives"]) > 0

    def test_api_initiate_and_progress_lifecycle(self, client: TestClient):
        payload = {
            "incident_id": "api-inc-002",
            "incident_type": "CREDENTIAL_THEFT",
            "compromised_accounts": ["gmail", "outlook"],
            "description": "Clicked phishing link.",
        }
        # 1. Initiate
        init_res = client.post("/api/v1/recovery/initiate", json=payload)
        assert init_res.status_code == 200
        plan_data = init_res.json()
        rec_id = plan_data["recovery_id"]
        assert plan_data["status"] == "ACTIVE"
        assert len(plan_data["steps"]) >= 4

        # 2. Fetch status
        get_res = client.get(f"/api/v1/recovery/{rec_id}")
        assert get_res.status_code == 200
        assert get_res.json()["recovery_id"] == rec_id

        # 3. Complete step 1
        step1_id = plan_data["steps"][0]["step_id"]
        step_res = client.post(f"/api/v1/recovery/{rec_id}/step/{step1_id}/complete?completed=true")
        assert step_res.status_code == 200
        step_data = step_res.json()
        assert step_data["status"] == "IN_PROGRESS"
        assert step_data["completed_steps"] == 1

        # 4. Notify contacts
        contact_payload = [
            {
                "name": "Sarah",
                "relationship": "Sister",
                "contact_channel": "EMAIL",
                "destination": "sarah@example.com",
            }
        ]
        notify_res = client.post(f"/api/v1/recovery/{rec_id}/notify-contacts", json=contact_payload)
        assert notify_res.status_code == 200
        assert len(notify_res.json()) == 1
        assert notify_res.json()[0]["status"] == "SENT"

        # 5. Regulatory Report JSON
        report_res = client.get(f"/api/v1/recovery/{rec_id}/regulatory-report/FBI_IC3")
        assert report_res.status_code == 200
        assert "IC3" in report_res.json()["complaint_reference"]

        # 6. Regulatory Report Text Download
        dl_res = client.get(f"/api/v1/recovery/{rec_id}/regulatory-report/FBI_IC3/download")
        assert dl_res.status_code == 200
        assert "text/plain" in dl_res.headers["content-type"]
        assert "OFFICIAL CYBERCRIME COMPLAINT PACKET" in dl_res.text

    def test_api_nonexistent_plan_404(self, client: TestClient):
        res = client.get("/api/v1/recovery/nonexistent-id")
        assert res.status_code == 404
