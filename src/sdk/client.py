"""
LifeLens Ω — Official Python Developer SDK (Phase 7)
Evolved Blueprint Phase 7 (Months 22-24)

Client library for ATS platforms (Greenhouse, Workday, Lever), job boards,
and enterprise security operations teams to integrate LifeLens Ω verification.
"""
from __future__ import annotations
import hashlib
import hmac
import time
import httpx
from typing import Dict, List, Optional, Any


class LifeLensError(Exception):
    """Base exception for LifeLens SDK operations."""
    pass


class AuthenticationError(LifeLensError):
    """Raised when API key is missing, invalid, or revoked."""
    pass


class RateLimitExceeded(LifeLensError):
    """Raised when requests exceed organization per-minute limits."""
    pass


class LifeLensClient:
    """
    Official Python Client for LifeLens Ω Reality Integrity Platform.

    Example:
        >>> from src.sdk.client import LifeLensClient
        >>> client = LifeLensClient(api_key="ll_live_...", base_url="http://localhost:8000")
        >>> result = client.verify_job(
        ...     company_name="DeepMind",
        ...     company_website="https://deepmind.google",
        ...     recruiter_email="careers@deepmind.google"
        ... )
        >>> print(result["risk_assessment"]["risk_level"])
        'LOW'
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "http://localhost:8000",
        timeout: int = 15,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        headers = {
            "User-Agent": "LifeLens-Python-SDK/2.0.0",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        self.client = httpx.Client(timeout=self.timeout, headers=headers)

    def _request(self, method: str, path: str, **kwargs) -> Any:
        url = f"{self.base_url}{path}"
        try:
            resp = self.client.request(method, url, **kwargs)
        except httpx.RequestError as exc:
            raise LifeLensError(f"Network error communicating with LifeLens: {exc}") from exc

        if resp.status_code == 401:
            raise AuthenticationError(f"Authentication failed: {resp.text}")
        if resp.status_code == 429:
            raise RateLimitExceeded(f"Rate limit exceeded: {resp.text}")
        if not resp.is_success:
            raise LifeLensError(f"API Error (HTTP {resp.status_code}): {resp.text}")

        if "text/plain" in resp.headers.get("content-type", ""):
            return resp.text
        return resp.json()

    # --- Verification & CECT Reasoning ---

    def verify_job(
        self,
        job_title: Optional[str] = None,
        company_name: Optional[str] = None,
        company_website: Optional[str] = None,
        recruiter_email: Optional[str] = None,
        recruiter_name: Optional[str] = None,
        job_description: Optional[str] = None,
        claimed_country: str = "GB",
    ) -> Dict[str, Any]:
        """Runs full CECT reality integrity verification on target recruiter claims."""
        payload = {
            "job_title": job_title,
            "company_name": company_name,
            "company_website": company_website,
            "recruiter_email": recruiter_email,
            "recruiter_name": recruiter_name,
            "job_description": job_description,
            "claimed_country": claimed_country,
            "consent_for_analysis": True,
        }
        return self._request("POST", "/api/v1/verify-job", json=payload)

    # --- Machine Learning Fast Detection ---

    def detect_scam_text(self, text: str) -> Dict[str, Any]:
        """Classifies recruiter text or job description via trained ML ensemble."""
        return self._request("POST", "/api/v1/ml/detect/text", json={"text": text})

    def detect_phishing_url(self, url: str) -> Dict[str, Any]:
        """Evaluates whether URL matches known phishing heuristics or PhishTank feed."""
        return self._request("POST", "/api/v1/ml/detect/url", json={"url": url})

    # --- Post-Incident Recovery ---

    def initiate_recovery(
        self,
        incident_type: str,
        financial_amount_lost: float = 0.0,
        currency: str = "USD",
        compromised_accounts: Optional[List[str]] = None,
        description: str = "",
    ) -> Dict[str, Any]:
        """Initiates an automated post-incident recovery workflow."""
        payload = {
            "incident_id": f"sdk-inc-{int(time.time())}",
            "incident_type": incident_type,
            "financial_amount_lost": financial_amount_lost,
            "currency": currency,
            "compromised_accounts": compromised_accounts or [],
            "description": description,
        }
        return self._request("POST", "/api/v1/recovery/initiate", json=payload)

    # --- Enterprise & Webhooks ---

    def get_enterprise_analytics(self, org_id: str = "org-default-enterprise") -> Dict[str, Any]:
        """Retrieves aggregated enterprise threat metrics and verification volume."""
        return self._request("GET", f"/api/v1/enterprise/analytics?org_id={org_id}")

    def create_webhook(
        self,
        target_url: str,
        subscribed_events: Optional[List[str]] = None,
        org_id: str = "org-default-enterprise",
    ) -> Dict[str, Any]:
        """Subscribes a webhook endpoint to LifeLens platform security events."""
        payload = {
            "org_id": org_id,
            "target_url": target_url,
            "subscribed_events": subscribed_events or [
                "verification.completed",
                "risk.high_detected",
            ],
        }
        return self._request("POST", "/api/v1/webhooks/subscriptions", json=payload)

    # --- Webhook Cryptographic Verification Helper ---

    @staticmethod
    def verify_webhook_signature(
        secret_key: str, signature_header: str, payload_json: str, tolerance_seconds: int = 300
    ) -> bool:
        """
        Validates HMAC-SHA256 signature on incoming webhook callbacks.

        Header format: t={timestamp},v1={hex_signature}
        """
        try:
            parts = dict(p.split("=", 1) for p in signature_header.split(","))
            timestamp = int(parts["t"])
            expected_v1 = parts["v1"]

            if abs(int(time.time()) - timestamp) > tolerance_seconds:
                return False

            signed_payload = f"{timestamp}.{payload_json}".encode("utf-8")
            computed = hmac.new(
                secret_key.encode("utf-8"), signed_payload, hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected_v1, computed)
        except Exception:
            return False

    # --- Phase 8: Production SRE & Observability ---

    def get_metrics(self) -> str:
        """Retrieves raw Prometheus telemetry metrics in official scrape text format."""
        return self._request("GET", "/metrics")

    def get_sre_health(self) -> Dict[str, Any]:
        """Deep subsystem health & readiness evaluation."""
        return self._request("GET", "/api/v1/sre/health")

    def get_sre_adapters(self) -> Dict[str, Any]:
        """Queries live adapter health matrix and active kill switches."""
        return self._request("GET", "/api/v1/sre/adapters")

    def run_sentinel_audit(self) -> Dict[str, Any]:
        """Triggers automated Sentinel quality gate evaluation and self-healing."""
        return self._request("POST", "/api/v1/sre/sentinel/audit")

    def evaluate_alerts(self) -> Dict[str, Any]:
        """Evaluates live system telemetry against Prometheus alerts.yml rules."""
        return self._request("GET", "/api/v1/sre/alerts/evaluate")

    def inject_chaos(
        self,
        adapter_key: str,
        fault_type: str = "ERROR_SPIKE",
        error_rate: float = 0.60,
        coverage_pct: float = 0.40,
        data_age_hours: float = 72.0,
    ) -> Dict[str, Any]:
        """Injects synthetic fault into a registry adapter to test circuit breaker trip."""
        payload = {
            "adapter_key": adapter_key,
            "fault_type": fault_type,
            "error_rate": error_rate,
            "coverage_pct": coverage_pct,
            "data_age_hours": data_age_hours,
        }
        return self._request("POST", "/api/v1/sre/chaos/inject", json=payload)

    def reset_chaos(self, adapter_key: Optional[str] = None) -> Dict[str, Any]:
        """Clears chaos faults and triggers automated Sentinel auto-healing."""
        payload = {"adapter_key": adapter_key}
        return self._request("POST", "/api/v1/sre/chaos/reset", json=payload)

