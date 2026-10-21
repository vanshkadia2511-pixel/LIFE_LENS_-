"""
LifeLens Ω — Database Models
Implementation Plan §39–40

Tables (§39):
  verification_requests
  entities
  claims
  evidence
  risk_signals
  cect_assessments
  verification_sources
  user_feedback
  audit_events
  adapter_runs

Relationships (§40):
  verification_request
    ├── entities → claims → evidence
    ├── verification_sources
    ├── cect_assessment
    ├── risk_signals
    └── user_feedback
"""
from __future__ import annotations
import os
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Enum as SAEnum, Float, ForeignKey,
    Integer, JSON, String, Text, create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./lifelens.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# verification_requests
# ---------------------------------------------------------------------------

class VerificationRequestDB(Base):
    __tablename__ = "verification_requests"

    id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=get_utc_now)
    status = Column(String, default="PENDING")       # PENDING | PROCESSING | COMPLETE | FAILED

    source_platform = Column(String, nullable=True)
    job_title = Column(String, nullable=True)
    job_description = Column(Text, nullable=True)
    company_name = Column(String, nullable=True)
    company_website = Column(String, nullable=True)
    recruiter_name = Column(String, nullable=True)
    recruiter_email = Column(String, nullable=True)
    recruiter_phone = Column(String, nullable=True)
    claimed_country = Column(String, nullable=True)
    claimed_location = Column(String, nullable=True)
    consent_for_analysis = Column(Boolean, default=False)

    # Result summary (populated after processing)
    risk_level = Column(String, nullable=True)       # LOW | MEDIUM | HIGH | CRITICAL
    risk_confidence = Column(String, nullable=True)  # LOW | MEDIUM | HIGH

    # Versioning (§73)
    cect_version = Column(String, nullable=True)
    risk_config_version = Column(String, nullable=True)
    extractor_version = Column(String, nullable=True)

    # Relationships
    entities = relationship("EntityDB", back_populates="request", cascade="all, delete-orphan")
    cect_assessment = relationship("CECTAssessmentDB", back_populates="request", uselist=False, cascade="all, delete-orphan")
    risk_signals = relationship("RiskSignalDB", back_populates="request", cascade="all, delete-orphan")
    verification_sources = relationship("VerificationSourceDB", back_populates="request", cascade="all, delete-orphan")
    user_feedback = relationship("UserFeedbackDB", back_populates="request", cascade="all, delete-orphan")
    adapter_runs = relationship("AdapterRunDB", back_populates="request", cascade="all, delete-orphan")
    audit_events = relationship("AuditEventDB", back_populates="request", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# entities
# ---------------------------------------------------------------------------

class EntityDB(Base):
    __tablename__ = "entities"

    id = Column(String, primary_key=True)
    request_id = Column(String, ForeignKey("verification_requests.id"), nullable=False)

    entity_type = Column(String, nullable=False)    # COMPANY | RECRUITER | AGENCY
    claimed_name = Column(String, nullable=True)
    claimed_role = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)
    normalized_name = Column(String, nullable=True)
    verification_status = Column(String, default="UNKNOWN")
    verification_confidence = Column(Float, default=0.0)
    source_references = Column(JSON, default=list)

    request = relationship("VerificationRequestDB", back_populates="entities")
    claims = relationship("ClaimDB", back_populates="entity", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# claims
# ---------------------------------------------------------------------------

class ClaimDB(Base):
    __tablename__ = "claims"

    id = Column(String, primary_key=True)
    entity_id = Column(String, ForeignKey("entities.id"), nullable=False)

    claim_text = Column(Text, nullable=False)
    claim_type = Column(String, nullable=False)
    source = Column(String, nullable=True)

    supporting_evidence_ids = Column(JSON, default=list)
    contradicting_evidence_ids = Column(JSON, default=list)

    verification_status = Column(String, default="UNVERIFIED")
    confidence = Column(Float, default=0.0)

    first_observed_at = Column(DateTime, default=get_utc_now)
    last_observed_at = Column(DateTime, default=get_utc_now)

    entity = relationship("EntityDB", back_populates="claims")
    evidence = relationship("EvidenceDB", back_populates="claim", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# evidence
# ---------------------------------------------------------------------------

class EvidenceDB(Base):
    __tablename__ = "evidence"

    id = Column(String, primary_key=True)
    claim_id = Column(String, ForeignKey("claims.id"), nullable=False)

    source_type = Column(String, nullable=False)
    source_name = Column(String, nullable=False)
    source_url = Column(String, nullable=True)
    observed_value = Column(Text, nullable=False)
    captured_at = Column(DateTime, default=get_utc_now)

    source_authority = Column(Float, default=0.0)
    source_independence = Column(Float, default=0.0)
    user_verifiable = Column(Boolean, default=False)
    verification_path = Column(Text, nullable=True)
    evidence_strength = Column(Float, default=0.0)
    source_status = Column(String, default="AVAILABLE")

    claim = relationship("ClaimDB", back_populates="evidence")


# ---------------------------------------------------------------------------
# risk_signals
# ---------------------------------------------------------------------------

class RiskSignalDB(Base):
    __tablename__ = "risk_signals"

    id = Column(String, primary_key=True)
    request_id = Column(String, ForeignKey("verification_requests.id"), nullable=False)

    category = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String, nullable=False)
    reliability = Column(Float, default=0.5)
    evidence_ids = Column(JSON, default=list)
    detected_by = Column(String, nullable=True)

    request = relationship("VerificationRequestDB", back_populates="risk_signals")


# ---------------------------------------------------------------------------
# cect_assessments
# ---------------------------------------------------------------------------

class CECTAssessmentDB(Base):
    __tablename__ = "cect_assessments"

    id = Column(String, primary_key=True)
    request_id = Column(String, ForeignKey("verification_requests.id"), nullable=False, unique=True)

    coherence_score = Column(Float, default=0.0)
    evidence_independence_score = Column(Float, default=0.0)
    consistency_score = Column(Float, default=0.0)
    trajectory_score = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)

    findings = Column(JSON, default=list)
    supporting_evidence_ids = Column(JSON, default=list)
    contradicting_evidence_ids = Column(JSON, default=list)

    request = relationship("VerificationRequestDB", back_populates="cect_assessment")


