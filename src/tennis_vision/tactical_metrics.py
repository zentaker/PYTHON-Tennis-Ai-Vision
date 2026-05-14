"""Tactical metrics helpers for Stage 9 prototypes."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Any

from tennis_vision.court_zones import assign_court_zone


def read_csv_rows(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Read CSV rows, returning warnings instead of raising for missing files."""
    if not path.exists():
        return [], [f"Missing CSV: {path}"]
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle)), []


def float_or_none(value: Any) -> float | None:
    """Convert a value to float when possible."""
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def int_or_none(value: Any) -> int | None:
    """Convert a value to int when possible."""
    try:
        if value in (None, ""):
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def build_ball_zone_assignments(
    *,
    labels: list[dict[str, Any]],
    trajectory_rows: list[dict[str, Any]],
    projected_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Create approximate court zone assignments for visible ball points."""
    projected_by_frame = {int(row["frame_index"]): row for row in projected_rows if int_or_none(row.get("frame_index")) is not None}
    trajectory_by_frame = {int(row["frame_index"]): row for row in trajectory_rows if int_or_none(row.get("frame_index")) is not None}
    rows: list[dict[str, Any]] = []
    for label in labels:
        visible = str(label.get("visible", "")).lower() in {"true", "1", "yes"} or label.get("visible") is True
        frame = int_or_none(label.get("frame_index"))
        if not visible or frame is None:
            continue
        projected = projected_by_frame.get(frame, {})
        trajectory = trajectory_by_frame.get(frame, {})
        projected_x = float_or_none(projected.get("projected_x") or trajectory.get("smooth_projected_x") or trajectory.get("raw_projected_x"))
        projected_y = float_or_none(projected.get("projected_y") or trajectory.get("smooth_projected_y") or trajectory.get("raw_projected_y"))
        zone = assign_court_zone(projected_x, projected_y)
        rows.append(
            {
                "frame_index": frame,
                "timestamp_seconds": trajectory.get("timestamp_seconds", ""),
                "x": float_or_none(label.get("x")),
                "y": float_or_none(label.get("y")),
                "projected_x": projected_x,
                "projected_y": projected_y,
                "court_zone": zone["zone_id"],
                "depth": zone["depth"],
                "lateral_lane": zone["lateral_lane"],
                "side": zone["side"],
                "source": label.get("source") or "manual_label",
                "confidence_like_score": zone["confidence_like_score"],
                "notes": zone["notes"],
            }
        )
    return sorted(rows, key=lambda row: int(row["frame_index"]))


def estimate_shot_directions(zone_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Estimate approximate direction between consecutive projected ball points."""
    rows: list[dict[str, Any]] = []
    usable = [row for row in zone_rows if row.get("court_zone") != "unknown"]
    for start, end in zip(usable, usable[1:]):
        start_lane = start.get("lateral_lane")
        end_lane = end.get("lateral_lane")
        start_side = start.get("side")
        end_side = end.get("side")
        if start_lane == "unknown" or end_lane == "unknown":
            direction = "unknown"
            confidence = 0.25
            reason = "One or both points had unknown lateral lane."
        elif start_side == end_side:
            direction = "center_like" if start_lane == end_lane else "unknown"
            confidence = 0.35
            reason = "Consecutive points are on the same side, so shot direction is weak evidence."
        elif start_lane == end_lane:
            direction = "down_the_line_like"
            confidence = 0.55
            reason = "Ball moved between court sides while staying in the same lateral lane."
        elif {start_lane, end_lane} <= {"left", "right"}:
            direction = "crosscourt_like"
            confidence = 0.55
            reason = "Ball moved between sides and crossed lateral lanes."
        else:
            direction = "center_like"
            confidence = 0.45
            reason = "Ball moved through the center lane; direction is approximate."
        rows.append(
            {
                "from_frame": start["frame_index"],
                "to_frame": end["frame_index"],
                "from_zone": start["court_zone"],
                "to_zone": end["court_zone"],
                "direction_type": direction,
                "confidence_like_score": confidence,
                "reason": reason,
            }
        )
    return rows


def summarize_player_context(refined_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize Stage 7.1 refined ball-player associations."""
    counts = Counter(row.get("nearest_player_id") or "unknown" for row in refined_rows)
    distances = [float_or_none(row.get("image_distance_px")) for row in refined_rows]
    distances = [value for value in distances if value is not None]
    return {
        "player_a_associated_events": counts.get("player_a", 0),
        "player_b_associated_events": counts.get("player_b", 0),
        "unknown_player_events": counts.get("unknown", 0) + counts.get("", 0),
        "average_ball_player_distance_px": round(sum(distances) / len(distances), 3) if distances else None,
    }


def build_rally_tactical_summary(rally_rows: list[dict[str, Any]], zone_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach dominant zone/depth/lane summaries to Stage 8 rally segments."""
    summaries: list[dict[str, Any]] = []
    for index, rally in enumerate(rally_rows, start=1):
        start = int_or_none(rally.get("start_frame")) or 0
        end = int_or_none(rally.get("end_frame")) or start
        segment_points = [row for row in zone_rows if start <= int(row["frame_index"]) <= end]
        dominant_depth = most_common(row.get("depth") for row in segment_points)
        dominant_lane = most_common(row.get("lateral_lane") for row in segment_points)
        dominant_zone = most_common(row.get("court_zone") for row in segment_points)
        summaries.append(
            {
                "rally_id": rally.get("rally_id") or f"rally_{index:03d}",
                "start_frame": start,
                "end_frame": end,
                "duration_seconds": rally.get("duration_seconds", ""),
                "event_count": rally.get("event_count", 0),
                "possible_hit_count": rally.get("possible_hit_count", 0),
                "possible_bounce_count": rally.get("possible_bounce_count", 0),
                "dominant_depth": dominant_depth,
                "dominant_lateral_lane": dominant_lane,
                "dominant_zone": dominant_zone,
                "confidence_like_score": rally.get("confidence_like_score", 0.5),
                "notes": "Prototype tactical summary from validated timeline and approximate zones.",
            }
        )
    return summaries


def distribution(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    """Count values for a row field."""
    counts = Counter(str(row.get(key) or "unknown") for row in rows)
    return dict(sorted(counts.items()))


def most_common(values: Any) -> str:
    """Return the most common non-empty value from an iterable."""
    filtered = [str(value) for value in values if value not in (None, "")]
    if not filtered:
        return "unknown"
    return Counter(filtered).most_common(1)[0][0]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> Path:
    """Write rows to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    return path


def write_tactical_summary(path: Path, summary: dict[str, Any]) -> Path:
    """Write a plain-text-friendly tactical summary."""
    lines = [
        "# Stage 9 Tactical Summary",
        "",
        "SUMMARY:",
        f"  Ball points analyzed: {summary['ball_points_analyzed']}",
        f"  Projected points: {summary['projected_points_count']}",
        f"  Most frequent zone: {summary['most_frequent_zone']}",
        f"  Dominant depth: {summary['dominant_depth']}",
        f"  Dominant lateral lane: {summary['dominant_lateral_lane']}",
        "",
        "INTERPRETATION:",
        "  These metrics are approximate. They turn validated trajectory and",
        "  court projection data into first-pass tennis-readable placement",
        "  signals. They are not official scoring, line calling, or confirmed",
        "  shot classification.",
        "",
        "NEXT STEP:",
        f"  {summary['recommended_next_step']}",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path
