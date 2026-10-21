"""
LifeLens Ω — Verification API Schemas
Implementation Plan §9, §15, §17, §21, §22
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VerificationApiRequest(BaseModel):
    """Incoming request payload from extension or web UI."""
    request_id: Optional[str] = None
    source_platform: Optional[str] = "LinkedIn"
    job_title: Optional[str] = None
    job_description: Optional[str] = None
    company_name: Optional[str] = None
    company_website: Optional[str] = None
    recruiter_name: Optional[str] = None
    recruiter_email: Optional[str] = None
    recruiter_phone: Optional[str] = None
    claimed_country: Optional[str] = "GB"
    claimed_location: Optional[str] = None
    consent_for_analysis: bool = True


class RiskSignalSchema(BaseModel):
    signal_id: str
    category: str
    description: str
    severity: str
    reliability: float
    detected_by: str
    evidence_ids: List[str] = []


class EvidenceCardSchema(BaseModel):
    evidence_id: str
    source_name: str
    source_type: str
    observed_value: str
    source_url: Optional[str] = None
    source_authority: float
    source_independence: float
    user_verifiable: bool
    verification_path: Optional[str] = None
    captured_at: str
    is_simulated: bool = False


class CECTScoresSchema(BaseModel):
    coherence: float
    evidence_independence: float
    consistency: float
    trajectory: float
    confidence: float


class ExplanationSchema(BaseModel):
    summary_headline: str
    confidence_label: str
    what_was_checked: List[str]
    what_was_found: List[str]
    why_it_matters: List[str]
    what_could_not_be_verified: List[str]
    recommended_next_steps: List[str]
    evidence_cards: List[EvidenceCardSchema]
    disclaimer: str


class VerificationApiResponse(BaseModel):
    """Outgoing response payload conforming to §21 and §22."""
    request_id: str
    processed_at: str
    risk_level: str
    risk_score: float
    confidence: float
    cect_scores: CECTScoresSchema
    signals: List[RiskSignalSchema]
    primary_concerns: List[str]
    mitigating_factors: List[str]
    explanation: ExplanationSchema


class FeedbackApiRequest(BaseModel):
    """Payload for submitting feedback on a verification result (§41, §68)."""
    request_id: str
    feedback_type: str                  # e.g., 'false_positive', 'false_negative', 'accurate', 'comment'
    comment: Optional[str] = None
    confirmed_outcome: Optional[str] = None  # e.g., 'LEGITIMATE', 'FRAUDULENT', 'UNSURE'


class FeedbackApiResponse(BaseModel):
    """Response confirming feedback storage."""
    status: str
    feedback_id: str
    request_id: str
    recorded_at: str

