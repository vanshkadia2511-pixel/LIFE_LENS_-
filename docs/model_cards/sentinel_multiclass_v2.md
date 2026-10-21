# Model Card: Sentinel Multiclass & Cross-Domain Fraud Classifiers (`sentinel_*_v2`)

**Model Status:** `MEASURED`  
**Artifact Directories:** [`models/sentinel_*_v2/`](../models/)  
**Created:** 2026-10-13  
**Harness:** [`scripts/train_and_evaluate.py`](../scripts/train_and_evaluate.py)

---

## 1. Intended Use & Prohibited Scenarios
- **Intended Use:** Triage, routing, and heuristic risk scoring of suspicious consumer messages and communication alerts into specific fraud taxonomy categories (Financial, Government Impersonation, Bank Phishing, Romance/Extortion).
- **What It Is NOT For:**
  - ❌ **No Automated Blocking:** Model scores must never trigger irreversible automated message blocking, account suspension, or financial transaction freezing.
  - ❌ **No Accusations:** Under no circumstances should model outputs be used to accuse named individuals, entities, or phone numbers of criminal activity.
  - ❌ **No Decisions Without Human Review:** All high-confidence detections must serve strictly as decision support for human investigators, compliance analysts, or end-user advisory warnings with explicit human override.

---

## 2. Data Source, License Status & SHA-256
- **Source Dataset:** Sentinel Indian Scam Multiclass Dataset from Hugging Face (`Shade63/scam-classification-multiclass`)
- **File:** `datasets/job_scam_text/indian_scam_multiclass/sentinel_dataset_multiclass.csv`
- **SHA-256:** `ebdec640f5d81a0e368aa6607579aad963881c57e16be4719b9791f581441d1d`
- **License:** Apache License 2.0 (Open Access)
- **Clean Rows:** 14,000 rows (0 missing, 0 empty, 0 duplicate)
- **Distribution:**
  - `legit`: 5,600 (40.0%)
  - `financial_fraud`: 3,080 (22.0%)
  - `government_impersonation`: 2,905 (20.8%)
  - `bank_phishing`: 1,875 (13.4%)
  - `romance_parcel_sextortion`: 540 (3.9%)

---

## 3. Split Methodology & Leakage Prevention
- **Split Scheme:** `StratifiedGroupKFold(5, shuffle=True, random_state=42)`
  - Fold 0 $\rightarrow$ **TEST** (~2,800 rows; scored exactly once at final evaluation)
  - Fold 1 $\rightarrow$ **VALIDATION** (~2,800 rows; hyperparameter $C$ and decision threshold selection)
  - Folds 2–4 $\rightarrow$ **TRAIN** (~8,401 rows)
- **Group Leakage Defense:** Near-duplicate grouping via TF-IDF cosine similarity $\ge 0.90$ with union-find. Near-copies and template variants are strictly confined to a single split. Total disjoint groups: 8,156.
- **Evaluation Paradigm:** One-vs-Rest (OVR) per category. **Note on Negatives:** In each category run, the negative split contains all legitimate samples PLUS all other scam categories.

---

## 4. Measured Performance & Gate Status

All metrics below are **MEASURED** on Fold 0 held-out test split.

| Model / Subtask | Chosen $C$ | Threshold | Test Precision | Test Recall | Test F1 (95% CI) | PR-AUC | Base-Rate (5%) Precision | Base-Rate (5%) FPR | False Alerts / 1k | Gate Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Financial Fraud** | 10.0 | 0.8165 | `0.9981` | `0.8328` | **0.9080** [0.8904, 0.9241] | `0.9927` | `0.9897` | `0.0005` | 0.46 | ✅ **PASS** |
| **Romance / Extortion** | 10.0 | 0.0280 | `1.0000` | `1.0000` | **1.0000** [1.0000, 1.0000] | `1.0000` | `1.0000` | `0.0000` | 0.00 | ✅ **PASS** |
| **Govt Impersonation** | 10.0 | 0.6006 | `0.9291` | `0.9003` | **0.9145** [0.8952, 0.9307] | `0.9407` | `0.7245` | `0.0180` | 18.02 | 🚨 **FAIL** (Prec 0.7245 < 0.75) |
| **Bank Phishing** | 10.0 | 0.0403 | `0.8188` | `1.0000` | **0.9004** [0.8793, 0.9207] | `0.9965` | `0.6060` | `0.0342` | 34.21 | 🚨 **FAIL** (Prec 0.6060 < 0.75) |
| **Binary Fraud (All Scams)** | 1.0 | 0.0796 | `0.8750` | `1.0000` | **0.9333** [0.9247, 0.9415] | `1.0000` | `0.1972` | `0.2143` | 214.29 | 🚨 **FAIL** (FPR > 0.05 & Prec < 0.75) |

