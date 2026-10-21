"""
LifeLens Ω — ML Detection API Router  (v1)
POST /api/v1/ml/detect/text  → job-scam / fraud text classification
POST /api/v1/ml/detect/url   → phishing URL detection
POST /api/v1/ml/enrich       → unified: ML + WHOIS + PhishTank + Companies House
GET  /api/v1/ml/health       → model readiness probe
"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from ..services.ml_inference import predict_text, predict_url, preload_all
from ..services.external_checks import check_domain_whois, check_phishtank, enrich_job_verification
from ..verification.companies_house import CompaniesHouseAdapter

router = APIRouter(prefix="/api/v1/ml", tags=["ML Detection"])


# ── Request / Response schemas ───────────────────────────────────────────────

class TextDetectRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=10,
        max_length=10_000,
        description="Job posting, email, SMS, or any free-text to classify.",
        examples=["Urgent hiring! Earn $500/day from home. Send fee via Telegram."],
    )


class TextDetectResponse(BaseModel):
    input_text: str
    binary_label: Literal["SCAM", "LEGITIMATE"] | None
    binary_is_scam: bool | None
    binary_confidence: float | None = Field(
        None, description="Probability that text is a scam (0-1). Null if model unavailable."
    )
    multiclass_category: str | None = Field(
        None, description="Fraud sub-category from multiclass model."
    )
    models_loaded: list[str]
    risk_level: str | None = None

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra={
            "example": {
                "input_text": "Urgent hiring! Earn $500/day from home.",
                "binary_label": "SCAM",
                "binary_is_scam": True,
                "binary_confidence": 0.97,
                "multiclass_category": "job_scam",
                "models_loaded": ["binary_job_scam", "multiclass_fraud"],
                "risk_level": "HIGH",
            }
        }
    )


class UrlDetectRequest(BaseModel):
    url: str = Field(
        ...,
        description="URL to evaluate for phishing.",
        examples=["http://paypa1-secure-login.tk/verify"],
    )


class UrlDetectResponse(BaseModel):
    input_url: str
    is_phishing: bool | None
    confidence: float | None = Field(None, description="Phishing probability (0-1).")
    label: Literal["PHISHING", "LEGITIMATE"] | None
    model_loaded: bool
    risk_level: str | None = None

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra={
            "example": {
                "input_url": "http://paypa1-secure-login.tk/verify",
                "is_phishing": True,
                "confidence": 0.98,
                "label": "PHISHING",
                "model_loaded": True,
                "risk_level": "CRITICAL",
            }
        }
    )


class MLHealthResponse(BaseModel):
    status: str
    models: dict[str, str]


# ── Risk level helper ────────────────────────────────────────────────────────

def _risk_level(confidence: float | None, is_bad: bool | None) -> str | None:
    if is_bad is None or confidence is None:
        return None
    if not is_bad:
        return "LOW"
    if confidence >= 0.9:
        return "CRITICAL"
    if confidence >= 0.7:
        return "HIGH"
    return "MEDIUM"


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post(
    "/detect/text",
    response_model=TextDetectResponse,
    summary="Classify free-text for job scams / fraud",
    status_code=status.HTTP_200_OK,
)
async def detect_text(body: TextDetectRequest) -> TextDetectResponse:
    """
    Runs the **Binary Job-Scam Detector** (Linear SVM) and the
    **Multiclass Fraud Classifier** (Sentinel) on the supplied text.

    Both models must be trained and present in `models/` for results to appear.
    If a model is missing the field will be `null` instead of raising an error.
    """
    try:
        result = predict_text(body.text)
    except Exception as exc:                         # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference failed: {exc}",
        ) from exc

    result["risk_level"] = _risk_level(
        result.get("binary_confidence"), result.get("binary_is_scam")
    )
    return TextDetectResponse(**result)


@router.post(
    "/detect/url",
    response_model=UrlDetectResponse,
    summary="Classify a URL as Phishing or Legitimate",
    status_code=status.HTTP_200_OK,
)
async def detect_url(body: UrlDetectRequest) -> UrlDetectResponse:
    """
    Runs the **Phishing URL Detector** (Char N-Gram model) on the supplied URL.
    """
    try:
        result = predict_url(body.url)
    except Exception as exc:                         # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"URL inference failed: {exc}",
        ) from exc

    result["risk_level"] = _risk_level(result.get("confidence"), result.get("is_phishing"))
    return UrlDetectResponse(**result)


@router.get(
    "/health",
    response_model=MLHealthResponse,
    summary="ML model readiness probe",
)
async def ml_health() -> MLHealthResponse:
    """
    Returns the load status of each ML model.
    Useful for Kubernetes liveness/readiness probes or healthcheck dashboards.
    """
    from pathlib import Path

    _ROOT = Path(__file__).resolve().parents[4]
    _MODEL_DIR = _ROOT / "models"

    models = {
        "binary_job_scam":   "ready" if (_MODEL_DIR / "best_model.joblib").exists() else "missing",
        "multiclass_fraud":  "ready" if (_MODEL_DIR / "multiclass" / "best_model.joblib").exists() else "missing",
        "phishing_url_ngram":"ready" if (_MODEL_DIR / "phishing_url" / "url_ngram_model.joblib").exists() else "missing",
    }
    overall = "healthy" if all(v == "ready" for v in models.values()) else "degraded"
    return MLHealthResponse(status=overall, models=models)
# ── Enriched unified endpoint ─────────────────────────────────────────────────

class EnrichRequest(BaseModel):
    job_description: str = Field(
        ..., min_length=10, max_length=10_000,
        description="Job posting / recruiter message text.",
    )
    company_name: str | None = Field(None, description="Claimed company name (for registry check).")
    company_website: str | None = Field(None, description="Company website URL (for WHOIS check).")
    recruiter_email: str | None = Field(None, description="Recruiter email (for domain WHOIS check).")
    job_posting_url: str | None = Field(None, description="URL in the job post (for PhishTank check).")
    country: str = Field("GB", description="ISO 2-letter country code for registry lookup.")


class EnrichResponse(BaseModel):
    ml_text: dict
    url_phishtank: dict | None = None
    company_whois: dict | None = None
    recruiter_whois: dict | None = None
    companies_house: dict | None = None
    overall_risk_level: str
    risk_signals: list[str]


@router.post(
    "/enrich",
    response_model=EnrichResponse,
    summary="Unified ML + WHOIS + PhishTank + Companies House analysis",
)
async def enrich_analysis(body: EnrichRequest) -> EnrichResponse:
    """
    One-shot enriched analysis combining:
    - Binary + multiclass ML text classification
    - PhishTank URL reputation check (if job_posting_url provided)
    - WHOIS/RDAP domain age for company website + recruiter email
    - UK Companies House registry lookup (if country == GB/UK)
    """
    signals: list[str] = []

    # 1. ML text inference
    ml_result = predict_text(body.job_description)
    if ml_result.get("binary_is_scam"):
        conf = ml_result.get("binary_confidence") or 0
        signals.append(f"ML model flagged text as SCAM (confidence: {conf:.0%})")
    cat = ml_result.get("multiclass_category")
    if cat and str(cat).strip().lower() not in ("legitimate", "legit", "clean", "safe", "none", "unknown", "normal", "non-scam"):
        signals.append(f"Fraud category detected: {cat}")

    # 2. PhishTank URL check
    phishtank_result = None
    if body.job_posting_url:
        phishtank_result = check_phishtank(body.job_posting_url)
        if phishtank_result.get("is_phishing"):
            signals.append("Job posting URL is listed in PhishTank as a known phishing site")

    # 3. WHOIS checks
    whois_enrichment = enrich_job_verification(
        company_website=body.company_website,
        recruiter_email=body.recruiter_email,
    )
    company_whois = whois_enrichment.get("company_domain_whois")
    recruiter_whois = whois_enrichment.get("recruiter_domain_whois")

    if company_whois and company_whois.get("is_new_domain"):
        age = company_whois.get("domain_age_days", "?")
        signals.append(f"Company domain is very new ({age} days old — under 180 days)")
    if recruiter_whois and recruiter_whois.get("is_new_domain"):
        age = recruiter_whois.get("domain_age_days", "?")
        signals.append(f"Recruiter email domain is very new ({age} days old)")

    # 4. Companies House registry check (UK)
    ch_result = None
    if body.company_name and body.country.upper() in ("GB", "UK", "UNITED KINGDOM"):
        adapter = CompaniesHouseAdapter()
        res = adapter.verify_company(body.company_name)
        status_val = res.status.value if res.status else None
        ch_result = {
            "found": res.found,
            "source": res.source,
            "source_url": res.source_url,
            "status": status_val,
            "data": res.result_data,
            "confidence": res.confidence,
            "error": res.error,
        }
        # Only treat as a missing entity signal if the registry was reachable and confirmed not found
        if status_val == "AVAILABLE" and not res.found:
            signals.append(
                f"Company '{body.company_name}' not found in UK Companies House registry"
            )

    # 5. Compute overall risk
    n = len(signals)
    if n == 0:
        overall = "LOW"
    elif n == 1:
        overall = "MEDIUM"
    elif n <= 3:
        overall = "HIGH"
    else:
        overall = "CRITICAL"

    # Overlay ML confidence if very high
    conf = ml_result.get("binary_confidence") or 0
    if ml_result.get("binary_is_scam") and conf >= 0.9:
        overall = "CRITICAL"

    ml_result["risk_level"] = _risk_level(conf if conf else None, ml_result.get("binary_is_scam"))

    return EnrichResponse(
        ml_text=ml_result,
        url_phishtank=phishtank_result,
        company_whois=company_whois,
        recruiter_whois=recruiter_whois,
        companies_house=ch_result,
        overall_risk_level=overall,
        risk_signals=signals,
    )
