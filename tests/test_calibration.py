"""
tests/test_calibration.py: Unit tests for Expected Calibration Error (ECE) calculation.
Adheres to Phase 7 requirements: 10 equal-width bins, exact mathematical verification.
"""

import pytest
from apps.api.app.services.media_authenticity import compute_expected_calibration_error


def test_ece_perfect_calibration():
    """Perfect calibration yields an ECE of 0.0."""
    confidences = [0.0] * 20 + [1.0] * 20
    labels = [0] * 20 + [1] * 20
    ece = compute_expected_calibration_error(confidences, labels, n_bins=10)
    assert ece == 0.0


def test_ece_complete_miscalibration():
    """Worst-case miscalibration (conf=1.0 when label=0) yields an ECE of 1.0."""
    confidences = [1.0] * 20
    labels = [0] * 20
    ece = compute_expected_calibration_error(confidences, labels, n_bins=10)
    assert ece == 1.0


def test_ece_hand_calculated_two_bin_case():
    """
    Hand-calculated case with 10 bins:
    - 2 samples in [0.0, 0.1): confidences [0.05, 0.05], labels [0, 0].
      bin_size = 2, bin_conf = 0.05, bin_acc = 0.0, diff = 0.05.
    - 2 samples in [0.9, 1.0]: confidences [0.95, 0.95], labels [1, 0].
      bin_size = 2, bin_conf = 0.95, bin_acc = 0.5, diff = 0.45.
    Total N = 4.
    ECE = (2/4) * 0.05 + (2/4) * 0.45 = 0.025 + 0.225 = 0.25.
    """
    confidences = [0.05, 0.05, 0.95, 0.95]
    labels = [0, 0, 1, 0]
    ece = compute_expected_calibration_error(confidences, labels, n_bins=10)
    assert ece == 0.25


def test_ece_empty_or_mismatched_inputs():
    """Empty or mismatched arrays return 0.0 gracefully."""
    assert compute_expected_calibration_error([], [], n_bins=10) == 0.0
    assert compute_expected_calibration_error([0.5], [1, 0], n_bins=10) == 0.0
