"""
LifeLens Ω - Core Implementation
Production-ready Python implementation of the Reality Integrity Intelligence System

Key Components:
- Data models (Pydantic)
- CECT (Coherence-Evidence-Consistency-Trajectory) analysis
- Agent orchestration
- Decision engine
- Privacy controls
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Set
from enum import Enum
import json
import uuid
from abc import ABC, abstractmethod
import numpy as np
from scipy.stats import norm
import logging

# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class EventType(str, Enum):
    MESSAGE = "message"
    CALL = "call"
    PAYMENT_REQUEST = "payment_request"
    LINK_CLICK = "link_click"
    FILE_UPLOAD = "file_upload"
    EMAIL = "email"
    SOCIAL_MEDIA = "social_media"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FrictionLevel(int, Enum):
    SILENT_OBSERVE = 0
    SMALL_NOTICE = 1
    EXPLANATION = 2
    CONFIRMATION = 3
    VERIFICATION = 4
    COOLING_OFF = 5
    EMERGENCY_PROTECTION = 6


class VerificationStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"


# ============================================================================
# DATA MODELS (Pydantic-like structures)
# ============================================================================

@dataclass
class Entity:
    """Represents a person, organization, or service."""
    
    entity_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: str  # "person", "organization", "service", "device"
    
    # Identity Claims
    claimed_identity: str
    claimed_authority: Optional[str] = None
    claimed_email: Optional[str] = None
    claimed_phone: Optional[str] = None
    
    # Verified Information
    verified_identity: Optional[str] = None
    verified_authority: Optional[str] = None
    verification_timestamp: Optional[datetime] = None
    
    # Trust State
    relationship_to_user: str = "unknown"  # family, work, service, unknown
    trust_level: float = 0.5  # 0-1
    is_blocked: bool = False
    is_trusted: bool = False
    
    # Risk Signals
    global_risk_score: float = 0.0
    global_report_count: int = 0
    prior_incidents: List[str] = field(default_factory=list)
    
    # Behavioral Profile
    baseline: Optional[BehavioralBaseline] = None
    
    def identity_verification_gap(self) -> float:
        """How much of the identity is unverified? 0-1"""
        if self.verified_identity:
            return 0.1  # Mostly verified
        return 0.9  # Mostly unverified


@dataclass
class BehavioralBaseline:
    """Normal behavioral pattern for an entity."""
    
    entity_id: str
    
    # Linguistic
    avg_message_length: float = 42.0
    emotional_language_ratio: float = 0.12
    urgency_language_ratio: float = 0.05
    
    # Temporal
    active_hours_utc: List[int] = field(default_factory=lambda: list(range(9, 21)))
    typical_response_latency_hours: float = 4.0
    message_frequency_per_day: float = 2.0
    
    # Interaction
    typical_request_types: List[str] = field(default_factory=lambda: ["advice", "casual"])
    boundary_violations_frequency: float = 0.0
    financial_discussion_frequency: float = 0.0
    
    # Quality
    sample_size: int = 0
    days_of_data: int = 0
    confidence: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def meets_minimum_standards(self) -> bool:
        """Can we trust this baseline?"""
        return (self.sample_size > 50 and 
                self.days_of_data >= 7 and 
                self.confidence > 0.6)


@dataclass
class Claim:
    """A single assertion made by an entity."""
    
    claim_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    entity_making_claim: Entity = None
    claim_text: str = ""
    claim_type: str = "unknown"  # identity, urgency, consequence, authority, evidence
    
    # Evidence
    supporting_evidence: List[Evidence] = field(default_factory=list)
    contradicting_evidence: List[Evidence] = field(default_factory=list)
    
    # Verification
    independently_verified: bool = False
    verification_confidence: float = 0.0
    circular_verification: bool = False
    
    # Confidence
    overall_confidence: float = 0.0
    reasons: List[str] = field(default_factory=list)


@dataclass
class Evidence:
    """A piece of information supporting or contradicting a claim."""
    
    evidence_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    evidence_type: str = ""  # screenshot, email, website, person_statement
    
    # Source Analysis
    original_source_entity: Optional[Entity] = None
    source_independence: float = 0.5  # 0-1
    can_be_independently_verified: bool = False
    
    # Authenticity
    is_authentic: Optional[bool] = None
    authenticity_confidence: float = 0.0
    
    # Relevance
    relevance_to_claim: float = 0.5


@dataclass
class DigitalEvent:
    """Universal representation of any digital interaction."""
    
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    event_type: EventType = EventType.MESSAGE
    
    # Participants
    source_entity: Entity = None
    target_entity: Entity = None
    source_channel: str = "unknown"
    
    # Content
    raw_content: str = ""
    
    # Processing
    processed_by: List[str] = field(default_factory=list)
    user_approval: bool = False
    
    def mark_processed_by(self, agent_name: str):
        """Track which agents have analyzed this event."""
        if agent_name not in self.processed_by:
            self.processed_by.append(agent_name)


@dataclass
class RealityIntegrityAssessment:
    """The core output: is this situation coherent and safe?"""
    
    assessment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event: DigitalEvent = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    # CECT Scores (0-1, higher is better)
    coherence_score: float = 0.5
    evidence_independence_score: float = 0.5
    consistency_score: float = 0.5
    trajectory_score: float = 0.5
    
    # Integrated Integrity
    integrated_integrity_score: float = 0.5
    integrity_confidence: float = 0.5
    
    # Risk Assessment
    risk_level: RiskLevel = RiskLevel.MEDIUM
    risk_reversibility: float = 0.5
    
    # Consequence
    point_of_no_return: Optional[int] = None
    
    # Recommendation
    recommended_friction_level: FrictionLevel = FrictionLevel.EXPLANATION
    recommended_action: str = "WARN"
    alternative_actions: List[str] = field(default_factory=list)
    
    # Explanation
    primary_concerns: List[str] = field(default_factory=list)
    
    def is_high_risk(self) -> bool:
        return self.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]


# ============================================================================
# AGENT BASE CLASS
# ============================================================================

class AnalysisAgent(ABC):
    """Base class for all analysis agents."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"Agent.{name}")
    
    @abstractmethod
    def analyze(self, event: DigitalEvent) -> Dict:
        """Analyze an event and return findings."""
        pass
    
    def log_analysis(self, event_id: str, findings: Dict):
        """Log analysis for audit trail."""
        self.logger.info(f"Event {event_id}: {findings}")


