# LifeLens Ω — Comprehensive Claims & Reproducibility Audit

**Generated:** 2026-10-13  
**Audit Standard:** Non-Negotiable Rule 1 & Rule 2 (All numbers classified as MEASURED, BENCHMARK, TARGET, or ILLUSTRATIVE; all claims ungrounded until reproduced).

---

## 1. System & Environment Baseline
- **Python Version:** `Python 3.12.13`
- **Key Installed Dependencies:**
  - `scikit-learn`: `1.9.1`
  - `pandas`: `3.0.6`
  - `numpy`: `1.26.2`
  - `joblib`: `1.6.0`
  - `pytest`: `7.4.3`
- **Git Branch:** `feature/honest-metrics`
- **Git Status:** Clean branch creation, zero commits yet on feature branch.
- **Pytest Baseline:** **273 passed, 0 failed, 0 skipped in 42.01s** (recorded in [`docs/audit/pytest_baseline.txt`](file:///d:/Life_Lens_Ai/docs/audit/pytest_baseline.txt)).

---

## 2. Documentation vs. Code Claims Audit Table

| CLAIM | WHERE CLAIMED | FOUND IN CODE | REPRODUCED | NOTES |
| :--- | :--- | :--- | :--- | :--- |
| **Job-Scam F1-macro: 0.8346** | `README.md` (historical lines 218, 373) | Naive 80/20 train/test split in `train_baseline_model.py` | **No** (Leakage artifact) | The 0.8346 score was obtained from an un-grouped 80/20 random split where identical scam templates were split between train and test. **MEASURED on DIFrauD fold 0 under near-duplicate grouping: F1 = 0.5931** (95% CI: `0.4897`–`0.6809`). |
| **Multiclass F1-macro: 0.9837** | `README.md` (historical lines 219, 374) | Naive 80/20 train/test split in `train_baseline_model.py` | **No** (Leakage artifact) | Obtained from an un-grouped 80/20 random split on Sentinel with 60% scam base rate. When measured per category under near-duplicate grouping: Financial Fraud F1 = 0.9080, Govt Impersonation F1 = 0.9145, Bank Phishing F1 = 0.9004, Romance Extortion F1 = 1.0000. Binary fraud base-rate precision drops to 0.1972 at 5% base rate. |
| **URL Phishing F1: 0.9524, ROC-AUC: 0.9905** | `README.md` (historical lines 220, 375) | `train_phishing_url_model.py` (80/20 random split) | **No** (Domain leakage artifact) | Un-grouped random split split URLs from the same host (e.g. `vercel.app`, `webflow.io`) across train and test. **MEASURED with domain-grouped split: F1 = 0.9251** (95% CI: `0.9151`–`0.9348`), Base-Rate 5% Precision = 0.3467. |
| **Tabular URL F1: 0.9680, ROC-AUC: 0.9961** | `README.md` (historical line 376) | `train_phishing_url_model.py` (80/20 random split on HistGB) | **No** (Domain leakage artifact) | Evaluated without domain grouping. **MEASURED with domain-grouped split: F1 = 0.9442** (95% CI: `0.9361`–`0.9526`), Base-Rate 5% Precision = 0.3710. |
| **p95 Latency: 1,850 ms** | Historical roadmap / benchmark notes; `IMPLEMENTATION_PLAN.md:2341` (`TARGET <= 3,000 ms`) | Microsecond per-inference timings in CLI scripts; end-to-end HTTP pipeline benchmark runner | **Not Yet** (TARGET, not live SLA) | Individual model inference latency is sub-millisecond (0.05–0.3 ms), but end-to-end async registry lookups depend on external network latency. Labelled strictly as **TARGET: p95 <= 3,000 ms**. |
| **FPR: 0.038 (False Positive Rate)** | `docs/TRANSPARENCY_REPORT.md:21` (Infrastructure ECE) | Tranco-Top10k heuristic simulation | **Not Yet** (Historical benchmark) | Claimed on heuristic ECE. Under honest 5% base-rate testing on DIFrauD text, **MEASURED FPR is 0.0027** (PASS). On URL phishing, **MEASURED FPR is 0.0945** (Gate Alert). |
| **Test Count: 119 passing tests** | `README.md:173`, `README.md:232` | `tests/` directory | **No** (Stale claim) | Stale snapshot from earlier development phase. Pytest currently executes 273 tests. |
| **Test Count: 184 passing tests** | `ADDENDUM_AUDIT.md:7`, `CHANGELOG.md:47`, architecture reports | `tests/` directory | **No** (Stale claim) | Stale count from Phase 8. Pytest currently executes 273 tests. |
| **Test Count: 245 passing tests** | `README.md:9`, `README.md:433`, `README.md:502` | `tests/` directory | **No** (Stale claim) | Stale snapshot from Phase L. Real count is **273 passed, 0 failed, 0 skipped**. |
| **"Production-Ready"** | Historical docstrings, `IMPLEMENTATION_PLAN.md:500`, business strategy docs | Core engines and APIs implemented, but no candidate corridor live pilots | **No** (Inaccurate status) | System has not undergone field trials with real applicants or live recruitment agencies. Must be classified as **"Feature-complete prototype, not field-validated"**. |
| **DIFrauD Row Count: 14,295** | `datasets/dataset_manifest.md:33`, `README.md:373` | `datasets/job_scam_text/difraud/train.jsonl` (11,436), `validation.jsonl` (1,429), `test.jsonl` (1,430) | **Yes** (11,436 + 1,429 + 1,430 = 14,295) | Confirmed across splits: 11,436 train + 1,429 validation + 1,430 test = exactly 14,295 rows. Cleaning drops 6 rows $<5$ chars, leaving 11,430 train rows. |
| **Sentinel Multiclass Row Count: 14,000** | `datasets/dataset_manifest.md:34`, `README.md:374` | `datasets/job_scam_text/indian_scam_multiclass/sentinel_dataset_multiclass.csv` | **Yes** | Exactly 14,000 rows in CSV, zero missing values, zero duplicates. |
| **CompPhish Row Count: 15,358** | `datasets/dataset_manifest.md:38`, `README.md:375` | `datasets/phishing_urls/compphish/all_features_threshold90.csv` | **Yes** | Exactly 15,358 rows. 7 duplicate URLs removed during cleaning leaves 15,351 unique URLs. |
| **PhishTank Row Count: 77,204** | `datasets/dataset_manifest.md:35` | `datasets/phishing_urls/phishtank/online-valid.csv` | **Yes** | Exactly 77,204 rows verified active phishing feed. |

---

## 3. Harness Verification
- [`scripts/train_and_evaluate.py`](file:///d:/Life_Lens_Ai/scripts/train_and_evaluate.py) is confirmed present and operational in the workspace.
- Hard stop (d) does not trigger.
- Proceeding to Phase 1: Harness Hardening.
