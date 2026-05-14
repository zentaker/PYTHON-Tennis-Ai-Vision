"""Package manifest helpers for Stage 11."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def artifact(
    *,
    name: str,
    artifact_type: str,
    source_path: Path,
    package_path: Path,
    purpose: str,
    required: bool = False,
) -> dict[str, Any]:
    """Create an artifact descriptor."""
    return {
        "name": name,
        "type": artifact_type,
        "source_path": str(source_path),
        "package_path": str(package_path),
        "purpose": purpose,
        "required": required,
        "exists": source_path.exists(),
        "copied": False,
    }


def build_manifest(
    *,
    generated_at: str,
    package_root: Path,
    verdict: str,
    confidence_level: str | None,
    artifacts: list[dict[str, Any]],
    warnings: list[str],
    errors: list[str],
    output_paths: dict[str, str],
    recommended_next_step: str,
) -> dict[str, Any]:
    """Build the package manifest."""
    included = [item for item in artifacts if item.get("exists")]
    missing = [item for item in artifacts if not item.get("exists")]
    return {
        "generated_at": generated_at,
        "stage": "stage_11_report_package",
        "package_root": str(package_root),
        "source_stage": "stage_10_analytical_report",
        "verdict": verdict,
        "confidence_level": confidence_level,
        "included_artifacts": included,
        "missing_artifacts": missing,
        "warnings": warnings,
        "errors": errors,
        "output_paths": output_paths,
        "recommended_next_step": recommended_next_step,
    }


def write_manifest(path: Path, manifest: dict[str, Any]) -> Path:
    """Write package manifest JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
