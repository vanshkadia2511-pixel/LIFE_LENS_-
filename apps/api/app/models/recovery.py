"""
LifeLens Ω — Phase 6: Post-Incident Recovery Automation Models
Implementation Plan §6 & Evolved Blueprint Phase 6 (Months 19-21)

Domain models for:
- Incident categorization and damage assessment
- Account criticality prioritization (Tier 1 to Tier 4)
- Actionable credential rotation & containment steps
- Trusted contact notifications
- Regulatory / law enforcement complaint packets (IC3, FTC, Action Fraud, NCRP)
"""
from __future__ import annotations
from enum import Enum
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone


class IncidentType(str, Enum):
    CREDENTIAL_THEFT = "CREDENTIAL_THEFT"            # Phishing password/2FA theft
    IDENTITY_THEFT = "IDENTITY_THEFT"                # SSN/Passport/Govt ID harvesting
    ADVANCE_FEE_PAID = "ADVANCE_FEE_PAID"            # Wire, gift cards, crypto, Zelle
    SESSION_HIJACK = "SESSION_HIJACK"                # Cookie theft, token hijack
    MALWARE_EXECUTED = "MALWARE_EXECUTED"            # Fraudulent screening software
    OFF_PLATFORM_EXTORTION = "OFF_PLATFORM_EXTORTION"# Telegram/WhatsApp blackmail


class AccountTier(str, Enum):
    TIER_1_CRITICAL = "TIER_1_CRITICAL"   # Primary Email, Banking, Crypto Wallets
    TIER_2_HIGH = "TIER_2_HIGH"           # Govt Portals, Password Managers, Secondary Email
    TIER_3_MEDIUM = "TIER_3_MEDIUM"       # Professional (LinkedIn), Cloud Storage
    TIER_4_LOW = "TIER_4_LOW"             # Social Media, General E-Commerce


class UrgencyLevel(str, Enum):
    IMMEDIATE_15_MIN = "IMMEDIATE_15_MIN" # Financial drain / active session in progress
    HIGH_1_HOUR = "HIGH_1_HOUR"           # Credential harvest without confirmed transaction
    STANDARD_24_HOUR = "STANDARD_24_HOUR" # Identity exposure, preventative freeze


class ActionType(str, Enum):
    FREEZE_FINANCIAL = "FREEZE_FINANCIAL"
    CREDIT_BUREAU_FREEZE = "CREDIT_BUREAU_FREEZE"
    ROTATE_CREDENTIALS = "ROTATE_CREDENTIALS"
    REVOKE_ALL_SESSIONS = "REVOKE_ALL_SESSIONS"
    ENABLE_HARDWARE_MFA = "ENABLE_HARDWARE_MFA"
    DISCONNECT_DEVICE = "DISCONNECT_DEVICE"
    NOTIFY_TRUSTED_CONTACTS = "NOTIFY_TRUSTED_CONTACTS"
    FILE_REGULATORY_REPORT = "FILE_REGULATORY_REPORT"


class RecoveryStep(BaseModel):
    step_id: str
    order: int
    tier: AccountTier
    action_type: ActionType
    target_service: str
    title: str
    instructions: str
    direct_url: Optional[str] = None
    estimated_minutes: int
    completed: bool = False
    completed_at: Optional[str] = None

    model_config = ConfigDict(protected_namespaces=())


class DamageAssessment(BaseModel):
    severity_score: float = Field(..., ge=0.0, le=1.0)
    severity_label: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    urgency_level: UrgencyLevel
    estimated_financial_loss: float
    currency: str
    compromised_identity_assets: List[str]
    blast_radius_summary: str
    containment_directives: List[str]

    model_config = ConfigDict(protected_namespaces=())


class IncidentReport(BaseModel):
    incident_id: str
    user_id: Optional[str] = "local-user"
    incident_type: IncidentType
    financial_amount_lost: float = 0.0
    currency: str = "USD"
    compromised_accounts: List[str] = Field(default_factory=list)
    scammer_identifiers: Dict[str, Any] = Field(default_factory=dict)
    description: str = ""
    occurred_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    model_config = ConfigDict(protected_namespaces=())


class RecoveryPlan(BaseModel):
    recovery_id: str
    incident: IncidentReport
    assessment: DamageAssessment
    steps: List[RecoveryStep]
    total_steps: int
    completed_steps: int
    estimated_total_minutes: int
    status: Literal["ACTIVE", "IN_PROGRESS", "COMPLETED"]
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    model_config = ConfigDict(protected_namespaces=())


class TrustedContact(BaseModel):
    name: str
    relationship: str
    contact_channel: Literal["EMAIL", "SMS", "WEBHOOK"]
    destination: str

    model_config = ConfigDict(protected_namespaces=())


class ContactNotificationResult(BaseModel):
    recipient: str
    channel: str
    status: Literal["SENT", "SIMULATED", "FAILED"]
    sent_at: str
    message_preview: str

    model_config = ConfigDict(protected_namespaces=())


class RegulatoryAgency(str, Enum):
    FBI_IC3 = "FBI_IC3"                    # US Federal Bureau of Investigation
    FTC = "FTC"                            # US Federal Trade Commission
    ACTION_FRAUD_UK = "ACTION_FRAUD_UK"    # UK National Fraud & Cyber Crime
    NCRP_INDIA = "NCRP_INDIA"              # India Cyber Crime Reporting Portal
    INTERPOL = "INTERPOL"                  # International Cross-Border


class RegulatoryComplaintPacket(BaseModel):
    agency: RegulatoryAgency
    agency_full_name: str
    complaint_reference: str
    incident_summary: str
    monetary_loss: str
    perpetrator_identifiers: Dict[str, Any]
    evidence_fingerprint_sha256: str
    narrative: str
    submission_portal_url: str
    formatted_complaint_text: str
    generated_at: str
    is_filed_automatically: bool = False
    submission_api_available: bool = False
    filing_disclaimer: str = (
        "This packet is prepared for manual submission by the victim. "
        "LifeLens Ω does not file complaints automatically. "
        "No public filing API exists for this portal. "
        "Confirm all portal URLs and official helplines are current."
    )

    model_config = ConfigDict(protected_namespaces=())
