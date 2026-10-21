"""
LifeLens Ω — DIFrauD Dataset Downloader
Downloads train.jsonl, test.jsonl, validation.jsonl from HuggingFace
into ./datasets/ without requiring the `datasets` library.

Source: huggingface.co/datasets/redasers/difraud
"""
from __future__ import annotations

import urllib.request
import urllib.error
import sys
from pathlib import Path

# HuggingFace raw file URLs for redasers/difraud
BASE_URL = "https://huggingface.co/datasets/redasers/difraud/resolve/main"

FILES = {
    "train.jsonl":      f"{BASE_URL}/train.jsonl",
    "test.jsonl":       f"{BASE_URL}/test.jsonl",
    "validation.jsonl": f"{BASE_URL}/validation.jsonl",
}

# Fallback paths (parquet) if JSONL is not available
PARQUET_FILES = {
    "train.parquet":      f"{BASE_URL}/data/train-00000-of-00001.parquet",
    "test.parquet":       f"{BASE_URL}/data/test-00000-of-00001.parquet",
    "validation.parquet": f"{BASE_URL}/data/validation-00000-of-00001.parquet",
}


def download_file(url: str, dest: Path) -> bool:
    if dest.exists():
        print(f"  [SKIP] Already exists: {dest}")
        return True
    print(f"  Downloading {dest.name} ...")
    try:
        urllib.request.urlretrieve(url, dest)
        size_kb = dest.stat().st_size / 1024
        print(f"  [OK]   {dest.name}  ({size_kb:.1f} KB)")
        return True
    except urllib.error.HTTPError as e:
        print(f"  [FAIL] HTTP {e.code}: {url}")
        return False
    except Exception as e:
        print(f"  [FAIL] {e}: {url}")
        return False


def convert_parquet_to_jsonl(parquet_path: Path, jsonl_path: Path) -> bool:
    """Convert a parquet file to JSONL format."""
    try:
        import pandas as pd
        df = pd.read_parquet(parquet_path)
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for _, row in df.iterrows():
                import json
                f.write(json.dumps(row.to_dict()) + "\n")
        print(f"  [CONVERTED] {parquet_path.name} → {jsonl_path.name}  ({len(df):,} rows)")
        return True
    except ImportError:
        print("  [ERROR] pandas not installed. Cannot convert parquet.")
        return False
    except Exception as e:
        print(f"  [ERROR] Conversion failed: {e}")
        return False


def main() -> None:
    out_dir = Path("datasets")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  LIFELENS Ω — DIFrauD Dataset Download")
    print("=" * 60)
    print(f"  Source : {BASE_URL}")
    print(f"  Target : {out_dir.resolve()}")
    print()

    # Try JSONL first
    all_ok = True
    for fname, url in FILES.items():
        dest = out_dir / fname
        if not download_file(url, dest):
            all_ok = False

    if not all_ok:
        # Fallback: try parquet and convert
        print("\n  JSONL download failed for some files. Trying parquet fallback...")
        for fname, url in PARQUET_FILES.items():
            stem = fname.replace(".parquet", "")
            dest_parquet = out_dir / fname
            dest_jsonl   = out_dir / f"{stem}.jsonl"
            if dest_jsonl.exists():
                print(f"  [SKIP] JSONL already exists: {dest_jsonl}")
                continue
            if download_file(url, dest_parquet):
                convert_parquet_to_jsonl(dest_parquet, dest_jsonl)
                dest_parquet.unlink()  # remove parquet after conversion
            else:
                print(f"\n  [ERROR] Could not download {fname}.")
                print("  Manual download instructions:")
                print(f"    Visit: https://huggingface.co/datasets/redasers/difraud/tree/main")
                print(f"    Download the split files and place them as:")
                print(f"    datasets/train.jsonl, datasets/test.jsonl, datasets/validation.jsonl")
                sys.exit(1)

    print("\n  ✅ All dataset files ready.")
    print(f"  Directory: {out_dir.resolve()}")

    # Quick sanity peek
    for fname in ["train.jsonl", "test.jsonl", "validation.jsonl"]:
        p = out_dir / fname
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
            print(f"    {fname}: {len(lines):,} records")


if __name__ == "__main__":
    main()
