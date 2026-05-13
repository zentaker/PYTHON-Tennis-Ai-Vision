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


def read_manual_labels(
    path: Path,
    *,
    source: str = "stage_4_1_existing",
    label_session: str = "stage_4_1",
) -> tuple[list[dict[str, Any]], list[str]]:
    """Read label CSV rows into the Stage 8.1 label schema."""
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
                        "source": row.get("source") or source,
                        "label_session": row.get("label_session") or label_session,
                        "notes": row.get("notes", ""),
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
    return rows, []


def visible_label_count(labels: list[dict[str, Any]]) -> int:
    """Count visible labels with usable coordinates."""
    return sum(1 for label in labels if label.get("visible") and label.get("x") is not None and label.get("y") is not None)


def visible_label_frames(labels: list[dict[str, Any]]) -> list[int]:
    """Return sorted frame indices for visible labels with usable coordinates."""
    return sorted(
        int(label["frame_index"])
        for label in labels
        if label.get("visible") and label.get("x") is not None and label.get("y") is not None
    )


def latest_label_session_csv(session_dir: Path) -> Path | None:
    """Return the newest Stage 8.1 label session backup CSV."""
    if not session_dir.exists():
        return None
    sessions = sorted(session_dir.glob("stage_8_1_labels_*.csv"), key=lambda path: path.stat().st_mtime)
    return sessions[-1] if sessions else None


def load_durable_or_fallback_labels(
    *,
    expanded_path: Path,
    fallback_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[str]]:
    """Load persisted Stage 8.1 labels first, then session backups, then Stage 4.1 labels."""
    session_dir = expanded_path.parent / "label_sessions"
    expanded_labels, expanded_warnings = read_manual_labels(
        expanded_path,
        source="stage_8_1_persisted",
        label_session="stage_8_1_persisted",
    )
    latest_session_path = latest_label_session_csv(session_dir)
    session_labels: list[dict[str, Any]] = []
    session_warnings: list[str] = []
    if latest_session_path:
        session_labels, session_warnings = read_manual_labels(
            latest_session_path,
            source="stage_8_1_latest_session",
            label_session=latest_session_path.stem,
        )
    fallback_labels, fallback_warnings = read_manual_labels(
        fallback_path,
        source="stage_4_1_existing",
        label_session="stage_4_1",
    )

    expanded_visible = visible_label_count(expanded_labels)
    session_visible = visible_label_count(session_labels)
    fallback_visible = visible_label_count(fallback_labels)
    warnings: list[str] = []

    if expanded_visible > 0 and session_visible > 0:
        merged = merge_labels(fallback_labels, expanded_labels)
        merged = merge_labels(merged, session_labels)
        source = "merged_sources" if fallback_visible > 0 else "stage_8_1_expanded"
        return (
            merged,
            {
                "label_source_used": source,
                "expanded_labels_loaded_successfully": True,
                "expanded_labels_path": str(expanded_path),
                "latest_session_path": str(latest_session_path),
                "fallback_labels_path": str(fallback_path),
                "label_persistence_status": "loaded_and_merged_persisted_expanded_and_latest_session_labels",
            },
            warnings,
        )

    if expanded_visible > 0:
        source = "stage_8_1_expanded"
        status = "loaded_persisted_expanded_labels"
        if fallback_visible > 0 and expanded_visible <= fallback_visible:
            source = "stage_4_1_fallback"
            status = "expanded_file_matches_fallback_label_count"
            warnings.append(
                "Expanded label file exists but does not contain more visible labels than the Stage 4.1 fallback labels."
            )
        return (
            expanded_labels,
            {
                "label_source_used": source,
                "expanded_labels_loaded_successfully": True,
                "expanded_labels_path": str(expanded_path),
                "latest_session_path": str(latest_session_path) if latest_session_path else "Not available",
                "fallback_labels_path": str(fallback_path),
                "label_persistence_status": status,
            },
            warnings,
        )

    if session_visible > 0:
        merged = merge_labels(fallback_labels, session_labels)
        return (
            merged,
            {
                "label_source_used": "stage_8_1_latest_session" if fallback_visible == 0 else "merged_sources",
                "expanded_labels_loaded_successfully": False,
                "expanded_labels_path": str(expanded_path),
                "latest_session_path": str(latest_session_path),
                "fallback_labels_path": str(fallback_path),
                "label_persistence_status": "loaded_latest_session_backup_labels",
            },
            session_warnings,
        )

    if fallback_visible > 0:
        return (
            fallback_labels,
            {
                "label_source_used": "stage_4_1_fallback",
                "expanded_labels_loaded_successfully": False,
                "expanded_labels_path": str(expanded_path),
                "latest_session_path": "Not available",
                "fallback_labels_path": str(fallback_path),
                "label_persistence_status": "fallback_labels_loaded_no_persisted_expanded_labels",
            },
            ["No persisted Stage 8.1 expanded labels or session backups were found; using Stage 4.1 fallback labels."],
        )

    warnings = [*expanded_warnings, *session_warnings, *fallback_warnings]
    return (
        [],
        {
            "label_source_used": "missing",
            "expanded_labels_loaded_successfully": False,
            "expanded_labels_path": str(expanded_path),
            "latest_session_path": str(latest_session_path) if latest_session_path else "Not available",
            "fallback_labels_path": str(fallback_path),
            "label_persistence_status": "no_labels_available",
        },
        warnings or ["No visible labels were available from persisted expanded labels or Stage 4.1 fallback labels."],
    )


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


def write_label_session_backup(session_dir: Path, timestamp: str, labels: list[dict[str, Any]]) -> dict[str, Path]:
    """Write timestamped backups for labels collected in an interactive session."""
    safe_timestamp = timestamp.replace(":", "").replace("+", "Z")
    csv_path = session_dir / f"stage_8_1_labels_{safe_timestamp}.csv"
    json_path = session_dir / f"stage_8_1_labels_{safe_timestamp}.json"
    write_expanded_labels_csv(csv_path, labels)
    write_expanded_labels_json(json_path, labels)
    return {"csv": csv_path, "json": json_path}


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
