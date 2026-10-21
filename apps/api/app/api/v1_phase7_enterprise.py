"""
LifeLens Ω — Phase 7: Enterprise & Developer Webhooks API Router
Evolved Blueprint Phase 7 (Months 22-24)

Endpoints:
- POST   /api/v1/enterprise/organizations            -> Register organization
- GET    /api/v1/enterprise/organizations/{org_id}   -> Get organization details
- POST   /api/v1/enterprise/api-keys                 -> Create scoped API key
- GET    /api/v1/enterprise/api-keys                 -> List API keys for org
- DELETE /api/v1/enterprise/api-keys/{key_id}        -> Revoke API key
- GET    /api/v1/enterprise/analytics                -> Real-time enterprise analytics
- POST   /api/v1/webhooks/subscriptions              -> Register webhook listener
- GET    /api/v1/webhooks/subscriptions              -> List webhooks
- DELETE /api/v1/webhooks/subscriptions/{sub_id}     -> Delete webhook
- POST   /api/v1/webhooks/test-dispatch              -> Dispatch signed test event
"""
from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel, Field

from apps.api.app.models.enterprise import (
    EnterpriseTier,
    ApiKeyScope,
    WebhookEventType,
    Organization,
    ApiKey,
    ApiKeyCreateResponse,
    WebhookSubscription,
    WebhookEventPayload,
    EnterpriseAnalytics,
)
from apps.api.app.services.enterprise_service import enterprise_service

router = APIRouter(tags=["phase7-enterprise"])


class CreateOrgRequest(BaseModel):
    name: str = Field(..., description="Organization name")
    tier: EnterpriseTier = Field(EnterpriseTier.STARTUP, description="Subscription tier")
    contact_email: str = Field(..., description="Administrative email")


class CreateApiKeyRequest(BaseModel):
    org_id: str = Field("org-default-enterprise", description="Organization ID")
    name: str = Field("Production API Key", description="Descriptive label")
    scopes: List[ApiKeyScope] = Field(
        default_factory=lambda: [ApiKeyScope.VERIFY_READ, ApiKeyScope.VERIFY_WRITE, ApiKeyScope.ML_INFERENCE],
        description="Permission scopes",
    )


class CreateWebhookRequest(BaseModel):
    org_id: str = Field("org-default-enterprise", description="Organization ID")
    target_url: str = Field(..., description="HTTPS endpoint to receive events")
    subscribed_events: List[WebhookEventType] = Field(
        default_factory=lambda: [
            WebhookEventType.VERIFICATION_COMPLETED,
            WebhookEventType.HIGH_RISK_DETECTED,
            WebhookEventType.CRITICAL_SCAM_FLAGGED,
        ],
        description="Event types to subscribe to",
    )


class TestDispatchEventRequest(BaseModel):
    org_id: str = Field("org-default-enterprise", description="Organization ID")
    event_type: WebhookEventType = WebhookEventType.HIGH_RISK_DETECTED
    data: dict = Field(
        default_factory=lambda: {
            "job_title": "Executive Recruiter Scam",
            "risk_level": "CRITICAL",
            "detected_signals": ["upfront_fee_requested", "domain_mismatch"],
        }
    )


# =============================================================================
# 1. ORGANIZATIONS
# =============================================================================

@router.post("/api/v1/enterprise/organizations", response_model=Organization, summary="Register Organization")
async def create_organization(req: CreateOrgRequest) -> Organization:
    return enterprise_service.create_organization(req.name, req.tier, req.contact_email)


@router.get("/api/v1/enterprise/organizations/{org_id}", response_model=Organization, summary="Get Organization Details")
async def get_organization(org_id: str) -> Organization:
    org = enterprise_service.get_organization(org_id)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization '{org_id}' not found.")
    return org


# =============================================================================
# 2. API KEYS
# =============================================================================

@router.post("/api/v1/enterprise/api-keys", response_model=ApiKeyCreateResponse, summary="Generate Scoped API Key")
async def create_api_key(req: CreateApiKeyRequest) -> ApiKeyCreateResponse:
    org = enterprise_service.get_organization(req.org_id)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization '{req.org_id}' not found.")
    key_resp, _ = enterprise_service.create_api_key(req.org_id, req.name, req.scopes)
    return key_resp


@router.get("/api/v1/enterprise/api-keys", response_model=List[ApiKey], summary="List Organization API Keys")
async def list_api_keys(org_id: str = Query("org-default-enterprise")) -> List[ApiKey]:
    return enterprise_service.list_api_keys(org_id)


@router.delete("/api/v1/enterprise/api-keys/{key_id}", summary="Revoke API Key")
async def revoke_api_key(key_id: str) -> dict:
    success = enterprise_service.revoke_api_key(key_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"API Key '{key_id}' not found.")
    return {"status": "revoked", "key_id": key_id}


# =============================================================================
# 3. WEBHOOKS
# =============================================================================

@router.post("/api/v1/webhooks/subscriptions", response_model=WebhookSubscription, summary="Create Webhook Subscription")
async def create_webhook(req: CreateWebhookRequest) -> WebhookSubscription:
    return enterprise_service.create_webhook_subscription(
        req.org_id, req.target_url, req.subscribed_events
    )


@router.get("/api/v1/webhooks/subscriptions", response_model=List[WebhookSubscription], summary="List Webhook Subscriptions")
async def list_webhooks(org_id: str = Query("org-default-enterprise")) -> List[WebhookSubscription]:
    return enterprise_service.list_webhook_subscriptions(org_id)


@router.delete("/api/v1/webhooks/subscriptions/{sub_id}", summary="Delete Webhook Subscription")
async def delete_webhook(sub_id: str) -> dict:
    success = enterprise_service.delete_webhook_subscription(sub_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Webhook subscription '{sub_id}' not found.")
    return {"status": "deleted", "subscription_id": sub_id}


@router.post("/api/v1/webhooks/test-dispatch", response_model=List[WebhookEventPayload], summary="Dispatch Test Signed Webhook Event")
async def dispatch_test_event(req: TestDispatchEventRequest) -> List[WebhookEventPayload]:
    events = enterprise_service.dispatch_event(req.org_id, req.event_type, req.data)
    return events


# =============================================================================
# 4. ENTERPRISE ANALYTICS & TELEMETRY
# =============================================================================

@router.get("/api/v1/enterprise/analytics", response_model=EnterpriseAnalytics, summary="Get Enterprise Analytics & Telemetry")
async def get_analytics(
    org_id: str = Query("org-default-enterprise", description="Organization ID"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> EnterpriseAnalytics:
    if x_api_key:
        api_key = enterprise_service.authenticate_api_key(x_api_key)
        if not api_key:
            raise HTTPException(status_code=401, detail="Invalid API Key.")
        allowed, remaining = enterprise_service.check_rate_limit(api_key)
        if not allowed:
            raise HTTPException(status_code=429, detail="API rate limit exceeded.")

    return enterprise_service.get_analytics(org_id)
