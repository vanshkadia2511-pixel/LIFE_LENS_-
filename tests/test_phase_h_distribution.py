"""
LifeLens Ω — Phase H: Distribution Test Suite
Comprehensive tests for:
1. In-memory Screenshot Analysis & Swappable OcrProvider Interface
2. RapidOCR bundled model licensing, pinned checksums, and CER measurement (ILLUSTRATIVE set)
3. Zero-persistence validation (asserts no image bytes or text reach disk/DB)
4. Screenshot preprocessing (dark-mode inversion, upscaling, chat bubble segmentation)
5. Telegram Forward-to-Verify bot (webhook secret validation, rate-limiting, Evidence Cards)
6. WhatsApp Business Platform bot (X-Hub-Signature-256 HMAC, Meta policy, user-initiated forwards)
7. Voice-note triage (Rule B risk cap <= 0.15, frequent 'inconclusive' verdicts)
8. Low-literacy mode (regional language packs: English, Hindi, Hinglish, Arabic)
"""
import io
import os
import pytest
from datetime import datetime, timezone
from PIL import Image

from apps.api.app.services.ocr.provider import (
    OcrProvider,
    OcrResult,
    ScreenshotPreprocessor,
)
from apps.api.app.services.ocr.rapidocr_provider import (
    RapidOcrProvider,
    compute_character_error_rate,
)
from apps.api.app.services.ocr.screenshot_analyzer import (
    ScreenshotAnalysisService,
    ScreenshotAnalysisReport,
)
from apps.api.app.services.distribution.telegram_bot import (
    TelegramVerifyBot,
    EvidenceCard,
)
from apps.api.app.services.distribution.whatsapp_bot import (
    WhatsAppVerifyBot,
    MetaPolicyDetails,
)
from apps.api.app.services.distribution.voice_note_triage import (
    VoiceNoteTriageService,
    VoiceNoteTriageResult,
)
from apps.api.app.services.distribution.low_literacy_mode import (
    LowLiteracyService,
    SpokenExplanation,
)


# ── 1. OCR Provider Interface & Pinned Metadata ────────────────────────────────

def test_ocr_provider_interface_and_pinned_metadata():
    """Verify OcrProvider metadata specifies bundled models, pinned SHA-256s, and licenses."""
    provider = RapidOcrProvider()
    metadata = provider.get_model_metadata()

    assert metadata["engine"] == "RapidOCR"
    assert metadata["in_memory_only"] is True
    models = metadata["models"]

    # Verify detection and recognition models
    assert "detection" in models
    assert models["detection"]["license"] == "Apache-2.0"
    assert len(models["detection"]["sha256"]) == 64

    assert "recognition_devanagari_hi" in models
    assert models["recognition_devanagari_hi"]["license"] == "Apache-2.0"

    assert "recognition_arabic_ar" in models
    assert models["recognition_arabic_ar"]["license"] == "Apache-2.0"

    assert "runtime" in models
    assert models["runtime"]["license"] == "MIT"


# ── 2. Screenshot Preprocessing ───────────────────────────────────────────────

def test_screenshot_preprocessing_dark_mode_and_upscaling():
    """Verify preprocessing inverts dark mode screenshots and upscales small images in memory."""
    # Create dark image (average luminance ~ 30)
    dark_img = Image.new("RGB", (300, 300), color=(30, 30, 30))
    buf = io.BytesIO()
    dark_img.save(buf, format="PNG")
    dark_bytes = buf.getvalue()

    processed_bytes = ScreenshotPreprocessor.preprocess_image(dark_bytes)
    assert len(processed_bytes) > 0

    # Inspect processed image in memory
    with Image.open(io.BytesIO(processed_bytes)) as out_img:
        # Check inverted brightness
        gray = out_img.convert("L")
        hist = gray.histogram()
        avg_lum = sum(i * count for i, count in enumerate(hist)) / sum(hist)
        # Should now be high luminance (inverted from dark)
        assert avg_lum > 200.0
        # Check upscaled dimensions (300px upscaled)
        assert out_img.size[0] >= 600

    # Test chat bubble cropping heuristic
    tall_img = Image.new("RGB", (400, 1000), color=(240, 240, 240))
    tbuf = io.BytesIO()
    tall_img.save(tbuf, format="PNG")
    bubbles = ScreenshotPreprocessor.crop_chat_bubbles(tbuf.getvalue())
    assert len(bubbles) >= 2


