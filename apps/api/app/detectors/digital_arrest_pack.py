"""
LifeLens Ω — Phase G: Digital-Arrest / Fake-Officer Pattern Pack
India-focused enforcement intimidation, courier parcel lures, CBI/ED/Cyber Cell,
and Hindi/Hinglish phrasing.
Adheres to Rule A (Never labels people; evaluates claims/requests).
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class DigitalArrestAssessment:
    text: str
    is_flagged: bool
    risk_score: float
    verdict: str
    matched_patterns: List[str] = field(default_factory=list)
    law_enforcement_note: str = (
        "Official Indian law enforcement agencies (Police, CBI, ED, NCB, Customs) "
        "NEVER execute arrests, conduct trials, or demand bail bond deposits over video calls. "
        "'Digital arrest' has no legal standing under Indian Criminal Procedure."
    )


class DigitalArrestPatternPack:
    """
    Identifies fake law enforcement intimidation and digital arrest patterns
    across English, Hindi, and Hinglish.
    """

    PATTERNS: List[Dict[str, Any]] = [
        {
            "id": "DIGITAL_ARREST_DIRECT",
            "regex": re.compile(r"\b(?:digital\s+arrest|digital\s+warrant|digital\s+custody)\b", re.IGNORECASE),
            "weight": 0.95,
            "description": "Explicit 'digital arrest' or 'digital warrant' phrasing",
        },
        {
            "id": "HINGLISH_ARREST_WARRANT",
            "regex": re.compile(r"\b(?:warrant\s+nikla\s+hai|arrest\s+kar\s+lenge|police\s+aayegi|jail\s+jana\s+padega)\b", re.IGNORECASE),
            "weight": 0.85,
            "description": "Hinglish arrest threat phrasing",
        },
        {
            "id": "VIDEO_CALL_COERCION",
            "regex": re.compile(r"\b(?:video\s+call\s+pe\s+aao|video\s+call\s+join\s+karo|room\s+lock\s+kijiye|camera\s+band\s+mat\s+karna)\b", re.IGNORECASE),
            "weight": 0.80,
            "description": "Hinglish video call coercion / forced isolation",
        },
        {
            "id": "POLICE_CYBER_AADHAAR",
            "regex": re.compile(r"\b(?:mumbai\s+police|delhi\s+police|cyber\s+crime\s+cell|cyber\s+cell)\b.*?\b(?:aadhaar|parcel|illegal|sim\s+card|passport)\b", re.IGNORECASE),
            "weight": 0.85,
            "description": "Police Cyber Cell parcel / Aadhaar misuse lure",
        },
        {
            "id": "COURIER_DRUG_PARCEL",
            "regex": re.compile(r"\b(?:fedex|dhl|bluedart|customs|illegal\s+parcel)\b.*?\b(?:drugs|mdma|passports|taiwan|cambodia|narcotics)\b", re.IGNORECASE),
            "weight": 0.85,
            "description": "Customs courier narcotics / contraband parcel intimidation",
        },
        {
            "id": "ED_CBI_PMLA_INTIMIDATION",
            "regex": re.compile(r"\b(?:enforcement\s+directorate|cbi|ed\s+summons|pmla\s+act|money\s+laundering\s+case)\b", re.IGNORECASE),
            "weight": 0.90,
            "description": "Enforcement Directorate / CBI / PMLA statutory intimidation",
        },
        {
            "id": "ISOLATION_DEMAND",
            "regex": re.compile(r"\b(?:do\s+not\s+disconnect|remain\s+on\s+line|confidential\s+investigation|national\s+security\s+act)\b", re.IGNORECASE),
            "weight": 0.70,
            "description": "Secrecy and continuous connection coercion",
        },
    ]

    def evaluate_text(self, text: str) -> DigitalArrestAssessment:
        matched: List[str] = []
        max_weight = 0.0

        for pat in self.PATTERNS:
            if pat["regex"].search(text):
                matched.append(f"{pat['id']}: {pat['description']}")
                if pat["weight"] > max_weight:
                    max_weight = pat["weight"]

        if matched:
            risk_score = min(1.0, round(max_weight, 2))
            is_flagged = True
            verdict = "Request looks high-risk"
        else:
            risk_score = 0.05
            is_flagged = False
            verdict = "Verification step completed"

        return DigitalArrestAssessment(
            text=text,
            is_flagged=is_flagged,
            risk_score=risk_score,
            verdict=verdict,
            matched_patterns=matched,
        )
