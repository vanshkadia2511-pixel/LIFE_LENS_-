"""
LifeLens Ω — Phase K: Secret Scanning Pre-Commit & CI Tool
Scans repository source code for exposed API keys, private keys, and credentials.
Fails CI if secrets are detected.
"""
from __future__ import annotations
import re
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple


class SecretScanner:
    """
    Detects unencrypted secrets and private keys across repository files.
    """

    PATTERNS = [
        ("PRIVATE_KEY", re.compile(r"-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----")),
        ("AWS_ACCESS_KEY", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
        ("GENERIC_API_SECRET", re.compile(r"""(?:api_secret|app_secret|client_secret)\s*=\s*['"][0-9a-zA-Z\-_]{32,}['"]""")),
        ("HARDCODED_JWT_SECRET", re.compile(r"""(?:jwt_secret|jwt_key)\s*=\s*['"][0-9a-zA-Z\-_]{32,}['"]""")),
    ]

    IGNORE_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", "node_modules", "dist", "build", "datasets", ".trunk", ".vscode"}
    IGNORE_EXTS = {".png", ".jpg", ".onnx", ".pyc", ".lock", ".csv", ".parquet"}

    def scan_directory(self, root_dir: str = ".") -> Tuple[bool, List[Dict[str, Any]]]:
        findings: List[Dict[str, Any]] = []

        for root, dirs, files in os.walk(root_dir):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]

            for file in files:
                p = Path(root) / file
                if p.suffix in self.IGNORE_EXTS:
                    continue

                try:
                    with open(p, "r", encoding="utf-8", errors="ignore") as f:
                        for line_no, line in enumerate(f, start=1):
                            # Skip lines containing simulated mock test markers
                            if any(k in line for k in ["SIMULATED", "mock", "test_meta_app_secret", "dummy", "synthetic", "ILLUSTRATIVE"]):
                                continue

                            for rule_name, pattern in self.PATTERNS:
                                if pattern.search(line):
                                    findings.append({
                                        "file": str(p),
                                        "line": line_no,
                                        "rule": rule_name,
                                        "snippet": line.strip()[:60],
                                    })
                except Exception:
                    continue

        is_passed = len(findings) == 0
        return is_passed, findings


def run_scan() -> int:
    scanner = SecretScanner()
    passed, findings = scanner.scan_directory(".")

    if not passed:
        print(f"SECRET SCAN FAILED: {len(findings)} exposed secrets detected!")
        for f in findings:
            print(f" - [{f['rule']}] {f['file']}:{f['line']} -> {f['snippet']}")
        return 1

    print("SECRET SCAN PASSED: Zero unmasked secrets detected in repository.")
    return 0


if __name__ == "__main__":
    sys.exit(run_scan())
