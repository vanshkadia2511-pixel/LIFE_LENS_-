#!/usr/bin/env python3
"""
train_and_evaluate.py: leakage-aware training and evaluation harness (binary).

Pipeline
  1. Load CSV/JSONL, keep text and label, clean, drop exact duplicates.
  2. Group near-duplicates (TF-IDF cosine >= --dup-threshold, union-find) so
     near-copies can never be split across train, validation and test.
     Alternatively, use --group-col if explicit grouping exists (e.g. domain).
  3. Grouped, stratified split from StratifiedGroupKFold(5):
        fold 0 -> TEST        (touched once, at the very end)
        fold 1 -> VALIDATION  (used to choose C and the decision threshold)
        folds 2-4 -> TRAIN
  4. Choose the regularisation strength C by validation PR-AUC.
  5. Choose the decision threshold on validation: the most recall available
     while validation precision stays >= --target-precision.
  6. Optional calibration with CalibratedClassifierCV(cv=5) on train split.
  7. Evaluate once on TEST, with bootstrap 95% confidence intervals.
  8. Re-weight TEST to a realistic positive rate (--base-rate) and report
     precision, recall, FPR and false alerts per 1,000 legitimate items.
  9. Optional cross-dataset tests (--external) with exact-overlap counts.
  10. Save model.joblib, metadata.json, and error-analysis CSVs.

Every number is MEASURED on the named dataset and split (rule P4).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline

SEED = 42

# Domain extractor configured to NEVER fetch over network
try:
    import tldextract
    _tld_extractor = tldextract.TLDExtract(suffix_list_urls=())
    DOMAIN_EXTRACTOR_NAME = f"tldextract-{tldextract.__version__} (suffix_list_urls=())"
except Exception:
    _tld_extractor = None
    DOMAIN_EXTRACTOR_NAME = "urllib.parse-psl-fallback"


def extract_domain(url: str) -> str:
    """Extract registered domain strictly offline."""
    url = str(url).strip()
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    if _tld_extractor is not None:
        try:
            ext = _tld_extractor(url)
            if ext.registered_domain:
                return ext.registered_domain.lower()
        except Exception:
            pass
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


# ----------------------------------------------------------------- data

def load_any(path: str) -> pd.DataFrame:
    p = Path(path)
    if p.suffix == ".jsonl":
        lines = p.read_text(encoding="utf-8").splitlines()
        return pd.DataFrame([json.loads(line) for line in lines if line.strip()])
    if p.suffix == ".csv":
        return pd.read_csv(p)
    raise ValueError(f"Unsupported file type: {p.suffix} (use .csv or .jsonl)")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def clean_text(value) -> str:
    text = str(value).lower()
    text = re.sub(r"<[^>]+>", " ", text)  # strip HTML tags
    return re.sub(r"\s+", " ", text).strip()


def _norm_label(v) -> str:
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip()


def prepare(df: pd.DataFrame, text_col: str, label_col: str, positive_label: str, group_col: str | None = None) -> pd.DataFrame:
    missing = [c for c in [text_col, label_col] if c not in df.columns]
    if missing:
        sys.exit(f"Columns not found: {missing}. Available: {list(df.columns)}")
    cols = [text_col, label_col]
    if group_col and group_col in df.columns:
        cols.append(group_col)
    out = df[cols].dropna(subset=[text_col, label_col]).copy()
    out["text"] = out[text_col].map(clean_text)
    out = out[out["text"].str.len() >= 5]
    out = out.drop_duplicates(subset=["text"]).reset_index(drop=True)
    out["y"] = (out[label_col].map(_norm_label) == str(positive_label).strip()).astype(int)
    ret_cols = ["text", "y"]
    if group_col:
        if group_col in out.columns:
            ret_cols.append(group_col)
        elif group_col in ("domain", "registered_domain"):
            out[group_col] = out[text_col].apply(extract_domain)
            ret_cols.append(group_col)
    return out[ret_cols]


# ------------------------------------------------- near-duplicate groups

def near_duplicate_groups(texts, analyzer, ngram_range, threshold, chunk=256) -> np.ndarray:
    """Union-find over pairs whose TF-IDF cosine similarity >= threshold."""
    vec = TfidfVectorizer(analyzer=analyzer, ngram_range=ngram_range, sublinear_tf=True)
    X = vec.fit_transform(texts)  # rows are L2-normalised, so dot product = cosine
    n = X.shape[0]
    parent = np.arange(n)

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    XT = X.T.tocsr()
    for start in range(0, n, chunk):
        stop = min(start + chunk, n)
        sims = (X[start:stop] @ XT).toarray()
        for r in range(stop - start):
            i = start + r
            for j in np.flatnonzero(sims[r] >= threshold):
                if j > i:
                    a, b = find(i), find(int(j))
                    if a != b:
                        parent[b] = a

    roots = np.fromiter((find(i) for i in range(n)), dtype=np.int64, count=n)
    _, groups = np.unique(roots, return_inverse=True)
    return groups


# ------------------------------------------------------------- splitting

def grouped_split(y: np.ndarray, groups: np.ndarray, seed: int):
    sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)
    folds = [test for _, test in sgkf.split(np.zeros(len(y)), y, groups)]
    test_idx = folds[0]
    val_idx = folds[1]
    train_idx = np.concatenate(folds[2:])
    return train_idx, val_idx, test_idx


# ----------------------------------------------------------------- model

def build_pipeline(args, C: float) -> Pipeline:
    clf = LogisticRegression(
        C=C, class_weight="balanced", max_iter=3000, random_state=args.seed,
    )
    if getattr(args, "calibrate", False):
        clf = CalibratedClassifierCV(estimator=clf, cv=5)
    return Pipeline([
        ("vec", TfidfVectorizer(
            analyzer=args.analyzer,
            ngram_range=(args.ngram_min, args.ngram_max),
            min_df=2,
            max_features=args.max_features,
            sublinear_tf=True,
        )),
        ("clf", clf),
    ])


def pick_threshold(y: np.ndarray, p: np.ndarray, target_precision: float):
    """Lowest threshold that keeps precision >= target, i.e. the most recall."""
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


# ------------------------------------------------------------ evaluation

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
    """Importance-weight the test set so positives make up target_rate of it."""
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


def export_errors(test_df: pd.DataFrame, p: np.ndarray, thr: float, out_dir: Path, k: int = 25):
    d = test_df.assign(score=p, pred=(p >= thr).astype(int))
    fps = d[(d.pred == 1) & (d.y == 0)].nlargest(k, "score")
    fns = d[(d.pred == 0) & (d.y == 1)].nsmallest(k, "score")
    for name, frame in (("false_positives.csv", fps), ("false_negatives.csv", fns)):
        frame.assign(text=frame.text.str.slice(0, 300)).to_csv(out_dir / name, index=False)
    return int(len(fps)), int(len(fns))


def top_features(pipe: Pipeline, n: int = 20) -> dict:
    clf = pipe.named_steps["clf"]
    if hasattr(clf, "coef_"):
        coef = clf.coef_[0]
    elif hasattr(clf, "calibrated_classifiers_"):
        coefs = [c.estimator.coef_[0] for c in clf.calibrated_classifiers_ if hasattr(c.estimator, "coef_")]
        coef = np.mean(coefs, axis=0) if coefs else None
    else:
        coef = None

    if coef is None:
        return {"toward_positive_class": [], "toward_negative_class": []}

    names = pipe.named_steps["vec"].get_feature_names_out()
    order = np.argsort(coef)
    return {
        "toward_positive_class": [str(names[i]) for i in order[::-1][:n]],
        "toward_negative_class": [str(names[i]) for i in order[:n]],
    }


# ------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser(description="Leakage-aware train + evaluate harness (binary).")
    ap.add_argument("--train", required=True, help="Dataset file (.csv or .jsonl)")
    ap.add_argument("--text-col", required=True)
    ap.add_argument("--label-col", required=True)
    ap.add_argument("--positive-label", required=True,
                    help="Value in label-col that means scam/phishing")
    ap.add_argument("--analyzer", default="word", choices=["word", "char_wb"])
    ap.add_argument("--ngram-min", type=int, default=1)
    ap.add_argument("--ngram-max", type=int, default=2)
    ap.add_argument("--max-features", type=int, default=50000)
    ap.add_argument("--dup-threshold", type=float, default=0.9)
    ap.add_argument("--group-col", default=None,
                    help="Optional column name to group directly by (e.g. domain/registered_domain)")
    ap.add_argument("--calibrate", action="store_true",
                    help="Wrap classifier in CalibratedClassifierCV(cv=5) on train split")
    ap.add_argument("--c-grid", default="0.1,1,10")
    ap.add_argument("--target-precision", type=float, default=0.90)
    ap.add_argument("--base-rate", type=float, default=0.05)
    ap.add_argument("--external", nargs="*", default=[],
                    help="Other datasets with the same column names (cross-dataset test)")
    ap.add_argument("--n-boot", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    # 1. Load and prepare
    df = prepare(load_any(args.train), args.text_col, args.label_col, args.positive_label, group_col=args.group_col)
    if df.y.nunique() < 2:
        sys.exit("Need both classes after cleaning. Check --positive-label.")
    print(f"[data] rows={len(df)} positives={int(df.y.sum())} ({df.y.mean():.2%})")

    # 2. Grouping
    if args.group_col and args.group_col in df.columns:
        _, groups = np.unique(df[args.group_col].astype(str), return_inverse=True)
        n_groups = int(groups.max()) + 1
        print(f"[groups] {n_groups} groups from {len(df)} rows (using group-col '{args.group_col}')")
    else:
        groups = near_duplicate_groups(
            df.text.tolist(), args.analyzer, (args.ngram_min, args.ngram_max), args.dup_threshold,
        )
        n_groups = int(groups.max()) + 1
        print(f"[groups] {n_groups} groups from {len(df)} rows (dup threshold {args.dup_threshold})")

    # 3. Grouped, stratified split
    tr, va, te = grouped_split(df.y.values, groups, args.seed)
    Xtr, ytr = df.text.values[tr], df.y.values[tr]
    Xva, yva = df.text.values[va], df.y.values[va]
    Xte, yte = df.text.values[te], df.y.values[te]
    if ytr.sum() == 0 or yva.sum() == 0:
        sys.exit("Train or validation split has no positives. Dataset too small or too skewed.")
    print(f"[split] train={len(tr)} validation={len(va)} test={len(te)} (grouped, stratified)")

    # 4. Choose C on validation only
    search, best = [], None
    for C in [float(c) for c in args.c_grid.split(",")]:
        pipe = build_pipeline(args, C).fit(Xtr, ytr)
        pv = pipe.predict_proba(Xva)[:, 1]
        score = float(average_precision_score(yva, pv))
        search.append({"C": C, "val_pr_auc": round(score, 4)})
        if best is None or score > best[0]:
            best = (score, C, pipe, pv)
    _, C, pipe, pv = best
    print(f"[tune] C results {search} -> chosen C={C}")

    # 5. Threshold on validation
    th = pick_threshold(yva, pv, args.target_precision)
    if th is None:
        print(f"[threshold] WARNING: precision >= {args.target_precision} not reachable on "
              f"validation. Falling back to 0.5. Report this.")
        thr = 0.5
        th = {"threshold": 0.5, "note": "fallback: target precision unreachable on validation"}
    else:
        thr = th["threshold"]
        print(f"[threshold] {thr:.4f} (val precision {th['val_precision']}, "
              f"val recall {th['val_recall']})")

    # 6. Single evaluation on TEST
    pt = pipe.predict_proba(Xte)[:, 1]
    test = metrics_at(yte, pt, thr)
    test["bootstrap"] = bootstrap_ci(yte, pt, thr, args.n_boot, args.seed)
    test["base_rate_reweighted"] = base_rate_metrics(yte, pt, thr, args.base_rate)
    if test["positives"] < 30:
        print("[warning] fewer than 30 positives in test: confidence intervals will be wide.")
    print(f"[test] precision={test['precision']} recall={test['recall']} f1={test['f1']} "
          f"pr_auc={test['pr_auc']} fpr={test['fpr']}  f1_95ci={test['bootstrap']['f1_95ci']}")
    br = test["base_rate_reweighted"]
    print(f"[test @ base rate {br['assumed_positive_rate']:.0%}] precision={br['precision']} "
          f"recall={br['recall']} false alerts/1000 legitimate={br['false_alerts_per_1000_legitimate']}")

    # Check Gate 1 rules: FPR > 0.05 or precision < 0.75 at 5% base rate
    if br["fpr"] > 0.05 or br["precision"] < 0.75:
        print(f"[GATE 1 ALERT] Model failed Gate 1 threshold at base rate {br['assumed_positive_rate']:.0%}: "
              f"FPR={br['fpr']:.4f} (>0.05) or Precision={br['precision']:.4f} (<0.75)")

    # 7. External datasets
    external = {}
    train_set = set(Xtr)
    for ep in args.external:
        ed = prepare(load_any(ep), args.text_col, args.label_col, args.positive_label)
        pe = pipe.predict_proba(ed.text.values)[:, 1]
        res = metrics_at(ed.y.values, pe, thr)
        res["exact_text_overlap_with_train_split"] = int(ed.text.isin(train_set).sum())
        res["sha256"] = sha256_file(ep)
        external[Path(ep).name] = res
        print(f"[external] {Path(ep).name}: precision={res['precision']} recall={res['recall']} "
              f"f1={res['f1']} pr_auc={res['pr_auc']} overlap={res['exact_text_overlap_with_train_split']}")

    # 8. Error analysis and feature inspection
    test_df = df.iloc[te].reset_index(drop=True)
    n_fp, n_fn = export_errors(test_df, pt, thr, out)

    # 9. Save model and metadata
    joblib.dump({
        "pipeline": pipe,
        "threshold": thr,
        "C": C,
        "calibrated": args.calibrate,
        "analyzer": args.analyzer,
        "ngram_range": [args.ngram_min, args.ngram_max],
    }, out / "model.joblib")

    meta = {
        "label": "MEASURED",
        "dataset_file": args.train,
        "dataset_sha256": sha256_file(args.train),
        "rows_after_cleaning": int(len(df)),
        "positive_rate": round(float(df.y.mean()), 4),
        "split": {
            "method": (f"StratifiedGroupKFold(5, shuffle, seed={args.seed}); "
                       "fold0=test, fold1=validation, folds2-4=train"),
            "near_duplicate_threshold": args.dup_threshold if not args.group_col else None,
            "group_col": args.group_col,
            "domain_extractor": DOMAIN_EXTRACTOR_NAME if args.group_col else None,
            "groups": n_groups,
            "sizes": {"train": int(len(tr)), "validation": int(len(va)), "test": int(len(te))},
        },
        "features": {
            "analyzer": args.analyzer,
            "ngram_range": [args.ngram_min, args.ngram_max],
            "max_features": args.max_features,
        },
        "calibration": "CalibratedClassifierCV(cv=5)" if args.calibrate else "none",
        "tuning": {"c_grid": search, "chosen_C": C},
        "threshold": th,
        "test_metrics": test,
        "error_counts_test": {"false_positives_exported": n_fp, "false_negatives_exported": n_fn},
        "external": external,
        "top_features": top_features(pipe),
        "environment": {
            "python": platform.python_version(),
            "sklearn": sklearn.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "tldextract": tldextract.__version__ if _tld_extractor is not None else "N/A",
        },
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (out / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"[saved] {out / 'model.joblib'}, {out / 'metadata.json'}, error CSVs in {out}")


if __name__ == "__main__":
    main()
