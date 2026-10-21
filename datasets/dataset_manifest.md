# LifeLens Ω — Local Dataset Library Manifest

**Generated:** 2026-09-24  
**Project:** LifeLens Ω (Recruitment Fraud & Job-Scam Defense System)  
**Root Path:** [`d:/Life_Lens_Ai/datasets/`](file:///d:/Life_Lens_Ai/datasets/)

---

## 📁 Library Structure Overview

```text
datasets/
├── dataset_manifest.md                <- This manifest
├── job_scam_text/
│   ├── difraud/                      <- DIFrauD job_scams split (JSONL) [DOWNLOADED]
│   ├── indian_scam_multiclass/       <- Sentinel Indian scam multiclass (CSV) [DOWNLOADED]
│   ├── fraud_r1/                     <- Fraud-R1 Benchmark [GATED / MANUAL HF APPROVAL REQUIRED]
│   └── emscad/                       <- EMSCAD Real/Fake Job Postings [MANUAL KAGGLE DOWNLOAD]
├── phishing_urls/
│   ├── phishtank/                    <- PhishTank active verified feed (CSV) [DOWNLOADED]
│   ├── url_phish/                    <- Mendeley URL-Phish [MANUAL MENDELEY DOWNLOAD]
│   └── compphish/                    <- Mendeley CompPhish [DOWNLOADED / INTEGRATED]
├── company_registry_reference/       <- Reference registries & entity databases
└── misc/                             <- Supplementary lookup tables & test fixtures
```

---

## 📊 Dataset Inventory & Quality Audit Summary

| Dataset Name | Category / Split | Source & Link | License | Format | Row Count | Local Status | Quality Audit Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DIFrauD** (`job_scams`) | Job Scam Text | [redasers/difraud](https://huggingface.co/datasets/redasers/difraud) | MIT | JSONL | 14,295 | ✅ Downloaded | 🚨 **Severe Imbalance** (95.8% legit / 4.2% scam), 0 missing, 0 dupes |
| **Indian Scam Multiclass (Sentinel)** | Job / Fin / Impersonation Scam Text | [Shade63/scam-classification-multiclass](https://huggingface.co/datasets/Shade63/scam-classification-multiclass) | Apache 2.0 / Open | CSV | 14,000 | ✅ Downloaded | ✅ **Clean & Balanced** (60% scam / 40% legit), 0 missing, 0 dupes |
| **PhishTank Feed** | Phishing URL Intelligence | [PhishTank Data](http://data.phishtank.com/data/online-valid.csv) | Open Data | CSV | 77,204 | ✅ Downloaded | ✅ **Verified Active Phishing** (100% verified, 3 URL dupes) |
| **Fraud-R1 Benchmark** | Fraud LLM Benchmark | [Chouoftears/Fraud-R1](https://huggingface.co/datasets/Chouoftears/Fraud-R1-LLM-Defense-Fraud-Benchmark) | Research License | Tar/JSONL | ~15k+ | ⚠️ Manual Approval | Requires accepting HF gated license agreement |
| **Mendeley URL-Phish** | Phishing URL Lexical Features | [Mendeley 65z9twcx3r](https://data.mendeley.com/datasets/65z9twcx3r/1) | CC BY 4.0 | CSV | 111,660 | ⚠️ Manual Download | Cloudflare protected, requires browser download |
| **Mendeley CompPhish** | URL & HTML Phishing Features | [Mendeley fmbs4kp9wz](https://data.mendeley.com/datasets/fmbs4kp9wz/1) | CC BY 4.0 | CSV/XLSX | 15,358 | ✅ Integrated | ✅ **Balanced** (53% legit / 47% phishing), 70 lexical/structural features |
| **EMSCAD Real/Fake Job Postings** | Job Scam Text | [Kaggle Real/Fake Jobs](https://www.kaggle.com/datasets/shivamb/real-or-fake-fake-jobposting-prediction) | CC0 Public Domain | CSV | 17,880 | ⚠️ Manual Download | Kaggle API key not configured on host |

---

## 🔍 Detailed Dataset Audits

### 1. DIFrauD (`job_scams` subset)
- **Local Path:** [`datasets/job_scam_text/difraud/`](file:///d:/Life_Lens_Ai/datasets/job_scam_text/difraud/)
  - `train.jsonl` (11,436 rows, 14.5 MB)
  - `test.jsonl` (1,430 rows, 1.8 MB)
  - `validation.jsonl` (1,429 rows, 1.8 MB)
- **Source:** [HuggingFace - redasers/difraud](https://huggingface.co/datasets/redasers/difraud)
- **Columns:** `text` (string, job posting content), `label` (int: 0=legitimate, 1=scam)
- **Quality Audit Results:**
  - Missing text / labels: **0 (0.00%)**
  - Duplicate rows: **0 (0.00%)**
  - Text length stats: min=44 chars, median=1,055 chars, mean=1,246 chars, max=14,810 chars
  - Class distribution (Train):
    - `0` (Legitimate): 10,957 (95.8%)
    - `1` (Scam): 479 (4.2%)
  - Class distribution (Test):
    - `0` (Legitimate): 1,370 (95.8%)
    - `1` (Scam): 60 (4.2%)
  - **Flags:** 🚨 `[SEVERE]` Class imbalance (95.8% majority class). Must use `class_weight='balanced'` or calibrated thresholding during training.

---

### 2. Indian Scam Multiclass Dataset (Sentinel)
- **Local Path:** [`datasets/job_scam_text/indian_scam_multiclass/`](file:///d:/Life_Lens_Ai/datasets/job_scam_text/indian_scam_multiclass/)
  - `sentinel_dataset_multiclass.csv` (14,000 rows, 2.76 MB)
  - `sentinel_dataset_multiclass_clean.csv` (14,000 rows, 2.47 MB)
  - `README.md` (2.6 KB)
- **Source:** [HuggingFace - Shade63/scam-classification-multiclass](https://huggingface.co/datasets/Shade63/scam-classification-multiclass)
- **Columns:** `id`, `text`, `label`, `category`, `category_name`
- **Quality Audit Results:**
  - Missing text / labels: **0 (0.00%)**
  - Duplicate rows: **0 (0.00%)**
  - Text length stats: min=110 chars, median=172 chars, mean=172 chars, max=257 chars
  - Binary Distribution (`label`):
    - `0` (Legit): 5,600 (40.0%)
    - `1` (Scam): 8,400 (60.0%)
  - Multiclass Breakdown (`category_name`):
    - `legit`: 5,600 (40.0%)
    - `financial_fraud`: 3,080 (22.0%)
    - `government_impersonation`: 2,905 (20.8%)
    - `bank_phishing`: 1,875 (13.4%)
    - `romance_parcel_sextortion`: 540 (3.9%)
  - **Flags:** ✅ `[PASS]` 0 severe flags. Balanced distribution suitable for multiclass and cross-domain fraud generalization.

---

### 3. PhishTank Live Feed
- **Local Path:** [`datasets/phishing_urls/phishtank/online-valid.csv`](file:///d:/Life_Lens_Ai/datasets/phishing_urls/phishtank/online-valid.csv) (77,204 rows, 14.8 MB)
- **Source:** [PhishTank Data Feed](http://data.phishtank.com/data/online-valid.csv)
- **Columns:** `phish_id`, `url`, `phish_detail_url`, `submission_time`, `verified`, `verification_time`, `online`, `target`
- **Quality Audit Results:**
  - Total records: **77,204 active verified phishing URLs**
  - Missing values: **0** across all 8 columns
  - URL uniqueness: 77,201 unique URLs (3 duplicate submissions)
  - Verification: 100% verified (`verified == 'yes'`)
  - Top targets: Generic/Other (67,563), Allegro (4,463), Internal Revenue Service (927), Amazon.com (828), Facebook (461), Microsoft (420), Bradesco (262), Netflix (248).
  - **Flags:** ✅ `[PASS]` High-confidence real-time ground truth for URL reputation scoring (§11).

---

## 🚫 Missing / Manual Action Datasets & Guidance

The following datasets require manual user actions due to authentication, Cloudflare bot protection, or host API credentials:

### 1. Fraud-R1 Benchmark
- **Source:** [HuggingFace - Chouoftears/Fraud-R1-LLM-Defense-Fraud-Benchmark](https://huggingface.co/datasets/Chouoftears/Fraud-R1-LLM-Defense-Fraud-Benchmark)
- **Reason:** Dataset repository is **Gated (`gated: auto`)**. Hugging Face requires researchers to click *"Agree and access repository"* to sign the research license agreement.
- **Action Required:**
  1. Visit the repository link above in your browser while logged into Hugging Face.
  2. Click the agreement button to gain access.
  3. Download the repository files or log in via CLI with `huggingface-cli login` and pull to [`datasets/job_scam_text/fraud_r1/`](file:///d:/Life_Lens_Ai/datasets/job_scam_text/fraud_r1/).

### 2. Mendeley URL-Phish Dataset (`65z9twcx3r`)
- **Source:** [Mendeley Data - 65z9twcx3r](https://data.mendeley.com/datasets/65z9twcx3r/1) (DOI: `10.17632/65z9twcx3r.1`)
- **Reason:** Mendeley Data endpoints enforce Cloudflare challenge protection and dynamic S3 session tokens for asset downloads, returning HTTP 403 to automated scripts.
- **Action Required:**
  1. Open the Mendeley Data link in your browser.
  2. Click **Download All** or the CSV file download.
  3. Extract/move the downloaded CSV file to [`datasets/phishing_urls/url_phish/`](file:///d:/Life_Lens_Ai/datasets/phishing_urls/url_phish/).

### 3. EMSCAD / Real-Fake Job Posting Prediction (Kaggle)
- **Source:** [Kaggle - Real / Fake Job Posting Prediction](https://www.kaggle.com/datasets/shivamb/real-or-fake-fake-jobposting-prediction)
- **Reason:** Kaggle API credentials (`~/.kaggle/kaggle.json` or `KAGGLE_USERNAME`/`KAGGLE_KEY`) are not configured on this machine.
- **Action Required:**
  - **Option A (Manual Download):** Download `fake_job_postings.csv` from the Kaggle link above and save to [`datasets/job_scam_text/emscad/`](file:///d:/Life_Lens_Ai/datasets/job_scam_text/emscad/).
  - **Option B (Kaggle CLI):** Place your `kaggle.json` into `C:\Users\VRAJESH\.kaggle\kaggle.json` and run:
    ```bash
    kaggle datasets download -d shivamb/real-or-fake-fake-jobposting-prediction -p datasets/job_scam_text/emscad --unzip
    ```

