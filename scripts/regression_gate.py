#!/usr/bin/env python3
"""
scripts/regression_gate.py
Automated regression gate comparing candidate model run metadata against saved baseline.
Compares saved PR-AUC metrics only (never touches test set).
Fails (exit 1) if candidate test PR-AUC drops by more than --margin (default: TARGET 0.02).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_meta(path_str: str) -> dict:
    p = Path(path_str)
    if p.is_dir():
        p = p / "metadata.json"
    if not p.exists():
        sys.exit(f"Metadata file not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def check_regression(candidate_meta: dict, baseline_meta: dict, margin: float = 0.02) -> tuple[bool, str]:
    c_pr_auc = candidate_meta.get("test_metrics", {}).get("pr_auc")
    b_pr_auc = baseline_meta.get("test_metrics", {}).get("pr_auc")

    if c_pr_auc is None or b_pr_auc is None:
        return False, f"Missing test PR-AUC: candidate={c_pr_auc}, baseline={b_pr_auc}"

    delta = c_pr_auc - b_pr_auc
    # Regression threshold: drops more than margin
    if delta < -margin:
        msg = (
            f"REGRESSION DETECTED: Candidate PR-AUC {c_pr_auc:.4f} dropped by {abs(delta):.4f} "
            f"below Baseline {b_pr_auc:.4f} (allowed margin: {margin:.4f})."
        )
        return False, msg
    else:
        msg = (
            f"REGRESSION GATE PASSED: Candidate PR-AUC {c_pr_auc:.4f} vs Baseline {b_pr_auc:.4f} "
            f"(delta: {delta:+.4f}, allowed margin: -{margin:.4f})."
        )
        return True, msg


def main():
    ap = argparse.ArgumentParser(description="Regression Gate for model re-training validation.")
    ap.add_argument("--candidate", required=True, help="Path to candidate metadata.json or directory")
    ap.add_argument("--baseline", required=True, help="Path to baseline metadata.json or directory")
    ap.add_argument("--margin", type=float, default=0.02, help="Maximum allowed drop in PR-AUC (default: 0.02)")
    args = ap.parse_args()

    cand = load_meta(args.candidate)
    base = load_meta(args.baseline)

    passed, message = check_regression(cand, base, margin=args.margin)
    print(message)
    if not passed:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
