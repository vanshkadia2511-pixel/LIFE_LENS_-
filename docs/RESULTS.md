# LifeLens Ω — Master Evaluation Results (`docs/RESULTS.md`)

**Generated Automatically by:** [`scripts/make_results_table.py`](../scripts/make_results_table.py)  
**Standard:** Strictly **MEASURED** figures from `models/*_v2/metadata.json` artifacts.  
**Gate 1 Criterion:** At a 5% positive base rate, `FPR <= 0.05` and `Precision >= 0.75`.

| Model | Dataset (SHA-256) | Split | n_test | Positives | Precision | Recall | F1 (95% CI) | PR-AUC | Base-Rate (5%) Precision | Base-Rate (5%) FPR | False Alerts / 1k | External Overlap | Gate Status | Label |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **job_scam_v2** | train.jsonl (`ed64c355`) | Fold 0 of 5 (Grouped) | 2286 | 96 | `0.8776` | `0.4479` | `0.5931 [0.4897, 0.6809]` | `0.6461` | `0.8959` | `0.0027` | `2.74` | test.jsonl: 1 | **PASS** | **MEASURED** |
| **sentinel_bank_phishing_v2** | sentinel_dataset_multiclass.csv (`ebdec640`) | Fold 0 of 5 (Grouped) | 2801 | 375 | `0.8188` | `1.0000` | `0.9004 [0.8793, 0.9207]` | `0.9965` | `0.6060` | `0.0342` | `34.21` | 0 (Disjoint) | **FAIL (FPR=0.0342, Prec=0.6060)** | **MEASURED** |
| **sentinel_binary_fraud_v2** | sentinel_dataset_multiclass.csv (`ebdec640`) | Fold 0 of 5 (Grouped) | 2800 | 1680 | `0.8750` | `1.0000` | `0.9333 [0.9247, 0.9415]` | `1.0000` | `0.1972` | `0.2143` | `214.29` | 0 (Disjoint) | **FAIL (FPR=0.2143, Prec=0.1972)** | **MEASURED** |
| **sentinel_financial_fraud_v2** | sentinel_dataset_multiclass.csv (`ebdec640`) | Fold 0 of 5 (Grouped) | 2800 | 616 | `0.9981` | `0.8328` | `0.9080 [0.8904, 0.9241]` | `0.9927` | `0.9897` | `0.0005` | `0.46` | 0 (Disjoint) | **PASS** | **MEASURED** |
| **sentinel_government_impersonation_v2** | sentinel_dataset_multiclass.csv (`ebdec640`) | Fold 0 of 5 (Grouped) | 2802 | 582 | `0.9291` | `0.9003` | `0.9145 [0.8952, 0.9307]` | `0.9407` | `0.7245` | `0.0180` | `18.02` | 0 (Disjoint) | **FAIL (FPR=0.0180, Prec=0.7245)** | **MEASURED** |
| **sentinel_romance_sextortion_v2** | sentinel_dataset_multiclass.csv (`ebdec640`) | Fold 0 of 5 (Grouped) | 2800 | 108 | `1.0000` | `1.0000` | `1.0000 [1.0000, 1.0000]` | `1.0000` | `1.0000` | `0.0000` | `0.00` | 0 (Disjoint) | **PASS** | **MEASURED** |
| **url_char_ngram_calibrated_v2** | all_features_threshold90.csv (`2ae569c2`) | Fold 0 of 5 (Grouped) | 3070 | 1439 | `0.8920` | `0.9757` | `0.9320 [0.9232, 0.9411]` | `0.9872` | `0.3301` | `0.1042` | `104.23` | 0 (Disjoint) | **FAIL (FPR=0.1042, Prec=0.3301)** | **MEASURED** |
| **url_char_ngram_v2** | all_features_threshold90.csv (`2ae569c2`) | Fold 0 of 5 (Grouped) | 3070 | 1439 | `0.8848` | `0.9771` | `0.9287 [0.9198, 0.9382]` | `0.9871` | `0.3143` | `0.1122` | `112.20` | 0 (Disjoint) | **FAIL (FPR=0.1122, Prec=0.3143)** | **MEASURED** |
| **url_tabular_calibrated_v2** | all_features_threshold90.csv (`2ae569c2`) | Fold 0 of 5 (Grouped) | 3070 | 1439 | `0.9030` | `0.9896` | `0.9443 [0.9356, 0.9524]` | `0.9962` | `0.3570` | `0.0938` | `93.81` | 0 (Disjoint) | **FAIL (FPR=0.0938, Prec=0.3570)** | **MEASURED** |
| **url_tabular_v2** | all_features_threshold90.csv (`2ae569c2`) | Fold 0 of 5 (Grouped) | 3070 | 1439 | `0.8985` | `0.9903` | `0.9421 [0.9340, 0.9502]` | `0.9961` | `0.3455` | `0.0987` | `98.71` | 0 (Disjoint) | **FAIL (FPR=0.0987, Prec=0.3455)** | **MEASURED** |


### Sentinel Multiclass Macro-Average (4 OVR Categories)
- **Macro Precision:** `0.9365`
- **Macro Recall:** `0.9333`
- **Macro F1:** `0.9307`
- *Note:* In each One-vs-Rest category run, negatives contain instances from all other categories.


---
*Report generated on metadata.json sync.*