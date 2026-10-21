# ADR 0001: Leakage-Aware Evaluation Grouping (Near-Duplicate Text & Registered-Domain URLs)

- **Status:** Accepted
- **Date:** 2026-10-13
- **Deciders:** Senior ML Engineering & LifeLens Maintainers
- **Applies to:** [`scripts/train_and_evaluate.py`](../../scripts/train_and_evaluate.py), [`scripts/evaluate_tabular.py`](../../scripts/evaluate_tabular.py), all benchmark evaluation runners.

---

## 1. Context and Problem Statement

LifeLens Ω relies on machine learning models to perform rapid heuristic triage on suspicious recruitment messages and phishing URLs. Previously, models were evaluated using naive, un-grouped random 80/20 train/test splits.

This methodology suffered from two severe forms of evaluation data leakage:

1. **Text Template Leakage:** Online scammers rely heavily on standardized boilerplates, modifying only minor details (names, amounts, phone numbers) across hundreds of job postings or phishing SMS lures. In un-grouped splits, nearly identical twins of the same scam template fell into both training and test sets. The model memorized template-specific n-grams rather than generalizable scam mechanics, producing deceptively high test scores (e.g., claimed F1 0.8346 on DIFrauD, claimed F1 0.9837 on Sentinel) that plummeted when exposed to real-world variations.
2. **Domain-Level Subdomain Leakage:** URL datasets (e.g., CompPhish) contain hundreds of subdomains or landing pages hosted on free or multi-tenant platforms (e.g., `*.vercel.app`, `*.webflow.io`, `*.weebly.com`). A random split placed different subdomains of the same host in both train and test splits. The model learned to classify specific registered domains rather than general lexical phishing signals, creating artificially elevated scores (claimed F1 0.9524 for Char N-Gram, 0.9680 for Tabular HistGB).

---

## 2. Decision Drivers

- **Rule P4 (No fake metrics):** Every metric reported to users, enterprise partners, and stakeholders must be honest, reproducible, and reflective of field performance.
- **Leakage Elimination:** Splits must guarantee that no near-duplicate text cluster and no registered domain spans across train, validation, and test splits.
- **Zero Network Dependencies:** Evaluation pipelines must operate completely offline, without network calls to fetch dynamic suffix lists or external APIs.
- **Validation-Only Tuning:** Hyperparameters (regularization $C$) and decision thresholds must be selected strictly on validation data; test sets must be scored exactly once.

---

## 3. Considered Options

1. **Option A (Historical):** Random stratified splits (`StratifiedKFold` / naive 80/20).
2. **Option B (Exact Deduplication Only):** Remove exact text/URL duplicates and perform random stratified splits.
3. **Option C (Leakage-Aware Grouped Splits):** Near-duplicate clustering ($\ge 0.90$ cosine similarity) for text corpora, and registered-domain isolation (`tldextract`) for URL corpora, partitioned via `StratifiedGroupKFold(5)`.

---

## 4. Decision Outcome

**Chosen Option: Option C (Leakage-Aware Grouped Splits).**

### Implementation Architecture:

1. **Near-Duplicate Text Grouping:**
   - Text is normalized and vectorized using TF-IDF word n-grams (1–2).
   - Pairwise cosine similarity is computed in chunks.
   - Any pair of texts with cosine similarity $\ge 0.90$ is joined into an equivalence class using a disjoint-set (Union-Find) algorithm.
   - Text grouping operates strictly on text features without label inputs, preventing label leakage.
   - Instances belonging to the same cluster receive an identical group ID.

2. **Registered-Domain URL Grouping:**
   - URLs are parsed to extract the registered domain (effective top-level domain plus one level, e.g. `example.co.uk` from `sub.login.example.co.uk`).
   - Domain extraction uses `tldextract` pinned to `5.1.2` configured strictly with `suffix_list_urls=()`, enforcing offline operation using its bundled Public Suffix List snapshot.
   - All URLs sharing the same registered domain are assigned the same group ID.

3. **Grouped Stratified Partitioning:**
   - Data is split into 5 folds using `StratifiedGroupKFold(5, shuffle=True, random_state=42)`.
   - Fold 0 is designated as **TEST** (evaluated once at the very end).
   - Fold 1 is designated as **VALIDATION** (used to tune $C$ on PR-AUC and select decision thresholds).
   - Folds 2–4 are designated as **TRAIN**.
   - No group ID ever crosses fold boundaries.

---

## 5. Consequences

### Positive Consequences
- **True Generalization:** Reported metrics accurately measure the model's ability to classify novel scam templates and unseen domains.
- **Reproducibility:** Splits and metrics are strictly deterministic across seeds and hardware.
- **Zero Network Leakage:** `tldextract` operates 100% offline with zero external network queries.

### Trade-offs & Score Corrections
- **Score Correction:** Under rigorous grouped evaluation, test scores dropped across all models:
  - DIFrauD Job Scam F1 dropped from claimed `0.8346` to MEASURED `0.5931` (95% CI: `[0.4897, 0.6809]`).
  - Sentinel Multiclass macro-F1 dropped from claimed `0.9837` to MEASURED `0.9307`.
  - URL Char N-Gram F1 dropped from claimed `0.9524` to MEASURED `0.9287` (uncalibrated) / `0.9320` (calibrated).
  - Tabular HistGB F1 dropped from claimed `0.9680` to MEASURED `0.9421` (uncalibrated) / `0.9443` (calibrated).
- **Base-Rate Realities Exposed:** Re-weighting test metrics to a realistic 5% positive prevalence revealed high false alert volume on URL phishing (~94–112 false alerts per 1,000 legitimate links), triggering Gate 1 failure alerts and establishing clear engineering directions for low-prevalence threshold re-tuning.