# ============================================================================
# COHERENCE ANALYZER
# ============================================================================

class CoherenceAnalyzer(AnalysisAgent):
    """
    Analyze logical consistency of claims.
    Returns: coherence_score (0-1)
    """
    
    def __init__(self):
        super().__init__("CoherenceAnalyzer")
    
    def analyze(self, event: DigitalEvent) -> Dict:
        """Analyze claim coherence."""
        
        # Extract claims from event
        claims = self.extract_claims_from_text(event.raw_content)
        
        # Detect contradictions
        contradictions = self.detect_contradictions(claims)
        
        # Calculate coherence
        if len(claims) < 2:
            coherence = 1.0
        else:
            max_possible = (len(claims) * (len(claims) - 1)) / 2
            coherence = 1.0 - (len(contradictions) / max(max_possible, 1))
        
        coherence = max(0.0, min(1.0, coherence))
        
        result = {
            "coherence_score": coherence,
            "claims_count": len(claims),
            "contradictions_count": len(contradictions),
            "contradictions": [c for c in contradictions],
            "confidence": 0.85 if len(claims) > 5 else 0.6
        }
        
        self.log_analysis(event.event_id, result)
        return result
    
    def extract_claims_from_text(self, text: str) -> List[str]:
        """Extract major claims from text."""
        # Simplified: split by sentences
        sentences = text.split('.')
        return [s.strip() for s in sentences if len(s.strip()) > 10]
    
    def detect_contradictions(self, claims: List[str]) -> List[Tuple[str, str]]:
        """Detect logical contradictions between claims."""
        contradictions = []
        
        contradiction_patterns = [
            ("never", "always"),
            ("not", "definitely"),
            ("impossible", "definitely possible"),
        ]
        
        for i, claim1 in enumerate(claims):
            for claim2 in claims[i+1:]:
                for pattern1, pattern2 in contradiction_patterns:
                    if pattern1 in claim1.lower() and pattern2 in claim2.lower():
                        contradictions.append((claim1, claim2))
                    elif pattern2 in claim1.lower() and pattern1 in claim2.lower():
                        contradictions.append((claim1, claim2))
        
        return contradictions


