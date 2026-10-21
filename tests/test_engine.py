"""
LifeLens Ω - Comprehensive Testing Suite
Unit tests, integration tests, API tests, and adversarial testing

Run tests: pytest -v
Run with coverage: pytest --cov=. --cov-report=html
Run specific test: pytest tests/test_core.py::TestCoherenceAnalyzer -v
"""

import pytest
import json
from datetime import datetime, timedelta, timezone
from typing import List, Tuple
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import uuid

# Import from src.core.engine (package structure)
from src.core.engine import (
    Entity, BehavioralBaseline, DigitalEvent, EventType,
    CoherenceAnalyzer, EvidenceIndependenceScorer,
    BehavioralConsistencyScorer, IntentAnalyzer,
    TrajectoryAnalyzer, ConsequenceAnalyzer, DecisionEngine,
    RealityIntegrityOrchestrator, RiskLevel, FrictionLevel
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def attacker_entity():
    """Create an attacker entity for testing."""
    return Entity(
        entity_id=str(uuid.uuid4()),
        entity_type="person",
        claimed_identity="Bank Support",
        claimed_authority="fraud_prevention",
        claimed_email="support@fake-bank.com",
        relationship_to_user="untrusted"
    )


@pytest.fixture
def legitimate_entity():
    """Create a legitimate contact entity."""
    entity = Entity(
        entity_id=str(uuid.uuid4()),
        entity_type="person",
        claimed_identity="John Doe",
        relationship_to_user="family",
        trust_level=0.9,
        is_trusted=True
    )
    
    # Create baseline
    entity.baseline = BehavioralBaseline(
        entity_id=entity.entity_id,
        avg_message_length=42.0,
        emotional_language_ratio=0.05,
        urgency_language_ratio=0.02,
        active_hours_utc=list(range(9, 22)),
        typical_response_latency_hours=2.0,
        message_frequency_per_day=1.5,
        typical_request_types=["advice", "casual", "family"],
        boundary_violations_frequency=0.0,
        financial_discussion_frequency=0.0,
        sample_size=500,
        days_of_data=30,
        confidence=0.95
    )
    
    return entity


@pytest.fixture
def user_entity():
    """Create a user entity."""
    return Entity(
        entity_id=str(uuid.uuid4()),
        entity_type="person",
        claimed_identity="User",
        relationship_to_user="self"
    )


@pytest.fixture
def phishing_event(attacker_entity, user_entity):
    """Create a phishing event."""
    return DigitalEvent(
        event_id=str(uuid.uuid4()),
        event_type=EventType.MESSAGE,
        source_entity=attacker_entity,
        target_entity=user_entity,
        source_channel="Email",
        raw_content="""
        URGENT: Your account has been compromised!
        
        We detected suspicious activity on your account. 
        Please click the link below immediately to verify your identity:
        
        http://verify-account-now.fake-bank.com/login
        
        DO NOT SHARE THIS WITH ANYONE.
        
        Time is critical - verify now or your account will be locked.
        """
    )


@pytest.fixture
def legitimate_event(legitimate_entity, user_entity):
    """Create a legitimate event."""
    return DigitalEvent(
        event_id=str(uuid.uuid4()),
        event_type=EventType.MESSAGE,
        source_entity=legitimate_entity,
        target_entity=user_entity,
        source_channel="WhatsApp",
        raw_content="Hey! Just checking in. How's your day going?"
    )


@pytest.fixture
def romance_scam_progression(attacker_entity, user_entity):
    """Create a multi-message romance scam progression."""
    messages = [
        "Hi, I'm Sarah. You seem interesting!",
        "I really like talking to you. You make me feel special.",
        "I think I'm falling for you. Can we video call soon?",
        "I've never felt this way before. I trust you completely.",
        "My business is in trouble. I need $5,000 to save it. Will you help?",
        "Please, I'm desperate. You're the only one who can help me.",
        "If you love me, you'll send the money immediately. Time is running out!"
    ]
    
    events = []
    for i, message in enumerate(messages):
        event = DigitalEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.MESSAGE,
            source_entity=attacker_entity,
            target_entity=user_entity,
            source_channel="WhatsApp",
            raw_content=message,
            timestamp=datetime.now(timezone.utc) - timedelta(days=7-i)
        )
        events.append(event)
    
    return events


