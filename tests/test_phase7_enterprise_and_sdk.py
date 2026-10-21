"""
LifeLens Ω — Phase 7: Enterprise & Developer SDK Test Suite
Evolved Blueprint Phase 7 (Months 22-24)

Tests:
1. Multi-tenant Organization management (Creation, tiers, retrieval)
2. Scoped API Key lifecycle (Issuance, SHA-256 hashing, scope checks, revocation)
3. Sliding-window 60-second rate limiter enforcement
4. Webhooks registry & HMAC-SHA256 signature verification
5. Enterprise threat telemetry & analytics aggregation
6. FastAPI REST endpoints integration
7. Official Python Developer SDK (LifeLensClient) end-to-end integration
"""
import time
import pytest
from fastapi.testclient import TestClient

from apps.api.app.main import app
from apps.api.app.models.enterprise import (
    EnterpriseTier,
    ApiKeyScope,
    WebhookEventType,
)
from apps.api.app.services.enterprise_service import EnterpriseService
from src.sdk.client import LifeLensClient, AuthenticationError, RateLimitExceeded


@pytest.fixture
def service():
    return EnterpriseService()


@pytest.fixture
def client():
    return TestClient(app)


# ==============================================================================
# 1. UNIT TESTS: Enterprise Service Layer
# ==============================================================================

class TestEnterpriseService:
    def test_organization_lifecycle(self, service: EnterpriseService):
        org = service.create_organization(
            name="Acme Global Recruiting",
            tier=EnterpriseTier.ENTERPRISE,
            contact_email="admin@acme-global.com",
        )
        assert org.org_id.startswith("org-")
        assert org.tier == EnterpriseTier.ENTERPRISE
        fetched = service.get_organization(org.org_id)
        assert fetched is not None
        assert fetched.name == "Acme Global Recruiting"

    def test_api_key_issuance_and_authentication(self, service: EnterpriseService):
        org = service.create_organization("Beta Staffing", EnterpriseTier.STARTUP, "it@beta.com")
        key_resp, raw_key = service.create_api_key(
            org_id=org.org_id,
            name="CI Pipeline Key",
            scopes=[ApiKeyScope.VERIFY_READ, ApiKeyScope.VERIFY_WRITE],
        )

        assert raw_key.startswith("ll_live_")
        assert key_resp.key_prefix.startswith("ll_live_")
        assert key_resp.rate_limit_per_minute == 300

        # Authenticate valid raw key
        auth_key = service.authenticate_api_key(raw_key)
        assert auth_key is not None
        assert auth_key.key_id == key_resp.key_id
        assert auth_key.is_active is True

        # Invalid key fails
        assert service.authenticate_api_key("ll_live_tampered_key_value") is None

        # Revocation
        assert service.revoke_api_key(key_resp.key_id) is True
        assert service.authenticate_api_key(raw_key) is None

    def test_scope_enforcement(self, service: EnterpriseService):
        org = service.create_organization("Scoped Org", EnterpriseTier.FREE, "test@scoped.org")
        key_resp, raw_key = service.create_api_key(
            org_id=org.org_id,
            name="Read Only Key",
            scopes=[ApiKeyScope.VERIFY_READ],
        )
        key = service.authenticate_api_key(raw_key)
        assert service.check_scope(key, ApiKeyScope.VERIFY_READ) is True
        assert service.check_scope(key, ApiKeyScope.RECOVERY_MANAGE) is False

        # Admin key has wildcard
        admin_resp, admin_raw = service.create_api_key(
            org_id=org.org_id,
            name="Super Admin Key",
            scopes=[ApiKeyScope.ADMIN_ALL],
        )
        admin_key = service.authenticate_api_key(admin_raw)
        assert service.check_scope(admin_key, ApiKeyScope.VERIFY_READ) is True
        assert service.check_scope(admin_key, ApiKeyScope.RECOVERY_MANAGE) is True
        assert service.check_scope(admin_key, ApiKeyScope.WEBHOOKS_MANAGE) is True

    def test_sliding_window_rate_limiter(self, service: EnterpriseService):
        org = service.create_organization("Rate Limited Org", EnterpriseTier.FREE, "free@org.com")
        key_resp, raw_key = service.create_api_key(
            org_id=org.org_id,
            name="Low Limit Key",
            scopes=[ApiKeyScope.VERIFY_READ],
        )
        key = service.authenticate_api_key(raw_key)
        # Override rate limit to 3 for fast deterministic testing
        key.rate_limit_per_minute = 3

        allowed, _ = service.check_rate_limit(key)
        assert allowed is True
        allowed, _ = service.check_rate_limit(key)
        assert allowed is True
        allowed, _ = service.check_rate_limit(key)
        assert allowed is True

        # 4th request must be blocked
        allowed, remaining = service.check_rate_limit(key)
        assert allowed is False
        assert remaining == 0

    def test_webhook_hmac_signatures_and_dispatch(self, service: EnterpriseService):
        org = service.create_organization("Webhook Client", EnterpriseTier.ENTERPRISE, "wh@client.com")
        sub = service.create_webhook_subscription(
            org_id=org.org_id,
            target_url="https://client-portal.com/lifelens-callback",
            subscribed_events=[WebhookEventType.HIGH_RISK_DETECTED, WebhookEventType.CRITICAL_SCAM_FLAGGED],
        )

        assert sub.secret_key.startswith("whsec_")
        assert sub.status == "ACTIVE"

        # Dispatch an event
        event_data = {"applicant_id": "app-101", "risk_score": 0.94, "verdict": "CRITICAL_FRAUD"}
        dispatched = service.dispatch_event(
            org_id=org.org_id,
            event_type=WebhookEventType.HIGH_RISK_DETECTED,
            data=event_data,
        )
        assert len(dispatched) == 1
        event = dispatched[0]
        assert "t=" in event.signature_header
        assert "v1=" in event.signature_header

        # Verify signature using static helper
        import json
        payload_json = json.dumps(event_data, sort_keys=True)
        is_valid = EnterpriseService.verify_webhook_signature(
            secret_key=sub.secret_key,
            signature_header=event.signature_header,
            payload_json=payload_json,
        )
        assert is_valid is True

        # Tampered payload fails
        tampered_json = json.dumps({"applicant_id": "app-101", "risk_score": 0.10}, sort_keys=True)
        is_valid_tampered = EnterpriseService.verify_webhook_signature(
            secret_key=sub.secret_key,
            signature_header=event.signature_header,
            payload_json=tampered_json,
        )
        assert is_valid_tampered is False

    def test_enterprise_analytics_aggregation(self, service: EnterpriseService):
        org = service.create_organization("Analytics Corp", EnterpriseTier.ENTERPRISE, "analytics@corp.com")
        service.record_verification(org.org_id, "CRITICAL", is_scam=True, is_phishing=False, latency_ms=120.0, threat_category="advance_fee")
        service.record_verification(org.org_id, "LOW", is_scam=False, is_phishing=False, latency_ms=80.0)
        service.record_recovery(org.org_id)

        analytics = service.get_analytics(org.org_id)
        assert analytics.org_id == org.org_id
        assert analytics.total_verifications >= 2
        assert analytics.tier == EnterpriseTier.ENTERPRISE


