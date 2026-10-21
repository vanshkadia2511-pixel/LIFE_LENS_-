"""
LifeLens Ω — Dataset Quality Audit Tool
§62, §63, §64, §65, §76 of the Implementation Plan

Usage:
    python scripts/dataset_quality_check.py \
        --train datasets/train.jsonl \
        --test  datasets/test.jsonl \
        --text-col text \
        --label-col is_deceptive

Exit codes:
    0  = No severe flags (safe to proceed with training)
    1  = Severe flag(s) raised (DO NOT train without review)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from collections import Counter
import re

import pandas as pd
import numpy as np

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Thresholds (§64 — targets, not validated production numbers)
# ---------------------------------------------------------------------------
SEVERE_MISSING_RATE   = 0.30   # >30% missing in required column → SEVERE
WARN_MISSING_RATE     = 0.05   # >5% missing → WARNING
SEVERE_IMBALANCE      = 0.90   # majority class >90% → SEVERE
WARN_IMBALANCE        = 0.80   # majority class >80% → WARNING
SEVERE_DUPLICATE_RATE = 0.20   # >20% duplicate rows → SEVERE
WARN_DUPLICATE_RATE   = 0.05   # >5% duplicate rows → WARNING
MIN_ROWS_SEVERE       = 50     # fewer rows than this → SEVERE
MIN_TEXT_LEN          = 5      # text shorter than this flagged as suspicious
WARN_SHORT_TEXT_RATE  = 0.10   # >10% very short texts → WARNING


def load_jsonl(path: Path) -> pd.DataFrame:
    """Load a dataset file (supports .jsonl, .json, and .csv)."""
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"  [PARSE ERROR] Line {lineno}: {e}")
    return pd.DataFrame(rows)


def flag(level: str, message: str) -> dict:
    return {"level": level, "message": message}


def audit_split(name: str, df: pd.DataFrame, text_col: str, label_col: str) -> tuple[list[dict], bool]:
    """
    Audit one split (train or test).
    Returns (flags_list, has_severe).
    """
    flags: list[dict] = []
    print(f"\n{'='*60}")
    print(f"  AUDITING SPLIT: {name.upper()}  ({len(df):,} rows)")
    print(f"{'='*60}")

    # 1. Row count
    if len(df) < MIN_ROWS_SEVERE:
        flags.append(flag("SEVERE", f"Only {len(df)} rows — too few for reliable training."))
    else:
        print(f"  [OK]  Row count: {len(df):,}")

    # 2. Required columns present
    missing_cols = [c for c in [text_col, label_col] if c not in df.columns]
    if missing_cols:
        flags.append(flag("SEVERE", f"Required column(s) missing: {missing_cols}. "
                          f"Available: {list(df.columns)}"))
        # Can't continue most checks without columns
        return flags, True

    print(f"  [OK]  Columns present: '{text_col}', '{label_col}'")

    # 3. Missing values in text column
    n_missing_text = df[text_col].isna().sum()
    missing_text_rate = n_missing_text / len(df)
    if missing_text_rate >= SEVERE_MISSING_RATE:
        flags.append(flag("SEVERE", f"'{text_col}' has {n_missing_text} missing values "
                          f"({missing_text_rate:.1%}) — exceeds {SEVERE_MISSING_RATE:.0%} threshold."))
    elif missing_text_rate >= WARN_MISSING_RATE:
        flags.append(flag("WARNING", f"'{text_col}' has {n_missing_text} missing values "
                          f"({missing_text_rate:.1%})."))
    else:
        print(f"  [OK]  Missing text: {n_missing_text} ({missing_text_rate:.2%})")

    # 4. Missing values in label column
    n_missing_label = df[label_col].isna().sum()
    missing_label_rate = n_missing_label / len(df)
    if missing_label_rate >= SEVERE_MISSING_RATE:
        flags.append(flag("SEVERE", f"'{label_col}' has {n_missing_label} missing values "
                          f"({missing_label_rate:.1%}) — exceeds {SEVERE_MISSING_RATE:.0%} threshold."))
    elif missing_label_rate >= WARN_MISSING_RATE:
        flags.append(flag("WARNING", f"'{label_col}' has {n_missing_label} missing values "
                          f"({missing_label_rate:.1%})."))
    else:
        print(f"  [OK]  Missing labels: {n_missing_label} ({missing_label_rate:.2%})")

    # Work on clean rows only
    clean = df.dropna(subset=[text_col, label_col]).copy()
    print(f"  [INFO] Clean rows after dropping missing: {len(clean):,}")

    # 5. Label distribution / class imbalance
    label_counts = Counter(clean[label_col].astype(str))
    total = sum(label_counts.values())
    majority_frac = max(label_counts.values()) / total if total > 0 else 1.0
    print(f"\n  Label distribution:")
    for lbl, cnt in sorted(label_counts.items()):
        print(f"    {lbl}: {cnt:,}  ({cnt/total:.1%})")

    if majority_frac >= SEVERE_IMBALANCE:
        flags.append(flag("SEVERE", f"Severe class imbalance: majority class = {majority_frac:.1%}. "
                          f"Model will be strongly biased. Consider resampling or class weighting."))
    elif majority_frac >= WARN_IMBALANCE:
        flags.append(flag("WARNING", f"Moderate class imbalance: majority class = {majority_frac:.1%}. "
                          f"Consider class_weight='balanced'."))
    else:
        print(f"  [OK]  Class balance: majority = {majority_frac:.1%}")

    # 6. Duplicate rows (exact text + label)
    n_dupes = clean.duplicated(subset=[text_col, label_col]).sum()
    dupe_rate = n_dupes / len(clean) if len(clean) > 0 else 0
    if dupe_rate >= SEVERE_DUPLICATE_RATE:
        flags.append(flag("SEVERE", f"{n_dupes} duplicate rows ({dupe_rate:.1%}) — "
                          f"exceeds {SEVERE_DUPLICATE_RATE:.0%}. May cause data leakage."))
    elif dupe_rate >= WARN_DUPLICATE_RATE:
        flags.append(flag("WARNING", f"{n_dupes} duplicate rows ({dupe_rate:.1%})."))
    else:
        print(f"  [OK]  Duplicate rows: {n_dupes} ({dupe_rate:.2%})")

    # 7. Very short text
    text_lengths = clean[text_col].astype(str).str.len()
    n_short = (text_lengths < MIN_TEXT_LEN).sum()
    short_rate = n_short / len(clean) if len(clean) > 0 else 0
    print(f"\n  Text length stats:")
    print(f"    min={text_lengths.min()}  median={text_lengths.median():.0f}  "
          f"mean={text_lengths.mean():.0f}  max={text_lengths.max()}")
    if short_rate >= WARN_SHORT_TEXT_RATE:
        flags.append(flag("WARNING", f"{n_short} rows ({short_rate:.1%}) have text shorter than "
                          f"{MIN_TEXT_LEN} chars. These may be meaningless samples."))
    else:
        print(f"  [OK]  Very short texts (<{MIN_TEXT_LEN} chars): {n_short} ({short_rate:.2%})")

    # 8. Label type sanity — should be 0/1 or True/False or similar binary
    unique_labels = set(str(v) for v in clean[label_col].unique())
    if len(unique_labels) > 2:
        flags.append(flag("WARNING", f"More than 2 unique label values found: {unique_labels}. "
                          f"Expected binary classification."))
    elif len(unique_labels) < 2:
        flags.append(flag("SEVERE", f"Only one unique label value: {unique_labels}. "
                          f"Cannot train a classifier."))
    else:
        print(f"  [OK]  Label values: {unique_labels}")

    # 9. Check for potential PII in text (very basic heuristic)
    sample_text = " ".join(clean[text_col].astype(str).head(500).tolist())
    email_matches = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', sample_text)
    phone_matches = re.findall(r'\b\d{10,13}\b', sample_text)
    if email_matches:
        flags.append(flag("INFO", f"Sample contains {len(email_matches)} email-like patterns. "
                          f"Review for PII before sharing."))
    if phone_matches:
        flags.append(flag("INFO", f"Sample contains {len(phone_matches)} phone-number-like patterns. "
                          f"Review for PII before sharing."))

    has_severe = any(f["level"] == "SEVERE" for f in flags)
    return flags, has_severe


def print_flags(flags: list[dict]) -> None:
    if not flags:
        print("\n  ✅  No flags raised.")
        return
    print(f"\n  Flags ({len(flags)}):")
    for f in flags:
        icon = {"SEVERE": "🚨", "WARNING": "⚠️ ", "INFO": "ℹ️ "}.get(f["level"], "?")
        print(f"  {icon} [{f['level']}] {f['message']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="LifeLens Ω — Dataset Quality Audit (§62–§65)"
    )
    parser.add_argument("--train",     required=True, help="Path to train / primary dataset file")
    parser.add_argument("--test",      default=None, help="Path to test dataset file (optional)")
    parser.add_argument("--text-col",  required=True, help="Column name for text")
    parser.add_argument("--label-col", required=True, help="Column name for label")
    args = parser.parse_args()

    train_path = Path(args.train)
    test_path  = Path(args.test) if args.test else None

    print("\n" + "="*60)
    print("  LIFELENS Ω — DATASET QUALITY AUDIT REPORT")
    print("="*60)
    print(f"  Train file : {train_path}")
    print(f"  Test file  : {test_path if test_path else 'None (single split)'}")
    print(f"  Text col   : {args.text_col}")
    print(f"  Label col  : {args.label_col}")

    all_flags: list[dict] = []
    any_severe = False

    splits_to_check = [("TRAIN", train_path)]
    if test_path:
        splits_to_check.append(("TEST", test_path))

    for name, path in splits_to_check:
        if not path.exists():
            print(f"\n🚨 [SEVERE] File not found: {path}")
            all_flags.append(flag("SEVERE", f"File not found: {path}"))
            any_severe = True
            continue
        df = load_jsonl(path)
        split_flags, has_severe = audit_split(name, df, args.text_col, args.label_col)
        print_flags(split_flags)
        all_flags.extend(split_flags)
        if has_severe:
            any_severe = True

    # Final verdict
    print("\n" + "="*60)
    print("  AUDIT VERDICT")
    print("="*60)
    severe_flags  = [f for f in all_flags if f["level"] == "SEVERE"]
    warning_flags = [f for f in all_flags if f["level"] == "WARNING"]
    info_flags    = [f for f in all_flags if f["level"] == "INFO"]

    print(f"  SEVERE   : {len(severe_flags)}")
    print(f"  WARNING  : {len(warning_flags)}")
    print(f"  INFO     : {len(info_flags)}")

    if any_severe:
        print("\n  🚨 RESULT: SEVERE FLAGS RAISED — DO NOT PROCEED WITH TRAINING")
        print("     Review the flags above and resolve them first.")
        sys.exit(1)
    else:
        print("\n  ✅ RESULT: NO SEVERE FLAGS — Safe to proceed with training.")
        if warning_flags:
            print("     ⚠️  Warnings present — review above before training.")
        sys.exit(0)


if __name__ == "__main__":
    main()
