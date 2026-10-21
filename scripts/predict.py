import argparse
import sys
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import joblib

def main():
    parser = argparse.ArgumentParser(description="LifeLens Scam & Phishing Detection CLI")
    parser.add_argument("--text", type=str, help="Text (job posting / SMS / email) to classify")
    parser.add_argument("--url",  type=str, help="URL to classify as Phishing vs Legitimate")
    parser.add_argument("--model", type=str, default="both", choices=["binary", "multiclass", "both"], help="Text model type")
    args = parser.parse_args()

    # 1. URL Phishing Detector
    if args.url:
        print("=" * 60)
        print("  LIFELENS - URL PHISHING DETECTION INFERENCE")
        print("=" * 60)
        print(f"  Input URL: \"{args.url}\"\n")
        url_model_path = Path("models/phishing_url/url_ngram_model.joblib")
        if url_model_path.exists():
            bundle = joblib.load(url_model_path)
            pipe = bundle["pipeline"]
            pred = pipe.predict([args.url])[0]
            prob = pipe.predict_proba([args.url])[0][1]
            status = "🚨 PHISHING URL (1)" if pred == 1 else "✅ LEGITIMATE DOMAIN (0)"
            print(f"  [Phishing URL Detector]      Verdict:      {status}")
            print(f"  [Phishing Risk Score]        Probability:  {prob:.1%}")
        else:
            print(f"  Model not found at {url_model_path}")
        print("=" * 60)
        if not args.text:
            return

    # 2. Text Scam Classification
    sample_job_scam = "Urgent hiring! Immediate start data entry assistant. Earn $500/day working from home. No interview needed, send registration fee via Telegram to start."
    text_to_test = args.text if args.text else sample_job_scam

    print("\n" + "=" * 60)
    print("  LIFELENS - TEXT SCAM DETECTION INFERENCE")
    print("=" * 60)
    print(f"  Input Text: \"{text_to_test}\"\n")

    # Binary Job Scam Detector
    if args.model in ["binary", "both"]:
        job_model_path = Path("models/best_model.joblib")
        if job_model_path.exists():
            bundle = joblib.load(job_model_path)
            pipe = bundle["pipeline"]
            pred = pipe.predict([text_to_test])[0]
            label_str = "🚨 SCAM (1)" if str(pred) == "1" else "✅ LEGITIMATE (0)"
            print(f"  [Binary Job Scam Model]      Prediction:   {label_str}")
        else:
            print(f"  [Binary Job Scam Model]      Model file not found at {job_model_path}")

    # Multiclass Fraud Classifier
    if args.model in ["multiclass", "both"]:
        multi_model_path = Path("models/multiclass/best_model.joblib")
        if multi_model_path.exists():
            bundle = joblib.load(multi_model_path)
            pipe = bundle["pipeline"]
            classes = bundle.get("classes", [])
            pred = pipe.predict([text_to_test])[0]
            category = classes[pred] if (isinstance(pred, (int, np.integer)) and pred < len(classes)) else pred
            print(f"  [Multiclass Fraud Model]     Category:     🏷️ {category}")
        else:
            print(f"  [Multiclass Fraud Model]     Model file not found at {multi_model_path}")

    print("=" * 60)

if __name__ == "__main__":
    main()
