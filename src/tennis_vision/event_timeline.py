"""Event timeline helpers for Stage 8."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any


def read_smoothed_trajectory(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Read Stage 6 smoothed trajectory rows."""
    if not path.exists():
        return [], [f"Smoothed trajectory CSV not found: {path}"]
    rows: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                rows.append(
                    {
                        "frame_index": int(float(row["frame_index"])),
                        "ball_x": float(row["smooth_x"]),
                        "ball_y": float(row["smooth_y"]),
                        "ball_projected_x": _float_or_none(row.get("smooth_projected_x")),
                        "ball_projected_y": _float_or_none(row.get("smooth_projected_y")),
                        "is_interpolated": str(row.get("is_interpolated", "")).lower() == "true",
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
    return sorted(rows, key=lambda item: item["frame_index"]), []


def read_stage_events(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Read Stage 6 trajectory event hypotheses."""
    if not path.exists():
        return [], [f"Stage 6 trajectory events CSV not found: {path}"]
    rows: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                event_type = normalize_event_type(row.get("event_type", "unknown"))
                rows.append(
                    {
                        "frame_index": int(float(row["frame_index"])),
                        "event_type": event_type,
                        "event_source": "stage_6_trajectory_events",
                        "player_id": "",
                        "player_side_state": "",
                        "ball_x": _float_or_none(row.get("x")),
                        "ball_y": _float_or_none(row.get("y")),
                        "ball_projected_x": _float_or_none(row.get("projected_x")),
                        "ball_projected_y": _float_or_none(row.get("projected_y")),
                        "confidence_like_score": _float_or_none(row.get("confidence_like_score")) or 0.35,
                        "reason": row.get("reason", ""),
                        "notes": "Stage 6 event hypothesis.",
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
    return rows, []


def read_interactions(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Read Stage 7 interaction hypotheses."""
    if not path.exists():
        return [], [f"Stage 7 interaction CSV not found: {path}"]
    rows: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                rows.append(
                    {
                        "frame_index": int(float(row["frame_index"])),
                        "event_type": normalize_event_type(row.get("interaction_type", "unknown")),
                        "event_source": "stage_7_interactions",
                        "player_id": "",
                        "player_side_state": "",
                        "ball_x": None,
                        "ball_y": None,
                        "ball_projected_x": None,
                        "ball_projected_y": None,
                        "confidence_like_score": _float_or_none(row.get("confidence_like_score")) or 0.25,
                        "reason": row.get("reason", ""),
                        "notes": f"Nearest Stage 7 track: {row.get('nearest_track_id', 'unknown')}",
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
    return rows, []


def read_refined_associations(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Read Stage 7.1 refined player associations."""
    if not path.exists():
        return [], [f"Stage 7.1 refined ball-player distance CSV not found: {path}"]
    rows: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                player_id = row.get("nearest_player_id", "")
                rows.append(
                    {
                        "frame_index": int(float(row["frame_index"])),
                        "event_type": "ball_near_player" if player_id else "unknown",
                        "event_source": "stage_7_1_refined_association",
                        "player_id": player_id,
                        "player_side_state": row.get("side_state", ""),
                        "ball_x": _float_or_none(row.get("ball_x")),
                        "ball_y": _float_or_none(row.get("ball_y")),
                        "ball_projected_x": None,
                        "ball_projected_y": None,
                        "confidence_like_score": _float_or_none(row.get("interaction_score")) or 0.2,
                        "reason": "Refined nearest player identity from Stage 7.1.",
                        "notes": row.get("notes", ""),
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
    return rows, []


def read_player_side_states(path: Path) -> dict[tuple[int, str], str]:
    """Read side state lookup by frame/player."""
    if not path.exists():
        return {}
    states: dict[tuple[int, str], str] = {}
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                states[(int(float(row["frame_index"])), row["player_id"])] = row.get("side_state", "")
            except (KeyError, TypeError, ValueError):
                continue
    return states


def make_trajectory_events(trajectory_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create timeline trajectory-point events from non-interpolated trajectory anchors."""
    events: list[dict[str, Any]] = []
    for row in trajectory_rows:
        if row.get("is_interpolated"):
            continue
        events.append(
            {
                "frame_index": row["frame_index"],
                "event_type": "trajectory_point",
                "event_source": "stage_6_smoothed_trajectory",
                "player_id": "",
                "player_side_state": "",
                "ball_x": row["ball_x"],
                "ball_y": row["ball_y"],
                "ball_projected_x": row.get("ball_projected_x"),
                "ball_projected_y": row.get("ball_projected_y"),
                "confidence_like_score": 0.85,
                "reason": "High-confidence smoothed trajectory anchor.",
                "notes": "Trajectory point, not a tennis event.",
            }
        )
    return events


def merge_timeline_events(events: list[dict[str, Any]], merge_window: int, fps: float | None) -> list[dict[str, Any]]:
    """Merge events within a frame window into timeline clusters."""
    sorted_events = sorted(events, key=lambda item: item["frame_index"])
    clusters: list[list[dict[str, Any]]] = []
    for event in sorted_events:
        if not clusters or event["frame_index"] - clusters[-1][-1]["frame_index"] > merge_window:
            clusters.append([event])
        else:
            clusters[-1].append(event)
    timeline: list[dict[str, Any]] = []
    for index, cluster in enumerate(clusters, start=1):
        primary = choose_primary_event(cluster)
        frame_index = int(round(mean([event["frame_index"] for event in cluster])))
        player_id = first_nonempty([event.get("player_id") for event in cluster])
        side_state = first_nonempty([event.get("player_side_state") for event in cluster])
        ball_x = first_number([event.get("ball_x") for event in cluster])
        ball_y = first_number([event.get("ball_y") for event in cluster])
        projected_x = first_number([event.get("ball_projected_x") for event in cluster])
        projected_y = first_number([event.get("ball_projected_y") for event in cluster])
        confidence = max(float(event.get("confidence_like_score") or 0) for event in cluster)
        timeline.append(
            {
                "event_id": f"evt_{index:03d}",
                "frame_index": frame_index,
                "timestamp_seconds": round(frame_index / fps, 3) if fps else None,
                "event_type": primary,
                "event_source": "+".join(sorted({event["event_source"] for event in cluster})),
                "player_id": player_id,
                "player_side_state": side_state,
                "ball_x": ball_x,
                "ball_y": ball_y,
                "ball_projected_x": projected_x,
                "ball_projected_y": projected_y,
                "confidence_like_score": round(confidence, 3),
                "reason": " | ".join(sorted({event.get("reason", "") for event in cluster if event.get("reason")})),
                "notes": f"source_count={len(cluster)}; source_events={','.join(event['event_type'] for event in cluster)}",
                "source_count": len(cluster),
                "source_events": [event["event_type"] for event in cluster],
            }
        )
    return timeline


def attach_player_side_states(timeline: list[dict[str, Any]], side_states: dict[tuple[int, str], str]) -> list[dict[str, Any]]:
    """Fill side state when player ID and frame match Stage 7.1 state data."""
    for event in timeline:
        if event.get("player_id") and not event.get("player_side_state"):
            event["player_side_state"] = side_states.get((event["frame_index"], event["player_id"]), "")
    return timeline


def write_timeline_csv(path: Path, rows: list[dict[str, Any]]) -> Path:
    """Write timeline CSV."""
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
        "reason",
        "notes",
        "source_count",
    ]
    write_csv(path, rows, fields)
    return path


def write_timeline_json(path: Path, rows: list[dict[str, Any]]) -> Path:
    """Write timeline JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")
    return path


def build_player_event_attribution(
    timeline_rows: list[dict[str, Any]],
    refined_associations: list[dict[str, Any]],
    *,
    merge_window: int,
) -> list[dict[str, Any]]:
    """Attach stable player identities to timeline events when nearby evidence exists."""
    rows: list[dict[str, Any]] = []
    for event in timeline_rows:
        match = nearest_refined_association(event, refined_associations, merge_window)
        player_id = event.get("player_id") or (match or {}).get("player_id") or "unknown"
        side_state = event.get("player_side_state") or (match or {}).get("player_side_state") or "unknown"
        rows.append(
            {
                "event_id": event["event_id"],
                "frame_index": event["frame_index"],
                "event_type": event["event_type"],
                "player_id": player_id,
                "player_side_state": side_state,
                "attribution_source": "stage_7_1_refined_association" if match else "timeline_event",
                "confidence_like_score": event.get("confidence_like_score"),
                "reason": "Stable player identity attached from Stage 7.1; near/far remains side state.",
            }
        )
    return rows


def write_player_event_attribution_csv(path: Path, rows: list[dict[str, Any]]) -> Path:
    """Write player event attribution rows to CSV."""
    fields = [
        "event_id",
        "frame_index",
        "event_type",
        "player_id",
        "player_side_state",
        "attribution_source",
        "confidence_like_score",
        "reason",
    ]
    write_csv(path, rows, fields)
    return path


def events_by_type(rows: list[dict[str, Any]]) -> dict[str, int]:
    """Count timeline events by type."""
    return dict(Counter(row["event_type"] for row in rows))


def nearest_refined_association(
    event: dict[str, Any],
    refined_associations: list[dict[str, Any]],
    merge_window: int,
) -> dict[str, Any] | None:
    """Find the nearest refined Stage 7.1 association around an event frame."""
    if not refined_associations:
        return None
    frame_index = int(event["frame_index"])
    candidates = [
        item
        for item in refined_associations
        if item.get("player_id") and abs(int(item["frame_index"]) - frame_index) <= merge_window
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda item: abs(int(item["frame_index"]) - frame_index))


def normalize_event_type(value: str) -> str:
    """Normalize source events to hypothesis-safe timeline event names."""
    mapping = {
        "possible_hit": "possible_hit",
        "possible_hit_window": "possible_hit",
        "possible_bounce": "possible_bounce",
        "direction_change": "possible_direction_change",
        "speed_spike": "possible_speed_spike",
        "speed_drop": "possible_speed_drop",
        "ball_near_player": "ball_near_player",
        "ball_approaching_player": "ball_approaching_player",
        "ball_leaving_player": "ball_leaving_player",
        "trajectory_point": "trajectory_point",
    }
    return mapping.get(value, "unknown")


def choose_primary_event(events: list[dict[str, Any]]) -> str:
    """Choose the most meaningful event type for a cluster."""
    priority = [
        "possible_hit",
        "possible_bounce",
        "ball_near_player",
        "ball_approaching_player",
        "ball_leaving_player",
        "possible_direction_change",
        "possible_speed_spike",
        "possible_speed_drop",
        "trajectory_point",
        "unknown",
    ]
    types = {event["event_type"] for event in events}
    for event_type in priority:
        if event_type in types:
            return event_type
    return "unknown"


def read_fps(stage_1_report: Path) -> float | None:
    """Read FPS from Stage 1 report."""
    try:
        report = json.loads(stage_1_report.read_text(encoding="utf-8"))
        fps = report.get("metadata", {}).get("fps")
        return float(fps) if fps else None
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> Path:
    """Write rows to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    return path


def first_nonempty(values: list[Any]) -> str:
    """Return first non-empty string-like value."""
    for value in values:
        if value not in (None, ""):
            return str(value)
    return ""


def first_number(values: list[Any]) -> float | None:
    """Return first non-empty numeric value rounded for reports."""
    for value in values:
        number = _float_or_none(value)
        if number is not None:
            return round(number, 3)
    return None


def _float_or_none(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
