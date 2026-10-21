# LifeLens Ω — Dataset Verification Registry

**Generated:** 2026-10-13  
**Status Standard:** `VERIFIED`, `UNVERIFIED` (with rationale), or `BLOCKED` (with rationale).

---

## 1. Dataset Verification Summary

| Dataset Name | Local Path | License Status | Clean Row Count | SHA-256 (First 16 chars) | Text / Feature Col | Label Col | Positive Value | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DIFrauD** (`job_scams`) | `datasets/job_scam_text/difraud/train.jsonl` | MIT License | 11,430 (train) | `ed64c355d9a571e6` | `text` | `label` | `1` | **VERIFIED** |
| **DIFrauD Test** | `datasets/job_scam_text/difraud/test.jsonl` | MIT License | 1,430 (test) | `905790a8a762d3bd` | `text` | `label` | `1` | **VERIFIED** |
| **Sentinel Multiclass** | `datasets/job_scam_text/indian_scam_multiclass/sentinel_dataset_multiclass.csv` | Apache-2.0 | 14,000 | `ebdec640f5d81a0e` | `text` | `category_name`, `label` | `financial_fraud`, `government_impersonation`, `bank_phishing`, `romance_parcel_sextortion` (OVR); `1` (binary) | **VERIFIED** |
| **CompPhish** | `datasets/phishing_urls/compphish/all_features_threshold90.csv` | CC BY 4.0 | 15,351 | `2ae569c2d2abff08` | `url` (70 numeric features) | `label` | `1` | **VERIFIED** |
| **PhishTank Live Feed** | `datasets/phishing_urls/phishtank/online-valid.csv` | Open Data / Developer Terms | 77,204 | `3c1327db6cfe8162` | `url` | `verified` | `yes` | **VERIFIED** |
| **Fraud-R1 Benchmark** | N/A | Research License (Gated) | ~15,000 | N/A | N/A | N/A | N/A | **BLOCKED** (Gated on Hugging Face; bypass strictly prohibited by Rule 6) |
| **Mendeley URL-Phish** | N/A | CC BY 4.0 | 111,660 | N/A | N/A | N/A | N/A | **BLOCKED** (Cloudflare challenge on download endpoint) |
| **EMSCAD Real/Fake** | N/A | CC0 Public Domain | 17,880 | N/A | N/A | N/A | N/A | **BLOCKED** (Kaggle API token not configured) |

---

## 2. Dataset Cards & Metadata

### 1. DIFrauD (`job_scams` subset)
- **Source URL:** [https://huggingface.co/datasets/redasers/difraud](https://huggingface.co/datasets/redasers/difraud)
- **License (quoted):** `"MIT License"`
- **Row Counts:** Train: 11,436 (11,430 clean after dropping $<5$ chars), Validation: 1,429, Test: 1,430. Total: 14,295.
- **SHA-256 (train.jsonl):** `ed64c355d9a571e675804e0d83b9b27d29b475fd4b6b9c96f20a0874db3b322c`
- **SHA-256 (test.jsonl):** `905790a8a762d3bd46ab0943f627cf94d7184d5876ebf358bba630f4d20d2fc0`
- **Columns:** `text` (job posting description), `label` (0 = legitimate, 1 = scam)
- **Positive Label:** `1`
- **Exact Overlap with Test Split:** 1 exact text match.
- **Authors' Stated Limitations:** Severe class imbalance (4.2% scam rate); templated job descriptions scraped from public job boards; lacks non-English and regional Indian recruitment formats.
- **Audit Verdict:** [`docs/audit/quality_difraud.txt`](file:///d:/Life_Lens_Ai/docs/audit/quality_difraud.txt) (Severe imbalance flag confirmed; resolved via `class_weight='balanced'` and validation threshold tuning).

### 2. Sentinel Indian Scam Multiclass Dataset
- **Source URL:** [https://huggingface.co/datasets/Shade63/scam-classification-multiclass](https://huggingface.co/datasets/Shade63/scam-classification-multiclass)
- **License (quoted):** `"Apache License 2.0"`
- **Row Count:** 14,000 rows (0 missing, 0 empty, 0 duplicate)
- **SHA-256:** `ebdec640f5d81a0e368aa6607579aad963881c57e16be4719b9791f581441d1d`
- **Columns:** `id`, `text`, `label`, `category`, `category_name`
- **Positive Labels:**
  - One-vs-Rest: `financial_fraud` (3,080), `government_impersonation` (2,905), `bank_phishing` (1,875), `romance_parcel_sextortion` (540).
  - Binary Scam: `1` (8,400 scams, 5,600 legitimate).
- **Exact Overlap with DIFrauD Train:** 0 exact text matches.
- **Authors' Stated Limitations:** High scam prevalence (60% scams) uncharacteristic of real consumer inboxes; short message texts (median 172 chars); specific to Indian mobile cybercrime modalities.
- **Audit Verdict:** [`docs/audit/quality_sentinel.txt`](file:///d:/Life_Lens_Ai/docs/audit/quality_sentinel.txt) (Clean pass, 0 severe flags).

### 3. CompPhish (Mendeley Data)
- **Source URL:** [https://data.mendeley.com/datasets/fmbs4kp9wz/1](https://data.mendeley.com/datasets/fmbs4kp9wz/1)
- **License (quoted):** `"Creative Commons Attribution 4.0 International (CC BY 4.0)"`
- **Row Count:** 15,358 rows (15,351 unique URLs after dropping 7 duplicates)
- **SHA-256:** `2ae569c2d2abff08b24a66099b466a21423f55d3c823e45ac5362f22337492c6`
- **Columns:** `url`, `label`, and 70 numerical lexical/HTML features
- **Positive Label:** `1` (Phishing), Negative: `0` (Legitimate)
- **Exact Overlap with PhishTank:** 954 overlapping URLs.
- **Authors' Stated Limitations:** High concentration of multi-tenant application hosts (`vercel.app`, `webflow.io`, `weebly.com`) requiring strict registered-domain grouping to avoid leakage.
- **Audit Verdict:** [`docs/audit/quality_compphish.txt`](file:///d:/Life_Lens_Ai/docs/audit/quality_compphish.txt) (Clean pass, 0 flags).

### 4. PhishTank Live Verified Feed
- **Source URL:** [http://data.phishtank.com/data/online-valid.csv](http://data.phishtank.com/data/online-valid.csv)
- **License (quoted):** `"PhishTank Developer Terms of Use / Open Data"`
- **Row Count:** 77,204 active verified phishing URLs
- **SHA-256:** `3c1327db6cfe81626fd121db2d5ea0568f220f772dd60117626f56cc71e88cd1`
- **Columns:** `phish_id`, `url`, `phish_detail_url`, `submission_time`, `verified`, `verification_time`, `online`, `target`
- **Positive Label:** `yes`
- **Authors' Stated Limitations:** Contains 100% positive phishing samples with 0 legitimate baseline rows; used as live threat feed and external recall test only.
- **Audit Verdict:** [`docs/audit/quality_phishtank.txt`](file:///d:/Life_Lens_Ai/docs/audit/quality_phishtank.txt).