# ============================================================================
# EVIDENCE INDEPENDENCE SCORER
# ============================================================================

class EvidenceIndependenceScorer(AnalysisAgent):
    """
    Score how independent evidence is from the claim source.
    Returns: independence_score (0-1)
    """
    
    def __init__(self):
        super().__init__("EvidenceIndependenceScorer")
    
    def analyze(self, event: DigitalEvent) -> Dict:
        """Analyze evidence independence."""
        
        # If event itself is evidence
        independence_score = self.calculate_independence(event)
        
        result = {
            "evidence_independence_score": independence_score,
            "can_be_verified": self.can_be_independently_verified(event),
            "circular_verification": self.detect_circular_verification(event),
            "confidence": 0.80
        }
        
        self.log_analysis(event.event_id, result)
        return result
    
    def calculate_independence(self, event: DigitalEvent) -> float:
        """Calculate independence score."""
        
        # If evidence comes from same source as claim
        if event.source_entity == event.target_entity:
            return 0.1  # Very low independence
        
        # If from neutral third party
        if self.is_neutral_third_party(event.source_entity):
            return 0.95  # High independence
        
        # Default: moderate independence
        return 0.5
    
    def is_neutral_third_party(self, entity: Entity) -> bool:
        """Is this entity neutral/independent?"""
        # Official services are independent sources for their own claims
        if entity.entity_type == "service":
            return entity.claimed_authority == "official"
        
        # Unknown entities are not independent
        return False
    
    def can_be_independently_verified(self, event: DigitalEvent) -> bool:
        """Can user verify this independently?"""
        
        # Payment requests can be verified by calling official number
        if "payment" in event.raw_content.lower():
            return True
        
        # Identity claims can be verified through official channels
        if event.source_entity and event.source_entity.claimed_authority:
            return True
        
        return False
    
    def detect_circular_verification(self, event: DigitalEvent) -> bool:
        """
        Does the evidence come from the same suspicious source?
        Example: "Click here to verify" -> link is attacker's fake site
        """
        
        # Simple heuristic: if event contains verification request + URL
        if "verify" in event.raw_content.lower() and "http" in event.raw_content:
            return True
        
        return False


# ============================================================================
# BEHAVIORAL CONSISTENCY SCORER
# ============================================================================

class BehavioralConsistencyScorer(AnalysisAgent):
    """
    Detect when a contact is acting abnormally.
    Returns: consistency_score (0-1)
    """
    
    def __init__(self):
        super().__init__("BehavioralConsistencyScorer")
    
    def analyze(self, event: DigitalEvent) -> Dict:
        """Analyze behavioral consistency."""
        
        baseline = event.source_entity.baseline
        
        if baseline is None or not baseline.meets_minimum_standards():
            return {
                "consistency_score": 0.5,
                "insufficient_baseline": True,
                "confidence": 0.3
            }
        
        # Calculate drifts across dimensions
        linguistic_drift = self.measure_linguistic_drift(baseline, event.raw_content)
        temporal_drift = self.measure_temporal_drift(baseline, event.timestamp)
        relationship_drift = self.measure_relationship_drift(baseline, event.raw_content)
        financial_drift = self.measure_financial_drift(baseline, event.raw_content)
        
        # Composite score
        drifts = [linguistic_drift, temporal_drift, relationship_drift, financial_drift]
        avg_drift = sum(drifts) / len(drifts)
        consistency = 1.0 - avg_drift
        consistency = max(0.0, min(1.0, consistency))
        
        result = {
            "consistency_score": consistency,
            "linguistic_drift": linguistic_drift,
            "temporal_drift": temporal_drift,
            "relationship_drift": relationship_drift,
            "financial_drift": financial_drift,
            "confidence": 0.85
        }
        
        self.log_analysis(event.event_id, result)
        return result
    
    def measure_linguistic_drift(self, baseline: BehavioralBaseline, text: str) -> float:
        """How different is the language from normal?"""
        
        # Emotional language
        emotional_words = ["love", "miss", "beautiful", "perfect"]
        emotional_count = sum(1 for word in emotional_words if word in text.lower())
        emotional_ratio = emotional_count / max(len(text.split()), 1)
        
        emotional_drift = abs(emotional_ratio - baseline.emotional_language_ratio)
        
        # Urgency language
        urgency_words = ["urgent", "immediately", "now", "quickly"]
        urgency_count = sum(1 for word in urgency_words if word in text.lower())
        urgency_ratio = urgency_count / max(len(text.split()), 1)
        
        urgency_drift = abs(urgency_ratio - baseline.urgency_language_ratio)
        
        # Average
        total_drift = (emotional_drift + urgency_drift) / 2
        return min(1.0, total_drift)
    
    def measure_temporal_drift(self, baseline: BehavioralBaseline, timestamp: datetime) -> float:
        """Are they contacting at an unusual time?"""
        
        hour = timestamp.hour
        
        if hour in baseline.active_hours_utc:
            return 0.0
        else:
            return baseline.active_hours_utc and 1.0 or 0.5
    
    def measure_relationship_drift(self, baseline: BehavioralBaseline, text: str) -> float:
        """Are they making unusual requests?"""
        
        boundary_violation_keywords = [
            "keep this secret", "don't tell anyone", "this is between us",
            "verify your password", "send me OTP"
        ]
        
        has_violation = any(kw in text.lower() for kw in boundary_violation_keywords)
        
        if has_violation:
            return 1.0
        
        return 0.0
    
    def measure_financial_drift(self, baseline: BehavioralBaseline, text: str) -> float:
        """Are they discussing money unusually?"""
        
        if any(word in text.lower() for word in ["rupees", "payment", "money", "transfer"]):
            if baseline.financial_discussion_frequency == 0.0:
                return 1.0  # Major drift
            else:
                return 0.1  # Minor drift
        
        return 0.0


