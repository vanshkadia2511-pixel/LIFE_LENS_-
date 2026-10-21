"""
LifeLens Omega - Full ML Pipeline
8-stage fraud detection pipeline for DIFrauD job_scams dataset.
Stages: Inspect -> Audit -> Clean -> Baseline -> Evaluate ->
        Feature Explanation -> Stronger Model -> Save
"""
import json, pathlib, textwrap, random, re, sys, time, warnings
import numpy as np
import pandas as pd
from collections import Counter

warnings.filterwarnings('ignore')
RANDOM_STATE = 42
random.seed(RANDOM_STATE)
np.random.seed(RANDOM_STATE)

TRAIN_PATH = pathlib.Path("datasets/train.jsonl")
TEST_PATH  = pathlib.Path("datasets/test.jsonl")
VAL_PATH   = pathlib.Path("datasets/validation.jsonl")
MODEL_DIR  = pathlib.Path("models")
MODEL_DIR.mkdir(exist_ok=True)


# ============================================================
def sep(title):
    print()
    print("=" * 65)
    print(f"  {title}")
    print("=" * 65)

def load_jsonl(p):
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return pd.DataFrame(rows)


# ============================================================
# STAGE 1 — INSPECT
# ============================================================
sep("STAGE 1 — DATASET INSPECTION")

df_train = load_jsonl(TRAIN_PATH)
df_test  = load_jsonl(TEST_PATH)
df_val   = load_jsonl(VAL_PATH)

print(f"\n  File              Rows     Size")
print(f"  train.jsonl    {len(df_train):>7,}   {TRAIN_PATH.stat().st_size//1024:,} KB")
print(f"  test.jsonl     {len(df_test):>7,}   {TEST_PATH.stat().st_size//1024:,} KB")
print(f"  validation.jsonl {len(df_val):>7,}  {VAL_PATH.stat().st_size//1024:,} KB")
print(f"  TOTAL          {len(df_train)+len(df_test)+len(df_val):>7,}")

print(f"\n  Columns: {list(df_train.columns)}")
print(f"  Dtypes:")
for col, dt in df_train.dtypes.items():
    print(f"    {col}: {dt}")

print("\n  Text length statistics (train):")
lengths = df_train["text"].str.len()
print(f"    min={lengths.min()}, median={lengths.median():.0f}, "
      f"mean={lengths.mean():.0f}, max={lengths.max()}")

print("\n  --- 3 LEGITIMATE examples ---")
legit_sample = df_train[df_train["label"] == 0].sample(3, random_state=42)
for _, row in legit_sample.iterrows():
    snip = textwrap.shorten(str(row["text"]), width=200, placeholder="...")
    print(f"  [label={row['label']}]  {snip}")
    print()

print("  --- 3 SCAM examples ---")
scam_sample = df_train[df_train["label"] == 1].sample(3, random_state=42)
for _, row in scam_sample.iterrows():
    snip = textwrap.shorten(str(row["text"]), width=200, placeholder="...")
    print(f"  [label={row['label']}]  {snip}")
    print()


# ============================================================
# STAGE 2 — AUDIT
# ============================================================
sep("STAGE 2 — RELIABILITY AUDIT")

problems = []

# Missing values
print("\n  [2a] MISSING VALUES")
for name, df in [("train", df_train), ("test", df_test)]:
    for col in ["text", "label"]:
        n = df[col].isna().sum()
        rate = n / len(df)
        status = "OK" if n == 0 else ("WARN" if rate < 0.05 else "SEVERE")
        print(f"    {name}.{col}: {n} missing ({rate:.2%})  [{status}]")
        if status == "SEVERE":
            problems.append(f"SEVERE: {name}.{col} has {rate:.1%} missing values")

# Duplicates within each split
print("\n  [2b] DUPLICATE ROWS (text+label)")
for name, df in [("train", df_train), ("test", df_test)]:
    dupes = df.duplicated(subset=["text", "label"]).sum()
    rate = dupes / len(df)
    status = "OK" if rate < 0.05 else ("WARN" if rate < 0.20 else "SEVERE")
    print(f"    {name}: {dupes} duplicates ({rate:.2%})  [{status}]")
    if rate >= 0.05:
        problems.append(f"WARN: {name} has {rate:.1%} duplicates")

