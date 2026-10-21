"""
LifeLens Ω — Phase 7: Enterprise & Developer API Models
Evolved Blueprint Phase 7 (Months 22-24)

Domain models for:
- Multi-tenant organization accounts & subscription tiers
- Scoped API keys with cryptographically salted storage
- Webhook subscriptions & HMAC-SHA256 signed event delivery
- Enterprise security posture analytics & threat intelligence telemetry
"""
from __future__ import annotations
from enum import Enum
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone


class EnterpriseTier(str, Enum):
    FREE = "FREE"                 # 60 req/min
    STARTUP = "STARTUP"           # 300 req/min
    ENTERPRISE = "ENTERPRISE"     # 1,200 req/min, custom webhooks, SLA


class ApiKeyScope(str, Enum):
    VERIFY_READ = "verify:read"
    VERIFY_WRITE = "verify:write"
    ML_INFERENCE = "ml:inference"
    RECOVERY_MANAGE = "recovery:manage"
    WEBHOOKS_MANAGE = "webhooks:manage"
    ANALYTICS_READ = "analytics:read"
    ADMIN_ALL = "admin:*"


class WebhookEventType(str, Enum):
    VERIFICATION_COMPLETED = "verification.completed"
    HIGH_RISK_DETECTED = "risk.high_detected"
    CRITICAL_SCAM_FLAGGED = "scam.critical_flagged"
    RECOVERY_INITIATED = "recovery.initiated"
    THREAT_INTEL_MATCHED = "threat_intel.matched"


class Organization(BaseModel):
    org_id: str
    name: str
    tier: EnterpriseTier = EnterpriseTier.STARTUP
    contact_email: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: Literal["ACTIVE", "SUSPENDED"] = "ACTIVE"

    model_config = ConfigDict(protected_namespaces=())


class ApiKey(BaseModel):
    key_id: str
    org_id: str
    name: str
    key_prefix: str                        # First 8 chars e.g. "ll_live_a1b2..."
    key_hash: str                          # SHA-256 of full key for verification
    scopes: List[ApiKeyScope]
    rate_limit_per_minute: int = 300
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    revoked_at: Optional[str] = None
    is_active: bool = True

    model_config = ConfigDict(protected_namespaces=())


class ApiKeyCreateResponse(BaseModel):
    key_id: str
    name: str
    raw_api_key: str                       # Displayed ONLY ONCE upon creation
    key_prefix: str
    scopes: List[ApiKeyScope]
    rate_limit_per_minute: int
    created_at: str

    model_config = ConfigDict(protected_namespaces=())


class WebhookSubscription(BaseModel):
    subscription_id: str
    org_id: str
    target_url: str
    subscribed_events: List[WebhookEventType]
    secret_key: str                        # Used for HMAC-SHA256 signature
    status: Literal["ACTIVE", "PAUSED"] = "ACTIVE"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    model_config = ConfigDict(protected_namespaces=())


class WebhookEventPayload(BaseModel):
    event_id: str
    event_type: WebhookEventType
    org_id: str
    timestamp: str
    data: Dict[str, Any]
    signature_header: str                  # "t=1728...v1=hex_hmac"

    model_config = ConfigDict(protected_namespaces=())


class EnterpriseAnalytics(BaseModel):
    org_id: str
    tier: EnterpriseTier
    period: str
    total_verifications: int
    scams_blocked: int
    phishing_urls_detected: int
    recoveries_facilitated: int
    risk_distribution: Dict[str, int]      # {"LOW": 120, "MEDIUM": 45, "HIGH": 18, "CRITICAL": 5}
    top_threat_categories: List[Dict[str, Any]]
    average_latency_ms: float
    active_webhook_subscriptions: int

    model_config = ConfigDict(protected_namespaces=())