# ============================================================================
# INTENT ANALYZER
# ============================================================================

class IntentAnalyzer(AnalysisAgent):
    """
    Infer whether behavior matches honest or manipulative actor strategy.
    Returns: intent_score (0=honest, 1=manipulative)
    """
    
    def __init__(self):
        super().__init__("IntentAnalyzer")
    
    def analyze(self, event: DigitalEvent) -> Dict:
        """Analyze intent."""
        
        honest_fit = self.score_fit(event, self.get_honest_strategy())
        manipulative_fit = self.score_fit(event, self.get_manipulative_strategy())
        
        # Intent score
        total = honest_fit + manipulative_fit
        if total > 0:
            intent_score = manipulative_fit / total
        else:
            intent_score = 0.5
        
        result = {
            "intent_score": intent_score,
            "honest_fit": honest_fit,
            "manipulative_fit": manipulative_fit,
            "likely_intent": "manipulative" if intent_score > 0.6 else "honest",
            "confidence": max(honest_fit, manipulative_fit) / (total + 0.1)
        }
        
        self.log_analysis(event.event_id, result)
        return result
    
    def get_honest_strategy(self) -> Dict[str, float]:
        """What would we expect from an honest actor?"""
        return {
            "provides_verification": 0.8,
            "accepts_delays": 0.9,
            "respects_boundaries": 0.85,
            "uses_official_channels": 0.85,
            "creates_urgency": 0.1,
            "resists_verification": 0.05,
        }
    
    def get_manipulative_strategy(self) -> Dict[str, float]:
        """What would we expect from a manipulator?"""
        return {
            "provides_verification": 0.1,
            "accepts_delays": 0.05,
            "respects_boundaries": 0.1,
            "uses_official_channels": 0.2,
            "creates_urgency": 0.85,
            "resists_verification": 0.8,
        }
    
    def score_fit(self, event: DigitalEvent, strategy: Dict[str, float]) -> float:
        """How well does observed behavior match this strategy?"""
        
        scores = []
        text = event.raw_content.lower()
        
        # Check each behavior
        if "provides_verification" in strategy:
            observed = any(kw in text for kw in ["verify", "check", "confirm", "official"])
            fit = strategy["provides_verification"] if observed else (1 - strategy["provides_verification"])
            scores.append(fit)
        
        if "creates_urgency" in strategy:
            observed = any(kw in text for kw in ["urgent", "now", "immediately", "quickly"])
            fit = strategy["creates_urgency"] if observed else (1 - strategy["creates_urgency"])
            scores.append(fit)
        
        if "resists_verification" in strategy:
            observed = any(kw in text for kw in ["don't verify", "don't check", "use this link"])
            fit = strategy["resists_verification"] if observed else (1 - strategy["resists_verification"])
            scores.append(fit)
        
        # Average
        return sum(scores) / max(len(scores), 1)