# Text-only duplicates (same text, different label - contradictions)
print("\n  [2c] CONTRADICTORY ROWS (same text, different label)")
for name, df in [("train", df_train), ("test", df_test)]:
    text_labels = df.groupby("text")["label"].nunique()
    contradictions = (text_labels > 1).sum()
    print(f"    {name}: {contradictions} contradictory text samples  "
          f"[{'OK' if contradictions == 0 else 'WARN'}]")
    if contradictions > 0:
        problems.append(f"WARN: {name} has {contradictions} contradictory text labels")

# Class imbalance
print("\n  [2d] CLASS IMBALANCE")
for name, df in [("train", df_train), ("test", df_test)]:
    counts = df["label"].value_counts().sort_index()
    total  = len(df)
    majority_pct = counts.max() / total
    print(f"    {name}:")
    for lbl, cnt in counts.items():
        print(f"      label={lbl}: {cnt:,}  ({cnt/total:.1%})")
    if majority_pct >= 0.90:
        flag = "SEVERE"
        problems.append(f"SEVERE: {name} class imbalance — majority={majority_pct:.1%}")
    elif majority_pct >= 0.80:
        flag = "WARN"
    else:
        flag = "OK"
    print(f"      majority class = {majority_pct:.1%}  [{flag}]")

# TRAIN/TEST OVERLAP — data leakage check
print("\n  [2e] TRAIN/TEST TEXT OVERLAP (data-leakage check)")
train_texts = set(df_train["text"].str.strip())
test_texts  = set(df_test["text"].str.strip())
overlap     = train_texts & test_texts
overlap_pct = len(overlap) / len(test_texts) * 100
print(f"    Train unique texts : {len(train_texts):,}")
print(f"    Test  unique texts : {len(test_texts):,}")
print(f"    Overlapping texts  : {len(overlap):,}  ({overlap_pct:.2f}% of test)")
if len(overlap) > 0:
    problems.append(f"SEVERE: {len(overlap)} test texts exist in train — data leakage!")
    print(f"    STATUS: SEVERE — leaked rows will inflate test metrics!")
    print(f"    Example overlap texts:")
    for t in list(overlap)[:2]:
        print(f"      {textwrap.shorten(t, 120, placeholder='...')!r}")
else:
    print(f"    STATUS: OK — no overlap found")

# Verdict
print("\n  --- AUDIT VERDICT ---")
if not problems:
    print("  No severe problems found. Safe to proceed.")
else:
    for p in problems:
        icon = "🚨" if "SEVERE" in p else "⚠️ "
        print(f"  {icon} {p}")

print(f"\n  Total issues: {len(problems)} "
      f"(severe={sum(1 for p in problems if 'SEVERE' in p)}, "
      f"warn={sum(1 for p in problems if 'WARN' in p)})")

AUDIT_SEVERE = any("SEVERE" in p for p in problems)
print(f"\n  Decision: {'STOP — resolve SEVERE issues first' if AUDIT_SEVERE else 'PROCEED'}")
print("  NOTE: Class imbalance is real but mitigated via class_weight='balanced'")
print("        in the model. Accuracy will be ignored; F1-scam class is the metric.")


# ============================================================
# STAGE 3 — CLEAN AND PREPARE
# ============================================================
sep("STAGE 3 — CLEAN AND PREPARE")

def clean_text(text):
    """
    Minimal, signal-preserving cleaning.
    We deliberately keep: urgency phrases, payment keywords, caps words,
    special chars, email patterns — these are all scam signals.
    We only fix encoding artifacts and excessive whitespace.
    """
    text = str(text)
    # Decode common HTML entities
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&nbsp;", " ").replace("&#39;", "'").replace("&quot;", '"')
    # Normalize whitespace (collapse runs, strip leading/trailing)
    text = re.sub(r"\s+", " ", text).strip()
    return text

print("\n  [3a] Dropping duplicate rows from train...")
before = len(df_train)
df_train = df_train.drop_duplicates(subset=["text", "label"]).reset_index(drop=True)
print(f"    Dropped {before - len(df_train)} duplicate rows → {len(df_train):,} remain")