# ==============================================================================
# 2. INTEGRATION TESTS: FastAPI Enterprise Endpoints
# ==============================================================================

class TestEnterpriseEndpoints:
    def test_api_org_and_keys_endpoints(self, client: TestClient):
        # 1. Create org
        org_res = client.post(
            "/api/v1/enterprise/organizations",
            json={"name": "TalentShield ATS", "tier": "ENTERPRISE", "contact_email": "ops@talentshield.com"},
        )
        assert org_res.status_code == 200
        org_id = org_res.json()["org_id"]

        # 2. Create API key
        key_res = client.post(
            "/api/v1/enterprise/api-keys",
            json={"org_id": org_id, "name": "ATS Ingest Key", "scopes": ["verify:read", "verify:write"]},
        )
        assert key_res.status_code == 200
        key_data = key_res.json()
        assert key_data["raw_api_key"].startswith("ll_live_")
        key_id = key_data["key_id"]

        # 3. List keys
        list_res = client.get(f"/api/v1/enterprise/api-keys?org_id={org_id}")
        assert list_res.status_code == 200
        assert len(list_res.json()) >= 1

        # 4. Revoke key
        del_res = client.delete(f"/api/v1/enterprise/api-keys/{key_id}")
        assert del_res.status_code == 200
        assert del_res.json()["status"] == "revoked"

    def test_api_webhook_and_test_dispatch(self, client: TestClient):
        # Register webhook
        wh_res = client.post(
            "/api/v1/webhooks/subscriptions",
            json={
                "org_id": "org-default-enterprise",
                "target_url": "https://ats.example.com/alerts",
                "subscribed_events": ["risk.high_detected"],
            },
        )
        assert wh_res.status_code == 200
        sub_id = wh_res.json()["subscription_id"]

        # Test dispatch
        disp_res = client.post(
            "/api/v1/webhooks/test-dispatch",
            json={
                "org_id": "org-default-enterprise",
                "event_type": "risk.high_detected",
                "data": {"candidate": "Jane Doe", "verdict": "HIGH_RISK"},
            },
        )
        assert disp_res.status_code == 200
        events = disp_res.json()
        assert len(events) >= 1
        assert "v1=" in events[0]["signature_header"]

        # Delete webhook
        del_res = client.delete(f"/api/v1/webhooks/subscriptions/{sub_id}")
        assert del_res.status_code == 200

    def test_api_analytics_endpoint_with_auth(self, client: TestClient):
        # Query with default demo key
        demo_key = "ll_live_enterprise_demo_key_abcdef1234567890"
        res = client.get(
            "/api/v1/enterprise/analytics?org_id=org-default-enterprise",
            headers={"X-API-Key": demo_key},
        )
        assert res.status_code == 200
        data = res.json()
        assert "total_verifications" in data
        assert "risk_distribution" in data
        assert "top_threat_categories" in data

    def test_api_analytics_invalid_key_401(self, client: TestClient):
        res = client.get(
            "/api/v1/enterprise/analytics",
            headers={"X-API-Key": "ll_live_invalid_key_12345"},
        )
        assert res.status_code == 401


