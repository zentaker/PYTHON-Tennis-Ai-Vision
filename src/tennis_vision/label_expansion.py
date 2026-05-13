"""Label expansion helpers for Stage 8.1 timeline validation."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import mean
from typing import Any

from tennis_vision.ball_labeling import label_frames_interactively


EXPANDED_LABEL_FIELDS = [
    "frame_index",
    "visible",
    "x",
    "y",
    "original_width",
    "original_height",
    "source",
    "label_session",
    "notes",
]


def read_manual_labels(path: Path, *, source: str = "stage_4_1_existing") -> tuple[list[dict[str, Any]], list[str]]:
    """Read existing manual labels into the Stage 8.1 label schema."""
    if not path.exists():
        return [], [f"Manual labels CSV not found: {path}"]
    rows: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                rows.append(
                    {
                        "frame_index": int(float(row["frame_index"])),
                        "visible": str(row.get("visible", "")).lower() == "true",
                        "x": _float_or_none(row.get("x")),
                        "y": _float_or_none(row.get("y")),
                        "original_width": int(float(row.get("original_width") or 0)),
                        "original_height": int(float(row.get("original_height") or 0)),
                        "source": source,
                        "label_session": "stage_4_1",
                        "notes": row.get("notes", ""),
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
    return rows, []


def collect_interactive_labels(
    *,
    video_path: Path,
    frame_indices: list[int],
    output_dir: Path,
    resize_width: int,
    label_session: str,
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    """Collect new labels using the existing OpenCV click labeler."""
    result = label_frames_interactively(
        video_path=video_path,
        frame_indices=frame_indices,
        output_dir=output_dir,
        resize_width=resize_width,
    )
    labels: list[dict[str, Any]] = []
    for label in result.get("labels", []):
        labels.append(
            {
                "frame_index": int(label["frame_index"]),
                "visible": bool(label.get("visible")),
                "x": label.get("x"),
                "y": label.get("y"),
                "original_width": label.get("original_width"),
                "original_height": label.get("original_height"),
                "source": "stage_8_1_manual" if label.get("visible") else "skipped",
                "label_session": label_session,
                "notes": label.get("notes", ""),
            }
        )
    return labels, list(result.get("warnings", [])), list(result.get("errors", []))


def merge_labels(existing_labels: list[dict[str, Any]], new_labels: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge labels by frame, preferring Stage 8.1 labels while preserving provenance."""
    by_frame: dict[int, dict[str, Any]] = {}
    for label in existing_labels:
        by_frame[int(label["frame_index"])] = dict(label)
    for label in new_labels:
        frame_index = int(label["frame_index"])
        previous = by_frame.get(frame_index)
        merged = dict(label)
        if previous:
            prior = f"previous {previous.get('source')} label=({previous.get('x')}, {previous.get('y')})"
            merged["notes"] = "; ".join(item for item in [merged.get("notes"), prior] if item)
        by_frame[frame_index] = merged
    return [by_frame[key] for key in sorted(by_frame)]


def analyze_label_coverage(labels: list[dict[str, Any]], *, fps: float | None = None) -> dict[str, Any]:
    """Compute coverage metrics for visible labels."""
    visible = [label for label in labels if label.get("visible")]
    skipped = [label for label in labels if not label.get("visible")]
    frames = sorted(int(label["frame_index"]) for label in visible)
    gaps = [current - previous for previous, current in zip(frames, frames[1:])]
    frame_range = f"{frames[0]} to {frames[-1]}" if frames else "Not available"
    duration_seconds = ((frames[-1] - frames[0]) / fps) if fps and len(frames) >= 2 else None
    enough = len(visible) >= 10 and (max(gaps) if gaps else 0) <= 30
    return {
        "total_labels": len(labels),
        "visible_labels": len(visible),
        "skipped_frames": len(skipped),
        "label_frame_range": frame_range,
        "average_label_gap": round(mean(gaps), 3) if gaps else None,
        "maximum_label_gap": max(gaps) if gaps else None,
        "labels_per_second": round(len(visible) / duration_seconds, 3) if duration_seconds and duration_seconds > 0 else None,
        "coverage_enough_for_timeline_validation": enough,
    }


def write_expanded_labels_csv(path: Path, labels: list[dict[str, Any]]) -> Path:
    """Write expanded labels to CSV."""
    write_csv(path, labels, EXPANDED_LABEL_FIELDS)
    return path


def write_expanded_labels_json(path: Path, labels: list[dict[str, Any]]) -> Path:
    """Write expanded labels to JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(labels, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_coverage_csv(path: Path, coverage: dict[str, Any]) -> Path:
    """Write one-row label coverage report."""
    fields = [
        "total_labels",
        "visible_labels",
        "skipped_frames",
        "label_frame_range",
        "average_label_gap",
        "maximum_label_gap",
        "labels_per_second",
        "coverage_enough_for_timeline_validation",
    ]
    write_csv(path, [coverage], fields)
    return path


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> Path:
    """Write dictionaries to a CSV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    return path


def _float_or_none(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
