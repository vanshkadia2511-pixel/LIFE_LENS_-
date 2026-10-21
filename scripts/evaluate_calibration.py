#!/usr/bin/env python3
"""
scripts/evaluate_calibration.py: Compute Expected Calibration Error (ECE) with 10 equal-width bins
on validation and test splits for all binary models (uncalibrated and calibrated).
Uses compute_expected_calibration_error from apps.api.app.services.media_authenticity.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from apps.api.app.services.media_authenticity import compute_expected_calibration_error
from scripts.evaluate_tabular import grouped_split as tabular_grouped_split
from scripts.train_and_evaluate import (
    extract_domain,
    grouped_split as text_grouped_split,
    load_any,
    near_duplicate_groups,
    prepare,
)


def load_estimator(path: str):
    obj = joblib.load(path)
    if isinstance(obj, dict):
        return obj.get("pipeline") or obj.get("model") or obj
    return obj


def evaluate_text_model_calibration(
    dataset_path: str,
    text_col: str,
    label_col: str,
    pos_label,
    uncal_model_path: str,
    cal_model_path: str,
    dup_thresh: float = 0.9,
    seed: int = 42,
) -> dict:
    raw_df = load_any(dataset_path)
    df = prepare(raw_df, text_col, label_col, pos_label)
    texts = df["text"].tolist()
    y = df["y"].to_numpy(dtype=int)
    groups = near_duplicate_groups(texts, "word", (1, 2), dup_thresh)
    train_idx, val_idx, test_idx = text_grouped_split(y, groups, seed=seed)

    val_texts = [texts[i] for i in val_idx]
    y_val = y[val_idx]
    test_texts = [texts[i] for i in test_idx]
    y_test = y[test_idx]

    # Uncalibrated
    uncal = load_estimator(uncal_model_path)
    p_val_uncal = uncal.predict_proba(val_texts)[:, 1].tolist()
    p_test_uncal = uncal.predict_proba(test_texts)[:, 1].tolist()

    # Calibrated
    cal = load_estimator(cal_model_path)
    p_val_cal = cal.predict_proba(val_texts)[:, 1].tolist()
    p_test_cal = cal.predict_proba(test_texts)[:, 1].tolist()

    return {
        "val": {
            "uncalibrated_ece": compute_expected_calibration_error(p_val_uncal, y_val.tolist(), n_bins=10),
            "calibrated_ece": compute_expected_calibration_error(p_val_cal, y_val.tolist(), n_bins=10),
        },
        "test": {
            "uncalibrated_ece": compute_expected_calibration_error(p_test_uncal, y_test.tolist(), n_bins=10),
            "calibrated_ece": compute_expected_calibration_error(p_test_cal, y_test.tolist(), n_bins=10),
        },
    }


def evaluate_url_char_calibration(
    dataset_path: str,
    uncal_model_path: str,
    cal_model_path: str,
    seed: int = 42,
) -> dict:
    raw_df = load_any(dataset_path)
    df = prepare(raw_df, "url", "label", 1)
    texts = df["text"].tolist()
    y = df["y"].to_numpy(dtype=int)
    groups = np.array([extract_domain(u) for u in texts])
    train_idx, val_idx, test_idx = text_grouped_split(y, groups, seed=seed)

    val_texts = [texts[i] for i in val_idx]
    y_val = y[val_idx]
    test_texts = [texts[i] for i in test_idx]
    y_test = y[test_idx]

    uncal = load_estimator(uncal_model_path)
    p_val_uncal = uncal.predict_proba(val_texts)[:, 1].tolist()
    p_test_uncal = uncal.predict_proba(test_texts)[:, 1].tolist()

    cal = load_estimator(cal_model_path)
    p_val_cal = cal.predict_proba(val_texts)[:, 1].tolist()
    p_test_cal = cal.predict_proba(test_texts)[:, 1].tolist()

    return {
        "val": {
            "uncalibrated_ece": compute_expected_calibration_error(p_val_uncal, y_val.tolist(), n_bins=10),
            "calibrated_ece": compute_expected_calibration_error(p_val_cal, y_val.tolist(), n_bins=10),
        },
        "test": {
            "uncalibrated_ece": compute_expected_calibration_error(p_test_uncal, y_test.tolist(), n_bins=10),
            "calibrated_ece": compute_expected_calibration_error(p_test_cal, y_test.tolist(), n_bins=10),
        },
    }


def evaluate_url_tabular_calibration(
    dataset_path: str,
    uncal_model_path: str,
    cal_model_path: str,
    seed: int = 42,
) -> dict:
    df = pd.read_csv(dataset_path)
    df = df.dropna(subset=["url", "label"]).drop_duplicates(subset=["url"])
    y = df["label"].astype(int).to_numpy()
    urls = df["url"].tolist()
    groups = np.array([extract_domain(u) for u in urls])

    feature_cols = [c for c in df.columns if c not in ("url", "label", "serial_number", "registered_domain")]
    X = df[feature_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy()

    train_idx, val_idx, test_idx = tabular_grouped_split(y, groups, seed=seed)

    X_val, y_val = X[val_idx], y[val_idx]
    X_test, y_test = X[test_idx], y[test_idx]

    uncal = load_estimator(uncal_model_path)
    p_val_uncal = uncal.predict_proba(X_val)[:, 1].tolist()
    p_test_uncal = uncal.predict_proba(X_test)[:, 1].tolist()

    cal = load_estimator(cal_model_path)
    p_val_cal = cal.predict_proba(X_val)[:, 1].tolist()
    p_test_cal = cal.predict_proba(X_test)[:, 1].tolist()

    return {
        "val": {
            "uncalibrated_ece": compute_expected_calibration_error(p_val_uncal, y_val.tolist(), n_bins=10),
            "calibrated_ece": compute_expected_calibration_error(p_val_cal, y_val.tolist(), n_bins=10),
        },
        "test": {
            "uncalibrated_ece": compute_expected_calibration_error(p_test_uncal, y_test.tolist(), n_bins=10),
            "calibrated_ece": compute_expected_calibration_error(p_test_cal, y_test.tolist(), n_bins=10),
        },
    }


def main():
    print("Evaluating calibration across all binary models (10 equal-width bins)...")

    results = {}

    print("\n1. Job Scam Binary Detector (DIFrauD)...")
    results["job_scam"] = evaluate_text_model_calibration(
        dataset_path="datasets/job_scam_text/difraud/train.jsonl",
        text_col="text",
        label_col="label",
        pos_label="1",
        uncal_model_path="models/job_scam_v2/model.joblib",
        cal_model_path="models/job_scam_calibrated_v2/model.joblib",
    )

    print("2. Sentinel Binary Fraud Detector...")
    results["sentinel_binary_fraud"] = evaluate_text_model_calibration(
        dataset_path="datasets/job_scam_text/indian_scam_multiclass/sentinel_dataset_multiclass.csv",
        text_col="text",
        label_col="label",
        pos_label="1",
        uncal_model_path="models/sentinel_binary_fraud_v2/model.joblib",
        cal_model_path="models/sentinel_binary_fraud_calibrated_v2/model.joblib",
    )

    print("3. URL Phishing Char N-Gram (CompPhish)...")
    results["url_char_ngram"] = evaluate_url_char_calibration(
        dataset_path="datasets/phishing_urls/compphish/all_features_threshold90.csv",
        uncal_model_path="models/url_char_ngram_v2/model.joblib",
        cal_model_path="models/url_char_ngram_calibrated_v2/model.joblib",
    )

    print("4. URL Phishing Tabular HistGB (CompPhish)...")
    results["url_tabular"] = evaluate_url_tabular_calibration(
        dataset_path="datasets/phishing_urls/compphish/all_features_threshold90.csv",
        uncal_model_path="models/url_tabular_v2/model.joblib",
        cal_model_path="models/url_tabular_calibrated_v2/model.joblib",
    )

    print("\nCalibration Results (ECE with 10 bins, MEASURED):")
    print(json.dumps(results, indent=2))

    out_file = Path("docs/calibration_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved raw JSON to {out_file}")


if __name__ == "__main__":
    main()
