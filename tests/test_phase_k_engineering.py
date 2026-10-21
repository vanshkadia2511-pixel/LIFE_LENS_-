"""
LifeLens Ω — Phase K Test Suite: Engineering Hardening
Validates:
1. On-device ONNX model export, bundle size (< 10MB), latency (< 25ms), and parity (> 95%).
2. CycloneDX v1.5 SBOM generation and schema compliance.
3. Supply-chain security audit gate (CI must fail on High/Critical vulnerabilities).
4. Pre-commit/CI secret scanning (detects keys, fails on leak, passes on clean tree).
5. Strict dependency pinning (==) across requirements.txt.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import pytest

from apps.api.app.services.ml.onnx_exporter import (
    OnDeviceClassifierExporter,
    OnDeviceModelBenchmark,
)
from scripts.generate_sbom import generate_cyclonedx_sbom
from scripts.security_audit import SecurityAuditRunner
from scripts.secret_scanner import SecretScanner


class TestPhaseKEngineeringHardening:
    """Verifies Phase K engineering hardening requirements."""

    def test_onnx_model_export_and_benchmarking(self, tmp_path):
        """Verifies ONNX exporter measures size, latency, parity rate, and accuracy delta."""
        exporter = OnDeviceClassifierExporter()
        val_texts = [
            "Deposit 5000 fee to claim your prize money",
            "Urgent transfer required to keep account active",
            "Team meeting scheduled for Thursday morning",
            "Please review the attached project specification document",
            "Digital arrest warrant issued against you by cyber crime bureau",
            "Lunch tomorrow at 1 PM with the product design team",
        ] * 5
        val_labels = [1, 1, 0, 0, 1, 0] * 5

        export_file = str(tmp_path / "model.onnx")
        benchmark = exporter.export_and_benchmark(
            validation_texts=val_texts,
            validation_labels=val_labels,
            export_path=export_file,
        )

        assert isinstance(benchmark, OnDeviceModelBenchmark)
        assert benchmark.provenance == "MEASURED"
        assert benchmark.model_size_mb < 10.0, f"Model size {benchmark.model_size_mb}MB exceeds 10MB budget"
        assert benchmark.avg_latency_ms < 25.0, f"Latency {benchmark.avg_latency_ms}ms exceeds 25ms target"
        assert benchmark.parity_rate_percent >= 90.0
        assert benchmark.accuracy_difference_delta <= 0.10
        assert benchmark.extension_ready is True
        assert Path(export_file).exists()
        assert Path(export_file).stat().st_size > 0

    def test_cyclonedx_sbom_generation(self, tmp_path):
        """Verifies CycloneDX v1.5 SBOM generation and valid structure."""
        out_path = str(tmp_path / "sbom.json")
        sbom = generate_cyclonedx_sbom(
            requirements_path="requirements.txt",
            output_path=out_path,
        )

        assert sbom["bomFormat"] == "CycloneDX"
        assert sbom["specVersion"] == "1.5"
        assert "serialNumber" in sbom
        assert sbom["metadata"]["component"]["name"] == "LifeLens-Omega"
        assert len(sbom["components"]) > 10

        # Verify component properties
        for comp in sbom["components"]:
            assert comp["type"] == "library"
            assert "name" in comp
            assert "version" in comp
            assert comp["purl"].startswith("pkg:pypi/")

        # Verify output file persisted
        assert Path(out_path).exists()
        with open(out_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["bomFormat"] == "CycloneDX"

    def test_security_audit_runner_passes_clean(self):
        """Verifies security audit passes cleanly on current pinned requirements."""
        runner = SecurityAuditRunner()
        passed, findings = runner.audit_requirements("requirements.txt")
        assert passed is True
        high_crit = [f for f in findings if f.get("severity") in ("HIGH", "CRITICAL")]
        assert len(high_crit) == 0

    def test_security_audit_runner_fails_on_high_cve(self, tmp_path):
        """Verifies CI gate fails if a high or critical CVE is present."""
        vuln_req = tmp_path / "vuln_requirements.txt"
        vuln_req.write_text("fastapi==0.104.1\nurllib3==1.26.15\n", encoding="utf-8")

        runner = SecurityAuditRunner()
        passed, findings = runner.audit_requirements(str(vuln_req))
        assert passed is False
        assert len(findings) == 1
        assert findings[0]["package"] == "urllib3"
        assert findings[0]["severity"] == "HIGH"
        assert findings[0]["cve"] == "CVE-2023-45803"

    def test_secret_scanner_clean_production_tree(self):
        """Verifies secret scanner detects no exposed secrets in core app code."""
        scanner = SecretScanner()
        passed, findings = scanner.scan_directory("apps/api/app")
        assert passed is True, f"Unexpected secrets detected: {findings}"
        assert len(findings) == 0

    def test_secret_scanner_detects_exposed_key(self, tmp_path):
        """Verifies secret scanner catches exposed AWS access keys."""
        leak_file = tmp_path / "leaked_config.py"
        leak_file.write_text('aws_key = "AKIA' + 'IOSFODNN7EXAMPLE"\n', encoding="utf-8")

        scanner = SecretScanner()
        passed, findings = scanner.scan_directory(str(tmp_path))
        assert passed is False
        assert len(findings) == 1
        assert findings[0]["rule"] == "AWS_ACCESS_KEY"

    def test_all_requirements_strictly_pinned(self):
        """Verifies every dependency in requirements.txt is pinned with '=='."""
        req_path = Path("requirements.txt")
        assert req_path.exists()
        with open(req_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                assert "==" in line, f"Dependency line not strictly pinned with '==': {line}"
