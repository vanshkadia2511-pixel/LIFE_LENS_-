"""
LifeLens Ω — FastAPI Application Entrypoint
Implementation Plan §6, §7, §59
"""
from __future__ import annotations
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1_verification import router as verification_router
from .api.v1_admin import router as admin_router
from .api.v1_phase3 import router as phase3_router
from .api.v1_phases4_5 import router as phases4_5_router
from .api.v1_call_guard import router as call_guard_router
from .api.v1_desktop_guard import router as desktop_guard_router
from .api.v1_ml import router as ml_router
from .api.v1_phase6_recovery import router as recovery_router
from .api.v1_phase7_enterprise import router as enterprise_router
from .api.v1_phase8_sre import router as sre_router
from .api.v1_detectors import router as detectors_router
from .api.v1_distribution import router as distribution_router
from .api.v1_response import router as response_router
from .api.v1_governance import router as governance_router
from .services.ml_inference import preload_all as preload_ml_models
from .services.sre_sentinel import sre_sentinel
from .services.metrics import generate_prometheus_metrics, PROMETHEUS_CONTENT_TYPE, metrics_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("lifelens-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting LifeLens Ω API Server...")
    preload_ml_models()          # warm all ML models into memory at startup
    sre_sentinel.run_health_audit()  # initial baseline SRE health audit (§76)
    yield
    logger.info("Shutting down LifeLens Ω API Server...")


app = FastAPI(
    title="LifeLens Ω API",
    description="Reality Integrity Intelligence & Job/Offer Verification Platform",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS middleware for extension and web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^(chrome-extension://.*|https?://(localhost|127\.0\.0\.1)(:\d+)?)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from pathlib import Path
from fastapi.staticfiles import StaticFiles

import re
import time
from fastapi.responses import Response
from starlette.requests import Request

# Include routers
app.include_router(verification_router)
app.include_router(admin_router)
app.include_router(phase3_router)
app.include_router(phases4_5_router)
app.include_router(call_guard_router)      # Phase B Call Guardian Layer 0 (pre-call link checker)
app.include_router(desktop_guard_router)   # Phase C Desktop Call Guard (Layers 2, 3, 4, Receipt)
app.include_router(ml_router)             # ML scam / phishing detection endpoints
app.include_router(recovery_router)    # Phase 6 post-incident recovery automation
app.include_router(enterprise_router)  # Phase 7 enterprise API & webhooks
app.include_router(sre_router)         # Phase 8 SRE health sentinel & diagnostics
app.include_router(detectors_router)   # Phase G new specialized detectors
app.include_router(distribution_router) # Phase H distribution bots & screenshot OCR
app.include_router(response_router)     # Phase I response & impact (takedown, recovery, clustering)
app.include_router(governance_router)   # Phase J trust & governance (disputes, calibration, canary, transparency)

_ID_PATTERN = re.compile(r"/(?:rec_|sub_|org_|key_|pat_)?[0-9a-fA-F-]{8,}")

def _normalize_metric_path(path: str) -> str:
    norm = _ID_PATTERN.sub("/{id}", path)
    return norm or "/"

@app.middleware("http")
async def prometheus_telemetry_middleware(request: Request, call_next):
    norm_path = _normalize_metric_path(request.url.path)
    if norm_path.endswith((".css", ".js", ".png", ".jpg", ".ico", ".svg")):
        return await call_next(request)

    start_time = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        duration = time.perf_counter() - start_time
        metrics_service.record_http_request(
            method=request.method,
            endpoint=norm_path,
            status_code=status_code,
            duration_seconds=duration,
        )
        return response
    except Exception as exc:
        duration = time.perf_counter() - start_time
        metrics_service.record_http_request(
            method=request.method,
            endpoint=norm_path,
            status_code=500,
            duration_seconds=duration,
        )
        metrics_service.record_http_error(
            method=request.method,
            endpoint=norm_path,
            error_type=type(exc).__name__,
        )
        raise

@app.get("/metrics", tags=["monitoring"], include_in_schema=False)
async def prometheus_metrics():
    """Prometheus-compatible scrape endpoint matching prometheus.yml (§70)."""
    return Response(
        content=generate_prometheus_metrics(),
        media_type=PROMETHEUS_CONTENT_TYPE,
    )

@app.get("/health", tags=["system"])
@app.get("/api/v1/health", tags=["system"])
async def health_check():
    return {
        "status": "healthy",
        "service": "lifelens-omega-api",
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# Mount web workspace frontend (§49)
web_dir = Path(__file__).resolve().parent.parent.parent / "web"
if web_dir.exists():
    app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")