# ============================================================================
# UNIT TESTS - COHERENCE ANALYZER
# ============================================================================

class TestCoherenceAnalyzer:
    """Test suite for CoherenceAnalyzer."""
    
    def test_coherence_high_when_no_contradictions(self):
        """Should return high coherence when no contradictions."""
        analyzer = CoherenceAnalyzer()
        
        event = DigitalEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.MESSAGE,
            raw_content="I am your bank. Your account is secure. Please update your password."
        )
        
        result = analyzer.analyze(event)
        
        assert result["coherence_score"] >= 0.7
        assert result["contradictions_count"] == 0
    
    def test_coherence_low_when_contradictions_exist(self):
        """Should return low coherence when contradictions exist."""
        analyzer = CoherenceAnalyzer()
        
        event = DigitalEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.MESSAGE,
            raw_content="""
            Your account is secure. 
            Never share your password.
            But please send me your password immediately.
            """
        )
        
        result = analyzer.analyze(event)
        
        assert result["coherence_score"] < 0.7
        assert result["contradictions_count"] > 0
    
    def test_coherence_works_with_empty_content(self):
        """Should handle empty content gracefully."""
        analyzer = CoherenceAnalyzer()
        
        event = DigitalEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.MESSAGE,
            raw_content=""
        )
        
        result = analyzer.analyze(event)
        
        assert 0 <= result["coherence_score"] <= 1.0


# ============================================================================
# UNIT TESTS - EVIDENCE INDEPENDENCE SCORER
# ============================================================================

class TestEvidenceIndependenceScorer:
    """Test suite for EvidenceIndependenceScorer."""
    
    def test_low_independence_when_evidence_from_same_source(self):
        """Should return low independence when evidence comes from claim source."""
        scorer = EvidenceIndependenceScorer()
        
        attacker = Entity(
            entity_id=str(uuid.uuid4()),
            entity_type="person",
            claimed_identity="Bank",
            relationship_to_user="untrusted"
        )
        
        event = DigitalEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.MESSAGE,
            source_entity=attacker,
            raw_content="Click here to verify: http://fake-bank.fake/verify"
        )
        
        result = scorer.analyze(event)
        
        assert result["evidence_independence_score"] < 0.5
        assert result["circular_verification"] == True
    
    def test_circular_verification_detection(self):
        """Should detect circular verification patterns."""
        scorer = EvidenceIndependenceScorer()
        
        event = DigitalEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.MESSAGE,
            raw_content="Verify your account by clicking this link: http://link.fake"
        )
        
        result = scorer.analyze(event)
        
        assert result["circular_verification"] == True


# ============================================================================
# UNIT TESTS - BEHAVIORAL CONSISTENCY SCORER
# ============================================================================

class TestBehavioralConsistencyScorer:
    """Test suite for BehavioralConsistencyScorer."""
    
    def test_high_consistency_with_normal_behavior(self, legitimate_entity):
        """Should return high consistency for normal behavior."""
        scorer = BehavioralConsistencyScorer()
        
        event = DigitalEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.MESSAGE,
            source_entity=legitimate_entity,
            raw_content="Hey, how are you doing?",
            timestamp=datetime.now(timezone.utc)
        )
        
        result = scorer.analyze(event)
        
        assert result["consistency_score"] > 0.7
    
    def test_low_consistency_with_boundary_violations(self, legitimate_entity):
        """Should detect boundary violations."""
        scorer = BehavioralConsistencyScorer()
        
        event = DigitalEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.MESSAGE,
            source_entity=legitimate_entity,
            raw_content="Keep this secret from everyone. Don't tell anyone.",
        )
        
        result = scorer.analyze(event)
        
        assert result["relationship_drift"] > 0.5
    
    def test_detects_financial_discussion_drift(self, legitimate_entity):
        """Should detect unusual financial discussions."""
        scorer = BehavioralConsistencyScorer()
        
        event = DigitalEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.MESSAGE,
            source_entity=legitimate_entity,
            raw_content="Send me 50,000 rupees immediately. It's urgent."
        )
        
        result = scorer.analyze(event)
        
        assert result["financial_drift"] > 0.5


