"""
LifeLens Ω — Phase G: Fake-Interview "Technical Test" Safety Scanner
STATIC analysis only of repository / take-home archives.
NEVER executes untrusted code (§STATIC ONLY).
"""
from __future__ import annotations
import io
import re
import json
import zipfile
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

# Malicious installer patterns in package.json / setup.py
_MALICIOUS_HOOK_PATTERNS = [
    re.compile(r"\b(?:curl|wget|fetch|powershell|cmd\.exe|bash|sh)\s+.*?https?://", re.IGNORECASE),
    re.compile(r"\b(?:eval|Function)\s*\(\s*(?:atob|Buffer\.from|base64)", re.IGNORECASE),
    re.compile(r"\b(?:child_process|subprocess)\s*\.\s*(?:exec|spawn|execSync)", re.IGNORECASE),
    re.compile(r"\b(?:socket\.connect|net\.connect|ReverseShell)\b", re.IGNORECASE),
    re.compile(r"\b(?:payload|c2|drop|reverse_tcp|exfil)\b", re.IGNORECASE),
]

# Camera fix / fake tool download lures
_CAMERA_LURE_PATTERNS = [
    re.compile(r"\b(?:download|install)\b.*?(?:camera|webcam|codec|driver|setup\.exe|fix)\b", re.IGNORECASE),
    re.compile(r"\b(?:to\s+(?:start|attend|join)\s+(?:the\s+)?(?:interview|test)).*?(?:download|install|run)\b", re.IGNORECASE),
    re.compile(r"\b(?:install\s+this\s+software\s+to\s+fix\s+your\s+camera)\b", re.IGNORECASE),
]


@dataclass
class ScanResult:
    archive_name: str
    is_safe: bool
    risk_score: float
    verdict: str
    risk_indicators: List[str] = field(default_factory=list)
    scanned_files: List[str] = field(default_factory=list)
    execution_performed: bool = False
    disclaimer: str = "Static signature and heuristic scan only. No untrusted code was executed."


class TechTestSafetyScanner:
    """
    Performs purely static analysis of take-home interview repos and zip archives.
    Never executes or imports code from submitted packages.
    """

    def scan_archive_bytes(self, zip_bytes: bytes, filename: str = "archive.zip") -> ScanResult:
        risk_indicators: List[str] = []
        scanned_files: List[str] = []

        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                file_list = zf.namelist()
                scanned_files = file_list[:50]  # Cap audit to first 50 entries

                for fname in file_list:
                    # Skip massive or binary files to prevent decompression bombs
                    info = zf.getinfo(fname)
                    if info.file_size > 2 * 1024 * 1024:  # 2MB text limit
                        continue

                    lower_name = fname.lower()

                    # 1. Inspect package.json
                    if lower_name.endswith("package.json"):
                        try:
                            content = zf.read(fname).decode("utf-8", errors="ignore")
                            pkg = json.loads(content)
                            scripts = pkg.get("scripts", {})
                            for hook in ["preinstall", "postinstall", "install"]:
                                if hook in scripts:
                                    cmd = scripts[hook]
                                    if any(p.search(cmd) for p in _MALICIOUS_HOOK_PATTERNS) or "http" in cmd:
                                        risk_indicators.append(
                                            f"Suspicious {hook} script in {fname}: '{cmd[:80]}'"
                                        )
                        except Exception as e:
                            logger.warning("Error parsing package.json in zip: %s", e)

                    # 2. Inspect text instructions / README / HTML for camera lures
                    if any(lower_name.endswith(ext) for ext in [".md", ".txt", ".html", ".js", ".py", ".sh"]):
                        try:
                            content = zf.read(fname).decode("utf-8", errors="ignore")
                            for p in _CAMERA_LURE_PATTERNS:
                                m = p.search(content)
                                if m:
                                    risk_indicators.append(
                                        f"Camera / codec download lure in {fname}: '{m.group(0)[:80]}'"
                                    )
                                    break
                            for p in _MALICIOUS_HOOK_PATTERNS:
                                m = p.search(content)
                                if m and lower_name.endswith((".js", ".py", ".sh")):
                                    risk_indicators.append(
                                        f"Suspicious network execution pattern in {fname}: '{m.group(0)[:80]}'"
                                    )
                                    break
                        except Exception:
                            pass

        except zipfile.BadZipFile:
            risk_indicators.append("Corrupted or invalid zip archive format.")

        is_safe = len(risk_indicators) == 0
        if not is_safe:
            has_critical = any(
                any(k in r.lower() for k in ["postinstall", "preinstall", "install script", "camera", "codec", "payload", "c2", "execution pattern"])
                for r in risk_indicators
            )
            base_score = 0.85 if has_critical else 0.50
            risk_score = round(min(1.0, base_score + (len(risk_indicators) - 1) * 0.10), 2)
        else:
            risk_score = 0.05

        if risk_score >= 0.60:
            verdict = "Request looks high-risk"
        elif risk_score >= 0.25:
            verdict = "Needs Verification"
        else:
            verdict = "Verification step completed"

        return ScanResult(
            archive_name=filename,
            is_safe=is_safe,
            risk_score=risk_score,
            verdict=verdict,
            risk_indicators=risk_indicators,
            scanned_files=scanned_files,
            execution_performed=False,
        )
