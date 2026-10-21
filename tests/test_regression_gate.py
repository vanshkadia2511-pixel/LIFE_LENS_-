"""
tests/test_regression_gate.py
Tests the automated PR-AUC regression gate with fabricated metadata payloads.
"""
from __future__ import annotations

import pytest
from scripts.regression_gate import check_regression


def test_regression_gate_passes_within_margin():
    baseline_meta = {"test_metrics": {"pr_auc": 0.8500}}
    # Drop of 0.01 (0.84 vs 0.85), allowed margin 0.02 -> should pass
    candidate_meta = {"test_metrics": {"pr_auc": 0.8400}}

    passed, message = check_regression(candidate_meta, baseline_meta, margin=0.02)
    assert passed is True
    assert "REGRESSION GATE PASSED" in message


def test_regression_gate_fails_exceeding_margin():
    baseline_meta = {"test_metrics": {"pr_auc": 0.8500}}
    # Drop of 0.03 (0.82 vs 0.85), allowed margin 0.02 -> should fail
    candidate_meta = {"test_metrics": {"pr_auc": 0.8200}}

    passed, message = check_regression(candidate_meta, baseline_meta, margin=0.02)
    assert passed is False
    assert "REGRESSION DETECTED" in message


def test_regression_gate_passes_on_improvement():
    baseline_meta = {"test_metrics": {"pr_auc": 0.8500}}
    # Gain of 0.02 (0.87 vs 0.85) -> should pass
    candidate_meta = {"test_metrics": {"pr_auc": 0.8700}}

    passed, message = check_regression(candidate_meta, baseline_meta, margin=0.02)
    assert passed is True
    assert "REGRESSION GATE PASSED" in message
