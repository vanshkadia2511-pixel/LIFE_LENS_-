"""
LifeLens Ω — Phase H: Distribution API Router
Exposes endpoints for:
- In-memory screenshot OCR analysis
- Telegram Bot API webhooks
- WhatsApp Business Platform Meta Cloud API webhooks
- Voice-note triage
- Low-literacy spoken scripts
"""
from __future__ import annotations
from typing import Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, Form, Header, Request, HTTPException, Query, Response
from pydantic import BaseModel, Field

from apps.api.app.services.ocr.screenshot_analyzer import ScreenshotAnalysisService
from apps.api.app.services.distribution.telegram_bot import TelegramVerifyBot
from apps.api.app.services.distribution.whatsapp_bot import WhatsAppVerifyBot
from apps.api.app.services.distribution.voice_note_triage import VoiceNoteTriageService
from apps.api.app.services.distribution.low_literacy_mode import LowLiteracyService

router = APIRouter(prefix="/api/v1/distribution", tags=["Phase H Distribution"])

_screenshot_service = ScreenshotAnalysisService()
_telegram_bot = TelegramVerifyBot()
_whatsapp_bot = WhatsAppVerifyBot()
_voice_triage = VoiceNoteTriageService()
_low_literacy = LowLiteracyService()


# ── 1. Screenshot Analysis Endpoint ───────────────────────────────────────────

@router.post("/screenshot/analyze")
async def analyze_screenshot(
    file: UploadFile = File(...),
    consent_given: bool = Form(False),
    store_ocr_text_opt_in: bool = Form(False),
):
    """
    Performs purely in-memory OCR extraction and threat claims triage.
    Raw image bytes are never persisted to disk or database.
    """
    try:
        content = await file.read()
        report = _screenshot_service.analyze_screenshot(
            image_bytes=content,
            consent_given=consent_given,
            store_ocr_text_opt_in=store_ocr_text_opt_in,
        )
        return {
            "is_flagged": report.is_flagged,
            "risk_score": report.risk_score,
            "verdict": report.verdict,
            "extracted_claims": report.extracted_claims,
            "extracted_text_preview": report.extracted_text_preview,
            "language_detected": report.language_detected,
            "ocr_confidence": report.ocr_confidence,
            "in_memory_only": report.in_memory_only,
            "persisted_to_disk": report.persisted_to_disk,
            "persisted_to_db": report.persisted_to_db,
            "educational_guidance": report.educational_guidance,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Screenshot processing failed: {str(e)}")


# ── 2. Telegram Bot Webhook ────────────────────────────────────────────────────

@router.post("/telegram/webhook")
async def telegram_webhook(
    update: Dict[str, Any],
    x_telegram_bot_api_secret_token: Optional[str] = Header(None),
):
    """Handles Telegram Bot API updates. Verifies secret header and rate limits senders."""
    if not _telegram_bot.verify_webhook_secret(x_telegram_bot_api_secret_token):
        raise HTTPException(status_code=403, detail="Invalid Telegram webhook secret token")

    success, card, msg = _telegram_bot.process_forwarded_update(update, consent_given=True)
    if not success:
        return {"status": "rejected", "detail": msg}

    return {
        "status": "success",
        "evidence_card": {
            "verdict": card.verdict,
            "stamp_code": card.stamp_code,
            "key_findings": card.key_findings,
            "immediate_actions": card.immediate_actions,
            "educational_note": card.educational_note,
            "provenance": card.provenance,
        },
    }


# ── 3. WhatsApp Business Platform Webhook ──────────────────────────────────────

@router.get("/whatsapp/webhook")
async def whatsapp_verify_subscription(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
):
    """Meta Cloud API webhook verification handshake."""
    challenge = _whatsapp_bot.verify_webhook_subscription(hub_mode, hub_verify_token, hub_challenge)
    if challenge:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification token mismatch")


@router.post("/whatsapp/webhook")
async def whatsapp_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None),
):
    """Handles incoming forwarded WhatsApp messages with HMAC-SHA256 signature verification."""
    body_bytes = await request.body()
    if not _whatsapp_bot.verify_webhook_hub_signature(body_bytes, x_hub_signature_256):
        raise HTTPException(status_code=403, detail="Invalid Meta X-Hub-Signature-256")

    payload = await request.json()
    success, card, msg = _whatsapp_bot.process_incoming_forward(payload, consent_given=True)
    if not success:
        return {"status": "ignored_or_rejected", "detail": msg}

    return {
        "status": "success",
        "evidence_card": {
            "verdict": card.verdict,
            "stamp_code": card.stamp_code,
            "key_findings": card.key_findings,
            "immediate_actions": card.immediate_actions,
            "educational_note": card.educational_note,
        },
    }


# ── 4. Voice-Note Triage Endpoint ──────────────────────────────────────────────

@router.post("/voice-note/triage")
async def triage_voice_note(
    file: UploadFile = File(...),
    consent_given: bool = Form(False),
):
    """
    Evaluates forwarded audio voice-notes under Rule B.
    Risk boost is hard-capped at <= 0.15; outputs 'inconclusive' frequently on ambiguous audio.
    """
    try:
        content = await file.read()
        res = _voice_triage.triage_voice_note(content, consent_given=consent_given)
        return {
            "is_processed": res.is_processed,
            "verdict": res.verdict,
            "authenticity_finding": res.authenticity_finding,
            "risk_boost": res.risk_boost,
            "audio_duration_seconds": res.audio_duration_seconds,
            "snr_db": res.snr_db,
            "in_memory_only": res.in_memory_only,
            "persisted_to_disk": res.persisted_to_disk,
            "notes": res.notes,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Voice note triage failed: {str(e)}")


# ── 5. Low-Literacy Spoken Script Endpoint ─────────────────────────────────────

@router.get("/low-literacy/script")
async def get_low_literacy_script(lang: str = Query("en", description="Language code (en, hi, hi_en, ar)")):
    """Returns spoken audio synthesis scripts for low-literacy users."""
    res = _low_literacy.generate_spoken_explanation(lang)
    return {
        "language_code": res.language_code,
        "language_name": res.language_name,
        "spoken_audio_script": res.spoken_audio_script,
        "core_warning_phrase": res.core_warning_phrase,
        "simple_action_instruction": res.simple_action_instruction,
        "field_comprehension_validated": res.field_comprehension_validated,
        "disclaimer": res.disclaimer,
    }
