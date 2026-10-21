#!/usr/bin/env python3
"""
train_and_evaluate_tabular.py: Leakage-aware tabular training and evaluation harness (HistGradientBoosting).
Groups by registered domain to prevent domain leakage across splits.
Tunes only on validation, threshold selection for target precision, 95% bootstrap CI, 5% base-rate reweighting.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold

SEED = 42


def extract_domain(url: str) -> str:
    url = str(url).strip()
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    try:
        host = urllib.parse.urlparse(url).netloc.lower().split(":")[0]
    except Exception:
        host = url
    parts = host.split(".")
    if len(parts) >= 3 and parts[-2] in ("co", "com", "org", "net", "edu", "gov"):
        return ".".join(parts[-3:])
    elif len(parts) >= 2:
        return ".".join(parts[-2:])
    return host


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def grouped_split(y: np.ndarray, groups: np.ndarray, seed: int):
    sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)
    folds = [test for _, test in sgkf.split(np.zeros(len(y)), y, groups)]
    test_idx = folds[0]
    val_idx = folds[1]
    train_idx = np.concatenate(folds[2:])
    return train_idx, val_idx, test_idx


def pick_threshold(y: np.ndarray, p: np.ndarray, target_precision: float):
    order = np.argsort(-p, kind="stable")
    y_sorted, p_sorted = y[order], p[order]
    tp = np.cumsum(y_sorted)
    k = np.arange(1, len(y) + 1)
    precision = tp / k
    recall = tp / max(int(y.sum()), 1)
    ok = np.flatnonzero(precision >= target_precision)
    if ok.size == 0:
        return None
    i = ok[-1]
    return {
        "threshold": float(p_sorted[i]),
        "val_precision": round(float(precision[i]), 4),
        "val_recall": round(float(recall[i]), 4),
    }


def metrics_at(y: np.ndarray, p: np.ndarray, thr: float) -> dict:
    pred = (p >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        "n": int(len(y)),
        "positives": int(y.sum()),
        "threshold": round(float(thr), 4),
        "precision": round(float(precision_score(y, pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y, pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y, pred, zero_division=0)), 4),
        "fpr": round(float(fp / max(fp + tn, 1)), 4),
        "pr_auc": round(float(average_precision_score(y, p)), 4),
        "roc_auc": round(float(roc_auc_score(y, p)), 4) if len(np.unique(y)) > 1 else None,
        "confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }


def bootstrap_ci(y: np.ndarray, p: np.ndarray, thr: float, n_boot: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    n = len(y)
    f1s, aps = [], []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        yb = y[idx]
        if yb.sum() == 0:
            continue
        pb = p[idx]
        f1s.append(f1_score(yb, (pb >= thr).astype(int), zero_division=0))
        aps.append(average_precision_score(yb, pb))

    def ci(values):
        if not values:
            return None
        lo, hi = np.percentile(values, [2.5, 97.5])
        return [round(float(lo), 4), round(float(hi), 4)]

    return {
        "f1_95ci": ci(f1s),
        "pr_auc_95ci": ci(aps),
        "resamples_used": len(f1s),
    }


def base_rate_metrics(y: np.ndarray, p: np.ndarray, thr: float, target_rate: float) -> dict:
    pred = p >= thr
    prev = y.mean()
    w = np.where(y == 1, target_rate / prev, (1 - target_rate) / (1 - prev))
    tp = w[(y == 1) & pred].sum()
    fn = w[(y == 1) & ~pred].sum()
    fp = w[(y == 0) & pred].sum()
    tn = w[(y == 0) & ~pred].sum()
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    return {
        "assumed_positive_rate": target_rate,
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "fpr": round(float(fpr), 4),
        "false_alerts_per_1000_legitimate": round(float(fpr) * 1000, 2),
        "caveat": (
            "Importance-weighted estimate under a prior-shift assumption: per-class "
            "score behaviour is assumed unchanged at the new base rate. Confirm with "
            "a real sample from the target population."
        ),
    }


def main():
    ap = argparse.ArgumentParser(description="Leakage-aware tabular HistGradientBoosting trainer.")
    ap.add_argument("--train", required=True, help="Path to CSV with tabular features")
    ap.add_argument("--url-col", default="url")
    ap.add_argument("--label-col", default="label")
    ap.add_argument("--positive-label", default="1")
    ap.add_argument("--target-precision", type=float, default=0.90)
    ap.add_argument("--base-rate", type=float, default=0.05)
    ap.add_argument("--n-boot", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.train)
    df = df.dropna(subset=[args.url_col, args.label_col]).copy()
    df = df.drop_duplicates(subset=[args.url_col]).reset_index(drop=True)

    y = (df[args.label_col].astype(str).str.strip() == str(args.positive_label).strip()).astype(int).values
    domains = df[args.url_col].apply(extract_domain)
    _, groups = np.unique(domains, return_inverse=True)
    n_groups = int(groups.max()) + 1

    feature_cols = [c for c in df.columns if c not in [args.url_col, args.label_col, "serial_number", "registered_domain"]]
    X = df[feature_cols].apply(pd.to_numeric, errors="coerce").fillna(0).values

    print(f"[data] rows={len(df)} positives={int(y.sum())} ({y.mean():.2%}) features={len(feature_cols)}")
    print(f"[groups] {n_groups} groups by domain from {len(df)} rows")

    tr, va, te = grouped_split(y, groups, args.seed)
    Xtr, ytr = X[tr], y[tr]
    Xva, yva = X[va], y[va]
    Xte, yte = X[te], y[te]
    print(f"[split] train={len(tr)} validation={len(va)} test={len(te)} (grouped, stratified)")

    # Tune HistGradientBoosting on validation PR-AUC
    search, best = [], None
    for l2 in [0.0, 1.0, 10.0]:
        clf = HistGradientBoostingClassifier(
            l2_regularization=l2,
            random_state=args.seed,
            max_iter=200,
            class_weight="balanced",
        ).fit(Xtr, ytr)
        pv = clf.predict_proba(Xva)[:, 1]
        score = float(average_precision_score(yva, pv))
        search.append({"l2_regularization": l2, "val_pr_auc": round(score, 4)})
        if best is None or score > best[0]:
            best = (score, l2, clf, pv)

    _, best_l2, clf, pv = best
    print(f"[tune] L2 results {search} -> chosen L2={best_l2}")

    th = pick_threshold(yva, pv, args.target_precision)
    if th is None:
        thr = 0.5
        th = {"threshold": 0.5, "note": "fallback: target precision unreachable on validation"}
    else:
        thr = th["threshold"]
    print(f"[threshold] {thr:.4f} (val precision {th.get('val_precision', 'N/A')}, val recall {th.get('val_recall', 'N/A')})")

    pt = clf.predict_proba(Xte)[:, 1]
    test = metrics_at(yte, pt, thr)
    test["bootstrap"] = bootstrap_ci(yte, pt, thr, args.n_boot, args.seed)
    test["base_rate_reweighted"] = base_rate_metrics(yte, pt, thr, args.base_rate)

    print(f"[test] precision={test['precision']} recall={test['recall']} f1={test['f1']} "
          f"pr_auc={test['pr_auc']} fpr={test['fpr']}  f1_95ci={test['bootstrap']['f1_95ci']}")
    br = test["base_rate_reweighted"]
    print(f"[test @ base rate {br['assumed_positive_rate']:.0%}] precision={br['precision']} "
          f"recall={br['recall']} false alerts/1000 legitimate={br['false_alerts_per_1000_legitimate']}")

    if br["fpr"] > 0.05 or br["precision"] < 0.75:
        print(f"[GATE 1 ALERT] Model failed Gate 1 threshold at base rate {br['assumed_positive_rate']:.0%}: "
              f"FPR={br['fpr']:.4f} (>0.05) or Precision={br['precision']:.4f} (<0.75)")

    # Save
    joblib.dump({"model": clf, "threshold": thr, "feature_names": feature_cols}, out / "model.joblib")

    meta = {
        "label": "MEASURED",
        "dataset_file": args.train,
        "dataset_sha256": sha256_file(args.train),
        "rows_after_cleaning": int(len(df)),
        "positive_rate": round(float(y.mean()), 4),
        "split": {
            "method": f"StratifiedGroupKFold(5, shuffle, seed={args.seed}); fold0=test, fold1=validation, folds2-4=train",
            "group_method": "registered_domain",
            "groups": n_groups,
            "sizes": {"train": int(len(tr)), "validation": int(len(va)), "test": int(len(te))},
        },
        "features": {"n_features": len(feature_cols), "feature_names": feature_cols},
        "tuning": {"l2_grid": search, "chosen_l2": best_l2},
        "threshold": th,
        "test_metrics": test,
        "environment": {
            "python": platform.python_version(),
            "sklearn": sklearn.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (out / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"[saved] {out / 'model.joblib'}, {out / 'metadata.json'}")


if __name__ == "__main__":
    main()
