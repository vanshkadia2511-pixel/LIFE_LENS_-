"""
LifeLens Ω — Baseline Scam-Detection Model Trainer
§62, §63, §64, §65 of the Implementation Plan

Trains a TF-IDF + Logistic Regression baseline and a TF-IDF + SGDClassifier
(linear SVM) using scikit-learn best practices:
  - Split BEFORE fitting any preprocessing (§ml-best-practices: Strict Featurization Ordering)
  - class_weight='balanced' to handle imbalance
  - Reports: classification report, confusion matrix, F1 (macro & weighted)
  - Saves the best model to models/ with joblib

Usage:
    python scripts/train_baseline_model.py \
        --train datasets/train.jsonl \
        --test  datasets/test.jsonl \
        --text-col text \
        --label-col is_deceptive \
        [--output-dir models/]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_data_file(path: Path) -> pd.DataFrame:
    """Load dataset file (supports .jsonl, .json, and .csv)."""
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return pd.DataFrame(rows)


def load_jsonl(path: Path) -> pd.DataFrame:
    return load_data_file(path)


def prepare_split(df: pd.DataFrame, text_col: str, label_col: str) -> tuple[list[str], np.ndarray]:
    """Clean a split and return (texts, labels). Must NOT fit any encoders here."""
    clean = df.dropna(subset=[text_col, label_col]).copy()
    texts  = clean[text_col].astype(str).tolist()
    labels = clean[label_col].values
    return texts, labels


def print_section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_confusion_matrix(cm: np.ndarray, class_names: list) -> None:
    """Pretty-print confusion matrix."""
    col_w = max(len(str(n)) for n in class_names) + 2
    header = " " * (col_w + 2) + "  ".join(f"{n:>{col_w}}" for n in class_names)
    print(header)
    print(" " * (col_w + 2) + "-" * (col_w * len(class_names) + 2 * (len(class_names) - 1)))
    for i, row_name in enumerate(class_names):
        row = f"{row_name:>{col_w}} |" + "  ".join(f"{cm[i][j]:>{col_w}}" for j in range(len(class_names)))
        print(row)


def build_pipelines() -> dict[str, Pipeline]:
    """
    Build candidate pipelines.
    TF-IDF fitted on TRAIN text only — never leaked to test.
    """
    tfidf_shared = dict(
        ngram_range=(1, 2),
        max_features=50_000,
        sublinear_tf=True,
        min_df=2,
    )

    return {
        "LogisticRegression (TF-IDF)": Pipeline([
            ("tfidf", TfidfVectorizer(**tfidf_shared)),
            ("clf",   LogisticRegression(
                class_weight="balanced",
                max_iter=1000,
                solver="lbfgs",
                C=1.0,
                random_state=42,
            )),
        ]),
        "LinearSVM / SGD (TF-IDF)": Pipeline([
            ("tfidf", TfidfVectorizer(**tfidf_shared)),
            ("clf",   SGDClassifier(
                loss="hinge",
                class_weight="balanced",
                max_iter=1000,
                random_state=42,
                n_jobs=-1,
            )),
        ]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="LifeLens Ω — Baseline Scam-Detection Model Trainer (§62–§65)"
    )
    parser.add_argument("--train",      required=True, help="Path to train / primary dataset file")
    parser.add_argument("--test",       default=None, help="Path to test dataset file (optional)")
    parser.add_argument("--text-col",   required=True, help="Column name for text")
    parser.add_argument("--label-col",  required=True, help="Column name for label")
    parser.add_argument("--output-dir", default="models", help="Directory to save models")
    args = parser.parse_args()

    train_path = Path(args.train)
    test_path  = Path(args.test) if args.test else None
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print_section("LIFELENS Ω — BASELINE MODEL TRAINING")
    print(f"  Train : {train_path}")
    print(f"  Test  : {test_path if test_path else 'Auto 80/20 Stratified Split'}")
    print(f"  Text  : {args.text_col}")
    print(f"  Label : {args.label_col}")
    print(f"  Out   : {output_dir}")

    # -----------------------------------------------------------------------
    # STEP 1: Load raw data
    # -----------------------------------------------------------------------
    print_section("STEP 1: Load Data")
    train_df = load_data_file(train_path)
    if test_path:
        test_df = load_data_file(test_path)
    else:
        clean_full = train_df.dropna(subset=[args.text_col, args.label_col])
        train_df, test_df = train_test_split(
            clean_full, test_size=0.2, stratify=clean_full[args.label_col], random_state=42
        )
    print(f"  Train rows (raw): {len(train_df):,}")
    print(f"  Test  rows (raw): {len(test_df):,}")

    # -----------------------------------------------------------------------
    # STEP 2: Prepare splits BEFORE fitting any transforms (§ml-best-practices)
    # -----------------------------------------------------------------------
    print_section("STEP 2: Prepare Splits (No Preprocessing Fitted Yet)")
    X_train_raw, y_train_raw = prepare_split(train_df, args.text_col, args.label_col)
    X_test_raw,  y_test_raw  = prepare_split(test_df,  args.text_col, args.label_col)
    print(f"  Train clean: {len(X_train_raw):,}  |  Test clean: {len(X_test_raw):,}")

    # Encode labels — fit encoder on TRAIN labels only
    le = LabelEncoder()
    y_train = le.fit_transform(y_train_raw)
    y_test  = le.transform(y_test_raw)
    class_names = [str(c) for c in le.classes_]
    print(f"  Classes: {class_names}")

    label_counts_train = {c: int((y_train == i).sum()) for i, c in enumerate(class_names)}
    label_counts_test  = {c: int((y_test  == i).sum()) for i, c in enumerate(class_names)}
    print(f"  Train distribution: {label_counts_train}")
    print(f"  Test  distribution: {label_counts_test}")

    # -----------------------------------------------------------------------
    # STEP 3: Train and evaluate each pipeline
    # -----------------------------------------------------------------------
    results: list[dict] = []
    pipelines = build_pipelines()

    for model_name, pipe in pipelines.items():
        print_section(f"STEP 3: Training — {model_name}")
        t0 = time.perf_counter()

        # Fit ONLY on training data
        pipe.fit(X_train_raw, y_train)
        train_time = time.perf_counter() - t0
        print(f"  Training time: {train_time:.2f}s")

        # Predict on test set
        t1 = time.perf_counter()
        y_pred = pipe.predict(X_test_raw)
        predict_time = time.perf_counter() - t1
        avg_latency_ms = (predict_time / len(X_test_raw)) * 1000
        print(f"  Inference: {predict_time:.3f}s total  |  {avg_latency_ms:.3f}ms/sample")

        # Metrics
        f1_macro    = f1_score(y_test, y_pred, average="macro",    zero_division=0)
        f1_weighted = f1_score(y_test, y_pred, average="weighted", zero_division=0)
        f1_binary   = f1_score(y_test, y_pred, average="binary",   pos_label=1, zero_division=0) if len(class_names) == 2 else None

        # AUC (if predict_proba available)
        auc = None
        if hasattr(pipe, "predict_proba"):
            try:
                if len(class_names) == 2:
                    y_prob = pipe.predict_proba(X_test_raw)[:, 1]
                    auc = roc_auc_score(y_test, y_prob)
                else:
                    y_prob = pipe.predict_proba(X_test_raw)
                    auc = roc_auc_score(y_test, y_prob, multi_class="ovr")
            except Exception:
                pass

        cm = confusion_matrix(y_test, y_pred)
        cr = classification_report(y_test, y_pred, target_names=class_names, zero_division=0)

        print(f"\n  Classification Report:")
        print(cr)
        print(f"  Confusion Matrix (rows=actual, cols=predicted):")
        print_confusion_matrix(cm, class_names)
        print(f"\n  F1 (macro)    : {f1_macro:.4f}")
        print(f"  F1 (weighted) : {f1_weighted:.4f}")
        if f1_binary is not None:
            print(f"  F1 (binary=1) : {f1_binary:.4f}")
        if auc is not None:
            print(f"  ROC-AUC       : {auc:.4f}")

        results.append({
            "model": model_name,
            "f1_macro": f1_macro,
            "f1_weighted": f1_weighted,
            "f1_binary": f1_binary,
            "auc": auc,
            "train_time_s": train_time,
            "avg_latency_ms": avg_latency_ms,
            "pipe": pipe,
        })

        # Save each model
        slug = model_name.replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "").lower()
        model_path = output_dir / f"{slug}.joblib"
        joblib.dump({"pipeline": pipe, "label_encoder": le, "classes": class_names}, model_path)
        print(f"\n  Model saved: {model_path}")

    # -----------------------------------------------------------------------
    # STEP 4: Compare and pick best model
    # -----------------------------------------------------------------------
    print_section("STEP 4: Model Comparison & Best Model")
    results_sorted = sorted(results, key=lambda r: r["f1_macro"], reverse=True)

    print(f"  {'Model':<40} {'F1-macro':>10} {'F1-weighted':>12} {'Latency(ms)':>12}")
    print("  " + "-"*76)
    for r in results_sorted:
        print(
            f"  {r['model']:<40} {r['f1_macro']:>10.4f} {r['f1_weighted']:>12.4f} "
            f"{r['avg_latency_ms']:>12.4f}"
        )

    best = results_sorted[0]
    best_slug = best["model"].replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "").lower()
    best_path = output_dir / f"{best_slug}.joblib"

    # Also save as "best_model.joblib" for easy loading
    best_model_path = output_dir / "best_model.joblib"
    joblib.dump(
        {"pipeline": best["pipe"], "label_encoder": le, "classes": class_names,
         "model_name": best["model"], "f1_macro": best["f1_macro"]},
        best_model_path
    )

    print(f"\n  🏆 Best model : {best['model']}")
    print(f"     F1 (macro)  : {best['f1_macro']:.4f}")
    if best["f1_binary"] is not None:
        print(f"     F1 (binary) : {best['f1_binary']:.4f}")
    if best["auc"] is not None:
        print(f"     ROC-AUC     : {best['auc']:.4f}")
    print(f"     Saved to    : {best_model_path}")

    # -----------------------------------------------------------------------
    # STEP 5: Calibration warning per §P4 (No fake metrics)
    # -----------------------------------------------------------------------
    print_section("STEP 5: Metric Integrity Note (§P4)")
    print("""
  All metrics above are measured on the provided test split.
  They are BENCHMARK results on this specific dataset — not
  claims of production performance. Per the Implementation Plan:

    TARGET   = engineering aspiration
    BENCHMARK = measured on a fixed evaluation set (this run)
    MEASURED  = validated in production with real traffic
    ILLUSTRATIVE = example for documentation

  These results are classified as: BENCHMARK
  Do not present them as production-grade accuracy claims.
    """)

    print_section("TRAINING COMPLETE")
    print(f"  Models directory : {output_dir.resolve()}")
    print(f"  Best model       : {best_model_path.resolve()}")


if __name__ == "__main__":
    main()
