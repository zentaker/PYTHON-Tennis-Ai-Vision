"""Report package helpers for Stage 11."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any


def ensure_package_dirs(package_root: Path) -> None:
    """Create the Stage 11 package directory structure."""
    for relative in ("analysis", "data", "visuals", "notes"):
        (package_root / relative).mkdir(parents=True, exist_ok=True)


def copy_or_reference_artifacts(artifacts: list[dict[str, Any]], *, copy_mode: str) -> tuple[list[dict[str, Any]], list[str]]:
    """Copy selected artifacts or leave them as references."""
    warnings: list[str] = []
    for item in artifacts:
        source = Path(item["source_path"])
        destination = Path(item["package_path"])
        if not source.exists():
            warnings.append(f"Missing artifact: {source}")
            item["exists"] = False
            item["copied"] = False
            continue
        item["exists"] = True
        if copy_mode == "reference_only":
            item["copied"] = False
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(source, destination)
            item["copied"] = True
        except OSError as exc:
            warnings.append(f"Could not copy {source} to {destination}: {exc}")
            item["copied"] = False
    return artifacts, warnings


def build_report_package(
    *,
    package_root: Path,
    artifacts: list[dict[str, Any]],
    copy_mode: str = "copy",
) -> tuple[list[dict[str, Any]], list[str]]:
    """Collect selected analysis outputs into a clean delivery package."""
    ensure_package_dirs(package_root)
    return copy_or_reference_artifacts(artifacts, copy_mode=copy_mode)


def write_package_readme(
    path: Path,
    *,
    verdict: str,
    confidence_level: str | None,
    generated_at: str,
    next_step: str,
) -> Path:
    """Write package README in plain-text-friendly format."""
    lines = [
        "# Tennis AI Vision - Stage 11 Report Package",
        "",
        "PACKAGE STATUS",
        f"  Verdict: {verdict}",
        f"  Confidence: {confidence_level or 'Not available'}",
        f"  Generated at: {generated_at}",
        "",
        "WHAT THIS PACKAGE IS",
        "  This is a local prototype report package generated from the Tennis AI Vision analysis pipeline.",
        "  It organizes selected reports, tactical maps, timeline artifacts, and CSV evidence into one folder.",
        "",
        "WHAT IT INCLUDES",
        "  - analytical report",
        "  - coaching-style summary",
        "  - key findings",
        "  - tactical maps",
        "  - timeline artifacts",
        "  - selected CSV data",
        "  - visual references",
        "  - limitations",
        "",
        "WHAT IT DOES NOT CLAIM",
        "  - no official scoring",
        "  - no official line calling",
        "  - no confirmed professional coaching",
        "  - no production-grade tracking",
        "",
        "HOW TO READ",
        "  1. Start with analysis/analytical_report.md",
        "  2. Read analysis/key_findings.md",
        "  3. Review analysis/coaching_summary.md",
        "  4. Open visuals/tuned_ball_placement_map.jpg",
        "  5. Inspect data/ only if needed",
        "",
        "NEXT STEP",
        f"  {next_step}",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def write_package_index(path: Path, artifacts: list[dict[str, Any]]) -> Path:
    """Write a vertical-block package index."""
    lines = ["# Stage 11 Package Index", "", "This index is plain-text friendly.", ""]
    for item in artifacts:
        lines.extend(
            [
                f"ARTIFACT: {Path(item['package_path']).name}",
                f"TYPE: {item['type']}",
                f"LOCATION: {_relative_package_path(item['package_path'])}",
                f"SOURCE: {item['source_path']}",
                "PURPOSE:",
                f"  {item['purpose']}",
                "",
                "STATUS:",
                f"  {'included' if item.get('exists') else 'missing'}",
                f"  copied: {'yes' if item.get('copied') else 'no'}",
                "",
                "---",
                "",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def write_limitations(path: Path) -> Path:
    """Write package limitations note."""
    lines = [
        "# Limitations",
        "",
        "- Limited sample video.",
        "- Limited label count.",
        "- possible_* events are hypotheses.",
        "- No official scoring.",
        "- No line calling.",
        "- No external validation.",
        "- No multi-angle support yet.",
        "- No real-time support yet.",
        "- Coaching summary is exploratory.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def write_source_artifacts(path: Path, artifacts: list[dict[str, Any]]) -> Path:
    """Write source artifact provenance note."""
    lines = ["# Source Artifacts", "", "Each block shows where a packaged item came from.", ""]
    for item in artifacts:
        lines.extend(
            [
                f"ARTIFACT: {item['name']}",
                f"SOURCE: {item['source_path']}",
                f"PACKAGE PATH: {_relative_package_path(item['package_path'])}",
                f"STATUS: {'included' if item.get('exists') else 'missing'}",
                "",
                "---",
                "",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def _relative_package_path(path: str) -> str:
    parts = Path(path).parts
    for marker in ("analysis", "data", "visuals", "notes"):
        if marker in parts:
            return str(Path(*parts[parts.index(marker) :]))
    return Path(path).name