print("  [3b] Dropping rows with missing text or label...")
before = len(df_train)
df_train = df_train.dropna(subset=["text","label"]).reset_index(drop=True)
df_test  = df_test.dropna(subset=["text","label"]).reset_index(drop=True)
print(f"    Train: {before} → {len(df_train):,}")
print(f"    Test : {len(df_test):,} (no changes)")

print("  [3c] Applying minimal text cleaning...")
df_train["text_clean"] = df_train["text"].apply(clean_text)
df_test["text_clean"]  = df_test["text"].apply(clean_text)
df_val["text_clean"]   = df_val["text"].apply(clean_text)
print("    Done. Example cleaning diff:")
orig = df_train["text"].iloc[0][:100]
cln  = df_train["text_clean"].iloc[0][:100]
print(f"    BEFORE: {orig!r}")
print(f"    AFTER:  {cln!r}")

print("  [3d] Handling train/test overlap (if any)...")
if len(overlap) > 0:
    before = len(df_test)
    df_test = df_test[~df_test["text_clean"].isin(train_texts)].reset_index(drop=True)
    print(f"    Removed {before - len(df_test)} leaked rows from test → {len(df_test):,} remain")
else:
    print("    No overlap — nothing to remove.")

print("  [3e] Casting labels to int...")
df_train["label"] = df_train["label"].astype(int)
df_test["label"]  = df_test["label"].astype(int)

print(f"\n  Final split sizes:")
for name, df in [("train", df_train), ("test", df_test), ("val", df_val)]:
    counts = df["label"].value_counts().sort_index()
    print(f"    {name}: {len(df):,} rows  "
          f"(legit={counts.get(0,0):,}, scam={counts.get(1,0):,}, "
          f"scam%={counts.get(1,0)/len(df)*100:.1f}%)")

X_train = df_train["text_clean"].tolist()
y_train = df_train["label"].values
X_test  = df_test["text_clean"].tolist()
y_test  = df_test["label"].values
X_val   = df_val["text_clean"].tolist()
y_val   = df_val["label"].values


# ============================================================
# STAGE 4 — BASELINE MODEL
# ============================================================
sep("STAGE 4 — BASELINE: TF-IDF + LOGISTIC REGRESSION")

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    classification_report, confusion_matrix, f1_score, precision_score,
    recall_score, roc_auc_score, average_precision_score
)

print("\n  Fitting TF-IDF (train only) ...")
# TF-IDF: bigrams, 80k features, sublinear TF
# Fit ONLY on training data — strict featurization ordering
baseline = Pipeline([
    ("tfidf", TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=80_000,
        sublinear_tf=True,
        min_df=2,
        strip_accents="unicode",
        analyzer="word",
    )),
    ("clf", LogisticRegression(
        class_weight="balanced",
        C=1.0,
        max_iter=1000,
        solver="lbfgs",
        random_state=RANDOM_STATE,
    )),
])

t0 = time.perf_counter()
baseline.fit(X_train, y_train)
train_time = time.perf_counter() - t0
print(f"  Training time: {train_time:.2f}s")

t0 = time.perf_counter()
y_pred_base   = baseline.predict(X_test)
y_prob_base   = baseline.predict_proba(X_test)[:, 1]
infer_time = time.perf_counter() - t0
print(f"  Inference:     {infer_time*1000:.1f}ms total  "
      f"({infer_time/len(X_test)*1000:.3f}ms/sample)")


# ============================================================
# STAGE 5 — EVALUATE BASELINE
# ============================================================
sep("STAGE 5 — BASELINE EVALUATION (on held-out test set)")

cm_base = confusion_matrix(y_test, y_pred_base)
cr_base = classification_report(y_test, y_pred_base,
                                target_names=["legitimate", "scam"],
                                digits=4, zero_division=0)

f1_scam   = f1_score(y_test, y_pred_base, pos_label=1, zero_division=0)
prec_scam = precision_score(y_test, y_pred_base, pos_label=1, zero_division=0)
rec_scam  = recall_score(y_test, y_pred_base, pos_label=1, zero_division=0)
f1_macro  = f1_score(y_test, y_pred_base, average="macro", zero_division=0)
roc_auc   = roc_auc_score(y_test, y_prob_base)
avg_prec  = average_precision_score(y_test, y_prob_base)

