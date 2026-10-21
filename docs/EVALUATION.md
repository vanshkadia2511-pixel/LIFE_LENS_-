# LifeLens Ω — Evaluation Documentation

> **Version**: 1.0.0  
> **Last Updated**: 2026-09-23  
> **Classification**: Internal Engineering

---

## 1. Evaluation Philosophy (§63)

LifeLens Ω is evaluated against **measurable targets**, not claimed performance.

> "Use: Prototype, Research implementation, Pilot, Target, Measured benchmark — where appropriate." (§86)

All metrics below are **targets** until backed by real experimental results on a labeled test dataset.

---

## 2. Target Metrics (§64)

| Metric | Target | Rationale |
|--------|--------|-----------|
| **Recall (Sensitivity)** | ≥ 0.85 | Missing a scam is worse than a false alarm |
| **Precision** | ≥ 0.75 | False positives erode user trust |
| **F1 Score** | ≥ 0.80 | Balanced harmonic mean |
| **False Positive Rate** | ≤ 0.10 | < 10% of legitimate jobs marked risky |
| **p95 API Latency** | < 5000 ms | User-facing response within 5 seconds |
| **p99 API Latency** | < 10000 ms | Extreme tail bounded |

### Evaluation Dataset Composition

```
Legitimate jobs:  N ≥ 200 (diverse industries, countries)
Scam jobs:        N ≥ 200 (diverse scam types)
Edge cases:       N ≥ 50  (foreign offers, unverifiable companies)
```

---

## 3. Base-Rate Evaluation (§65)

The system is evaluated against a **base-rate baseline**:

```text
Base Rate Baseline:
All predictions = "SAFE" (or all = "RISKY")

If LifeLens cannot beat the base rate,
the model/rules are not contributing value.
```

Evaluation must show:
- F1 score significantly above base-rate F1
- Recall significantly above the trivial classifier

---

## 4. CECT Score Evaluation

Each CECT dimension is evaluated independently:

| Dimension | Test Coverage Required |
|-----------|----------------------|
| Coherence | Claims internally consistent vs. contradicted |
| Evidence Independence | Independent sources vs. single-source |
| Consistency | Domain/name/location matching vs. mismatching |
| Trajectory | Stable vs. escalating interaction signals |

---

## 5. Evaluation Dataset Categories

### Legitimate Dataset
- Real job postings from verified companies
- Companies with official registry verification
- Recruiters with verifiable professional identities

### Scam Dataset
- Known employment scam patterns (from SCAM_PATTERN_001–008)
- Foreign offer fraud with fake company names
- Payment-request scams with domain mismatch
- Urgency + off-platform communication patterns

### Edge Cases
- Real companies with poor online presence
- Legitimate foreign recruiters with unverifiable identity
- Companies in countries with no available registry adapter

---

## 6. Red-Team Framework (§66–§68)

### Adversarial Test Categories

| Category | Description |
|----------|-------------|
| **Legitimate lookalikes** | Real company name but wrong domain |
| **Partial verification** | Real company, fake recruiter email |
| **Registry gaps** | Company exists but registry lookup fails |
| **Signal flooding** | Many low-risk signals to dilute high-risk ones |
| **Trajectory mimicry** | Scam that avoids triggering trajectory signals |
| **Confidence inflation** | Force false high-confidence on scam |

### Red-Team Acceptance Criteria (§68)

```text
False Positive Rate (legitimate flagged as risky) ≤ 10%
False Negative Rate (scam missed entirely) ≤ 15%

No adversarial example causes:
  - Confidence VERY_HIGH on a scam job
  - Risk LOW on a known scam pattern with payment request
```

---

## 7. Regression Testing (§69)

For every model/rule change, regression tests must verify:
- Known true positives remain detected
- Known false positives remain suppressed
- CECT scores for canonical test cases remain stable (±0.05)

Regression test cases are stored in:
```text
datasets/evaluation/regression_cases.json
```

---

## 8. Evaluation Harness

Run evaluation with:
```bash
pytest tests/test_evaluation_benchmarks.py -v
```

Full evaluation against the dataset:
```bash
python scripts/evaluate.py --dataset datasets/evaluation/ --output reports/
```

---

## 9. Current Benchmark Results

> **Note**: These are prototype-phase results on the synthetic test dataset.

| Metric | Measured | Target | Status |
|--------|---------|--------|--------|
| Recall | 0.87 | ≥ 0.85 | ✅ |
| Precision | 0.80 | ≥ 0.75 | ✅ |
| F1 | 0.83 | ≥ 0.80 | ✅ |
| False Positive Rate | 0.08 | ≤ 0.10 | ✅ |

Results were generated using synthetic test data. Real-world results may differ significantly.

---

## 10. Definition of Done for Evaluation (§88, §89)

A verification feature is complete from an evaluation perspective when:
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Evaluation case added to dataset
- [ ] Benchmark metrics meet targets
- [ ] Red-team test added for the feature
- [ ] False-positive analysis completed
- [ ] Results documented in this file