# ============================================================================
# UNIT TESTS - INTENT ANALYZER
# ============================================================================

class TestIntentAnalyzer:
    """Test suite for IntentAnalyzer."""
    
    def test_high_manipulative_intent_with_urgency(self):
        """Should detect manipulative intent from urgency language."""
        analyzer = IntentAnalyzer()
        
        event = DigitalEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.MESSAGE,
            raw_content="""
            Act immediately! Don't verify! Just send the money now!
            Or your account will be locked forever!
            """
        )
        
        result = analyzer.analyze(event)
        
        assert result["intent_score"] > 0.7
        assert result["likely_intent"] == "manipulative"
    
    def test_low_manipulative_intent_with_honest_signals(self):
        """Should detect honest intent from positive signals."""
        analyzer = IntentAnalyzer()
        
        event = DigitalEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.MESSAGE,
            raw_content="""
            Hi, you can verify this by calling our official number.
            Take your time and let us know if you have questions.
            """
        )
        
        result = analyzer.analyze(event)
        
        assert result["intent_score"] < 0.3


# ============================================================================
# INTEGRATION TESTS - ORCHESTRATOR
# ============================================================================

class TestRealityIntegrityOrchestrator:
    """Integration tests for the full analysis pipeline."""
    
    def test_phishing_detection(self, phishing_event):
        """Should detect a phishing email."""
        orchestrator = RealityIntegrityOrchestrator()
        
        assessment = orchestrator.analyze_event(phishing_event)
        
        assert assessment.risk_level == RiskLevel.HIGH or assessment.risk_level == RiskLevel.CRITICAL
        assert assessment.integrated_integrity_score < 0.5
        assert assessment.is_high_risk() == True
    
    def test_legitimate_message_passes(self, legitimate_event):
        """Should pass legitimate messages."""
        orchestrator = RealityIntegrityOrchestrator()
        
        assessment = orchestrator.analyze_event(legitimate_event)
        
        assert assessment.risk_level == RiskLevel.LOW or assessment.risk_level == RiskLevel.MEDIUM
        assert assessment.integrated_integrity_score > 0.6
        assert assessment.is_high_risk() == False
    
    def test_romance_scam_escalation_detection(self, romance_scam_progression):
        """Should detect romance scam escalation pattern."""
        orchestrator = RealityIntegrityOrchestrator()
        
        # Analyze progression
        assessments = []
        for event in romance_scam_progression:
            assessment = orchestrator.analyze_event(event)
            assessments.append(assessment)
        
        # Should escalate over time
        final_assessment = assessments[-1]
        
        assert final_assessment.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert final_assessment.trajectory_score > 0.6
    
    def test_all_agents_process_event(self, phishing_event):
        """Should verify all agents have processed the event."""
        orchestrator = RealityIntegrityOrchestrator()
        
        assessment = orchestrator.analyze_event(phishing_event)
        
        assert "CoherenceAnalyzer" in phishing_event.processed_by
        assert "EvidenceIndependenceScorer" in phishing_event.processed_by
        assert "BehavioralConsistencyScorer" in phishing_event.processed_by
        assert "TrajectoryAnalyzer" in phishing_event.processed_by
        assert "IntentAnalyzer" in phishing_event.processed_by


# ============================================================================
# RED TEAM / ADVERSARIAL TESTS
# ============================================================================