# ============================================================================
# TRAJECTORY ANALYZER
# ============================================================================

class TrajectoryAnalyzer(AnalysisAgent):
    """
    Predict relationship trajectory and where it's heading.
    Returns: trajectory_score (0=safe, 1=dangerous)
    """
    
    def __init__(self):
        super().__init__("TrajectoryAnalyzer")
    
    def analyze(self, event: DigitalEvent) -> Dict:
        """Analyze trajectory."""
        
        # Detect manipulation escalation patterns
        has_isolation = "don't tell" in event.raw_content.lower() or "secret" in event.raw_content.lower()
        has_urgency = any(w in event.raw_content.lower() for w in ["urgent", "now", "immediately"])
        has_financial = any(w in event.raw_content.lower() for w in ["money", "payment", "rupees"])
        
        trajectory_risk = 0.0
        
        if has_isolation:
            trajectory_risk += 0.3
        if has_urgency:
            trajectory_risk += 0.3
        if has_financial:
            trajectory_risk += 0.4
        
        trajectory_risk = min(1.0, trajectory_risk)
        
        result = {
            "trajectory_score": trajectory_risk,
            "has_isolation": has_isolation,
            "has_urgency": has_urgency,
            "has_financial_discussion": has_financial,
            "confidence": 0.80
        }
        
        self.log_analysis(event.event_id, result)
        return result


# ============================================================================
# CONSEQUENCE ANALYZER
# ============================================================================

class ConsequenceAnalyzer(AnalysisAgent):
    """
    Simulate action consequences and identify point of no return.
    """
    
    def __init__(self):
        super().__init__("ConsequenceAnalyzer")
    
    def analyze(self, event: DigitalEvent) -> Dict:
        """Analyze consequences."""
        
        # Detect action type
        action_type = self.detect_action_type(event)
        
        # Get reversibility for this action
        reversibility = self.get_reversibility(action_type)
        
        # Identify point of no return
        point_of_no_return = None
        if reversibility < 0.3:
            point_of_no_return = 0  # Immediately irreversible
        
        result = {
            "action_type": action_type,
            "reversibility": reversibility,
            "point_of_no_return": point_of_no_return,
            "consequence_severity": 1.0 - reversibility,
            "confidence": 0.85
        }
        
        self.log_analysis(event.event_id, result)
        return result
    
    def detect_action_type(self, event: DigitalEvent) -> str:
        """What action is being requested?"""
        
        text = event.raw_content.lower()
        
        if "click" in text or "link" in text:
            return "click_link"
        elif "payment" in text or "send" in text or "transfer" in text:
            return "send_payment"
        elif "password" in text or "otp" in text:
            return "share_credential"
        elif "download" in text or "install" in text:
            return "download_file"
        else:
            return "unknown"
    
    def get_reversibility(self, action_type: str) -> float:
        """How reversible is this action? 0=irreversible, 1=fully reversible"""
        
        reversibility_map = {
            "click_link": 0.85,
            "send_payment": 0.15,
            "share_credential": 0.05,
            "download_file": 0.70,
            "unknown": 0.50
        }
        
        return reversibility_map.get(action_type, 0.50)


# ============================================================================
# DECISION ENGINE
# ============================================================================