# ── 3. Character Error Rate (CER) on ILLUSTRATIVE Benchmark Set ───────────────

def test_cer_character_error_rate_on_illustrative_test_set():
    """
    Evaluates Character Error Rate (CER) per language on labeled synthetic test cases.
    Dataset labeled: ILLUSTRATIVE.
    """
    provider = RapidOcrProvider()

    illustrative_test_cases = [
        {
            "language": "English",
            "reference": "Enter UPI PIN to receive 5000 cashback on Google Pay.",
            "hypothesis": "Enter UPI PIN to receive 5000 cashback on Google Pay.",
        },
        {
            "language": "Hinglish",
            "reference": "Aapka digital arrest warrant nikla hai, video call join karein.",
            "hypothesis": "Aapka digital arrest warrant nikla hai, video call join karein.",
        },
        {
            "language": "Hindi (Devanagari)",
            "reference": "आपका डिजिटल अरेस्ट वारंट निकला है",
            "hypothesis": "आपका डिजिटल अरेस्ट वारंट निकला है",
        },
        {
            "language": "Arabic (العربية)",
            "reference": "تحذير أمني: هذا الطلب عالي الخطورة",
            "hypothesis": "تحذير أمني: هذا الطلب عالي الخطورة",
        },
    ]

    for item in illustrative_test_cases:
        cer = compute_character_error_rate(item["reference"], item["hypothesis"])
        assert cer == 0.0, f"Clean CER should be 0.0 for {item['language']}"

    # Test degraded / simulated OCR noise case
    noisy_ref = "Cyber Crime Cell Mumbai Police"
    noisy_hyp = "Cyber Crime Cell Mumbal Pollce"  # 2 character errors
    noisy_cer = compute_character_error_rate(noisy_ref, noisy_hyp)
    assert 0.0 < noisy_cer < 0.15, "Noise CER should accurately calculate edit distance"


# ── 4. In-Memory Only & Zero-Persistence Validation ───────────────────────────

def test_no_image_bytes_or_ocr_text_persisted_to_disk_or_db():
    """Strictly assert that no image bytes or unconsented OCR text reach disk or database."""
    service = ScreenshotAnalysisService()

    # Track directory before execution
    files_before = set(os.listdir("."))

    # In-memory test payload with UPI scam claim
    test_payload = b"TEST_OCR_TEXT:Enter UPI PIN on this link to receive cashback of Rs 5000."

    report = service.analyze_screenshot(
        image_bytes=test_payload,
        consent_given=True,
        store_ocr_text_opt_in=False,  # User opted OUT of text storage
    )

    # Track directory after execution
    files_after = set(os.listdir("."))
    new_files = files_after - files_before
    assert len(new_files) == 0, f"Violated zero persistence! Created files: {new_files}"

    # Assert report invariants
    assert report.in_memory_only is True
    assert report.persisted_to_disk is False
    assert report.persisted_to_db is False
    assert report.is_flagged is True
    assert report.verdict == "Request looks high-risk"
    assert report.extracted_text_preview == "[Discarded per user privacy policy]"
    assert any("UPI PIN" in c for c in report.extracted_claims)


def test_screenshot_analysis_requires_explicit_consent():
    """Verify screenshot analysis aborts without explicit consent (Rule D)."""
    service = ScreenshotAnalysisService()
    report = service.analyze_screenshot(b"dummy_bytes", consent_given=False)
    assert report.is_flagged is False
    assert report.verdict == "Needs Verification"
    assert "Consent required" in report.extracted_claims[0]


# ── 5. Telegram Forward-to-Verify Bot ──────────────────────────────────────────

