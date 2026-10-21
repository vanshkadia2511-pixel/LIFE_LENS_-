# Model Card: URL Phishing Detectors (`url_char_ngram_v2` & `url_tabular_v2`)

**Model Status:** `MEASURED`  
**Artifact Directories:** [`models/url_char_ngram_v2/`](../models/url_char_ngram_v2/), [`models/url_char_ngram_calibrated_v2/`](../models/url_char_ngram_calibrated_v2/), [`models/url_tabular_v2/`](../models/url_tabular_v2/), [`models/url_tabular_calibrated_v2/`](../models/url_tabular_calibrated_v2/)  
**Created:** 2026-10-13  
**Harnesses:** [`scripts/train_and_evaluate.py`](../scripts/train_and_evaluate.py) & [`scripts/evaluate_tabular.py`](../scripts/evaluate_tabular.py)

---

## 1. Intended Use & Prohibited Scenarios
- **Intended Use:** Fast, client-side heuristic pre-filtering and risk scoring of incoming URLs in browser extensions and gateway scanners to prioritize links for reputation lookups and sandboxing.
- **What It Is NOT For:**
  - ❌ **No Automated Blocking:** Model scores must never automatically block access to websites or drop messages without human intervention or authoritative blocklist confirmation (e.g. Google Safe Browsing, PhishTank).
  - ❌ **No Accusations:** Must never accuse website owners, registrars, or hosting providers of hosting malware or operating scams.
  - ❌ **No Autonomous Adjudication:** High-risk scores should produce a warning prompt with an option for the user to proceed or request manual review.

---

## 2. Data Source, License Status & SHA-256
- **Source Dataset:** CompPhish (Mendeley Data `fmbs4kp9wz`)
- **File:** `datasets/phishing_urls/compphish/all_features_threshold90.csv`
- **SHA-256:** `2ae569c2d2abff08b24a66099b466a21423f55d3c823e45ac5362f22337492c6`
- **License:** Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Total Clean Records:** 15,351 unique URLs (after dropping 7 duplicate rows)
- **Class Balance:**
  - Legitimate (`0`): 8,154 (53.12%)
  - Phishing (`1`): 7,197 (46.88%)

---

## 3. Split Methodology & Domain Leakage Prevention
- **Split Scheme:** `StratifiedGroupKFold(5, shuffle=True, random_state=42)`
  - Fold 0 $\rightarrow$ **TEST** (3,070 rows; scored once at final evaluation)
  - Fold 1 $\rightarrow$ **VALIDATION** (3,070 rows; parameter & threshold tuning)
  - Folds 2–4 $\rightarrow$ **TRAIN** (9,211 rows)
- **Registered Domain Grouping:** To prevent identical host domains (e.g., hundreds of subdomains under `vercel.app`, `webflow.io`, `weebly.com`) from being split across training and testing, URLs are grouped strictly by registered domain using offline `tldextract` (5.1.2) with `suffix_list_urls=()`. Total disjoint domain groups: 9,343.

---

## 4. Measured Performance & Gate Status

All metrics below are strictly **MEASURED** on Fold 0 held-out test split.

| Model Variant | Calibration | Test Precision | Test Recall | Test F1 (95% CI) | PR-AUC | Base-Rate (5%) Precision | Base-Rate (5%) FPR | False Alerts / 1k | Gate Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **URL Char N-Gram (3–5)** | None | `0.8848` | `0.9771` | **0.9287** [0.9198, 0.9382] | `0.9871` | `0.3143` | `0.1122` | 112.20 | 🚨 **FAIL** (FPR > 0.05, Prec < 0.75) |
| **URL Char N-Gram (3–5)** | Calibrated (cv=5) | `0.8920` | `0.9757` | **0.9320** [0.9232, 0.9411] | `0.9872` | `0.3301` | `0.1042` | 104.23 | 🚨 **FAIL** (FPR > 0.05, Prec < 0.75) |
| **Tabular HistGB (70 Feats)** | None | `0.8985` | `0.9903` | **0.9421** [0.9340, 0.9502] | `0.9961` | `0.3455` | `0.0987` | 98.71 | 🚨 **FAIL** (FPR > 0.05, Prec < 0.75) |
| **Tabular HistGB (70 Feats)** | Calibrated (cv=5) | `0.9030` | `0.9896` | **0.9443** [0.9356, 0.9524] | `0.9962` | `0.3570` | `0.0938` | 93.81 | 🚨 **FAIL** (FPR > 0.05, Prec < 0.75) |

### Gate 1 Failure Analysis
- At the test set's balanced distribution (~47% phishing), models achieve high F1 (0.928–0.944).
- When evaluated under a realistic 5% positive base rate, false alerts overwhelm legitimate traffic (~94–112 false alerts per 1,000 legitimate links), pulling precision down to 31–36% and causing both models to FAIL Gate 1.
- Previous un-grouped claims of F1 `0.9524` and `0.9680` were inflated by subdomain leakage across splits.

---

## 5. Cross-Dataset Results & Overlap Counts
- **Overlap with PhishTank Live Feed (`3c1327db`):** 954 exact URL matches identified between CompPhish and PhishTank.
- **External Evaluation:** Evaluating models on pure phishing feeds confirms high recall (>97%), but external legitimate baseline sets are required to test cross-dataset false positive rates.

---

## 6. Top Features & Suspected Artifacts
- **Char N-Gram Strongest Positive Features:** `.we`, `app`, `365`, `site`, `ebl`, `uan`, `bly`, `weeb`, `eebl`, `eebly`, `.weeb`, `ebly`, `weebl`, `-co`, `bly.c`
- **Tabular HistGB Key Features:** Subdomain depth, path entropy, presence of IP address in hostname, external form actions, abnormal URL length.
- **Suspected Artifacts:**
  - **Hosting Platform Bias:** Heavy weighting of character n-grams like `weeb`, `ebly`, and `site` reflects specific free hosting platforms (e.g. Weebly, Webflow) that were heavily represented among phishing targets in the scraping period.
  - **Brand Tokens:** N-grams like `365` reflect Microsoft 365 credential harvesting campaigns specific to the dataset collection window.

---

## 7. Failure Patterns & Error Analysis (from Error CSVs)
- **False Positives:** Legitimate small business, educational, or developer sites hosted on free multi-tenant cloud platforms (`*.weebly.com`, `*.vercel.app`) falsely flagged due to hosting n-grams; complex enterprise URLs with authentication redirect queries flagged due to high token entropy.
- **False Negatives:** Short, clean, branded phishing links on novel top-level domains that do not contain typical hyphenation or known hosting fragments; compromised legitimate domains hosting phishing sub-paths.

---

## 8. Languages Measured & Geographic Scope
- **Languages / Encodings Measured:** Standard ASCII and URL percent-encoded strings.
- **Not Evaluated:** Internationalized Domain Names (IDNs) with non-Latin scripts (Cyrillic, Arabic, Devanagari) or homograph attacks using Unicode confusable characters.

---

## 9. Prerequisites for Production Readiness
1. **Low-Prevalence Operational Calibration:** Re-tune decision thresholds on a representative stream with ~1–5% phishing prevalence to suppress FPR below 0.05.
2. **Reputation Lookup Orchestration:** Pair heuristic models with live threat intelligence APIs (PhishTank, OpenPhish, Safe Browsing) so heuristic scores only prompt deep sandboxing rather than immediate alerts.
3. **Real-World Labeled Benchmark:** Collect and annotate a prospective set of 500+ URLs from real email/SMS gateways with two independent raters (Cohen's kappa $\ge 0.85$).
