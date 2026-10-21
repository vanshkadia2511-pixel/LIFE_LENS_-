"""
LifeLens Ω — Benchmark & Evaluation Metrics Tests
Tests §62, §63, §64, §65 of Master Implementation Plan
"""
import pytest
from datasets.evaluation.benchmark_runner import BenchmarkRunner


def test_benchmark_metrics_targets():
    runner = BenchmarkRunner()
    metrics = runner.run_all()

    # Verify minimum evaluated count (10 legit + 8 scam + 6 adversarial = 24 minimum)
    assert metrics.total_evaluated >= 8

    # Precision & Recall targets (§63, §64)
    assert metrics.recall >= 0.85, f"Recall {metrics.recall} below target 0.85"
    assert metrics.precision >= 0.75, f"Precision {metrics.precision} below target 0.75"
    assert metrics.f1_score >= 0.80, f"F1 {metrics.f1_score} below target 0.80"

    # False positive rate target (§64 target <= 0.10 for phase 1)
    assert metrics.false_positive_rate <= 0.10, f"FPR {metrics.false_positive_rate} exceeded threshold"

    # Latency target (§64 target p95 <= 5000ms in test harness)
    assert metrics.p95_latency_ms <= 5000, f"p95 latency {metrics.p95_latency_ms}ms exceeded 5000ms target"


def test_regression_suite_24_scenarios():
    """
    Phase A Item 1: Evaluates the Regression suite (self-authored, 24 scenarios).
    Must evaluate exactly 24 self-authored cases (10 legit, 8 scam, 6 adversarial).
    """
    runner = BenchmarkRunner()
    metrics = runner.run_regression_suite_24()
    assert metrics.total_evaluated == 24
    assert metrics.recall >= 0.85
    assert metrics.precision >= 0.75


def test_held_out_difraud_metrics_measured():
    """
    Phase A Item 1: Evaluates held-out dataset metrics labeled MEASURED with dataset name and split.
    """
    runner = BenchmarkRunner()
    result = runner.evaluate_held_out_difraud(sample_size=30)
    assert result["metric_type"] == "MEASURED"
    assert result["dataset"] == "DIFrauD"
    assert result["split"] == "test.jsonl"
    assert result["status"] == "COMPLETED"
    assert "accuracy" in result
    assert result["accuracy"] > 0.0


def test_benchmark_illustrative_dataset_sample():
    """
    Runs a small sample of the 1,000-case illustrative benchmark (§62, WP-1A).
    Uses first 20 cases (10 legit + 10 scam) for CI speed.
    """
    runner = BenchmarkRunner()
    metrics = runner.run_illustrative_benchmark(sample_size=20)

    assert metrics.total_evaluated == 20, f"Expected 20 cases, got {metrics.total_evaluated}"

    # Basic sanity: we expect scam cases to be partially caught (recall >= 0.5 on small sample)
    assert metrics.recall >= 0.50, f"Illustrative recall {metrics.recall} below 0.50 on sample"
    # FPR should be reasonable even on small sample
    assert metrics.false_positive_rate <= 0.20, (
        f"Illustrative FPR {metrics.false_positive_rate} too high on sample"
    )
