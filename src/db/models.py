"""
LifeLens Ω - Database Models (SQLAlchemy ORM)
PostgreSQL schemas with full relationship mapping.
"""

from sqlalchemy import (
    create_engine, Column, String, Float, Integer, DateTime,
    Boolean, Text, ForeignKey, Enum as SQLEnum, JSON, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from typing import Optional, List
from datetime import datetime
from enum import Enum
import os
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE SETUP
# ============================================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://lifelens:password@localhost:5432/lifelens_db"
)

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ============================================================================
# ENUMS
# ============================================================================

class RiskLevelEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FrictionLevelEnum(int, Enum):
    SILENT_OBSERVE = 0
    SMALL_NOTICE = 1
    EXPLANATION = 2
    CONFIRMATION = 3
    VERIFICATION = 4
    COOLING_OFF = 5
    EMERGENCY_PROTECTION = 6


class EventTypeEnum(str, Enum):
    MESSAGE = "message"
    CALL = "call"
    PAYMENT_REQUEST = "payment_request"
    LINK_CLICK = "link_click"
    FILE_UPLOAD = "file_upload"
    EMAIL = "email"


# ============================================================================
# DATABASE MODELS
# ============================================================================

class UserModel(Base):
    """Represents a LifeLens user."""

    __tablename__ = "users"

    user_id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Privacy Settings
    consent_analysis = Column(Boolean, default=False)
    consent_learning = Column(Boolean, default=False)
    consent_global_sharing = Column(Boolean, default=False)
    consent_updated_at = Column(DateTime, nullable=True)

    # Preferences
    friction_preference = Column(SQLEnum(FrictionLevelEnum), default=FrictionLevelEnum.CONFIRMATION)
    language = Column(String(10), default="en")
    timezone = Column(String(50), default="UTC")

    # Account Status
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    premium_expires_at = Column(DateTime, nullable=True)

    # Relationships
    entities = relationship("EntityModel", back_populates="user", cascade="all, delete-orphan")
    events = relationship("EventModel", back_populates="user", cascade="all, delete-orphan")
    assessments = relationship("AssessmentModel", back_populates="user", cascade="all, delete-orphan")
    baselines = relationship("BaselineModel", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_user_email_active', 'email', 'is_active'),
        Index('idx_user_created', 'created_at'),
    )


class EntityModel(Base):
    """Represents a person, organization, or service that interacts with the user."""

    __tablename__ = "entities"

    entity_id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False, index=True)

    # Identity
    entity_type = Column(String(50), nullable=False)
    claimed_identity = Column(String(255), nullable=False)
    claimed_authority = Column(String(255), nullable=True)
    claimed_email = Column(String(255), nullable=True)
    claimed_phone = Column(String(20), nullable=True)

    # Verified Information
    verified_identity = Column(String(255), nullable=True)
    verified_authority = Column(String(255), nullable=True)
    verification_timestamp = Column(DateTime, nullable=True)
    verification_method = Column(String(100), nullable=True)

    # Relationship
    relationship_to_user = Column(String(50), default="unknown")
    trust_level = Column(Float, default=0.5)
    is_blocked = Column(Boolean, default=False)
    is_trusted = Column(Boolean, default=False)

    # Risk Signals
    global_risk_score = Column(Float, default=0.0)
    global_report_count = Column(Integer, default=0)
    prior_incidents = Column(JSON, default=list)

    # Timestamps
    first_contact_at = Column(DateTime, default=datetime.utcnow)
    last_contact_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("UserModel", back_populates="entities")
    events = relationship(
        "EventModel",
        back_populates="source_entity",
        foreign_keys="EventModel.source_entity_id"
    )
    baseline = relationship(
        "BaselineModel",
        back_populates="entity",
        uselist=False,
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index('idx_entity_user_identity', 'user_id', 'claimed_identity'),
        Index('idx_entity_trust_level', 'user_id', 'trust_level'),
        Index('idx_entity_last_contact', 'last_contact_at'),
    )


