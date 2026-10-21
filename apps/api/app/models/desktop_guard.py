"""
LifeLens Ω — Desktop Call Guard Models & Schemas
Phase C: Local Platform-Agnostic Desktop Guard (Layers 2, 3, 4, Receipt)
"""
from __future__ import annotations
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class DesktopSignalType(str, Enum):
    SIG_CALL_TRANSFER_REQUEST = "SIG_CALL_TRANSFER_REQUEST"
    SIG_CALL_SECRECY_DEMAND = "SIG_CALL_SECRECY_DEMAND"
    SIG_CALL_URGENCY_PRESSURE = "SIG_CALL_URGENCY_PRESSURE"
    SIG_CALL_CREDENTIAL_REQUEST = "SIG_CALL_CREDENTIAL_REQUEST"
    SIG_REMOTE_ACCESS_REQUEST = "SIG_REMOTE_ACCESS_REQUEST"
    SIG_OFFICIAL_IMPERSONATION = "SIG_OFFICIAL_IMPERSONATION"
    SIG_PAYMENT_DETAILS = "SIG_PAYMENT_DETAILS"


class DesktopGuardStartRequest(BaseModel):
    platform: str = Field("zoom", description="Platform hint e.g. zoom, whatsapp_desktop, meet, teams, telegram")
    session_title: Optional[str] = Field("Protected Call", description="Optional label for the session")
    consent_flag: bool = Field(False, description="Explicit user consent to run local transcript guard (§P5/§P6)")


class DesktopGuardSessionState(BaseModel):
    session_id: str
    is_active: bool
    guard_indicator: str = Field("GUARD_OFF", description="'GUARD_ON' or 'GUARD_OFF'")
    platform: str
    started_at: str
    status_message: str
    active_interstitial: bool = False


class DesktopGuardChunkRequest(BaseModel):
    session_id: str
    transcript_text: str = Field(..., description="Local ASR streaming transcript segment")
    speaker: Optional[str] = Field("remote_caller", description="'remote_caller' or 'user'")
    timestamp_ms: Optional[int] = None


class DesktopGuardAlert(BaseModel):
    alert_id: str
    session_id: str
    signal_type: DesktopSignalType
    severity: str = "HIGH"
    trigger_phrase: str
    detected_at: str
    latency_ms: float
    description: str
    recommended_action: str


class CallbackChecklistItem(BaseModel):
    step_id: int
    title: str
    instruction: str
    completed: bool = False


class VerificationInterstitial(BaseModel):
    interstitial_id: str
    session_id: str
    requires_pause: bool = True
    headline: str = "PAUSE: High-risk request detected. Do NOT pay, transfer money, or share credentials."
    cooling_off_minutes: int = 15
    callback_checklist: List[CallbackChecklistItem] = Field(default_factory=list)
    suggested_code_word: Optional[str] = None
    created_at: str


class LivenessChallenge(BaseModel):
    challenge_id: str
    action_instruction: str
    rationale: str
    evaluation_guidance: str
    automated_verdict_claimed: bool = False


class DesktopGuardEndRequest(BaseModel):
    session_id: str
    opt_in_retain_transcript: bool = Field(False, description="Default false: transcript purged immediately")


class PostCallReceipt(BaseModel):
    receipt_id: str
    session_id: str
    platform: str
    duration_seconds: int
    signals_fired: List[DesktopGuardAlert] = Field(default_factory=list)
    requests_detected: List[str] = Field(default_factory=list)
    verification_steps_completed: List[str] = Field(default_factory=list)
    ledger_entry_hash: str
    transcript_retained: bool = False
    disclaimer: str = (
        "Post-call receipt generated locally by LifeLens Ω. "
        "No raw audio/video was recorded or persisted. Signal is not proof (§P2)."
    )
