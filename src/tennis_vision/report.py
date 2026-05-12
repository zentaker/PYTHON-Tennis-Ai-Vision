"""Report writing helpers for terminal-driven experiments."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OUTPUT_FOLDERS = (
    "outputs/reports",
    "outputs/logs",
    "outputs/frames",
    "outputs/annotated",
)


def utc_timestamp() -> str:
    """Return an ISO 8601 UTC timestamp."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def safe_timestamp_for_filename() -> str:
    """Return a timestamp that is safe for filenames on Windows."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def ensure_output_folders(project_root: Path) -> None:
    """Create standard output folders if they are missing."""
    for folder in OUTPUT_FOLDERS:
        (project_root / folder).mkdir(parents=True, exist_ok=True)


def write_json_report(path: Path, data: dict[str, Any]) -> Path:
    """Write a JSON report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_markdown_report(path: Path, title: str, sections: list[tuple[str, str]]) -> Path:
    """Write a Markdown report from titled sections."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# {title}", ""]
    for heading, body in sections:
        lines.extend([f"## {heading}", "", body.strip() or "_No entries._", ""])
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def write_timestamped_log(project_root: Path, name: str, lines: list[str]) -> Path:
    """Write a timestamped log file under outputs/logs."""
    logs_dir = project_root / "outputs" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    safe_name = name.replace(" ", "_").lower()
    path = logs_dir / f"{safe_name}_{safe_timestamp_for_filename()}.log"
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path