### Multiclass Macro Summary (4 Scam Categories)
- **Macro Precision:** `0.9365`
- **Macro Recall:** `0.9333`
- **Macro F1:** `0.9307`
- *Comparison with Previous README Claim:* The previous claim of F1-macro `0.9837` was achieved under un-grouped 80/20 random splits. When near-duplicate template leakage is prevented, the honest macro-F1 is `0.9307`.

---

## 5. Cross-Dataset Results & Overlap Counts
- **Overlap with DIFrauD Training Set:** 0 exact text overlaps.
- **Cross-Domain Transfer:** Because Sentinel focuses on mobile consumer cybercrime (SMS, WhatsApp, UPI fraud) and DIFrauD focuses on recruitment listings, direct cross-evaluation yields near-zero domain alignment, highlighting the need for separate specialized sub-models.

---

## 6. Top Features & Suspected Artifacts
- **Financial Fraud Positive Signals:** `000`, `pnb`, `interpol`, `pnb transaction`, `ncb`, `fee`, `rs`, `lakh`, `customs`, `reward`, `pnb card`
- **Government Impersonation Positive Signals:** `cybercrime`, `narcotics`, `trafficking`, `cbi`, `trai`, `passport`, `pan card`, `money laundering`, `si`, `dcp`, `arrest`
- **Bank Phishing Positive Signals:** `kyc`, `account`, `bank`, `the otp`, `verify`, `detected`, `transaction`, `hdfc`
- **Romance / Extortion Positive Signals:** `am`, `my`, `me`, `with you`, `help me`, `to india`, `need rs`, `looking for`, `please send`
- **Suspected Artifacts:**
  - **Entity Overfitting:** Heavy reliance on specific institution names (`pnb`, `hdfc`, `cbi`, `interpol`, `ncb`, `trai`). Scammers altering brand names to ICICI, SBI, or local police stations evade detection or shift categories.
  - **Currency / Amount Boilerplate:** N-grams like `000`, `rs`, `lakh` reflect synthetic or template patterns in the source generation pipeline.

---

## 7. Failure Patterns & Error Analysis (from Error CSVs)
- **False Positives:** Legitimate bank alerts regarding high-value debits, legitimate statutory notices (e.g. IT department or passport appointment reminders), and standard two-factor authentication OTP messages triggering bank phishing or government impersonation alerts.
- **False Negatives:** Subtle conversational lures without overt regulatory threats or banking acronyms (e.g., initial friendly greetings or novel job-cum-crypto task invitations) misclassified as legitimate because they lack signature scam keywords.
- **Cross-Class Confusion:** When a fraudster combines tactics (e.g., an extortion scam claiming to be from the police regarding a bank transfer), the model struggles between `financial_fraud`, `government_impersonation`, and `bank_phishing`.

---

## 8. Languages Measured & Geographic Scope
- **Languages Measured:** **English only** (with Indian English phrasing and institutional nomenclature).
- **Not Evaluated:** Hindi (Devanagari script), Hinglish (Romanized Hindi), Tamil, Telugu, Bengali, or code-switched messaging.

---

## 9. Prerequisites for Production Readiness
1. **Real-World Low-Prevalence Labeled Benchmark:** Collect and annotate a prospective set of 500+ real incoming messages under true base rates (~1–5%), annotated by two independent reviewers with Cohen's kappa $\ge 0.85$.
2. **Threshold Re-Tuning on Target Distribution:** Decision thresholds must be recalibrated on low-prevalence validation sets to reduce false alert volume (FPR $\le 0.05$).
3. **Multilingual & Code-Mixed Support:** Evaluation of language-specific representations (e.g., IndicBERT or lightweight character models) for Romanized Hindi/regional languages.
4. **Human Review Protocol:** Integration into an analyst console with explicit reason-code attribution.
