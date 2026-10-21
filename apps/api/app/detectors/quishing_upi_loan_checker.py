"""
LifeLens Ω — Phase G: Quishing (QR) Checker, UPI Collect Explainer, and Fake Loan-APK Auditor
Covers:
1. UPICollectExplainer: Explains UPI mechanics and flags "Enter PIN to receive money" fraud.
2. QuishingChecker: Validates QR target URLs safely through SSRF-safe checks.
3. FakeLoanAPKChecker: Static Android manifest audit for black-hat / predatory lending apps.
"""
from __future__ import annotations
import re
from urllib.parse import urlparse
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from apps.api.app.security.ssrf import SSRFShield, SSRFValidationResult


# ── 1. UPI Collect Explainer ──────────────────────────────────────────────────

@dataclass
class UPIAssessment:
    message: str
    is_deceptive: bool
    verdict: str  # Rule A: "Request looks high-risk" | "Verification step completed"
    risk_score: float
    educational_warning: str
    key_takeaway: str = "Entering your UPI PIN always DEDUCTS money from your bank account. You NEVER need a PIN to receive payments."


class UPICollectExplainer:
    """
    Detects the pervasive 'Enter PIN to receive money / cashback' deception.
    Educates the victim on core UPI protocol mechanics.
    """

    _DECEPTIVE_PATTERNS = [
        re.compile(r"\b(?:enter|put|type)\s+(?:your\s+)?(?:upi\s+)?pin\b.*?\b(?:receive|get|claim|credit|refund|cashback|lottery)\b", re.IGNORECASE),
        re.compile(r"\b(?:receive|get|claim|collect)\b.*?\b(?:enter|put)\s+(?:your\s+)?(?:upi\s+)?pin\b", re.IGNORECASE),
        re.compile(r"\b(?:upi\s+pin)\b.*?\b(?:paise\s+milenge|cashback\s+aayega|account\s+me\s+credit)\b", re.IGNORECASE),
    ]

    def analyze_request(
        self,
        message: str,
        claimed_amount: float = 0.0,
        is_collect_request: bool = False,
    ) -> UPIAssessment:
        is_deceptive = False
        reasons: List[str] = []

        for p in self._DECEPTIVE_PATTERNS:
            if p.search(message):
                is_deceptive = True
                reasons.append("Message instructs entering a UPI PIN to receive money/cashback.")
                break

        if is_collect_request and ("receive" in message.lower() or "cashback" in message.lower() or "refund" in message.lower()):
            is_deceptive = True
            reasons.append("Incoming transaction is a Collect Request (debit), but framed as receiving funds.")

        if is_deceptive:
            verdict = "Request looks high-risk"
            risk_score = 0.95
            warning = (
                "CRITICAL WARNING: Entering your UPI PIN always DEDUCTS money from your bank account. "
                "Scammers send Collect Requests claiming you are receiving cashback or lottery winnings. "
                "Never enter your UPI PIN unless you intend to pay out."
            )
        else:
            verdict = "Verification step completed"
            risk_score = 0.10
            warning = "Legitimate payment instruction or standard outward transfer request."

        return UPIAssessment(
            message=message,
            is_deceptive=is_deceptive,
            verdict=verdict,
            risk_score=risk_score,
            educational_warning=warning,
        )


# ── 2. Quishing (QR) Target Checker ──────────────────────────────────────────

@dataclass
class QuishingAssessment:
    payload: str
    is_safe: bool
    verdict: str  # Rule A
    risk_score: float
    flags: List[str] = field(default_factory=list)
    resolved_host: Optional[str] = None


