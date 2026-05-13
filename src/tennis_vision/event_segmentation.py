"""Simple event segmentation heuristics for Stage 6."""

from __future__ import annotations

import csv
import math
from collections import Counter
from pathlib import Path
from typing import Any


def detect_events(raw_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    """Detect hypothesis-level trajectory events from raw candidate points."""
    warnings: list[str] = []
    events: list[dict[str, Any]] = []
    if len(raw_rows) < 5:
        warnings.append("Too few trajectory points for reliable event segmentation.")
    if len(raw_rows) < 3:
        return events, warnings

    velocities = _velocities(raw_rows)
    speeds = [item["speed"] for item in velocities]
    median_speed = _median(speeds) or 0.0

    for index in range(1, len(raw_rows) - 1):
        previous = raw_rows[index - 1]
        current = raw_rows[index]
        next_row = raw_rows[index + 1]
        before = _vector(previous, current)
        after = _vector(current, next_row)
        before_speed = math.hypot(before[0], before[1])
        after_speed = math.hypot(after[0], after[1])
        angle = _angle_between(before, after)
        if angle is not None and angle >= 35:
            events.append(_event(current, "direction_change", min(angle / 90.0, 1.0), f"Trajectory direction changed by {angle:.1f} degrees."))
        if median_speed and after_speed >= median_speed * 1.45 and after_speed - before_speed > 2:
            events.append(_event(current, "speed_spike", min(after_speed / max(median_speed, 1.0) / 2.0, 1.0), "Image-space speed increased sharply."))
        if before_speed > 0 and after_speed <= before_speed * 0.55:
            events.append(_event(current, "speed_drop", min((before_speed - after_speed) / max(before_speed, 1.0), 1.0), "Image-space speed dropped sharply."))
        if before[1] * after[1] < 0 or (abs(after[1]) < abs(before[1]) * 0.35 and before[1] > 0):
            events.append(_event(current, "possible_bounce", 0.45, "Vertical image motion changed; hypothesis only."))
        if angle is not None and angle >= 25 and (after_speed > before_speed * 1.2 or before_speed > after_speed * 1.2):
            events.append(_event(current, "possible_hit", 0.4, "Direction and speed changed together; hypothesis only."))

    deduped = _dedupe_events(events)
    return deduped, warnings


def events_by_type(events: list[dict[str, Any]]) -> dict[str, int]:
    """Count events by type."""
    return dict(Counter(event["event_type"] for event in events))


def write_events_csv(path: Path, events: list[dict[str, Any]]) -> Path:
    """Write event hypotheses to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["frame_index", "event_type", "confidence_like_score", "reason", "x", "y", "projected_x", "projected_y"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for event in events:
            writer.writerow({field: event.get(field, "") for field in fields})
    return path


def _velocities(rows: list[dict[str, Any]]) -> list[dict[str, float]]:
    values: list[dict[str, float]] = []
    for previous, current in zip(rows, rows[1:]):
        delta_frame = max(float(current["frame_index"] - previous["frame_index"]), 1.0)
        vector = ((current["x"] - previous["x"]) / delta_frame, (current["y"] - previous["y"]) / delta_frame)
        values.append({"frame_index": current["frame_index"], "vx": vector[0], "vy": vector[1], "speed": math.hypot(vector[0], vector[1])})
    return values


def _vector(start: dict[str, Any], end: dict[str, Any]) -> tuple[float, float]:
    delta_frame = max(float(end["frame_index"] - start["frame_index"]), 1.0)
    return ((float(end["x"]) - float(start["x"])) / delta_frame, (float(end["y"]) - float(start["y"])) / delta_frame)


def _angle_between(first: tuple[float, float], second: tuple[float, float]) -> float | None:
    first_norm = math.hypot(first[0], first[1])
    second_norm = math.hypot(second[0], second[1])
    if first_norm == 0 or second_norm == 0:
        return None
    cosine = max(-1.0, min(1.0, (first[0] * second[0] + first[1] * second[1]) / (first_norm * second_norm)))
    return math.degrees(math.acos(cosine))


def _event(row: dict[str, Any], event_type: str, score: float, reason: str) -> dict[str, Any]:
    return {
        "frame_index": int(row["frame_index"]),
        "event_type": event_type,
        "confidence_like_score": round(max(0.0, min(score, 1.0)), 3),
        "reason": reason,
        "x": round(float(row["x"]), 3),
        "y": round(float(row["y"]), 3),
        "projected_x": row.get("projected_x"),
        "projected_y": row.get("projected_y"),
    }


def _dedupe_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[int, str]] = set()
    deduped: list[dict[str, Any]] = []
    for event in sorted(events, key=lambda item: (item["frame_index"], item["event_type"])):
        key = (int(event["frame_index"]), str(event["event_type"]))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(event)
    return deduped


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2
