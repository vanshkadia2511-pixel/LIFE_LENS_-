"""
LifeLens Ω — Phase G: Romance / "Pig-Butchering" (Sha Zhu Pan) 6-Stage Trajectory Engine
Reuses LifeLens Ω Trajectory analysis principles across multi-week grooming interactions.
Stages:
1. STAGE_1_UNSOLICITED_CONTACT (Wrong number lure)
2. STAGE_2_RAPPORT_ROMANCE (Love-bombing, daily intimacy)
3. STAGE_3_WEALTH_FLEX_ARBITRAGE (Wealth boasting, uncle/mentor crypto arbitrage lure)
4. STAGE_4_SMALL_BAIT_WITHDRAWAL (Test deposit, fake profit, successful mock withdrawal)
5. STAGE_5_CAPITAL_FREEZE_EXTORTION (Account frozen, VIP upgrade tax, margin fee to unlock)
6. STAGE_6_SECONDARY_RECOVERY_LURE (Fake hacker/agent offering recovery for upfront fee)
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class StageTransition:
    day: int
    stage: str
    trigger_text: str
    confidence: float


@dataclass
class PigButcheringTrajectory:
    current_stage: str
    overall_risk_score: float
    verdict: str  # Rule A: "Request looks high-risk" | "Needs Verification" | "Verification step completed"
    stage_transitions: List[str] = field(default_factory=list)
    stage_history: List[Dict[str, Any]] = field(default_factory=list)
    intervention_recommendation: str = (
        "CRITICAL INTERVENTION: This conversation matches established 'Pig-Butchering' financial grooming. "
        "Do not transfer any additional funds. Any claimed 'tax' or 'unlock fee' is a secondary extortion stage. "
        "Freeze accounts and consult official authorities immediately."
    )


class PigButcheringTrajectoryEngine:
    """
    Evaluates historical communication logs to detect multi-stage grooming trajectories
    characteristic of organized crypto romance / pig-butchering syndicates.
    """

    _STAGE_PATTERNS = [
        (
            "STAGE_1_UNSOLICITED_CONTACT",
            re.compile(r"\b(?:wrong\s+number|mistaken\s+identity|sorry\s+to\s+disturb|sent\s+this.*?wrong|are\s+you\s+\w+)\b", re.IGNORECASE),
            0.30,
        ),
        (
            "STAGE_2_RAPPORT_ROMANCE",
            re.compile(r"\b(?:good\s+morning\s+dear|spiritual\s+connection|destiny|soulmate|fall\s+in\s+love|honey|babe)\b", re.IGNORECASE),
            0.50,
        ),
        (
            "STAGE_3_WEALTH_FLEX_ARBITRAGE",
            re.compile(r"\b(?:uncle|mentor|insider|arbitrage|gold\s+trading|crypto\s+node|made\s+\$[\d,]+|private\s+platform)\b", re.IGNORECASE),
            0.75,
        ),
        (
            "STAGE_4_SMALL_BAIT_WITHDRAWAL",
            re.compile(r"\b(?:try\s+with\s+(?:just\s+)?\$?\d+|withdraw\s+profits|test\s+with\s+small|guide\s+you\s+to\s+withdraw)\b", re.IGNORECASE),
            0.85,
        ),
        (
            "STAGE_5_CAPITAL_FREEZE_EXTORTION",
            re.compile(r"\b(?:unlock\s+your\s+(?:vip\s+)?capital|deposit\s+\$[\d,]+|liquidity\s+tax|margin\s+fee|frozen|anti-money\s+laundering\s+hold)\b", re.IGNORECASE),
            0.98,
        ),
        (
            "STAGE_6_SECONDARY_RECOVERY_LURE",
            re.compile(r"\b(?:recovery\s+agent|ethical\s+hacker|retrieve\s+your\s+lost\s+crypto|trace\s+blockchain\s+funds)\b", re.IGNORECASE),
            0.95,
        ),
    ]

    def evaluate_history(self, interactions: List[Dict[str, Any]]) -> PigButcheringTrajectory:
        detected_transitions: List[str] = []
        history_details: List[Dict[str, Any]] = []
        highest_stage = "STAGE_0_BASELINE"
        highest_risk = 0.05

        for item in interactions:
            day = item.get("day", 0)
            text = item.get("text", "")

            for stage_id, pattern, score in self._STAGE_PATTERNS:
                if pattern.search(text):
                    trans_desc = f"Day {day}: Transitioned to {stage_id} (Trigger: '{text[:60]}...')"
                    detected_transitions.append(trans_desc)
                    history_details.append({
                        "day": day,
                        "stage": stage_id,
                        "risk_score": score,
                        "text_snippet": text[:80],
                    })
                    highest_stage = stage_id
                    if score > highest_risk:
                        highest_risk = score
                    break

        if highest_risk >= 0.70:
            verdict = "Request looks high-risk"
        elif highest_risk >= 0.35:
            verdict = "Needs Verification"
        else:
            verdict = "Verification step completed"

        return PigButcheringTrajectory(
            current_stage=highest_stage,
            overall_risk_score=highest_risk,
            verdict=verdict,
            stage_transitions=detected_transitions,
            stage_history=history_details,
        )