print(f"\n  Classification Report:")
print(cr_base)

print(f"  Confusion Matrix (rows=actual, cols=predicted):")
print(f"                   pred=legit  pred=scam")
print(f"    actual=legit     {cm_base[0][0]:>8}  {cm_base[0][1]:>9}")
print(f"    actual=scam      {cm_base[1][0]:>8}  {cm_base[1][1]:>9}")
print()
tn, fp, fn, tp = cm_base.ravel()
print(f"    True  Positives (scams caught)          : {tp}")
print(f"    False Positives (legit jobs flagged)    : {fp}")
print(f"    False Negatives (scams missed!)         : {fn}")
print(f"    True  Negatives (legit correctly passed): {tn}")

print(f"\n  === KEY METRICS FOR SCAM CLASS ===")
print(f"  Precision (scam) : {prec_scam:.4f}")
print(f"  Recall    (scam) : {rec_scam:.4f}")
print(f"  F1        (scam) : {f1_scam:.4f}")
print(f"  F1-macro         : {f1_macro:.4f}")
print(f"  ROC-AUC          : {roc_auc:.4f}")
print(f"  Avg Precision    : {avg_prec:.4f}")
print(f"\n  IMPORTANT: Accuracy is {(tn+tp)/(tn+fp+fn+tp):.1%} but is MISLEADING")
print(f"  because a naive 'always-legit' classifier also gets "
      f"{tn/(tn+fp+fn+tp):.1%} accuracy.")
print(f"  The scam F1 ({f1_scam:.4f}) is the metric that matters.")

BASELINE_GOOD = f1_scam >= 0.55
print(f"\n  Baseline quality: {'GOOD — proceed to stronger model' if BASELINE_GOOD else 'WEAK — diagnose before escalating'}")


# ============================================================
# STAGE 6 — FEATURE EXPLANATION
# ============================================================
sep("STAGE 6 — WHAT DID THE MODEL ACTUALLY LEARN?")

tfidf_vocab  = baseline.named_steps["tfidf"].get_feature_names_out()
coef         = baseline.named_steps["clf"].coef_[0]  # shape: (n_features,)
top_n = 25

# Most scam-predictive features (highest coefficient)
scam_idx  = np.argsort(coef)[-top_n:][::-1]
legit_idx = np.argsort(coef)[:top_n]

print(f"\n  Top {top_n} features PREDICTING SCAM (label=1):")
print(f"  {'Feature':<30} {'Weight':>8}")
print(f"  {'-'*40}")
for i in scam_idx:
    print(f"  {tfidf_vocab[i]:<30} {coef[i]:>8.4f}")

print(f"\n  Top {top_n} features PREDICTING LEGITIMATE (label=0):")
print(f"  {'Feature':<30} {'Weight':>8}")
print(f"  {'-'*40}")
for i in legit_idx:
    print(f"  {tfidf_vocab[i]:<30} {coef[i]:>8.4f}")

print("\n  === SANITY-CHECK QUESTIONS ===")
print("  Are scam features real signals? Look for:")
print("  - Payment / upfront fee words: 'fee', 'payment', 'deposit', 'transfer'")
print("  - Urgency: 'urgent', 'immediately', 'limited'")
print("  - Suspicious contact: 'whatsapp', 'telegram', 'gmail'")
print("  - Credential asks: 'passport', 'ssn', 'bank account'")
print("  If you see generic English stop-words or job-unrelated tokens, that")
print("  would suggest the model is fitting noise.")


# ============================================================
# STAGE 7 — STRONGER MODEL
# ============================================================
sep("STAGE 7 — STRONGER MODEL: TF-IDF + GRADIENT BOOSTING (HistGB)")

if not BASELINE_GOOD:
    print("  Skipping: baseline did not meet quality threshold.")
    sys.exit(0)

print("  Model: HistGradientBoostingClassifier (sklearn's fastest tree ensemble)")
print("  Strategy: TF-IDF features → SVD(200 dims) → HistGradientBoosting")
print("  Note: HistGB natively handles class imbalance via class_weight-equivalent")
print()

from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder

# Compute class weight ratio
n_legit = (y_train == 0).sum()
n_scam  = (y_train == 1).sum()
pos_weight = n_legit / n_scam
print(f"  Class ratio (legit/scam) = {pos_weight:.1f}x → using as sample_weight")

# Build TF-IDF + SVD separately (fit on train only)
tfidf_strong = TfidfVectorizer(
    ngram_range=(1, 2), max_features=80_000,
    sublinear_tf=True, min_df=2, strip_accents="unicode",
)
svd = TruncatedSVD(n_components=200, random_state=RANDOM_STATE)

print("  Fitting TF-IDF + SVD on train ...")
t0 = time.perf_counter()
X_tr_tfidf  = tfidf_strong.fit_transform(X_train)
X_tr_svd    = svd.fit_transform(X_tr_tfidf)
X_te_svd    = svd.transform(tfidf_strong.transform(X_test))
print(f"  TF-IDF + SVD done ({time.perf_counter()-t0:.1f}s), "
      f"shape: {X_tr_svd.shape}")

# Sample weights to handle imbalance
sample_weights = np.where(y_train == 1, pos_weight, 1.0)

hgb = HistGradientBoostingClassifier(
    max_iter=300,
    learning_rate=0.05,
    max_leaf_nodes=63,
    random_state=RANDOM_STATE,
)

print("  Training HistGradientBoostingClassifier ...")
t0 = time.perf_counter()
hgb.fit(X_tr_svd, y_train, sample_weight=sample_weights)
train_time_hgb = time.perf_counter() - t0
print(f"  Training time: {train_time_hgb:.2f}s")

t0 = time.perf_counter()
y_pred_hgb  = hgb.predict(X_te_svd)
y_prob_hgb  = hgb.predict_proba(X_te_svd)[:, 1]
infer_time_hgb = time.perf_counter() - t0

cm_hgb = confusion_matrix(y_test, y_pred_hgb)
cr_hgb = classification_report(y_test, y_pred_hgb,
                               target_names=["legitimate", "scam"],
                               digits=4, zero_division=0)

f1_scam_hgb   = f1_score(y_test, y_pred_hgb, pos_label=1, zero_division=0)
prec_scam_hgb = precision_score(y_test, y_pred_hgb, pos_label=1, zero_division=0)
rec_scam_hgb  = recall_score(y_test, y_pred_hgb, pos_label=1, zero_division=0)
f1_macro_hgb  = f1_score(y_test, y_pred_hgb, average="macro", zero_division=0)
roc_auc_hgb   = roc_auc_score(y_test, y_prob_hgb)
avg_prec_hgb  = average_precision_score(y_test, y_prob_hgb)

print(f"\n  Classification Report:")
print(cr_hgb)

print(f"  Confusion Matrix:")
print(f"                   pred=legit  pred=scam")
print(f"    actual=legit     {cm_hgb[0][0]:>8}  {cm_hgb[0][1]:>9}")
print(f"    actual=scam      {cm_hgb[1][0]:>8}  {cm_hgb[1][1]:>9}")
tn_h, fp_h, fn_h, tp_h = cm_hgb.ravel()
print(f"\n    TP (scams caught)          : {tp_h}")
print(f"    FP (legit jobs flagged)    : {fp_h}")
print(f"    FN (scams missed)          : {fn_h}")
print(f"    TN (legit correctly passed): {tn_h}")

print(f"\n  === KEY METRICS FOR SCAM CLASS ===")
print(f"  Precision (scam) : {prec_scam_hgb:.4f}")
print(f"  Recall    (scam) : {rec_scam_hgb:.4f}")
print(f"  F1        (scam) : {f1_scam_hgb:.4f}")
print(f"  F1-macro         : {f1_macro_hgb:.4f}")
print(f"  ROC-AUC          : {roc_auc_hgb:.4f}")
print(f"  Avg Precision    : {avg_prec_hgb:.4f}")