# ==============================================================================
# 3. PYTHON DEVELOPER SDK INTEGRATION TESTS
# ==============================================================================

class TestPythonDeveloperSDK:
    def test_sdk_methods_with_test_client(self, monkeypatch):
        test_client = TestClient(app)

        # Route requests through FastAPI TestClient rather than real HTTP sockets
        def mock_request(method, url, **kwargs):
            path = url.replace("http://localhost:8000", "")
            json_body = kwargs.get("json")
            headers = kwargs.get("headers")
            return test_client.request(method, path, json=json_body, headers=headers)

        sdk = LifeLensClient(
            api_key="ll_live_enterprise_demo_key_abcdef1234567890",
            base_url="http://localhost:8000",
        )
        monkeypatch.setattr(sdk.client, "request", mock_request)

        # 1. Test Scam Text Detection
        scam_res = sdk.detect_scam_text("Urgent hiring! Send registration fee via Telegram.")
        assert "binary_label" in scam_res
        assert scam_res["binary_label"] in ["SCAM", "LEGITIMATE"]

        # 2. Test Phishing URL Detection
        phish_res = sdk.detect_phishing_url("http://secure-login.paypa1-update.biz/login")
        assert "is_phishing" in phish_res

        # 3. Test Full Job Verification
        verify_res = sdk.verify_job(
            job_title="Software Architect",
            company_name="DeepMind",
            company_website="https://deepmind.google",
            recruiter_email="careers@deepmind.google",
        )
        assert "risk_level" in verify_res
        assert verify_res["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

        # 4. Test Incident Recovery Initiation
        rec_res = sdk.initiate_recovery(
            incident_type="ADVANCE_FEE_PAID",
            financial_amount_lost=500.0,
            currency="USD",
            compromised_accounts=["bank_account"],
        )
        assert "recovery_id" in rec_res
        assert rec_res["status"] == "ACTIVE"

        # 5. Test Enterprise Analytics
        analytics = sdk.get_enterprise_analytics("org-default-enterprise")
        assert "total_verifications" in analytics

        # 6. Test Webhook Signature Verification Helper
        secret = "whsec_test_secret_key_123456"
        ts = int(time.time())
        import json
        payload = json.dumps({"event": "risk.high_detected"}, sort_keys=True)
        sig_header = EnterpriseService.sign_payload(secret, ts, payload)

        assert LifeLensClient.verify_webhook_signature(secret, sig_header, payload) is True
        assert LifeLensClient.verify_webhook_signature("whsec_wrong_key", sig_header, payload) is False
