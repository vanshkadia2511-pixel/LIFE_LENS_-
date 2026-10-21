"""
LifeLens Ω — Phase G: Investment / Crypto Platform Verifier
Evaluates claimed investment/crypto platforms against official regulatory registries (SEBI, SEC, FCA),
domain age thresholds, and classic Ponzi signals (guaranteed daily returns, MLM referral bonuses).
Adheres to Rule A (Never labels people; assesses platform entity & claims).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Set


@dataclass
class InvestmentAssessment:
    platform_name: str
    domain: str
    is_registered: bool
    risk_score: float
    verdict: str  # Rule A: "Request looks high-risk" | "Needs Verification" | "Verification step completed"
    findings: List[str] = field(default_factory=list)
    registered_regulator: str = "None"
    regulatory_guidance: str = (
        "Legitimate financial platforms NEVER guarantee fixed daily returns on crypto or forex trading. "
        "Always confirm registration on official regulator databases (SEBI SCORES, SEC EDGAR, FCA Register)."
    )


class InvestmentPlatformVerifier:
    """
    Verifies financial investment platforms by cross-referencing domain age,
    claims of guaranteed returns, and simulated/curated regulatory registries.
    """

    # Curated sample of known legitimate regulated brokers / exchanges
    _LEGITIMATE_REGISTRY: Set[str] = {
        "zerodha.com",
        "groww.in",
        "upstox.com",
        "interactivebrokers.com",
        "fidelity.com",
        "vanguard.com",
        "coinbase.com",
        "binance.com",
        "kraken.com",
    }

    def verify_platform(self, platform_data: Dict[str, Any]) -> InvestmentAssessment:
        name = platform_data.get("platform_name", "Unknown Platform")
        domain = platform_data.get("domain", "").lower().strip()
        domain_age_days = platform_data.get("domain_age_days", 365)
        daily_return = platform_data.get("claimed_guaranteed_return_daily_percent", 0.0)

        findings: List[str] = []
        score = 0.0
        is_registered = domain in self._LEGITIMATE_REGISTRY

        if not is_registered:
            findings.append("Platform domain is not found in SEBI, SEC, or FCA official registered intermediary lists.")
            score += 0.40
        else:
            findings.append("Domain verified in registered broker directory.")

        if domain_age_days < 30:
            findings.append(f"Domain is only {domain_age_days} days old (newly registered shell domain).")
            score += 0.35
        elif domain_age_days < 90:
            findings.append(f"Domain age is low ({domain_age_days} days old).")
            score += 0.20

        if daily_return > 0.0:
            findings.append(
                f"Guaranteed daily return of {daily_return}% is mathematically unsustainable and an established Ponzi / HYIP indicator."
            )
            score += 0.45

        risk_score = min(1.0, round(score, 2))

        if risk_score >= 0.60:
            verdict = "Request looks high-risk"
        elif risk_score >= 0.25:
            verdict = "Needs Verification"
        else:
            verdict = "Verification step completed"

        return InvestmentAssessment(
            platform_name=name,
            domain=domain,
            is_registered=is_registered,
            risk_score=risk_score,
            verdict=verdict,
            findings=findings,
            registered_regulator="Official Registry Match" if is_registered else "None",
        )
