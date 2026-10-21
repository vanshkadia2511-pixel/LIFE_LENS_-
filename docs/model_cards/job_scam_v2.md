# Model Card: Job Scam Binary Detector (`job_scam_v2`)

**Model Status:** `MEASURED`  
**Artifact Directory:** [`models/job_scam_v2/`](file:///d:/Life_Lens_Ai/models/job_scam_v2/)  
**Created:** 2026-10-13  
**Harness:** [`scripts/train_and_evaluate.py`](file:///d:/Life_Lens_Ai/scripts/train_and_evaluate.py)

---

## 1. Model Details
- **Architecture:** TF-IDF Word N-Grams (1–2) + Logistic Regression (`sublinear_tf=True`, `max_features=50,000`, `class_weight='balanced'`)
- **Regularization ($C$):** $C=10.0$ (tuned exclusively on validation PR-AUC across grid `[0.1, 1.0, 10.0]`)
- **Decision Threshold:** $0.5376$ (selected on validation split to satisfy target precision $\ge 0.90$, achieving val precision $0.9000$, val recall $0.3750$)
- **Task:** Binary recruitment fraud / job scam classification (0 = Legitimate, 1 = Scam)

---

## 2. Training Data & Licensing
- **Source Dataset:** DIFrauD (`job_scams` subset) from Hugging Face (`redasers/difraud`)
- **File:** `datasets/job_scam_text/difraud/train.jsonl`
- **SHA-256:** `ed64c355d9a571e675804e0d83b9b27d29b475fd4b6b9c96f20a0874db3b322c`
- **License:** MIT License
- **Clean Rows:** 11,430 rows (cleaned, dropped $<5$ chars, exact duplicates removed)
- **Positive Rate:** 4.19% (479 scams, 10,951 legitimate)

---

## 3. Split Methodology & Leakage Prevention
- **Split Scheme:** `StratifiedGroupKFold(5, shuffle=True, random_state=42)`
  - Fold 0 $\rightarrow$ **TEST** (2,286 rows; touched exactly once at final evaluation)
  - Fold 1 $\rightarrow$ **VALIDATION** (2,286 rows; used for hyperparameter $C$ tuning and decision threshold selection)
  - Folds 2–4 $\rightarrow$ **TRAIN** (6,858 rows)
- **Group Leakage Defense:** Near-duplicate grouping via TF-IDF cosine similarity $\ge 0.90$ with union-find. Near-copies and template twins are strictly confined to a single split, preventing identical scam templates from leaking between train and test. Total disjoint groups: 10,236.

---

## 4. Measured Performance

### Held-Out Test Evaluation (Fold 0)
- **Evaluation Standard:** MEASURED on DIFrauD, grouped held-out test (fold 0 of 5)
- **Test Precision:** `0.8776`
- **Test Recall:** `0.4479`
- **Test F1:** `0.5931` (95% Bootstrap CI: `0.4897` – `0.6809`, 1,000 resamples)
- **PR-AUC:** `0.6461`
- **ROC-AUC:** `0.9250`
- **Test Confusion Matrix:**
  - True Negatives (TN): 2,184
  - False Positives (FP): 6
  - False Negatives (FN): 53
  - True Positives (TP): 43

### Re-Weighted Realistic Base Rate (5% Positive Prevalence)
- **Assumed Base Rate:** 5.0% scams in realistic inbox / job feed
- **Base-Rate Precision:** `0.8959`
- **Base-Rate Recall:** `0.4479`
- **False Positive Rate (FPR):** `0.0027` (0.27%)
- **False Alerts per 1,000 Legitimate:** `2.74`
- **Gate 1 Compliance:** ✅ **PASSED** (FPR $\le 0.05$ and Precision $\ge 0.75$)

### Cross-Dataset / External Evaluation
- **External Dataset:** `datasets/job_scam_text/difraud/test.jsonl`
- **Exact Text Overlap with Training Split:** `1` (1 exact duplicate identified across splits)
- **External Precision:** `0.9062` | **External Recall:** `0.4833` | **External F1:** `0.6304` | **External PR-AUC:** `0.6622`

---

## 5. Top Predictive Features
- **Strongest Positive Signals (Scam):** `apply using`, `entered`, `with full`, `earn`, `jobs`, `data entry`, `1000`, `contact`, `subsea`, `audit`, `office`, `maintenance`, `reps`, `supplier`, `money`
- **Strongest Negative Signals (Legitimate):** `team`, `end`, `we re`, `specialist`, `new`, `digital`, `you ll`, `our`, `marketing`, `the right`, `love`, `user`, `creative`, `developer`

---

## 6. Failure Patterns & Error Analysis (from Error CSVs)
- **False Positives (6 exported):** Legitimate corporate job postings containing transaction/financial vocabulary (e.g., accounts receivable processing, collections workflows), manufacturing operations with structured quality standards, and genuine multi-region technical recruitment outreach.
- **False Negatives (53 exported):** High-tier executive and specialized tech job postings cloned verbatim by scammers (e.g., engineering management, video advertising director, corporate client services). Because these fraudsters omitted crude solicitation phrases ("quick cash", "daily payout"), lexical n-gram models score them very low. These necessitate Layer 2/3 deterministic registry verification rather than text heuristics.

---

## 7. Intended Use & Prohibited Scenarios
- **Intended Use:** Lightweight, low-latency client/edge heuristic scoring to prioritize job postings for deep entity verification.
- **What It Is NOT For:**
  - ❌ **No Automated Blocking:** Model scores must never automatically disqualify applicants, delete listings, or block employer accounts.
  - ❌ **No Accusations:** Must never accuse named individuals, recruiters, or organizations of criminal fraud.
  - ❌ **No Autonomous Adjudication:** High-risk flags require human reviewer triage and registry cross-referencing.

---

## 8. Languages Measured & Geographic Scope
- **Languages Measured:** **English only**.
- **Geographic Scope:** Primarily North American and international remote English postings from public web boards. Performance on multilingual job portals, code-mixed text (e.g., Hinglish), or regional scripts is unmeasured and unvalidated.

---

## 9. Prerequisites for Production Readiness
Before this model can be transitioned from prototype to production:
1. **Curated Real-World Labeled Benchmark:** A prospectively collected evaluation set of 300–500 real consumer-reported recruitment messages (including Hinglish and regional dialects), verified by two independent raters with Cohen's kappa $\ge 0.85$.
2. **Empirical Base-Rate Calibration:** Field validation of probability estimates under actual real-world base rates (~1–5%) using `CalibratedClassifierCV`.
3. **End-to-End Human-in-the-Loop User Testing:** Cognitive walk-throughs to ensure warning advisories do not cause alert fatigue or deter legitimate job seekers.