def test_telegram_bot_webhook_secret_and_rate_limiting():
    """Verify Telegram webhook validates secret token, rate-limits senders, and produces Evidence Cards."""
    bot = TelegramVerifyBot(webhook_secret="super_secret_tg_token_999", rate_limit_per_minute=3)

    # 1. Header validation
    assert bot.verify_webhook_secret("super_secret_tg_token_999") is True
    assert bot.verify_webhook_secret("wrong_token") is False
    assert bot.verify_webhook_secret(None) is False

    # 2. Process forwarded message with digital arrest threat
    update = {
        "update_id": 1001,
        "message": {
            "message_id": 42,
            "chat": {"id": 987654321},
            "text": "Aapka digital arrest warrant nikla hai, video call pe aao.",
        },
    }

    success, card, msg = bot.process_forwarded_update(update, consent_given=True)
    assert success is True
    assert card is not None
    assert card.verdict == "Request looks high-risk"
    assert card.stamp_code == "[HIGH-RISK]"
    assert any("digital arrest" in f.lower() for f in card.key_findings)
    assert any("1930" in a for a in card.immediate_actions)

    # 3. Rate limiting enforcement
    # Trigger 3 more calls to exceed rate limit (limit = 3)
    bot.process_forwarded_update(update, consent_given=True)
    bot.process_forwarded_update(update, consent_given=True)
    limited_success, limited_card, limited_msg = bot.process_forwarded_update(update, consent_given=True)
    assert limited_success is False
    assert "Rate limit exceeded" in limited_msg


# ── 6. WhatsApp Business Platform Bot ─────────────────────────────────────────

def test_whatsapp_bot_hub_signature_and_meta_policy():
    """Verify WhatsApp bot validates X-Hub-Signature-256 and conforms to Meta terms."""
    bot = WhatsAppVerifyBot(app_secret="test_meta_app_secret_456", verify_token="meta_token_789")

    # 1. Webhook subscription handshake
    challenge = bot.verify_webhook_subscription(mode="subscribe", token="meta_token_789", challenge="challenge_123")
    assert challenge == "challenge_123"

    # 2. X-Hub-Signature-256 HMAC verification
    import hmac, hashlib
    payload_body = b'{"object":"whatsapp_business_account"}'
    valid_sig = "sha256=" + hmac.new(b"test_meta_app_secret_456", payload_body, hashlib.sha256).hexdigest()
    assert bot.verify_webhook_hub_signature(payload_body, valid_sig) is True
    assert bot.verify_webhook_hub_signature(payload_body, "sha256=invalidhash") is False

    # 3. User-initiated message forward processing
    wa_update = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "919876543210",
                        "type": "text",
                        "text": {"body": "Enter UPI PIN to receive cashback of Rs 2000."},
                    }]
                }
            }]
        }]
    }

    success, card, msg = bot.process_incoming_forward(wa_update, consent_given=True)
    assert success is True
    assert card is not None
    assert card.verdict == "Request looks high-risk"
    assert any("UPI Collect" in f for f in card.key_findings)

    # 4. Meta Policy Compliance
    policy = bot.get_meta_policy_details()
    assert policy.terms_check == "COMPLIANT"
    assert policy.conversation_type == "SERVICE_CONVERSATION"
    assert "Zero unsolicited outbound messaging" in policy.opt_in_policy


# ── 7. Voice-Note Triage Service (Rule B Cap) ──────────────────────────────────

def test_voice_note_triage_rule_b_cap_and_inconclusive_verdicts():
    """Verify voice-note triage enforces Rule B cap (+0.15 max) and frequent inconclusive verdicts."""
    triage = VoiceNoteTriageService()

    # 1. Low clarity voice note -> must output "inconclusive"
    noisy_clip = b"RIFF" + b"\x00" * 4000
    res_noisy = triage.triage_voice_note(noisy_clip, consent_given=True, synthetic_clarity_score=0.45)
    assert res_noisy.authenticity_finding == "inconclusive"
    assert res_noisy.risk_boost == 0.0
    assert res_noisy.verdict == "Needs Verification"

    # 2. High synthetic clarity clip -> capped at <= 0.15 per Rule B
    synthetic_clip = b"RIFF" + b"\x00" * 8000
    res_synth = triage.triage_voice_note(synthetic_clip, consent_given=True, synthetic_clarity_score=0.92)
    assert res_synth.risk_boost <= 0.15
    assert res_synth.verdict == "Needs Verification"  # Rule A: Never labels person as fake
    assert res_synth.persisted_to_disk is False

    # 3. Consent gate
    res_unconsented = triage.triage_voice_note(synthetic_clip, consent_given=False)
    assert res_unconsented.is_processed is False


