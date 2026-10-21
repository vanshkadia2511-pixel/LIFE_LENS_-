"""
tests/test_train_and_evaluate.py
Unit tests for leakage-aware harness functions.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from scripts.train_and_evaluate import (
    base_rate_metrics,
    bootstrap_ci,
    grouped_split,
    near_duplicate_groups,
    pick_threshold,
    prepare,
)


def test_near_duplicate_groups():
    # Texts differing by one trailing word share a group
    t1 = "urgent hiring for work from home data entry clerk immediate start apply today"
    t2 = "urgent hiring for work from home data entry clerk immediate start apply tomorrow"
    # Unrelated text
    t3 = "annual financial report for manufacturing company including auditor statement and corporate tax"

    groups = near_duplicate_groups([t1, t2, t3], analyzer="word", ngram_range=(1, 2), threshold=0.85)
    assert groups[0] == groups[1], "Near-duplicate texts should be grouped together"
    assert groups[0] != groups[2], "Unrelated text should belong to a different group"


def test_grouped_split_no_leakage():
    # 50 samples across 10 groups
    y = np.array([0, 1] * 25)
    groups = np.repeat(np.arange(10), 5)

    for seed in (42, 123, 999):
        tr, va, te = grouped_split(y, groups, seed=seed)
        train_groups = set(groups[tr])
        val_groups = set(groups[va])
        test_groups = set(groups[te])

        assert len(train_groups & val_groups) == 0, f"Train and Val groups overlap on seed {seed}"
        assert len(train_groups & test_groups) == 0, f"Train and Test groups overlap on seed {seed}"
        assert len(val_groups & test_groups) == 0, f"Val and Test groups overlap on seed {seed}"


def test_pick_threshold():
    y = np.array([1, 1, 0, 0])
    p = np.array([0.95, 0.85, 0.70, 0.20])
    # Precision at 0.95 = 1.0 (rec 0.5)
    # Precision at 0.85 = 1.0 (rec 1.0)
    # Precision at 0.70 = 2/3 = 0.67 (< 0.90)
    res = pick_threshold(y, p, target_precision=0.90)
    assert res is not None
    assert pytest.approx(res["threshold"], 0.001) == 0.85
    assert res["val_precision"] == 1.0
    assert res["val_recall"] == 1.0


def test_base_rate_metrics():
    # Exactly matches user specification:
    # y=[1,0,0,0], p=[0.9,0.9,0.1,0.1], threshold 0.5, target rate 0.05
    # Expected precision: 0.1364, FPR: 0.3333
    y = np.array([1, 0, 0, 0])
    p = np.array([0.9, 0.9, 0.1, 0.1])
    res = base_rate_metrics(y, p, thr=0.5, target_rate=0.05)
    assert res["precision"] == 0.1364
    assert res["fpr"] == 0.3333


def test_bootstrap_ci_reproducible():
    y = np.array([1, 0, 1, 0, 1, 0, 1, 0, 1, 0])
    p = np.array([0.9, 0.1, 0.8, 0.2, 0.85, 0.15, 0.95, 0.05, 0.7, 0.3])
    ci1 = bootstrap_ci(y, p, thr=0.5, n_boot=200, seed=42)
    ci2 = bootstrap_ci(y, p, thr=0.5, n_boot=200, seed=42)
    assert ci1["f1_95ci"] == ci2["f1_95ci"]
    assert ci1["pr_auc_95ci"] == ci2["pr_auc_95ci"]


def test_prepare_label_normalization_and_filtering():
    raw_df = pd.DataFrame({
        "msg": [
            "valid job offer text number one",
            "valid job offer text number two",
            "valid job offer text number three",
            "valid job offer text number four",
            "hi",               # short (< 5 chars) -> dropped
            "",                 # empty -> dropped
            "duplicate message text here",
            "duplicate message text here",  # duplicate -> dropped
        ],
        "target": [
            1,          # int positive
            "1",        # str positive
            1.0,        # float positive
            0,          # negative
            1,
            1,
            0,
            0,
        ],
    })

    out = prepare(raw_df, text_col="msg", label_col="target", positive_label="1")
    # Rows with short/empty text dropped, duplicate dropped
    assert len(out) == 5
    # 1, "1", 1.0 are all treated as 1
    assert list(out["y"].iloc[:3]) == [1, 1, 1]
    assert out["y"].iloc[3] == 0


def test_group_col_no_cross_split():
    # DataFrame with explicit group column
    df = pd.DataFrame({
        "text": [f"posting content for company {i} with details" for i in range(40)],
        "label": [1, 0] * 20,
        "org_id": [f"org_{i // 4}" for i in range(40)],  # 10 orgs, 4 rows each
    })

    out = prepare(df, text_col="text", label_col="label", positive_label=1, group_col="org_id")
    _, groups = np.unique(out["org_id"].values, return_inverse=True)
    tr, va, te = grouped_split(out["y"].values, groups, seed=42)

    tr_orgs = set(out["org_id"].iloc[tr])
    va_orgs = set(out["org_id"].iloc[va])
    te_orgs = set(out["org_id"].iloc[te])

    assert len(tr_orgs & va_orgs) == 0
    assert len(tr_orgs & te_orgs) == 0
    assert len(va_orgs & te_orgs) == 0
