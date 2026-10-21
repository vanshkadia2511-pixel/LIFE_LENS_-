"""
LifeLens Ω — ML Inference Service
Loads trained scam-detection models once at startup and exposes
thread-safe predict() helpers used by the v1_ml API router.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np

logger = logging.getLogger("lifelens.ml_inference")

# ── Resolve model root (works regardless of working-directory) ──────────────
_ROOT = Path(__file__).resolve().parents[4]          # …/Life_Lens_Ai
_MODEL_DIR = _ROOT / "models"


# ── Lazy-loaded model cache ─────────────────────────────────────────────────
_cache: dict[str, Any] = {}


def _load(name: str, path: Path) -> Any | None:
    if name in _cache:
        return _cache[name]
    if not path.exists():
        logger.warning("Model not found: %s", path)
        return None
    try:
        bundle = joblib.load(path)
        _cache[name] = bundle
        logger.info("Loaded model '%s' from %s", name, path)
        return bundle
    except Exception as exc:                         # noqa: BLE001
        logger.error("Failed to load model '%s': %s", name, exc)
        return None


def _binary_bundle() -> Any | None:
    return _load("binary", _MODEL_DIR / "best_model.joblib")


def _multiclass_bundle() -> Any | None:
    return _load("multiclass", _MODEL_DIR / "multiclass" / "best_model.joblib")


def _url_bundle() -> Any | None:
    return _load("url_ngram", _MODEL_DIR / "phishing_url" / "url_ngram_model.joblib")


# ── Public helpers ───────────────────────────────────────────────────────────

def predict_text(text: str) -> dict:
    """
    Run binary + multiclass inference on a text snippet.
    Returns a dict with keys: binary_label, binary_is_scam,
                               multiclass_category, models_loaded.
    """
    result: dict[str, Any] = {
        "input_text": text,
        "binary_label": None,
        "binary_is_scam": None,
        "binary_confidence": None,
        "multiclass_category": None,
        "models_loaded": [],
    }

    # --- Binary Job-Scam Detector ---
    bundle = _binary_bundle()
    if bundle:
        pipe = bundle["pipeline"]
        pred = pipe.predict([text])[0]
        is_scam = str(pred) == "1"
        proba = None
        if hasattr(pipe, "predict_proba"):
            try:
                proba = float(pipe.predict_proba([text])[0][1])
            except Exception:          # noqa: BLE001
                proba = None
        result["binary_label"] = "SCAM" if is_scam else "LEGITIMATE"
        result["binary_is_scam"] = is_scam
        result["binary_confidence"] = proba
        result["models_loaded"].append("binary_job_scam")

    # --- Multiclass Fraud Classifier ---
    bundle = _multiclass_bundle()
    if bundle:
        pipe = bundle["pipeline"]
        classes = bundle.get("classes", [])
        pred = pipe.predict([text])[0]
        if isinstance(pred, (int, np.integer)) and pred < len(classes):
            category = classes[pred]
        else:
            category = str(pred)
        result["multiclass_category"] = category
        result["models_loaded"].append("multiclass_fraud")

    return result


def predict_url(url: str) -> dict:
    """
    Run phishing URL inference.
    Returns a dict with keys: input_url, is_phishing, confidence, model_loaded.
    """
    result: dict[str, Any] = {
        "input_url": url,
        "is_phishing": None,
        "confidence": None,
        "label": None,
        "model_loaded": False,
    }

    bundle = _url_bundle()
    if bundle:
        pipe = bundle["pipeline"]
        pred = int(pipe.predict([url])[0])
        proba = float(pipe.predict_proba([url])[0][1])
        result["is_phishing"] = pred == 1
        result["confidence"] = proba
        result["label"] = "PHISHING" if pred == 1 else "LEGITIMATE"
        result["model_loaded"] = True

    return result


def preload_all() -> None:
    """Call at startup to warm all models into memory."""
    _binary_bundle()
    _multiclass_bundle()
    _url_bundle()
    loaded = list(_cache.keys())
    logger.info("ML models preloaded: %s", loaded)