print(f"\n  === COMPARISON: BASELINE vs STRONGER MODEL ===")
print(f"  {'Metric':<25} {'LogReg (baseline)':>18} {'HistGB (stronger)':>18} {'Delta':>8}")
print(f"  {'-'*71}")
metrics = [
    ("F1-scam (KEY)", f1_scam, f1_scam_hgb),
    ("Precision-scam", prec_scam, prec_scam_hgb),
    ("Recall-scam", rec_scam, rec_scam_hgb),
    ("F1-macro", f1_macro, f1_macro_hgb),
    ("ROC-AUC", roc_auc, roc_auc_hgb),
    ("Avg Precision", avg_prec, avg_prec_hgb),
]
for name, v_base, v_hgb in metrics:
    delta = v_hgb - v_base
    arrow = "+" if delta >= 0 else ""
    print(f"  {name:<25} {v_base:>18.4f} {v_hgb:>18.4f} {arrow}{delta:>7.4f}")

BEST_IS_HGB = f1_scam_hgb > f1_scam
print(f"\n  Winner: {'HistGB' if BEST_IS_HGB else 'LogReg (baseline was better!)'}")


# ============================================================
# STAGE 8 — SAVE FINAL MODEL
# ============================================================
sep("STAGE 8 — SAVE FINAL MODEL")

import joblib

if BEST_IS_HGB:
    # Save HistGB components separately (pipeline with SVD isn't a single Pipeline obj)
    final_bundle = {
        "model_name": "HistGradientBoosting (TF-IDF + SVD)",
        "tfidf": tfidf_strong,
        "svd": svd,
        "clf": hgb,
        "label_map": {0: "legitimate", 1: "scam"},
        "f1_scam_benchmark": f1_scam_hgb,
        "train_rows": len(X_train),
        "test_rows": len(X_test),
    }
    final_path = MODEL_DIR / "final_fraud_model.joblib"
else:
    final_bundle = {
        "model_name": "LogisticRegression (TF-IDF)",
        "pipeline": baseline,
        "label_map": {0: "legitimate", 1: "scam"},
        "f1_scam_benchmark": f1_scam,
        "train_rows": len(X_train),
        "test_rows": len(X_test),
    }
    final_path = MODEL_DIR / "final_fraud_model.joblib"

joblib.dump(final_bundle, final_path, compress=3)
size_mb = final_path.stat().st_size / (1024*1024)
print(f"\n  Saved: {final_path.resolve()}")
print(f"  Size:  {size_mb:.1f} MB")

# Print exact loading + inference instructions
print(f"""
  === HOW TO LOAD AND USE THE MODEL ===

  import joblib
  bundle = joblib.load(r"{final_path.resolve()}")
""")

if BEST_IS_HGB:
    print("""  # Extract components
  tfidf  = bundle["tfidf"]
  svd    = bundle["svd"]
  clf    = bundle["clf"]
  labels = bundle["label_map"]   # {0: "legitimate", 1: "scam"}

  # Predict on new texts
  new_texts = [
      "Urgently hiring! Work from home. Send your bank account for deposit.",
      "Software Engineer at Google, 5+ years Python required, competitive salary.",
  ]
  X = svd.transform(tfidf.transform(new_texts))
  predictions  = clf.predict(X)           # [0, 1] etc.
  probabilities = clf.predict_proba(X)[:, 1]  # scam probability

  for text, pred, prob in zip(new_texts, predictions, probabilities):
      label = labels[pred]
      print(f"{label}  (scam_prob={prob:.3f})  {text[:60]}")
""")
else:
    print("""  # Extract pipeline
  pipe   = bundle["pipeline"]
  labels = bundle["label_map"]   # {0: "legitimate", 1: "scam"}

  # Predict on new texts
  new_texts = [
      "Urgently hiring! Work from home. Send your bank account for deposit.",
      "Software Engineer at Google, 5+ years Python required.",
  ]
  predictions   = pipe.predict(new_texts)
  probabilities = pipe.predict_proba(new_texts)[:, 1]

  for text, pred, prob in zip(new_texts, predictions, probabilities):
      label = labels[pred]
      print(f"{label}  (scam_prob={prob:.3f})  {text[:60]}")
""")

print("\n  Also saving baseline for reference comparison...")
joblib.dump({"model_name": "LogReg baseline", "pipeline": baseline,
             "f1_scam_benchmark": f1_scam}, MODEL_DIR / "baseline_logreg.joblib", compress=3)
print(f"  Saved: {(MODEL_DIR / 'baseline_logreg.joblib').resolve()}")

print()
print("=" * 65)
print("  PIPELINE COMPLETE")
print("=" * 65)
