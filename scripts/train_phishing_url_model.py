"""
LifeLens Ω — Phishing URL & Domain Classifier Trainer
Trained on CompPhish (Mendeley Data: Mapping_File & All_Features_threshold90)
"""
import sys
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.metrics import classification_report, confusion_matrix, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


def main():
    data_path = Path("datasets/phishing_urls/compphish/all_features_threshold90.csv")
    if not data_path.exists():
        print(f"Error: {data_path} not found.")
        sys.exit(1)

    print("=" * 60)
    print("  LIFELENS - PHISHING URL MODEL TRAINING")
    print("=" * 60)
    print(f"  Dataset: {data_path}")

    df = pd.read_csv(data_path)
    print(f"  Total records: {len(df):,}")
    print(f"  Class balance: {dict(df['label'].value_counts())}")

    # Train / Test split (80/20 stratified)
    train_df, test_df = train_test_split(df, test_size=0.2, stratify=df["label"], random_state=42)
    print(f"  Train samples: {len(train_df):,} | Test samples: {len(test_df):,}\n")

    # -------------------------------------------------------------
    # 1. URL Char N-Gram Pipeline (Raw URL Text Detector)
    # -------------------------------------------------------------
    print("-" * 60)
    print("  1. Training Raw URL Char N-Gram Detector (No HTML needed)")
    print("-" * 60)

    url_pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            analyzer="char",
            ngram_range=(3, 5),
            max_features=40000,
            sublinear_tf=True
        )),
        ("clf", LogisticRegression(
            C=4.0,
            max_iter=1000,
            class_weight="balanced",
            random_state=42
        ))
    ])

    url_pipeline.fit(train_df["url"].astype(str), train_df["label"])
    y_pred_url = url_pipeline.predict(test_df["url"].astype(str))
    y_prob_url = url_pipeline.predict_proba(test_df["url"].astype(str))[:, 1]

    f1_url = f1_score(test_df["label"], y_pred_url)
    auc_url = roc_auc_score(test_df["label"], y_prob_url)

    print(f"  F1 Score (Phishing): {f1_url:.4f}")
    print(f"  ROC-AUC:             {auc_url:.4f}")
    print("\n  Classification Report (URL N-Gram):")
    print(classification_report(test_df["label"], y_pred_url, target_names=["Legitimate", "Phishing"], digits=4))

    cm_url = confusion_matrix(test_df["label"], y_pred_url)
    print("  Confusion Matrix:")
    print(f"    Legit    (Actual 0): {cm_url[0][0]:>5} correct, {cm_url[0][1]:>4} false alarms")
    print(f"    Phishing (Actual 1): {cm_url[1][1]:>5} caught,  {cm_url[1][0]:>4} missed")

    # -------------------------------------------------------------
    # 2. Structural & Lexical Feature Classifier (Tabular HistGB)
    # -------------------------------------------------------------
    print("\n" + "-" * 60)
    print("  2. Training Structural / Lexical Feature Classifier (70 Features)")
    print("-" * 60)

    feature_cols = [c for c in df.columns if c not in ["serial_number", "url", "label"]]
    X_train_num = train_df[feature_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
    X_test_num = test_df[feature_cols].apply(pd.to_numeric, errors="coerce").fillna(0)

    tab_clf = HistGradientBoostingClassifier(random_state=42, max_iter=200)
    tab_clf.fit(X_train_num, train_df["label"])

    y_pred_tab = tab_clf.predict(X_test_num)
    y_prob_tab = tab_clf.predict_proba(X_test_num)[:, 1]

    f1_tab = f1_score(test_df["label"], y_pred_tab)
    auc_tab = roc_auc_score(test_df["label"], y_prob_tab)

    print(f"  F1 Score (Phishing): {f1_tab:.4f}")
    print(f"  ROC-AUC:             {auc_tab:.4f}")
    print("\n  Classification Report (Tabular Features):")
    print(classification_report(test_df["label"], y_pred_tab, target_names=["Legitimate", "Phishing"], digits=4))

    # Save models
    out_dir = Path("models/phishing_url")
    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": url_pipeline, "classes": ["Legitimate", "Phishing"], "f1": f1_url, "auc": auc_url}, out_dir / "url_ngram_model.joblib")
    joblib.dump({"model": tab_clf, "feature_names": feature_cols, "classes": ["Legitimate", "Phishing"], "f1": f1_tab, "auc": auc_tab}, out_dir / "tabular_features_model.joblib")
    print(f"\n  [SAVED] Models saved to: {out_dir.resolve()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
