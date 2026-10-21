"""
LifeLens Ω — Call Guardian Models & Schemas
Phase B: Layer 0 Pre-Call Link & Invite Checker
"""
from __future__ import annotations
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class CallGuardSignalType(str, Enum):
    SIG_CALL_INVITE_LOOKALIKE = "SIG_CALL_INVITE_LOOKALIKE"
    SIG_CALL_UNSOLICITED_CHANNEL = "SIG_CALL_UNSOLICITED_CHANNEL"
    SIG_CALL_URGENCY_FRAMING = "SIG_CALL_URGENCY_FRAMING"
    SIG_HOST_DOMAIN_MISMATCH = "SIG_HOST_DOMAIN_MISMATCH"
    SIG_SSRF_PROBE_BLOCKED = "SIG_SSRF_PROBE_BLOCKED"
    SIG_REDIRECT_UNRESOLVED = "SIG_REDIRECT_UNRESOLVED"


class SignalSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SignalProvenance(BaseModel):
    what: str
    where: str
    when: str
    source_reliability: str
    details: Dict[str, Any] = Field(default_factory=dict)


class CallGuardSignal(BaseModel):
    signal_id: str
    signal_type: CallGuardSignalType
    severity: SignalSeverity
    weight: float
    description: str
    provenance: SignalProvenance


class CallInviteCheckRequest(BaseModel):
    invite_url: str = Field(..., description="The meeting invite URL or hyperlink to inspect")
    platform_hint: Optional[str] = Field(None, description="Optional platform hint e.g. zoom, meet, teams, webex, whatsapp, telegram")
    channel: Optional[str] = Field(None, description="Channel invite arrived through e.g. telegram_dm, whatsapp_unknown_number, corporate_calendar, email")
    claimed_host_name: Optional[str] = Field(None, description="Optional claimed host name")
    claimed_host_email: Optional[str] = Field(None, description="Optional claimed host email address")
    message_context: Optional[str] = Field(None, description="Accompanying message text or invite description")
    consent_flag: bool = Field(False, description="Explicit user consent to inspect link metadata (P5/P6)")


class CallInviteAssessment(BaseModel):
    assessment_id: str
    invite_url: str
    canonical_url: str
    platform_detected: Optional[str] = None
    risk_score: float = Field(0.0, ge=0.0, le=1.0)
    verdict: str = Field(..., description="Rule A compliant verdict: 'Verification step completed', 'Needs Verification', or 'Request looks high-risk'")
    is_safe_to_join: bool = False
    signals: List[CallGuardSignal] = Field(default_factory=list)
    provenance: Dict[str, SignalProvenance] = Field(default_factory=dict)
    redirect_traces: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    disclaimer: str = (
        "Call Guardian Layer 0 inspects invite metadata only and never joins or records calls. "
        "Signal is not proof (§P2); verify critical requests via out-of-band channels (§P6)."
    )
