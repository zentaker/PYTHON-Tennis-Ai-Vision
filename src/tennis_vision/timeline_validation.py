"""Timeline validation helpers for Stage 8.1."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from statistics import mean, median
from typing import Any


THRESHOLDS = (10, 25, 50, 100, 200)


def read_candidates(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Read improved candidate rows."""
    if not path.exists():
        return [], [f"Improved candidate CSV not found: {path}"]
    rows: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                rows.append(
                    {
                        "frame_index": int(float(row["frame_index"])),
                        "x": float(row["x"]),
                        "y": float(row["y"]),
                        "score": _float_or_none(row.get("score")),
                        "strategy": row.get("strategy", ""),
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
    return rows, []


def read_timeline(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Read Stage 8 timeline rows."""
    if not path.exists():
        return [], [f"Stage 8 timeline CSV not found: {path}"]
    rows: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                row["frame_index"] = int(float(row["frame_index"]))
                row["confidence_like_score"] = _float_or_none(row.get("confidence_like_score")) or 0.0
                rows.append(row)
            except (KeyError, TypeError, ValueError):
                continue
    return rows, []


def validate_candidates_against_labels(
    *,
    labels: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    frame_tolerance: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Compare improved candidates against expanded visible labels."""
    visible_labels = [label for label in labels if label.get("visible") and label.get("x") is not None and label.get("y") is not None]
    rows: list[dict[str, Any]] = []
    distances: list[float] = []
    for label in visible_labels:
        match = nearest_candidate(label, candidates, frame_tolerance)
        distance = None
        if match:
            distance = math.dist((float(label["x"]), float(label["y"])), (float(match["x"]), float(match["y"])))
            distances.append(distance)
        output = {
            "frame_index": label["frame_index"],
            "label_x": label.get("x"),
            "label_y": label.get("y"),
            "candidate_frame_index": match.get("frame_index") if match else None,
            "candidate_x": match.get("x") if match else None,
            "candidate_y": match.get("y") if match else None,
            "frame_delta": abs(int(match["frame_index"]) - int(label["frame_index"])) if match else None,
            "distance_px": round(distance, 3) if distance is not None else None,
            "match_status": "matched" if match else "no_candidate_within_tolerance",
        }
        for threshold in THRESHOLDS:
            output[f"within_{threshold}_px"] = bool(distance is not None and distance <= threshold)
        rows.append(output)
    summary = {
        "candidate_validation_count": len(rows),
        "average_candidate_distance": round(mean(distances), 3) if distances else None,
        "median_candidate_distance": round(median(distances), 3) if distances else None,
        **{f"within_{threshold}_px": sum(1 for row in rows if row[f"within_{threshold}_px"]) for threshold in THRESHOLDS},
    }
    return rows, summary


def validate_timeline_events(
    *,
    timeline_rows: list[dict[str, Any]],
    labels: list[dict[str, Any]],
    near_frame_tolerance: int = 15,
    support_frame_tolerance: int = 5,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Validate Stage 8 timeline events against expanded ball labels."""
    visible_labels = [label for label in labels if label.get("visible") and label.get("x") is not None and label.get("y") is not None]
    label_frames = sorted(int(label["frame_index"]) for label in visible_labels)
    min_frame = min(label_frames) if label_frames else None
    max_frame = max(label_frames) if label_frames else None
    validation_rows: list[dict[str, Any]] = []
    validated_timeline: list[dict[str, Any]] = []
    for event in timeline_rows:
        nearest = nearest_label(event, visible_labels)
        frame_delta = abs(int(event["frame_index"]) - int(nearest["frame_index"])) if nearest else None
        status = "insufficient_data"
        reason = "No visible labels are available."
        adjustment = -0.25
        if nearest and frame_delta is not None and frame_delta <= support_frame_tolerance:
            status = "supported_by_label"
            reason = "Timeline event is directly supported by an expanded ball label near the same frame."
            adjustment = 0.05
        elif nearest and frame_delta is not None and frame_delta <= near_frame_tolerance:
            status = "near_labeled_frame"
            reason = "Timeline event is near labeled ball coverage but not directly labeled."
            adjustment = -0.05
        elif min_frame is not None and max_frame is not None and not (min_frame <= int(event["frame_index"]) <= max_frame):
            status = "outside_label_coverage"
            reason = "Timeline event is outside the labeled frame range."
            adjustment = -0.2
        elif nearest:
            status = "insufficient_data"
            reason = "Nearest label is too far from the event frame for strong support."
            adjustment = -0.15
        if str(event.get("event_type", "")).startswith("possible_") and status == "supported_by_label":
            reason += " This supports ball position only, not confirmed tennis event identity."
        adjusted = max(0.0, min(1.0, float(event.get("confidence_like_score") or 0.0) + adjustment))
        validation = {
            "event_id": event.get("event_id"),
            "frame_index": event.get("frame_index"),
            "event_type": event.get("event_type"),
            "player_id": event.get("player_id"),
            "nearest_label_frame": nearest.get("frame_index") if nearest else None,
            "frame_delta": frame_delta,
            "label_x": nearest.get("x") if nearest else None,
            "label_y": nearest.get("y") if nearest else None,
            "validation_status": status,
            "validation_reason": reason,
            "confidence_adjustment": adjustment,
        }
        validation_rows.append(validation)
        validated = dict(event)
        validated.update(
            {
                "validation_status": status,
                "adjusted_confidence_like_score": round(adjusted, 3),
                "label_support": status in {"supported_by_label", "near_labeled_frame"},
                "validation_warnings": "" if status == "supported_by_label" else reason,
            }
        )
        validated_timeline.append(validated)
    supported = sum(1 for row in validation_rows if row["validation_status"] == "supported_by_label")
    unsupported = sum(1 for row in validation_rows if row["validation_status"] in {"insufficient_data", "near_labeled_frame"})
    outside = sum(1 for row in validation_rows if row["validation_status"] == "outside_label_coverage")
    summary = {
        "timeline_events_validated": len(validation_rows),
        "supported_events_count": supported,
        "unsupported_events_count": unsupported,
        "outside_coverage_events_count": outside,
    }
    return validation_rows, validated_timeline, summary


def write_candidate_validation_csv(path: Path, rows: list[dict[str, Any]]) -> Path:
    """Write candidate validation CSV."""
    fields = [
        "frame_index",
        "label_x",
        "label_y",
        "candidate_frame_index",
        "candidate_x",
        "candidate_y",
        "frame_delta",
        "distance_px",
        "within_10_px",
        "within_25_px",
        "within_50_px",
        "within_100_px",
        "within_200_px",
        "match_status",
    ]
    return write_csv(path, rows, fields)


def write_timeline_validation_csv(path: Path, rows: list[dict[str, Any]]) -> Path:
    """Write timeline event validation CSV."""
    fields = [
        "event_id",
        "frame_index",
        "event_type",
        "player_id",
        "nearest_label_frame",
        "frame_delta",
        "label_x",
        "label_y",
        "validation_status",
        "validation_reason",
        "confidence_adjustment",
    ]
    return write_csv(path, rows, fields)


def write_validated_timeline_csv(path: Path, rows: list[dict[str, Any]]) -> Path:
    """Write validated timeline CSV."""
    fields = [
        "event_id",
        "frame_index",
        "timestamp_seconds",
        "event_type",
        "event_source",
        "player_id",
        "player_side_state",
        "ball_x",
        "ball_y",
        "ball_projected_x",
        "ball_projected_y",
        "confidence_like_score",
        "adjusted_confidence_like_score",
        "validation_status",
        "label_support",
        "validation_warnings",
        "reason",
        "notes",
        "source_count",
    ]
    return write_csv(path, rows, fields)


def write_validated_timeline_json(path: Path, rows: list[dict[str, Any]]) -> Path:
    """Write validated timeline JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def nearest_candidate(label: dict[str, Any], candidates: list[dict[str, Any]], frame_tolerance: int) -> dict[str, Any] | None:
    """Find nearest candidate within a frame tolerance."""
    frame = int(label["frame_index"])
    eligible = [candidate for candidate in candidates if abs(int(candidate["frame_index"]) - frame) <= frame_tolerance]
    if not eligible:
        return None
    return min(
        eligible,
        key=lambda candidate: (
            abs(int(candidate["frame_index"]) - frame),
            math.dist((float(label["x"]), float(label["y"])), (float(candidate["x"]), float(candidate["y"]))),
        ),
    )


def nearest_label(event: dict[str, Any], labels: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Find nearest visible label to an event frame."""
    if not labels:
        return None
    frame = int(event["frame_index"])
    return min(labels, key=lambda label: abs(int(label["frame_index"]) - frame))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> Path:
    """Write rows to CSV."""
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