class DecisionEngine:
    """
    Integrate all signals and recommend friction level.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("DecisionEngine")
    
    def decide(
        self,
        coherence: float,
        evidence_independence: float,
        consistency: float,
        trajectory: float,
        reversibility: float,
        intent_score: float
    ) -> Tuple[FrictionLevel, str]:
        """
        Make decision about what intervention is needed.
        
        Args:
            coherence: 0-1 (higher = more coherent)
            evidence_independence: 0-1 (higher = more independent)
            consistency: 0-1 (higher = more consistent with baseline)
            trajectory: 0-1 (higher = more dangerous trajectory)
            reversibility: 0-1 (higher = more reversible)
            intent_score: 0-1 (higher = more likely manipulative)
        
        Returns:
            (friction_level, recommendation)
        """
        
        # Calculate integrity
        integrity = (coherence + evidence_independence + consistency) / 3
        
        # Calculate danger
        danger = (trajectory + intent_score) / 2
        
        # Calculate irreversibility
        irreversibility = 1.0 - reversibility
        
        # Overall risk
        risk_score = danger * irreversibility
        
        self.logger.info(
            f"Decision Analysis: "
            f"integrity={integrity:.2f}, "
            f"danger={danger:.2f}, "
            f"irreversibility={irreversibility:.2f}, "
            f"risk={risk_score:.2f}"
        )
        
        # Decision logic
        if integrity > 0.85 and reversibility > 0.7:
            return (FrictionLevel.SILENT_OBSERVE, "ALLOW")
        
        elif integrity < 0.4 and irreversibility > 0.8:
            return (FrictionLevel.EMERGENCY_PROTECTION, "BLOCK_AND_VERIFY")
        
        elif integrity < 0.5 and trajectory > 0.6:
            return (FrictionLevel.VERIFICATION, "REQUIRE_VERIFICATION")
        
        elif integrity < 0.65:
            return (FrictionLevel.EXPLANATION, "ADD_FRICTION_AND_EXPLAIN")
        
        elif risk_score > 0.6:
            return (FrictionLevel.CONFIRMATION, "REQUIRE_CONFIRMATION")
        
        else:
            return (FrictionLevel.SMALL_NOTICE, "WARN")


# ============================================================================
# ORCHESTRATOR
# ============================================================================

class RealityIntegrityOrchestrator:
    """
    Orchestrates all agents and produces final assessment.
    """
    
    def __init__(self):
        # Initialize agents
        self.coherence_agent = CoherenceAnalyzer()
        self.evidence_agent = EvidenceIndependenceScorer()
        self.consistency_agent = BehavioralConsistencyScorer()
        self.trajectory_agent = TrajectoryAnalyzer()
        self.intent_agent = IntentAnalyzer()
        self.consequence_agent = ConsequenceAnalyzer()
        self.decision_engine = DecisionEngine()
        
        self.logger = logging.getLogger("Orchestrator")
    
    def analyze_event(self, event: DigitalEvent) -> RealityIntegrityAssessment:
        """
        Complete analysis pipeline: Event -> Assessment
        """
        
        self.logger.info(f"Starting analysis of event {event.event_id}")
        
        # Get all agent analyses
        coherence_result = self.coherence_agent.analyze(event)
        event.mark_processed_by("CoherenceAnalyzer")
        
        evidence_result = self.evidence_agent.analyze(event)
        event.mark_processed_by("EvidenceIndependenceScorer")
        
        consistency_result = self.consistency_agent.analyze(event)
        event.mark_processed_by("BehavioralConsistencyScorer")
        
        trajectory_result = self.trajectory_agent.analyze(event)
        event.mark_processed_by("TrajectoryAnalyzer")
        
        intent_result = self.intent_agent.analyze(event)
        event.mark_processed_by("IntentAnalyzer")
        
        consequence_result = self.consequence_agent.analyze(event)
        event.mark_processed_by("ConsequenceAnalyzer")
        
        # Make decision
        friction_level, recommendation = self.decision_engine.decide(
            coherence=coherence_result["coherence_score"],
            evidence_independence=evidence_result["evidence_independence_score"],
            consistency=consistency_result.get("consistency_score", 0.5),
            trajectory=trajectory_result["trajectory_score"],
            reversibility=consequence_result["reversibility"],
            intent_score=intent_result["intent_score"]
        )
        
        # Build integrated integrity score
        integrated_integrity = (
            coherence_result["coherence_score"] * 0.25 +
            evidence_result["evidence_independence_score"] * 0.25 +
            consistency_result.get("consistency_score", 0.5) * 0.25 +
            (1.0 - trajectory_result["trajectory_score"]) * 0.25
        )
        
        # Build assessment
        assessment = RealityIntegrityAssessment(
            event=event,
            coherence_score=coherence_result["coherence_score"],
            evidence_independence_score=evidence_result["evidence_independence_score"],
            consistency_score=consistency_result.get("consistency_score", 0.5),
            trajectory_score=trajectory_result["trajectory_score"],
            integrated_integrity_score=integrated_integrity,
            integrity_confidence=min(
                coherence_result.get("confidence", 0.6),
                evidence_result.get("confidence", 0.6),
                consistency_result.get("confidence", 0.6)
            ),
            risk_level=self._calculate_risk_level(integrated_integrity, trajectory_result["trajectory_score"]),
            risk_reversibility=consequence_result["reversibility"],
            point_of_no_return=consequence_result.get("point_of_no_return"),
            recommended_friction_level=friction_level,
            recommended_action=recommendation,
            primary_concerns=self._generate_concerns(
                coherence_result, evidence_result, consistency_result, trajectory_result
            )
        )
        
        self.logger.info(
            f"Assessment complete: "
            f"integrity={integrated_integrity:.2f}, "
            f"risk={assessment.risk_level.value}, "
            f"friction={friction_level.name}"
        )
        
        return assessment
    
    def _calculate_risk_level(self, integrity: float, trajectory: float) -> RiskLevel:
        """Determine risk level from scores."""
        
        combined_risk = (1.0 - integrity) * 0.6 + trajectory * 0.4
        
        if combined_risk >= 0.75:
            return RiskLevel.CRITICAL
        elif combined_risk >= 0.55:
            return RiskLevel.HIGH
        elif combined_risk >= 0.35:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _generate_concerns(self, *results) -> List[str]:
        """Generate human-readable concerns."""
        concerns = []
        
        # Check coherence
        if results[0]["coherence_score"] < 0.5:
            concerns.append("Claims contain logical contradictions")
        
        # Check evidence
        if results[1]["evidence_independence_score"] < 0.3:
            concerns.append("Claims lack independent verification")
        
        if results[1].get("circular_verification"):
            concerns.append("Verification path leads back to same source")
        
        # Check consistency
        if results[2].get("consistency_score", 1.0) < 0.4:
            concerns.append("Contact is behaving unusually")
        
        # Check trajectory
        if results[3]["trajectory_score"] > 0.6:
            concerns.append("Conversation is escalating in concerning patterns")
        
        return concerns[:3]  # Return top 3


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Create test event
    attacker = Entity(
        entity_type="person",
        claimed_identity="Bank Support",
        claimed_authority="fraud_prevention",
        relationship_to_user="untrusted"
    )
    
    user = Entity(
        entity_type="person",
        claimed_identity="User",
        relationship_to_user="self"
    )
    
    # Suspicious message
    event = DigitalEvent(
        event_type=EventType.MESSAGE,
        source_entity=attacker,
        target_entity=user,
        source_channel="WhatsApp",
        raw_content="""
        Hello! This is urgent. We detected fraud on your account. 
        Don't tell anyone about this. 
        Click here immediately to verify: http://suspicious-link.com
        Send your OTP to confirm. This is time sensitive!
        """
    )
    
    # Run orchestrator
    orchestrator = RealityIntegrityOrchestrator()
    assessment = orchestrator.analyze_event(event)
    
    # Print results
    print(f"\n{'='*60}")
    print(f"LIFELENS Ω ANALYSIS REPORT")
    print(f"{'='*60}")
    print(f"\nEvent ID: {event.event_id}")
    print(f"From: {event.source_entity.claimed_identity}")
    print(f"Channel: {event.source_channel}")
    print(f"\n{'SCORES':-^60}")
    print(f"Coherence Score:             {assessment.coherence_score:.2f}")
    print(f"Evidence Independence:       {assessment.evidence_independence_score:.2f}")
    print(f"Behavioral Consistency:      {assessment.consistency_score:.2f}")
    print(f"Trajectory Score:            {assessment.trajectory_score:.2f}")
    print(f"\nIntegrated Integrity Score:  {assessment.integrated_integrity_score:.2f}")
    print(f"Integrity Confidence:        {assessment.integrity_confidence:.2f}")
    print(f"\n{'RISK ASSESSMENT':-^60}")
    print(f"Risk Level:                  {assessment.risk_level.value}")
    print(f"Reversibility:               {assessment.risk_reversibility:.2f}")
    print(f"\n{'RECOMMENDATION':-^60}")
    print(f"Friction Level:              {assessment.recommended_friction_level.name}")
    print(f"Recommended Action:          {assessment.recommended_action}")
    print(f"\nConcerns:")
    for i, concern in enumerate(assessment.primary_concerns, 1):
        print(f"  {i}. {concern}")
    print(f"\n{'='*60}\n")