class QuishingChecker:
    """
    Audits decoded QR payloads (URLs or payment deep links) without fetching untrusted content.
    Enforces SSRFShield domain safety and looks for meeting/brand impersonation.
    """

    _SUSPICIOUS_DOMAINS = [
        re.compile(r"zoom-secure", re.IGNORECASE),
        re.compile(r"meet-verify", re.IGNORECASE),
        re.compile(r"login-auth-portal", re.IGNORECASE),
        re.compile(r"teams-meeting-online", re.IGNORECASE),
    ]

    def __init__(self) -> None:
        self.ssrf = SSRFShield()

    def inspect_qr_target(self, payload: str) -> QuishingAssessment:
        flags: List[str] = []
        is_safe = True
        risk_score = 0.05
        host = None

        if payload.startswith("http://") or payload.startswith("https://"):
            try:
                parsed = urlparse(payload)
                host = parsed.hostname or ""

                # Check SSRF safety
                ssrf_check = SSRFShield.validate_url(payload)
                if not ssrf_check.is_safe:
                    flags.append(f"SSRF / Unsafe Network Target: {ssrf_check.reason}")
                    is_safe = False
                    risk_score = max(risk_score, 0.90)

                # Check brand/platform lookalike
                for pat in self._SUSPICIOUS_DOMAINS:
                    if pat.search(host):
                        flags.append(f"Lookalike / Typosquatted Domain: {host}")
                        is_safe = False
                        risk_score = max(risk_score, 0.85)

                if parsed.scheme == "http":
                    flags.append("Insecure plain HTTP URL in QR code")
                    risk_score = max(risk_score, 0.40)

            except Exception as e:
                flags.append(f"Invalid URL structure: {e}")
                is_safe = False
                risk_score = 0.70
        else:
            flags.append("Non-HTTP payload or raw text string in QR")

        if risk_score >= 0.60:
            verdict = "Request looks high-risk"
        elif risk_score >= 0.25:
            verdict = "Needs Verification"
        else:
            verdict = "Verification step completed"

        return QuishingAssessment(
            payload=payload,
            is_safe=is_safe and risk_score < 0.50,
            verdict=verdict,
            risk_score=risk_score,
            flags=flags,
            resolved_host=host,
        )


# ── 3. Fake Loan APK Manifest Auditor ─────────────────────────────────────────

@dataclass
class LoanAPKReport:
    package_name: str
    is_predatory: bool
    verdict: str  # Rule A
    risk_score: float
    findings: List[str] = field(default_factory=list)
    rbi_compliance_note: str = (
        "Under Reserve Bank of India (RBI) and Google Play regulatory guidelines, "
        "personal loan apps are strictly prohibited from accessing user contacts, SMS, "
        "and external storage to prevent debt-trap harassment and extortion."
    )


class FakeLoanAPKChecker:
    """
    Performs static Android Manifest inspection for predatory instant loan applications.
    Flags unauthorized access to Contacts, SMS, Storage, and astronomical APR.
    """

    _INVASIVE_PERMISSIONS = {
        "android.permission.READ_CONTACTS": "Intrusive contact harvesting (used for family/contact extortion)",
        "android.permission.READ_SMS": "Intrusive SMS harvesting (financial OTP & transactional tracking)",
        "android.permission.RECEIVE_SMS": "Active SMS interception capability",
        "android.permission.READ_EXTERNAL_STORAGE": "Gallery / photo access (used for blackmail / morphing)",
    }

    def audit_manifest(self, manifest: Dict[str, Any]) -> LoanAPKReport:
        package_name = manifest.get("package_name", "unknown.apk")
        permissions = manifest.get("permissions", [])
        claimed_apr = manifest.get("claimed_apr_percent", 0.0)

        findings: List[str] = []
        score = 0.0

        for perm in permissions:
            if perm in self._INVASIVE_PERMISSIONS:
                findings.append(self._INVASIVE_PERMISSIONS[perm])
                score += 0.35

        if claimed_apr > 50.0:
            findings.append(f"Predatory usurious APR rate ({claimed_apr}% annually)")
            score += 0.30

        is_predatory = len(findings) > 0 and score >= 0.50
        risk_score = min(1.0, round(score, 2))

        if is_predatory or risk_score >= 0.60:
            verdict = "Request looks high-risk"
        elif risk_score >= 0.25:
            verdict = "Needs Verification"
        else:
            verdict = "Verification step completed"

        return LoanAPKReport(
            package_name=package_name,
            is_predatory=is_predatory,
            verdict=verdict,
            risk_score=risk_score,
            findings=findings,
        )