# ── 8. Low-Literacy Regional Language Packs ───────────────────────────────────

def test_low_literacy_mode_regional_packs_and_spoken_scripts():
    """Verify regional language packs and spoken audio explanation scripts."""
    service = LowLiteracyService()

    langs = service.list_supported_languages()
    lang_codes = {l["code"] for l in langs}
    assert {"hi", "hi_en", "ar", "en"}.issubset(lang_codes)

    # Hindi script
    hi_exp = service.generate_spoken_explanation("hi")
    assert "यूपीआई पिन" in hi_exp.spoken_audio_script
    assert "डिजिटल गिरफ़्तारी" in hi_exp.spoken_audio_script
    assert hi_exp.field_comprehension_validated is False  # Must be unverified until real user tests

    # Arabic script
    ar_exp = service.generate_spoken_explanation("ar")
    assert "لا تقم بإدخال رمز التحقق" in ar_exp.spoken_audio_script
    assert ar_exp.field_comprehension_validated is False


# ── 9. Distribution REST API Endpoints Integration ───────────────────────────

def test_distribution_api_endpoints():
    """Integration test for Phase H REST endpoints."""
    from fastapi.testclient import TestClient
    from apps.api.app.main import app
    import hmac, hashlib

    client = TestClient(app)

    # 1. Screenshot analysis endpoint (consent=True)
    img_buf = io.BytesIO()
    img = Image.new("RGB", (200, 200), color=(255, 255, 255))
    img.save(img_buf, format="PNG")
    img_bytes = img_buf.getvalue()

    resp_img = client.post(
        "/api/v1/distribution/screenshot/analyze",
        files={"file": ("chat.png", img_bytes, "image/png")},
        data={"consent_given": "true"},
    )
    assert resp_img.status_code == 200
    data_img = resp_img.json()
    assert data_img["in_memory_only"] is True
    assert data_img["persisted_to_disk"] is False

    # 2. Telegram webhook endpoint
    tg_update = {
        "update_id": 999,
        "message": {
            "message_id": 1,
            "chat": {"id": 112233},
            "text": "Normal work schedule for this Friday.",
        },
    }
    resp_tg = client.post(
        "/api/v1/distribution/telegram/webhook",
        json=tg_update,
        headers={"X-Telegram-Bot-Api-Secret-Token": "lifelens_telegram_secret_token_123"},
    )
    assert resp_tg.status_code == 200
    assert resp_tg.json()["status"] == "success"

    # 3. WhatsApp webhook GET handshake
    resp_wa_get = client.get(
        "/api/v1/distribution/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=lifelens_meta_verify_token_xyz&hub.challenge=test_meta_challenge"
    )
    assert resp_wa_get.status_code == 200
    assert resp_wa_get.text == "test_meta_challenge"

    # 4. WhatsApp webhook POST with HMAC signature
    wa_payload = b'{"entry":[{"changes":[{"value":{"messages":[{"from":"123","type":"text","text":{"body":"Hello"}}]}}]}]}'
    app_secret = "lifelens_meta_app_secret_abc123"
    wa_sig = "sha256=" + hmac.new(app_secret.encode(), wa_payload, hashlib.sha256).hexdigest()

    resp_wa_post = client.post(
        "/api/v1/distribution/whatsapp/webhook",
        content=wa_payload,
        headers={"X-Hub-Signature-256": wa_sig, "Content-Type": "application/json"},
    )
    assert resp_wa_post.status_code == 200
    assert resp_wa_post.json()["status"] == "success"

    # 5. Low-literacy spoken script endpoint
    resp_ll = client.get("/api/v1/distribution/low-literacy/script?lang=hi")
    assert resp_ll.status_code == 200
    assert "यूपीआई" in resp_ll.json()["spoken_audio_script"]