class BaselineModel(Base):
    """Behavioral baseline for an entity."""

    __tablename__ = "baselines"

    baseline_id = Column(String(36), primary_key=True)
    entity_id = Column(String(36), ForeignKey("entities.entity_id"), nullable=False, unique=True, index=True)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False, index=True)

    # Linguistic
    avg_message_length = Column(Float, default=42.0)
    emotional_language_ratio = Column(Float, default=0.12)
    urgency_language_ratio = Column(Float, default=0.05)
    formal_informal_ratio = Column(Float, default=0.7)

    # Temporal
    active_hours_utc = Column(JSON, default=list)
    typical_response_latency_hours = Column(Float, default=4.0)
    message_frequency_per_day = Column(Float, default=2.0)

    # Interaction
    typical_request_types = Column(JSON, default=list)
    boundary_violations_frequency = Column(Float, default=0.0)
    financial_discussion_frequency = Column(Float, default=0.0)

    # Quality Metrics
    sample_size = Column(Integer, default=0)
    days_of_data = Column(Integer, default=0)
    confidence = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    entity = relationship("EntityModel", back_populates="baseline")
    user = relationship("UserModel", back_populates="baselines")


class EventModel(Base):
    """A digital interaction event."""

    __tablename__ = "events"

    event_id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False, index=True)
    source_entity_id = Column(String(36), ForeignKey("entities.entity_id"), nullable=True)

    # Event Details
    event_type = Column(SQLEnum(EventTypeEnum), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    source_channel = Column(String(50), nullable=False)

    # Content
    raw_content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)

    # Processing State
    processed_by = Column(JSON, default=list)
    user_action = Column(String(50), nullable=True)
    user_action_at = Column(DateTime, nullable=True)

    # Privacy Flags
    user_approved_analysis = Column(Boolean, default=False)
    user_approved_learning = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("UserModel", back_populates="events")
    source_entity = relationship(
        "EntityModel",
        foreign_keys=[source_entity_id],
        primaryjoin="EventModel.source_entity_id==EntityModel.entity_id"
    )
    assessment = relationship(
        "AssessmentModel",
        back_populates="event",
        uselist=False,
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index('idx_event_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_event_entity_timestamp', 'source_entity_id', 'timestamp'),
        Index('idx_event_content_hash', 'content_hash'),
        Index('idx_event_not_deleted', 'deleted_at'),
    )


class AssessmentModel(Base):
    """Reality Integrity Assessment result."""

    __tablename__ = "assessments"

    assessment_id = Column(String(36), primary_key=True)
    event_id = Column(String(36), ForeignKey("events.event_id"), nullable=False, unique=True, index=True)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False, index=True)

    # CECT Scores
    coherence_score = Column(Float, nullable=False)
    evidence_independence_score = Column(Float, nullable=False)
    consistency_score = Column(Float, nullable=False)
    trajectory_score = Column(Float, nullable=False)

    # Integrated Scores
    integrated_integrity_score = Column(Float, nullable=False)
    integrity_confidence = Column(Float, nullable=False)

    # Risk Assessment
    risk_level = Column(SQLEnum(RiskLevelEnum), nullable=False, index=True)
    risk_reversibility = Column(Float, nullable=False)
    point_of_no_return = Column(Integer, nullable=True)

    # Recommendation
    recommended_friction_level = Column(SQLEnum(FrictionLevelEnum), nullable=False)
    recommended_action = Column(String(100), nullable=False)
    alternative_actions = Column(JSON, default=list)

    # Explanation
    primary_concerns = Column(JSON, default=list)

    # Outcome Tracking
    user_followed_recommendation = Column(Boolean, nullable=True)
    actual_outcome = Column(String(100), nullable=True)
    outcome_confidence = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    event = relationship("EventModel", back_populates="assessment")
    user = relationship("UserModel", back_populates="assessments")

    __table_args__ = (
        Index('idx_assessment_user_created', 'user_id', 'created_at'),
        Index('idx_assessment_risk_level', 'user_id', 'risk_level'),
    )


class AuditLogModel(Base):
    """Immutable audit trail for all system decisions."""

    __tablename__ = "audit_logs"

    log_id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=True, index=True)
    event_id = Column(String(36), nullable=True, index=True)

    # Action Details
    action = Column(String(100), nullable=False)
    agent_name = Column(String(100), nullable=True)

    # Data Changed
    data_before = Column(JSON, nullable=True)
    data_after = Column(JSON, nullable=True)

    # Metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index('idx_audit_user_created', 'user_id', 'created_at'),
        Index('idx_audit_event', 'event_id'),
    )


# ============================================================================
# DATABASE HELPERS
# ============================================================================

def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def drop_tables():
    """Drop all tables (for development/testing only)."""
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped")