# ---------------------------------------------------------------------------
# verification_sources
# ---------------------------------------------------------------------------

class VerificationSourceDB(Base):
    __tablename__ = "verification_sources"

    id = Column(String, primary_key=True)
    request_id = Column(String, ForeignKey("verification_requests.id"), nullable=False)

    source_name = Column(String, nullable=False)
    source_url = Column(String, nullable=True)
    adapter_name = Column(String, nullable=False)
    status = Column(String, nullable=False)      # AVAILABLE | UNAVAILABLE | STALE etc.
    result_summary = Column(Text, nullable=True)
    confidence = Column(Float, default=0.0)
    checked_at = Column(DateTime, default=get_utc_now)
    error_message = Column(Text, nullable=True)

    request = relationship("VerificationRequestDB", back_populates="verification_sources")


# ---------------------------------------------------------------------------
# user_feedback
# ---------------------------------------------------------------------------

class UserFeedbackDB(Base):
    __tablename__ = "user_feedback"

    id = Column(String, primary_key=True)
    request_id = Column(String, ForeignKey("verification_requests.id"), nullable=False)

    feedback_type = Column(String, nullable=False)   # false_positive | false_negative | accurate
    comment = Column(Text, nullable=True)
    confirmed_outcome = Column(String, nullable=True)  # LEGITIMATE | SCAM | UNKNOWN
    submitted_at = Column(DateTime, default=get_utc_now)

    # NOTE: Do not automatically treat user feedback as ground truth (§41)
    reviewed = Column(Boolean, default=False)

    request = relationship("VerificationRequestDB", back_populates="user_feedback")


# ---------------------------------------------------------------------------
# audit_events (§72)
# ---------------------------------------------------------------------------

class AuditEventDB(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String, ForeignKey("verification_requests.id"), nullable=True)

    event_type = Column(String, nullable=False)
    actor = Column(String, nullable=True)          # system component that triggered event
    resource = Column(String, nullable=True)
    action = Column(String, nullable=False)
    result = Column(String, nullable=True)
    timestamp = Column(DateTime, default=get_utc_now)

    # NOTE: Do NOT log passwords, tokens, or unnecessary private data (§72)
    event_metadata = Column(JSON, default=dict)

    request = relationship("VerificationRequestDB", back_populates="audit_events")


# ---------------------------------------------------------------------------
# adapter_runs
# ---------------------------------------------------------------------------

class AdapterRunDB(Base):
    __tablename__ = "adapter_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String, ForeignKey("verification_requests.id"), nullable=False)

    adapter_name = Column(String, nullable=False)
    adapter_version = Column(String, nullable=True)
    started_at = Column(DateTime, default=get_utc_now)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False)         # SUCCESS | TIMEOUT | RATE_LIMITED | etc.
    latency_ms = Column(Integer, nullable=True)
    error_detail = Column(Text, nullable=True)

    request = relationship("VerificationRequestDB", back_populates="adapter_runs")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_tables() -> None:
    """Create all tables. Called on application startup."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency: yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
