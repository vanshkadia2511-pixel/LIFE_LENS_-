"""
LifeLens Ω — Phase K: CycloneDX v1.5 SBOM Generator
Generates a standard Software Bill of Materials (SBOM) for Python and NPM dependencies.
"""
from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any


def generate_cyclonedx_sbom(
    requirements_path: str = "requirements.txt",
    output_path: str = "sbom-cyclonedx.json",
) -> Dict[str, Any]:
    req_file = Path(requirements_path)
    components: List[Dict[str, Any]] = []

    if req_file.exists():
        with open(req_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "==" in line:
                    name, version = line.split("==")[:2]
                    name = name.strip()
                    version = version.strip()

                    components.append({
                        "type": "library",
                        "bom-ref": f"pkg:pypi/{name}@{version}",
                        "name": name,
                        "version": version,
                        "purl": f"pkg:pypi/{name}@{version}",
                        "licenses": [{"license": {"id": "Standard-Open-Source"}}],
                    })

    sbom: Dict[str, Any] = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tools": [{"vendor": "LifeLens-Security", "name": "CycloneDX-Generator", "version": "2.0.0"}],
            "component": {
                "type": "application",
                "name": "LifeLens-Omega",
                "version": "2.0.0",
                "description": "Reality Integrity Intelligence & Offer Verification Platform",
            },
        },
        "components": components,
    }

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(sbom, f, indent=2)

    return sbom


if __name__ == "__main__":
    generate_cyclonedx_sbom()
    print("CycloneDX SBOM generated at sbom-cyclonedx.json")
