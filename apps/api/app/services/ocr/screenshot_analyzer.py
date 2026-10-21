"""
LifeLens Ω — Phase H: In-Memory Screenshot Analysis Service
Extracts claims from mobile and desktop chat screenshots.
Constraints:
- Strictly in-memory: image bytes never written to disk or database.
- Explicit consent gate required (Rule D / P5 Privacy by Default).
- Discards raw image bytes immediately after processing.
"""
from __future__ import annotations
import gc
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from .provider import OcrProvider, OcrResult
from .rapidocr_provider import RapidOcrProvider
from apps.api.app.detectors.digital_arrest_pack import DigitalArrestPatternPack
from apps.api.app.detectors.quishing_upi_loan_checker import UPICollectExplainer


@dataclass
class ScreenshotAnalysisReport:
    is_flagged: bool
    risk_score: float
    verdict: str  # Rule A: "Request looks high-risk" | "Needs Verification" | "Verification step completed"
    extracted_claims: List[str] = field(default_factory=list)
    extracted_text_preview: str = ""
    language_detected: str = "unknown"
    ocr_confidence: float = 0.0
    in_memory_only: bool = True
    persisted_to_disk: bool = False
    persisted_to_db: bool = False
    educational_guidance: str = ""


class ScreenshotAnalysisService:
    """
    Coordinates in-memory OCR extraction and threat claim analysis.
    Guarantees zero persistence of image bytes or unconsented text.
    """

    def __init__(self, ocr_provider: Optional[OcrProvider] = None) -> None:
        self.ocr_provider = ocr_provider or RapidOcrProvider()
        self.digital_arrest_pack = DigitalArrestPatternPack()
        self.upi_explainer = UPICollectExplainer()

    def analyze_screenshot(
        self,
        image_bytes: bytes,
        consent_given: bool = False,
        store_ocr_text_opt_in: bool = False,
    ) -> ScreenshotAnalysisReport:
        # P5 & Rule D: Explicit consent gate
        if not consent_given:
            return ScreenshotAnalysisReport(
                is_flagged=False,
                risk_score=0.0,
                verdict="Needs Verification",
                extracted_claims=["Consent required: Screenshot analysis aborted."],
                extracted_text_preview="",
                language_detected="none",
                in_memory_only=True,
                persisted_to_disk=False,
                persisted_to_db=False,
                educational_guidance="You must explicitly provide consent before screenshot analysis can proceed.",
            )

        # 1. Run in-memory OCR
        ocr_result: OcrResult = self.ocr_provider.extract_text(image_bytes)
        text = ocr_result.text

        # Zero Persistence: Immediately sever and free reference to raw image bytes
        del image_bytes
        gc.collect()

        # 2. Extract claims and evaluate threat signals
        claims: List[str] = []
        risk_score = 0.05
        educational_note = ""

        # Check digital arrest / impersonation
        da_check = self.digital_arrest_pack.evaluate_text(text)
        if da_check.is_flagged:
            claims.extend(da_check.matched_patterns)
            risk_score = max(risk_score, da_check.risk_score)
            educational_note = da_check.law_enforcement_note

        # Check UPI collect / PIN deception
        upi_check = self.upi_explainer.analyze_request(text)
        if upi_check.is_deceptive:
            claims.append("Deceptive UPI PIN instruction detected in screenshot text.")
            risk_score = max(risk_score, upi_check.risk_score)
            educational_note = upi_check.educational_warning

        # Check classic upfront payment / fee demands
        if any(w in text.lower() for w in ["registration fee", "security deposit", "processing charge", "courier fee"]):
            claims.append("Upfront payment / deposit demand found in chat screenshot.")
            risk_score = max(risk_score, 0.75)

        is_flagged = len(claims) > 0 and risk_score >= 0.50

        if risk_score >= 0.60:
            verdict = "Request looks high-risk"
        elif risk_score >= 0.25:
            verdict = "Needs Verification"
        else:
            verdict = "Verification step completed"

        text_preview = text[:150] if store_ocr_text_opt_in else "[Discarded per user privacy policy]"

        return ScreenshotAnalysisReport(
            is_flagged=is_flagged,
            risk_score=risk_score,
            verdict=verdict,
            extracted_claims=claims,
            extracted_text_preview=text_preview,
            language_detected=ocr_result.language_detected,
            ocr_confidence=ocr_result.confidence,
            in_memory_only=True,
            persisted_to_disk=False,
            persisted_to_db=False,
            educational_guidance=educational_note or "Verification completed. No critical scam patterns detected.",
        )
