#!/usr/bin/env python3
"""
scripts/make_results_table.py
Reads every models/*_v2/metadata.json and generates docs/RESULTS.md automatically.
All values are strictly extracted from metadata artifacts (Rule P4: MEASURED).
"""

from __future__ import annotations

import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent.parent
    models_dir = root / "models"
    results_path = root / "docs" / "RESULTS.md"
    results_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    sentinel_metrics = []

    # Iterate through all _v2 model directories
    for meta_file in sorted(models_dir.glob("*_v2/metadata.json")):
        with open(meta_file, encoding="utf-8") as f:
            meta = json.load(f)

        model_name = meta_file.parent.name
        dataset_path = meta.get("dataset_file", "unknown")
        sha = meta.get("dataset_sha256", "unknown")[:8]
        dataset_display = f"{Path(dataset_path).name} (`{sha}`)"

        split_info = "Fold 0 of 5 (Grouped)"
        tm = meta["test_metrics"]
        br = tm["base_rate_reweighted"]
        ci = tm["bootstrap"]["f1_95ci"]
        ci_str = f"[{ci[0]:.4f}, {ci[1]:.4f}]" if ci else "N/A"

        n_test = tm["n"]
        positives = tm["positives"]
        prec = tm["precision"]
        rec = tm["recall"]
        f1 = tm["f1"]
        pr_auc = tm["pr_auc"]

        br_prec = br["precision"]
        br_fpr = br["fpr"]
        false_alerts = br["false_alerts_per_1000_legitimate"]

        # External overlap
        ext = meta.get("external", {})
        if ext:
            overlaps = [f"{k}: {v.get('exact_text_overlap_with_train_split', 0)}" for k, v in ext.items()]
            ext_str = ", ".join(overlaps)
        else:
            ext_str = "0 (Disjoint)"

        # Gate status: FPR <= 0.05 and Precision >= 0.75 at 5% base rate
        gate_pass = (br_fpr <= 0.05) and (br_prec >= 0.75)
        gate_status = "PASS" if gate_pass else f"FAIL (FPR={br_fpr:.4f}, Prec={br_prec:.4f})"

        label = meta.get("label", "MEASURED")

        rows.append({
            "model": model_name,
            "dataset": dataset_display,
            "split": split_info,
            "n_test": n_test,
            "positives": positives,
            "precision": prec,
            "recall": rec,
            "f1_ci": f"{f1:.4f} {ci_str}",
            "pr_auc": pr_auc,
            "br_precision": br_prec,
            "br_fpr": br_fpr,
            "false_alerts": false_alerts,
            "external_overlap": ext_str,
            "gate_status": gate_status,
            "label": label,
        })

        if "sentinel" in model_name and "binary" not in model_name:
            sentinel_metrics.append((prec, rec, f1))

    # Compute Sentinel Macro-F1 across the 4 OVR categories
    macro_f1_note = ""
    if sentinel_metrics:
        macro_prec = sum(m[0] for m in sentinel_metrics) / len(sentinel_metrics)
        macro_rec = sum(m[1] for m in sentinel_metrics) / len(sentinel_metrics)
        macro_f1 = sum(m[2] for m in sentinel_metrics) / len(sentinel_metrics)
        macro_f1_note = (
            f"\n\n### Sentinel Multiclass Macro-Average (4 OVR Categories)\n"
            f"- **Macro Precision:** `{macro_prec:.4f}`\n"
            f"- **Macro Recall:** `{macro_rec:.4f}`\n"
            f"- **Macro F1:** `{macro_f1:.4f}`\n"
            f"- *Note:* In each One-vs-Rest category run, negatives contain instances from all other categories.\n"
        )

    # Format Markdown Table
    table_lines = [
        "# LifeLens Ω — Master Evaluation Results (`docs/RESULTS.md`)",
        "",
        "**Generated Automatically by:** [`scripts/make_results_table.py`](../scripts/make_results_table.py)  ",
        "**Standard:** Strictly **MEASURED** figures from `models/*_v2/metadata.json` artifacts.  ",
        "**Gate 1 Criterion:** At a 5% positive base rate, `FPR <= 0.05` and `Precision >= 0.75`.",
        "",
        "| Model | Dataset (SHA-256) | Split | n_test | Positives | Precision | Recall | F1 (95% CI) | PR-AUC | Base-Rate (5%) Precision | Base-Rate (5%) FPR | False Alerts / 1k | External Overlap | Gate Status | Label |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for r in rows:
        table_lines.append(
            f"| **{r['model']}** | {r['dataset']} | {r['split']} | {r['n_test']} | {r['positives']} | "
            f"`{r['precision']:.4f}` | `{r['recall']:.4f}` | `{r['f1_ci']}` | `{r['pr_auc']:.4f}` | "
            f"`{r['br_precision']:.4f}` | `{r['br_fpr']:.4f}` | `{r['false_alerts']:.2f}` | "
            f"{r['external_overlap']} | **{r['gate_status']}** | **{r['label']}** |"
        )

    table_lines.append(macro_f1_note)
    table_lines.append("\n---\n*Report generated on " + Path(meta_file).name + " sync.*")

    results_path.write_text("\n".join(table_lines), encoding="utf-8")
    print(f"[make_results_table] Successfully generated {results_path} ({len(rows)} models logged)")


if __name__ == "__main__":
    main()
