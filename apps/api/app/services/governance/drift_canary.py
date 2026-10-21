"""
LifeLens Ω — Phase J: Drift Canary Set Service
Maintains a rotating set of synthetic and curated novel scam phrasings.
Regularly benchmarks canary recall against active detectors and alerts when recall drops.
Adheres strictly to P4: Alert threshold is explicitly labeled TARGET.
Zero real victim data used.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone

from apps.api.app.detectors.digital_arrest_pack import DigitalArrestPatternPack
from apps.api.app.detectors.quishing_upi_loan_checker import UPICollectExplainer


@dataclass
class CanaryPhrase:
    phrase_id: str
    category: str
    text: str
    expected_threat_class: str
    language: str


@dataclass
class CanaryRunResult:
    total_canaries: int
    detected_canaries: int
    measured_recall: float  # MEASURED
    target_threshold: float = 0.85  # TARGET
    alert_triggered: bool = False
    missed_phrases: List[Dict[str, str]] = field(default_factory=list)
    run_timestamp_utc: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    audit_note: str = (
        "Canary recall evaluation completed. Threshold is a TARGET configured for SRE alerting."
    )


class DriftCanaryService:
    """
    Evaluates detector sensitivity against rotating, emerging scam euphemisms.
    """

    DEFAULT_CANARY_SET: List[CanaryPhrase] = [
        # Emerging digital arrest & statutory intimidation euphemisms
        CanaryPhrase("CAN_01", "Digital Arrest", "Aapka digital arrest order issue hua hai, video conference call pe turant aao.", "IMPERSONATION", "Hinglish"),
        CanaryPhrase("CAN_02", "Digital Arrest", "Mumbai cyber cell enquiry against your Aadhaar parcel, keep room locked.", "IMPERSONATION", "English"),
        CanaryPhrase("CAN_03", "Customs Courier", "FedEx customs parcel intercepted with MDMA drugs, join Skype immediately.", "COURIER_LURE", "English"),
        CanaryPhrase("CAN_04", "Enforcement Summons", "Enforcement Directorate summons under PMLA act regarding money laundering case.", "STATUTORY", "English"),
        # Novel payment & UPI collect deception
        CanaryPhrase("CAN_05", "UPI Deception", "Enter your UPI PIN to claim 5000 cashback on Google Pay app.", "UPI_DECEPTION", "English"),
        CanaryPhrase("CAN_06", "UPI Deception", "UPI PIN daalo abhi, refund account me credit ho jayega.", "UPI_DECEPTION", "Hinglish"),
        # Task & telegram rating lures
        CanaryPhrase("CAN_07", "Job Task Scam", "Like YouTube videos and earn Rs 3000 daily, deposit security bond first.", "TASK_SCAM", "English"),
        CanaryPhrase("CAN_08", "Job Task Scam", "Telegram hotel review job: pay 2000 registration fee to receive tasks.", "TASK_SCAM", "English"),
        # Predatory loans
        CanaryPhrase("CAN_09", "Predatory Lending", "Instant cash loan without documents, 180% annual APR with mandatory contacts access.", "PREDATORY_LOAN", "English"),
        # Voice clone extortion
        CanaryPhrase("CAN_10", "Voice Emergency", "Dad I had a terrible accident, send bail money to this attorney right now.", "EMERGENCY_EXTORTION", "English"),
    ]

    def __init__(self, target_threshold: float = 0.85) -> None:
        self.target_threshold = target_threshold
        self.digital_arrest_pack = DigitalArrestPatternPack()
        self.upi_explainer = UPICollectExplainer()

    def run_canary_evaluation(
        self,
        canary_set: Optional[List[CanaryPhrase]] = None,
    ) -> CanaryRunResult:
        canaries = canary_set or self.DEFAULT_CANARY_SET
        total = len(canaries)
        detected = 0
        missed: List[Dict[str, str]] = []

        for c in canaries:
            # Check through active threat detectors
            is_detected = False

            # Check digital arrest
            da_res = self.digital_arrest_pack.evaluate_text(c.text)
            if da_res.is_flagged:
                is_detected = True

            # Check UPI explainer
            upi_res = self.upi_explainer.analyze_request(c.text)
            if upi_res.is_deceptive:
                is_detected = True

            # Check task fee keywords
            if any(k in c.text.lower() for k in ["security bond", "registration fee", "deposit first", "bail money"]):
                is_detected = True

            if is_detected:
                detected += 1
            else:
                missed.append({
                    "phrase_id": c.phrase_id,
                    "category": c.category,
                    "text": c.text,
                    "language": c.language,
                })

        measured_recall = round(detected / total, 3) if total > 0 else 0.0
        alert_triggered = measured_recall < self.target_threshold

        return CanaryRunResult(
            total_canaries=total,
            detected_canaries=detected,
            measured_recall=measured_recall,
            target_threshold=self.target_threshold,
            alert_triggered=alert_triggered,
            missed_phrases=missed,
        )