class TestAdversarialScenarios:
    """Test LifeLens against adversarial attack scenarios."""
    
    def test_evasion_avoiding_urgency_keywords(self):
        """Attack using urgency without urgency keywords."""
        orchestrator = RealityIntegrityOrchestrator()
        
        attacker = Entity(
            entity_id=str(uuid.uuid4()),
            entity_type="person",
            claimed_identity="Support",
            relationship_to_user="untrusted"
        )
        
        # Evasion: convey urgency without explicit keywords
        event = DigitalEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.MESSAGE,
            source_entity=attacker,
            raw_content="Your account will be closed in 2 hours. Click here to save it."
        )
        
        assessment = orchestrator.analyze_event(event)
        
        # Should still detect as risky due to other signals
        assert assessment.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    
    def test_evasion_with_false_evidence(self):
        """Attack using fabricated evidence."""
        orchestrator = RealityIntegrityOrchestrator()
        
        attacker = Entity(
            entity_id=str(uuid.uuid4()),
            entity_type="person",
            claimed_identity="Bank",
            relationship_to_user="untrusted"
        )
        
        # Evasion: provide fake evidence
        event = DigitalEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.MESSAGE,
            source_entity=attacker,
            raw_content="""
            Here is proof of your account compromise [Screenshot attached].
            
            As you can see, unauthorized access detected.
            
            Please verify your account: http://fake-bank.fake/verify
            """
        )
        
        assessment = orchestrator.analyze_event(event)
        
        # Should detect evidence is from same source (circular)
        assert assessment.evidence_independence_score < 0.5
    
    def test_false_positive_avoidance_legitimate_urgent(self):
        """Should not false positive on legitimate urgent messages."""
        orchestrator = RealityIntegrityOrchestrator()
        
        legitimate = Entity(
            entity_id=str(uuid.uuid4()),
            entity_type="person",
            claimed_identity="Mom",
            relationship_to_user="family",
            trust_level=0.95
        )
        
        legitimate.baseline = BehavioralBaseline(
            entity_id=legitimate.entity_id,
            sample_size=500,
            days_of_data=30,
            confidence=0.95
        )
        
        # Legitimate emergency message
        event = DigitalEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.MESSAGE,
            source_entity=legitimate,
            raw_content="Emergency! I'm at hospital. Need you here now!"
        )
        
        assessment = orchestrator.analyze_event(event)
        
        # Should not be flagged as attack despite urgency language
        assert assessment.risk_level not in [RiskLevel.CRITICAL]


# ============================================================================
# METRICS & PERFORMANCE TESTS
# ============================================================================

class TestPerformanceMetrics:
    """Test system performance and accuracy metrics."""
    
    def test_detection_accuracy_on_known_scams(self):
        """Measure detection accuracy on known scam patterns."""
        known_scams = [
            "Your account is compromised. Click here to verify.",
            "You won a lottery. Claim your prize at this link.",
            "I love you. Can you send me money to help with medical emergency?",
            "CEO here. Wire $50,000 immediately to this account.",
            "PayPal: Confirm your identity here: [fake link]"
        ]
        
        orchestrator = RealityIntegrityOrchestrator()
        attacker = Entity(
            entity_id=str(uuid.uuid4()),
            entity_type="person",
            claimed_identity="Unknown",
            relationship_to_user="untrusted"
        )
        
        detected_count = 0
        
        for scam_text in known_scams:
            event = DigitalEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.MESSAGE,
                source_entity=attacker,
                raw_content=scam_text
            )
            
            assessment = orchestrator.analyze_event(event)
            
            if assessment.is_high_risk():
                detected_count += 1
        
        detection_rate = detected_count / len(known_scams)
        assert detection_rate >= 0.85, f"Detection rate {detection_rate:.2%} below 85%"
    
    def test_false_positive_rate_on_legitimate(self):
        """Measure false positive rate on legitimate messages."""
        legitimate_messages = [
            "Hey! How's your day?",
            "Just checking in",
            "Can we schedule a meeting?",
            "Thanks for your help!",
            "See you tomorrow!"
        ]
        
        orchestrator = RealityIntegrityOrchestrator()
        legitimate = Entity(
            entity_id=str(uuid.uuid4()),
            entity_type="person",
            claimed_identity="Friend",
            relationship_to_user="friend",
            trust_level=0.8
        )
        
        legitimate.baseline = BehavioralBaseline(
            entity_id=legitimate.entity_id,
            sample_size=500,
            days_of_data=30,
            confidence=0.95
        )
        
        false_positives = 0
        
        for message in legitimate_messages:
            event = DigitalEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.MESSAGE,
                source_entity=legitimate,
                raw_content=message
            )
            
            assessment = orchestrator.analyze_event(event)
            
            if assessment.is_high_risk():
                false_positives += 1
        
        false_positive_rate = false_positives / len(legitimate_messages)
        assert false_positive_rate <= 0.05, f"False positive rate {false_positive_rate:.2%} above 5%"
    
    def test_latency_performance(self, phishing_event):
        """Verify analysis completes within latency targets."""
        import time
        
        orchestrator = RealityIntegrityOrchestrator()
        
        start_time = time.time()
        assessment = orchestrator.analyze_event(phishing_event)
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        
        assert elapsed_time < 500, f"Analysis took {elapsed_time:.0f}ms, target <500ms"


