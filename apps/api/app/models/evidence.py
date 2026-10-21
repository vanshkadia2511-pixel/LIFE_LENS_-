"""
LifeLens Ω — Evidence Model
Implementation Plan §12–13

source_status values (§12):
  AVAILABLE, UNAVAILABLE, STALE, CONFLICTING, NOT_APPLICABLE

Evidence dimensions (§45):
  Source Independence, Source Authority, Verifiability, Freshness,
  Relevance, Consistency
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid


class SourceStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    STALE = "STALE"
    CONFLICTING = "CONFLICTING"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass
class Evidence:
    """
    A piece of evidence tied to a claim.
    The evidence ledger is a first-class object — every major risk
    statement must be traceable to evidence (§13).
    """
    evidence_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    source_type: str = ""   # "REGISTRY" | "WEBSITE" | "DOMAIN" | "MANUAL" etc.
    source_name: str = ""
    source_url: Optional[str] = None

    observed_value: str = ""

    captured_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Evidence dimensions (§45)
    source_authority: float = 0.0       # 0.0 – 1.0
    source_independence: float = 0.0    # 0.0 – 1.0

    user_verifiable: bool = False
    verification_path: Optional[str] = None

    evidence_strength: float = 0.0      # derived from dimensions
    is_simulated: bool = False          # True if generated via offline mock/fallback (contributes 0 weight)

    source_status: SourceStatus = SourceStatus.AVAILABLE
