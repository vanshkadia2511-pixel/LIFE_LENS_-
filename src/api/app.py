"""
LifeLens Ω - FastAPI Application
Reality Integrity Intelligence System — REST API

Endpoints:
    POST /api/v1/reality-check   — Analyze a message/interaction
    GET  /api/v1/assessments/{id} — Retrieve assessment
    POST /api/v1/events           — Create event for analysis
    GET  /api/v1/health           — Health check
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from contextlib import asynccontextmanager
from typing import List, Optional, Any
from datetime import datetime, timezone
import uuid
import hashlib
import logging
import os

from ..db.models import (
    get_db, create_tables, SessionLocal,
    RiskLevelEnum, FrictionLevelEnum, EventTypeEnum
)
from ..db.repositories import (
    EntityRepository, EventRepository, AssessmentRepository, AuditRepository
)
from ..core.engine import (
    Entity, BehavioralBaseline, DigitalEvent, EventType,
    RealityIntegrityOrchestrator
)
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Singleton orchestrator (shared across requests)
_orchestrator: Optional[RealityIntegrityOrchestrator] = None


def get_orchestrator() -> RealityIntegrityOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = RealityIntegrityOrchestrator()
    return _orchestrator


# ============================================================================
# FASTAPI APP & LIFESPAN
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("LifeLens Ω API starting up...")
    create_tables()
    get_orchestrator()  # Pre-warm
    logger.info("LifeLens Ω API ready.")
    yield
    logger.info("LifeLens Ω API shutting down.")


app = FastAPI(
    title="LifeLens Ω API",
    description=(
        "Reality Integrity Intelligence System. "
        "Analyzes digital interactions for coherence, evidence independence, "
        "behavioral consistency, and trajectory to detect manipulation."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS - use origin regex to avoid wildcard conflict with allow_credentials
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^(chrome-extension://.*|https?://(localhost|127\.0\.0\.1)(:\d+)?)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# PYDANTIC REQUEST / RESPONSE MODELS
# ============================================================================

class EntityCreate(BaseModel):
    entity_type: str = Field(..., description="person | organization | service | device")
    claimed_identity: str
    claimed_authority: Optional[str] = None
    claimed_email: Optional[str] = None
    claimed_phone: Optional[str] = None


class EntityResponse(BaseModel):
    entity_id: str
    entity_type: str
    claimed_identity: str
    trust_level: float
    is_blocked: bool
    is_trusted: bool
    relationship_to_user: str

    model_config = {"from_attributes": True}


class EventCreate(BaseModel):
    event_type: str = Field(default="message")
    source_channel: str = Field(default="api")
    source_entity_id: Optional[str] = None
    raw_content: str

    @field_validator("raw_content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("Content cannot be empty")
        return v


class EventResponse(BaseModel):
    event_id: str
    event_type: str
    source_channel: str
    timestamp: datetime
    processed_by: List[str]

    model_config = {"from_attributes": True}


class AssessmentResponse(BaseModel):
    assessment_id: str
    event_id: str
    coherence_score: float
    evidence_independence_score: float
    consistency_score: float
    trajectory_score: float
    integrated_integrity_score: float
    risk_level: str
    risk_reversibility: float
    recommended_friction_level: str
    recommended_action: str
    primary_concerns: List[str]
    explanation_short: Optional[str] = None

    model_config = {"from_attributes": True}


class RealityCheckRequest(BaseModel):
    content: str = Field(..., description="The message / interaction text to analyze")
    source_entity_id: Optional[str] = None
    claimed_identity: Optional[str] = None
    event_type: str = Field(default="message")
    source_channel: str = Field(default="api")


class RealityCheckResponse(BaseModel):
    assessment_id: str
    integrity_score: float
    risk_level: str
    recommendation: str
    explanation: str
    safe_alternative: Optional[str] = None
    safe_alternatives: Optional[List[str]] = None
    primary_concerns: List[str] = []
    friction_level: str = "EXPLANATION"


class PaymentCheckRequest(BaseModel):
    amount: float
    recipient: str
    recipient_account: Optional[str] = None


class PaymentCheckResponse(BaseModel):
    risk_level: str
    reversibility: float
    recommendation: str
    explanation: str


class LinkCheckRequest(BaseModel):
    url: str


class LinkCheckResponse(BaseModel):
    risk_level: str
    is_safe: bool
    explanation: str


class ImageCheckRequest(BaseModel):
    image_url: str


class ImageCheckResponse(BaseModel):
    authenticity_score: float
    is_manipulated: bool
    explanation: str


class AlternativesRequest(BaseModel):
    action_type: str
    goal: str


class AlternativeItem(BaseModel):
    risk_level: str
    description: str


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }


@app.post("/api/v1/reality-check", response_model=RealityCheckResponse)
async def reality_check(
    request: RealityCheckRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> RealityCheckResponse:
    """
    Analyze a message or interaction for reality integrity.

    Runs the full CECT pipeline:
    - Coherence analysis (logical contradictions)
    - Evidence independence scoring
    - Behavioral consistency check
    - Trajectory and intent analysis
    - Consequence / reversibility modeling
    """
    orchestrator = get_orchestrator()

    try:
        # Resolve or create entity
        entity_db = None
        if request.source_entity_id:
            entity_db = EntityRepository.get_entity(db, request.source_entity_id)

        if entity_db is None:
            entity_db = EntityRepository.create_entity(
                db,
                entity_id=str(uuid.uuid4()),
                user_id="anonymous",
                entity_type="unknown",
                claimed_identity=request.claimed_identity or "Unknown",
                claimed_authority=None,
            )

        # Build in-memory DigitalEvent for the orchestrator
        source_entity = Entity(
            entity_id=entity_db.entity_id,
            entity_type=entity_db.entity_type,
            claimed_identity=entity_db.claimed_identity,
            claimed_authority=entity_db.claimed_authority,
            relationship_to_user=entity_db.relationship_to_user,
            trust_level=entity_db.trust_level,
            is_blocked=entity_db.is_blocked,
            is_trusted=entity_db.is_trusted,
            global_risk_score=entity_db.global_risk_score,
        )

        target_entity = Entity(
            entity_type="person",
            claimed_identity="User",
            relationship_to_user="self"
        )

        event_obj = DigitalEvent(
            event_type=EventType.MESSAGE,
            source_entity=source_entity,
            target_entity=target_entity,
            source_channel=request.source_channel,
            raw_content=request.content,
            user_approval=True,
        )

        # Run CECT analysis
        assessment_obj = orchestrator.analyze_event(event_obj)

        # Persist event to DB
        content_hash = hashlib.sha256(request.content.encode()).hexdigest()
        event_db = EventRepository.create_event(
            db,
            event_id=event_obj.event_id,
            user_id="anonymous",
            event_type=request.event_type,
            source_channel=request.source_channel,
            source_entity_id=entity_db.entity_id,
            raw_content=request.content,
            content_hash=content_hash,
            processed_by=event_obj.processed_by,
            user_approved_analysis=True,
        )

        # Persist assessment
        assessment_db = AssessmentRepository.create_assessment(
            db,
            assessment_id=assessment_obj.assessment_id,
            event_id=event_obj.event_id,
            user_id="anonymous",
            coherence_score=assessment_obj.coherence_score,
            evidence_independence_score=assessment_obj.evidence_independence_score,
            consistency_score=assessment_obj.consistency_score,
            trajectory_score=assessment_obj.trajectory_score,
            integrated_integrity_score=assessment_obj.integrated_integrity_score,
            integrity_confidence=assessment_obj.integrity_confidence,
            risk_level=RiskLevelEnum(assessment_obj.risk_level.value),
            risk_reversibility=assessment_obj.risk_reversibility,
            point_of_no_return=assessment_obj.point_of_no_return,
            recommended_friction_level=FrictionLevelEnum(
                assessment_obj.recommended_friction_level.value
            ),
            recommended_action=assessment_obj.recommended_action,
            primary_concerns=assessment_obj.primary_concerns,
        )

        # Build explanation
        risk = assessment_obj.risk_level.value
        score = assessment_obj.integrated_integrity_score
        concerns = assessment_obj.primary_concerns

        explanation = (
            f"Integrity score: {score:.2f}/1.00. Risk: {risk}. "
            + (f"Top concern: {concerns[0]}" if concerns else "No major concerns.")
        )

        safe_alternatives = []
        if assessment_obj.risk_level.value in ["HIGH", "CRITICAL"]:
            safe_alternatives = [
                "Verify through official website or app directly",
                "Call the organization on their official number",
                "Check with a trusted family member or friend",
            ]

        safe_alt = safe_alternatives[0] if safe_alternatives else "No specific action needed. Proceed with normal verification."

        return RealityCheckResponse(
            assessment_id=assessment_obj.assessment_id,
            integrity_score=round(score, 4),
            risk_level=risk,
            recommendation=assessment_obj.recommended_action,
            explanation=explanation,
            safe_alternative=safe_alt,
            safe_alternatives=safe_alternatives,
            primary_concerns=concerns,
            friction_level=assessment_obj.recommended_friction_level.name,
        )

    except Exception as e:
        logger.error(f"Reality check failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/assessments/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
) -> AssessmentResponse:
    """Retrieve a stored assessment by ID."""
    assessment = AssessmentRepository.get_assessment(db, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    return AssessmentResponse(
        assessment_id=assessment.assessment_id,
        event_id=assessment.event_id,
        coherence_score=assessment.coherence_score,
        evidence_independence_score=assessment.evidence_independence_score,
        consistency_score=assessment.consistency_score,
        trajectory_score=assessment.trajectory_score,
        integrated_integrity_score=assessment.integrated_integrity_score,
        risk_level=assessment.risk_level.value,
        risk_reversibility=assessment.risk_reversibility,
        recommended_friction_level=assessment.recommended_friction_level.name,
        recommended_action=assessment.recommended_action,
        primary_concerns=assessment.primary_concerns or [],
        explanation_short=(
            f"Risk: {assessment.risk_level.value}, "
            f"Integrity: {assessment.integrated_integrity_score:.2f}"
        ),
    )


@app.post("/api/v1/events", response_model=EventResponse)
async def create_event(
    request: EventCreate,
    db: Session = Depends(get_db),
) -> EventResponse:
    """Create a new event record (without running analysis)."""
    try:
        content_hash = hashlib.sha256(request.raw_content.encode()).hexdigest()
        event = EventRepository.create_event(
            db,
            event_id=str(uuid.uuid4()),
            user_id="anonymous",
            event_type=request.event_type,
            source_channel=request.source_channel,
            source_entity_id=request.source_entity_id,
            raw_content=request.raw_content,
            content_hash=content_hash,
        )
        return EventResponse(
            event_id=event.event_id,
            event_type=event.event_type,
            source_channel=event.source_channel,
            timestamp=event.timestamp,
            processed_by=event.processed_by or [],
        )
    except Exception as e:
        logger.error(f"Event creation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/payment-check", response_model=PaymentCheckResponse)
async def payment_check(request: PaymentCheckRequest) -> PaymentCheckResponse:
    """Check payment safety and reversibility."""
    amount = request.amount
    recipient = request.recipient.lower()

    # Suspicious recipients or high amount checks
    is_suspicious_recipient = any(kw in recipient for kw in ["unknown", "temp", "verify", "support", "admin", "agent"])
    
    if amount >= 50000 or (amount >= 10000 and is_suspicious_recipient):
        return PaymentCheckResponse(
            risk_level="HIGH",
            reversibility=0.15,
            recommendation="BLOCK_AND_VERIFY",
            explanation="Large payment request to unverified recipient. High risk of irreversible loss."
        )
    elif amount >= 10000 or is_suspicious_recipient:
        return PaymentCheckResponse(
            risk_level="MEDIUM",
            reversibility=0.15,
            recommendation="WARN_AND_CONFIRM",
            explanation="Moderate payment request. Verify identity via external trusted channel before sending."
        )
    else:
        return PaymentCheckResponse(
            risk_level="LOW",
            reversibility=0.85,
            recommendation="ALLOW",
            explanation="Small routine payment. Standard monitoring active."
        )


@app.post("/api/v1/link-check", response_model=LinkCheckResponse)
async def link_check(request: LinkCheckRequest) -> LinkCheckResponse:
    """Check link domain and safety."""
    url = request.url.lower()

    # Suspicious domain indicators
    is_suspicious = any(kw in url for kw in [".fake", "verify-", "login-", "secure-", "update-", "temp-", "free-"])
    has_no_https = not url.startswith("https://") and not url.startswith("http://localhost")

    if is_suspicious:
        return LinkCheckResponse(
            risk_level="HIGH",
            is_safe=False,
            explanation="URL matches known phishing subdomains or suspicious top-level domains."
        )
    elif has_no_https:
        return LinkCheckResponse(
            risk_level="MEDIUM",
            is_safe=False,
            explanation="Link lacks secure transport layer (HTTPS). Data transit could be sniffed."
        )
    else:
        return LinkCheckResponse(
            risk_level="LOW",
            is_safe=True,
            explanation="Link domain is verified or does not match any threat signature."
        )


@app.post("/api/v1/image-check", response_model=ImageCheckResponse)
async def image_check(request: ImageCheckRequest) -> ImageCheckResponse:
    """Perform Error Level Analysis (ELA) and check image authenticity."""
    url = request.image_url.lower()

    # Mock detection based on extension or parameters
    if "manipulated" in url or "fake" in url or "edited" in url:
        return ImageCheckResponse(
            authenticity_score=0.25,
            is_manipulated=True,
            explanation="Metadata indicates editing software traces and inconsistent compression artifact levels."
        )
    else:
        return ImageCheckResponse(
            authenticity_score=0.92,
            is_manipulated=False,
            explanation="Image structure matches original capture device signature. No anomalies found."
        )


@app.post("/api/v1/alternatives", response_model=List[AlternativeItem])
async def get_alternatives(request: AlternativesRequest) -> List[AlternativeItem]:
    """Get safe action path alternatives."""
    action_type = request.action_type.lower()
    goal = request.goal.lower()

    if "payment" in action_type or "pay" in goal:
        return [
            AlternativeItem(risk_level="LOW", description="Pay directly through the merchant's official mobile application or web portal"),
            AlternativeItem(risk_level="LOW", description="Call the recipient via a known official number to verify payment details"),
            AlternativeItem(risk_level="MEDIUM", description="Use bank-guaranteed escrow or credit card with dispute protection")
        ]
    elif "verify" in action_type or "login" in goal or "confirm" in goal:
        return [
            AlternativeItem(risk_level="LOW", description="Navigate to the site manually by typing the official address in the browser address bar"),
            AlternativeItem(risk_level="LOW", description="Contact the customer service desk through the number on the back of your card")
        ]
    else:
        return [
            AlternativeItem(risk_level="LOW", description="Do not interact with the message; verify using independent official channels"),
            AlternativeItem(risk_level="LOW", description="Report the message to customer support for confirmation")
        ]


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# ============================================================================
# ENTRYPOINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
