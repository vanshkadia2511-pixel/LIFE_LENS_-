"""
LifeLens Ω — RiskSignal
Implementation Plan §17

severity values: critical | high | medium | low
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List
import uuid


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class RiskSignal:
    """
    A single risk signal detected during verification.
    §17 of the implementation plan.

    NOTE: A signal increases risk — it does not automatically prove fraud (§P2).
    """
    signal_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    category: str = ""

    description: str = ""

    severity: Severity = Severity.MEDIUM

    reliability: float = 0.5        # 0.0 – 1.0, how reliable is this signal

    evidence_ids: List[str] = field(default_factory=list)

    detected_by: str = ""           # which engine detected this signal