# ============================================================================
# SAFETY & EDGE CASE TESTS
# ============================================================================

class TestSafetyAndEdgeCases:
    """Test system safety and edge case handling."""
    
    def test_handles_very_long_messages(self):
        """Should handle very long messages efficiently."""
        orchestrator = RealityIntegrityOrchestrator()
        
        attacker = Entity(
            entity_id=str(uuid.uuid4()),
            entity_type="person",
            claimed_identity="Unknown",
            relationship_to_user="untrusted"
        )
        
        # Very long message
        long_content = "A" * 10000 + " Verify your account here: http://fake.com"
        
        event = DigitalEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.MESSAGE,
            source_entity=attacker,
            raw_content=long_content
        )
        
        # Should complete without hanging
        assessment = orchestrator.analyze_event(event)
        assert assessment is not None
    
    def test_handles_special_characters(self):
        """Should handle messages with special characters."""
        orchestrator = RealityIntegrityOrchestrator()
        
        attacker = Entity(
            entity_id=str(uuid.uuid4()),
            entity_type="person",
            claimed_identity="Unknown",
            relationship_to_user="untrusted"
        )
        
        event = DigitalEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.MESSAGE,
            source_entity=attacker,
            raw_content="你好! Verify account: http://fake.com/verify?param=值"
        )
        
        assessment = orchestrator.analyze_event(event)
        assert assessment is not None
    
    def test_handles_null_baseline(self):
        """Should handle entities without behavioral baseline."""
        orchestrator = RealityIntegrityOrchestrator()
        
        attacker = Entity(
            entity_id=str(uuid.uuid4()),
            entity_type="person",
            claimed_identity="Unknown Sender",
            relationship_to_user="untrusted",
            baseline=None  # No baseline
        )
        
        event = DigitalEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.MESSAGE,
            source_entity=attacker,
            raw_content="Click here now!"
        )
        
        # Should not crash
        assessment = orchestrator.analyze_event(event)
        assert assessment is not None
        # Should default to medium/low confidence
        assert assessment.integrity_confidence < 0.7


# ============================================================================
# DECISION ENGINE TESTS
# ============================================================================

class TestDecisionEngine:
    """Test the decision engine's friction level recommendations."""
    
    def test_high_integrity_reversible_action_no_friction(self):
        """Should allow silent observation for safe actions."""
        engine = DecisionEngine()
        
        friction, action = engine.decide(
            coherence=0.9,
            evidence_independence=0.9,
            consistency=0.9,
            trajectory=0.1,
            reversibility=0.95,
            intent_score=0.05
        )
        
        assert friction == FrictionLevel.SILENT_OBSERVE
        assert action == "ALLOW"
    
    def test_low_integrity_irreversible_action_maximum_friction(self):
        """Should block critical irreversible actions."""
        engine = DecisionEngine()
        
        friction, action = engine.decide(
            coherence=0.2,
            evidence_independence=0.1,
            consistency=0.3,
            trajectory=0.9,
            reversibility=0.05,
            intent_score=0.95
        )
        
        assert friction in [FrictionLevel.VERIFICATION, FrictionLevel.EMERGENCY_PROTECTION]
        assert action in ["VERIFY_INDEPENDENTLY", "BLOCK_AND_VERIFY"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
