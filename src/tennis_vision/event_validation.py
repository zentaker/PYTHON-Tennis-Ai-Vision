"""Event validation helpers for Stage 8.3."""

from __future__ import annotations

import csv
from pathlib import Path
from statistics import mean
from typing import Any


MANUAL_LABELS = {"bounce", "hit", "no_event", "uncertain", "skipped"}
AUTO_TYPE_MAP = {
    "possible_hit": "auto_possible_hit",
    "possible_hit_window": "auto_possible_hit",
    "possible_bounce": "auto_possible_bounce",
    "ball_near_player": "auto_ball_near_player",
    "ball_approaching_player": "auto_ball_near_player",
    "ball_leaving_player": "auto_ball_near_player",
    "direction_change": "auto_direction_change",
    "possible_direction_change": "auto_direction_change",
    "speed_spike": "auto_speed_spike",
    "possible_speed_spike": "auto_speed_spike",
    "speed_drop": "auto_speed_drop",
    "possible_speed_drop": "auto_speed_drop",
}


def read_manual_event_labels(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Read Stage 8.2 manual event labels."""
    if not path.exists():
        return [], [f"Manual event labels missing: {path}"]
    labels: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            frame = int_or_none(row.get("frame_index"))
            if frame is None:
                continue
            label = normalize_manual_event_label(row.get("event_label"))
            labels.append(
                {
                    "frame_index": frame,
                    "timestamp_seconds": float_or_none(row.get("timestamp_seconds")),
                    "event_label": label,
                    "player_id": row.get("player_id") or "unknown",
                    "confidence": row.get("confidence") or "medium",
                    "x": float_or_none(row.get("x")),
                    "y": float_or_none(row.get("y")),
                    "source": row.get("source") or "stage_8_2_existing",
                    "notes": row.get("notes") or "",
                }
            )
    return labels, []


def normalize_manual_event_label(value: Any) -> str:
    """Normalize manual event labels to the Stage 8.3 label vocabulary."""
    text = str(value or "").strip().lower()
    if text in MANUAL_LABELS:
        return text
    if "bounce" in text:
        return "bounce"
    if "hit" in text:
        return "hit"
    if "no" in text:
        return "no_event"
    if "skip" in text:
        return "skipped"
    return "uncertain"


def group_manual_event_windows(labels: list[dict[str, Any]], *, bounce_window_gap: int = 3) -> list[dict[str, Any]]:
    """Group adjacent manual bounce labels into bounce windows."""
    bounce_labels = sorted((label for label in labels if label.get("event_label") == "bounce"), key=lambda row: int(row["frame_index"]))
    windows: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    for label in bounce_labels:
        if not current:
            current = [label]
            continue
        if int(label["frame_index"]) - int(current[-1]["frame_index"]) <= bounce_window_gap:
            current.append(label)
        else:
            windows.append(build_window(current, len(windows) + 1))
            current = [label]
    if current:
        windows.append(build_window(current, len(windows) + 1))
    return windows


def read_manual_event_windows(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Read user-created Stage 8.2 manual event windows when available."""
    if not path.exists():
        return [], []
    windows: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row_index, row in enumerate(reader, start=1):
            start = int_or_none(row.get("start_frame"))
            end = int_or_none(row.get("end_frame"))
            if start is None or end is None:
                continue
            event_label = normalize_manual_event_label(row.get("event_label"))
            frames_text = row.get("frame_indices") or ""
            windows.append(
                {
                    "window_id": row.get("window_id") or f"manual_window_{row_index:03d}",
                    "event_label": event_label,
                    "start_frame": start,
                    "end_frame": end,
                    "center_frame": int_or_none(row.get("center_frame")) or int(round((start + end) / 2)),
                    "label_count": int_or_none(row.get("label_count")) or len([item for item in frames_text.split(",") if item.strip()]) or (end - start + 1),
                    "confidence": row.get("confidence") or "medium",
                    "source_frames": frames_text or ",".join(str(frame) for frame in range(start, end + 1)),
                    "notes": row.get("notes") or "User-created Stage 8.2 event window.",
                }
            )
    return windows, []


def build_window(labels: list[dict[str, Any]], index: int) -> dict[str, Any]:
    """Build one manual event window row."""
    frames = [int(label["frame_index"]) for label in labels]
    confidence = "high" if any(str(label.get("confidence")) == "high" for label in labels) else "medium"
    center = int(round(mean(frames)))
    return {
        "window_id": f"bounce_window_{index:03d}",
        "event_label": "bounce",
        "start_frame": min(frames),
        "end_frame": max(frames),
        "center_frame": center,
        "label_count": len(labels),
        "confidence": confidence,
        "source_frames": ",".join(str(frame) for frame in frames),
        "notes": "Adjacent manual bounce labels grouped into one temporal bounce window.",
    }


def summarize_manual_event_labels(labels: list[dict[str, Any]], windows: list[dict[str, Any]]) -> dict[str, int]:
    """Summarize manual event label counts."""
    return {
        "manual_labels_count": len(labels),
        "manual_bounce_count": sum(1 for row in labels if row.get("event_label") == "bounce"),
        "manual_hit_count": sum(1 for row in labels if row.get("event_label") == "hit"),
        "manual_no_event_count": sum(1 for row in labels if row.get("event_label") == "no_event"),
        "manual_uncertain_count": sum(1 for row in labels if row.get("event_label") == "uncertain"),
        "manual_skipped_count": sum(1 for row in labels if row.get("event_label") == "skipped"),
        "bounce_windows_count": len(windows),
    }


def read_automatic_events(paths: list[tuple[Path, str]]) -> tuple[list[dict[str, Any]], list[str]]:
    """Read and normalize automatic event hypotheses."""
    events: list[dict[str, Any]] = []
    warnings: list[str] = []
    for path, source in paths:
        if not path.exists():
            warnings.append(f"Optional automatic event file missing: {path}")
            continue
        with path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row_index, row in enumerate(reader, start=1):
                frame = int_or_none(row.get("frame_index"))
                if frame is None:
                    continue
                raw_type = row.get("event_type") or row.get("interaction_type") or row.get("related_stage_6_event") or "unknown"
                events.append(
                    {
                        "auto_event_id": row.get("event_id") or f"{source}_{row_index:04d}",
                        "auto_event_source": source,
                        "auto_frame_index": frame,
                        "auto_event_type": normalize_auto_event_type(raw_type),
                        "raw_event_type": raw_type,
                        "player_id": row.get("player_id") or row.get("nearest_track_id") or "",
                        "confidence_before": float_or_none(row.get("confidence_like_score")) or 0.5,
                        "source": source,
                    }
                )
    return events, warnings


def normalize_auto_event_type(value: Any) -> str:
    """Normalize automatic events to Stage 8.3 event types."""
    text = str(value or "").strip().lower()
    return AUTO_TYPE_MAP.get(text, "auto_unknown")


def nearest_manual_evidence(
    auto_event: dict[str, Any],
    labels: list[dict[str, Any]],
    windows: list[dict[str, Any]],
    *,
    validation_window: int,
) -> dict[str, Any]:
    """Find the nearest manual label or bounce window for an automatic event."""
    frame = int(auto_event["auto_frame_index"])
    candidates: list[dict[str, Any]] = []
    for window in windows:
        start = int(window["start_frame"])
        end = int(window["end_frame"])
        if start <= frame <= end:
            delta = 0
        else:
            delta = min(abs(frame - start), abs(frame - end), abs(frame - int(window["center_frame"])))
        candidates.append(
            {
                "kind": "window",
                "event_label": window["event_label"],
                "frame_or_window": window["window_id"],
                "center_frame": int(window["center_frame"]),
                "frame_delta": delta,
                "record": window,
            }
        )
    for label in labels:
        if label.get("event_label") == "skipped":
            continue
        delta = abs(frame - int(label["frame_index"]))
        candidates.append(
            {
                "kind": "label",
                "event_label": label["event_label"],
                "frame_or_window": int(label["frame_index"]),
                "center_frame": int(label["frame_index"]),
                "frame_delta": delta,
                "record": label,
            }
        )
    if not candidates:
        return {"event_label": "", "frame_or_window": "", "frame_delta": None, "within_window": False}
    nearest = min(candidates, key=lambda item: (int(item["frame_delta"]), evidence_priority(item)))
    nearest["within_window"] = int(nearest["frame_delta"]) <= validation_window
    return nearest


def classify_validation_status(
    auto_event: dict[str, Any],
    evidence: dict[str, Any],
    *,
    manual_hit_count: int,
    manual_frame_range: tuple[int, int] | None,
    validation_window: int,
) -> tuple[str, str]:
    """Classify automatic event validation status against manual evidence."""
    auto_type = str(auto_event.get("auto_event_type") or "")
    frame = int(auto_event["auto_frame_index"])
    if manual_frame_range and not (manual_frame_range[0] <= frame <= manual_frame_range[1]):
        return "outside_manual_coverage", "Automatic event is outside the manually labeled frame range."
    if not evidence.get("event_label") or not evidence.get("within_window"):
        if auto_type == "auto_possible_hit" and manual_hit_count == 0:
            return "no_manual_label_nearby", "No nearby manual label and no manual hit labels exist anywhere."
        return "no_manual_label_nearby", "No manual event label or window is near this automatic event."
    label = str(evidence.get("event_label") or "")
    if label == "uncertain":
        return "near_uncertain_label", "Nearest manual label is uncertain; do not hard reject."
    if auto_type == "auto_possible_hit" and label == "bounce":
        return "contradicted_by_bounce_window", "Manual bounce window contradicts automatic hit."
    if auto_type == "auto_possible_hit" and label == "no_event":
        return "contradicted_by_no_event", "Manual no_event label contradicts automatic hit."
    if auto_type == "auto_possible_hit" and label == "hit":
        return "validated_by_manual_label", "Manual hit label supports automatic hit."
    if auto_type == "auto_possible_bounce" and label == "bounce":
        return "validated_by_manual_label", "Manual bounce window supports automatic bounce."
    if auto_type == "auto_ball_near_player" and label == "hit":
        return "validated_by_manual_label", "Manual hit label gives weak support to player interaction cue."
    if label == "no_event" and auto_type in {"auto_possible_bounce", "auto_ball_near_player"}:
        return "contradicted_by_no_event", "Manual no_event label contradicts nearby automatic event."
    return "no_manual_label_nearby" if int(evidence.get("frame_delta") or 99) > validation_window else "near_uncertain_label", "Manual evidence is nearby but does not strongly validate or contradict this event."


def manual_frame_range(labels: list[dict[str, Any]]) -> tuple[int, int] | None:
    """Return frame range for non-skipped manual labels."""
    frames = [int(row["frame_index"]) for row in labels if row.get("event_label") != "skipped"]
    if not frames:
        return None
    return min(frames), max(frames)


def write_manual_event_windows_csv(path: Path, rows: list[dict[str, Any]]) -> Path:
    """Write manual event windows CSV."""
    return write_csv(
        path,
        rows,
        ["window_id", "event_label", "start_frame", "end_frame", "center_frame", "label_count", "confidence", "source_frames", "notes"],
    )


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> Path:
    """Write rows to CSV with stable fields."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    return path


def evidence_priority(evidence: dict[str, Any]) -> int:
    """Prefer bounce windows over single labels when deltas tie."""
    if evidence.get("kind") == "window":
        return 0
    label = evidence.get("event_label")
    if label in {"bounce", "hit"}:
        return 1
    if label == "no_event":
        return 2
    return 3


def float_or_none(value: Any) -> float | None:
    """Convert to float if possible."""
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def int_or_none(value: Any) -> int | None:
    """Convert to int if possible."""
    try:
        if value in (None, ""):
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None
