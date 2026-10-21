"""
LifeLens Ω - Quick smoke test script.
Run from the project root: python smoke_test.py
"""
import sys
sys.path.insert(0, '.')

from src.core.engine import (
    Entity, BehavioralBaseline, DigitalEvent, EventType,
    RealityIntegrityOrchestrator
)

def run_smoke_test():
    attacker = Entity(
        entity_type='person',
        claimed_identity='Bank Support',
        claimed_authority='fraud_prevention',
        relationship_to_user='untrusted'
    )
    user = Entity(
        entity_type='person',
        claimed_identity='User',
        relationship_to_user='self'
    )

    event = DigitalEvent(
        event_type=EventType.MESSAGE,
        source_entity=attacker,
        target_entity=user,
        source_channel='WhatsApp',
        raw_content=(
            "URGENT fraud detected on your account. "
            "Do not tell anyone. "
            "Click http://suspicious-link.com to verify immediately "
            "and send your OTP now."
        )
    )

    orchestrator = RealityIntegrityOrchestrator()
    assessment = orchestrator.analyze_event(event)

    print("=" * 60)
    print("LIFELENS Omega - SMOKE TEST RESULTS")
    print("=" * 60)
    print(f"Coherence Score:         {assessment.coherence_score:.2f}")
    print(f"Evidence Independence:   {assessment.evidence_independence_score:.2f}")
    print(f"Behavioral Consistency:  {assessment.consistency_score:.2f}")
    print(f"Trajectory Score:        {assessment.trajectory_score:.2f}")
    print(f"Integrated Integrity:    {assessment.integrated_integrity_score:.2f}")
    print(f"Risk Level:              {assessment.risk_level.value}")
    print(f"Friction Level:          {assessment.recommended_friction_level.name}")
    print(f"Recommended Action:      {assessment.recommended_action}")
    print(f"Primary Concerns:")
    for i, c in enumerate(assessment.primary_concerns, 1):
        print(f"  {i}. {c}")
    print("=" * 60)
    print("SMOKE TEST PASSED")


if __name__ == '__main__':
    run_smoke_test()
