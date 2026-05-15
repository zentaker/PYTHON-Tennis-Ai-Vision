"""Proxy feature extraction for Stage 8.4 bounce candidate propagation."""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any


def load_ball_sequence(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Load ball sequence rows from projected labels, tuned zones, or trajectory CSV."""
    if not path.exists():
        return [], [f"Ball sequence missing: {path}"]
    rows: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            frame = int_or_none(row.get("frame_index"))
            if frame is None:
                continue
            rows.append(
                {
                    "frame_index": frame,
                    "timestamp_seconds": float_or_none(row.get("timestamp_seconds")),
                    "x": float_or_none(row.get("x") or row.get("image_x")),
                    "y": float_or_none(row.get("y") or row.get("image_y")),
                    "projected_x": float_or_none(row.get("projected_x")),
                    "projected_y": float_or_none(row.get("projected_y")),
                    "source": row.get("source") or path.name,
                }
            )
    return sorted(rows, key=lambda item: int(item["frame_index"])), []


def compute_local_motion_features(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compute local proxy motion features for each ball point."""
    features: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        previous = rows[index - 1] if index > 0 else None
        next_row = rows[index + 1] if index + 1 < len(rows) else None
        delta_x = diff(row, previous, "x")
        delta_y = diff(row, previous, "y")
        next_delta_y = diff(next_row, row, "y") if next_row else None
        projected_delta_x = diff(row, previous, "projected_x")
        projected_delta_y = diff(row, previous, "projected_y")
        next_projected_delta_y = diff(next_row, row, "projected_y") if next_row else None
        local_speed = magnitude(delta_x, delta_y)
        next_speed = magnitude(diff(next_row, row, "x") if next_row else None, next_delta_y)
        projected_speed = magnitude(projected_delta_x, projected_delta_y)
        feature = {
            **row,
            "delta_x": delta_x,
            "delta_y": delta_y,
            "projected_delta_x": projected_delta_x,
            "projected_delta_y": projected_delta_y,
            "next_delta_y": next_delta_y,
            "next_projected_delta_y": next_projected_delta_y,
            "local_speed": local_speed,
            "projected_speed": projected_speed,
            "local_acceleration_proxy": None if local_speed is None or next_speed is None else next_speed - local_speed,
        }
        features.append(feature)
    return compute_height_proxy_features(compute_depth_turning_points(compute_direction_change_features(features)))


def compute_direction_change_features(features: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Mark image and projected direction changes as proxy bounce signals."""
    for row in features:
        row["image_y_direction_change"] = sign_change(row.get("delta_y"), row.get("next_delta_y"))
        row["projected_y_direction_change"] = sign_change(row.get("projected_delta_y"), row.get("next_projected_delta_y"))
    return features


def compute_depth_turning_points(features: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Mark local projected-depth turning points."""
    for row in features:
        row["projected_depth_turning_point"] = bool(row.get("projected_y_direction_change"))
    return features


def compute_height_proxy_features(features: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create a proxy score from image-y and projected-y turning patterns."""
    for row in features:
        score = 0.0
        if row.get("image_y_direction_change"):
            score += 0.35
        if row.get("projected_y_direction_change"):
            score += 0.35
        accel = abs(float(row.get("local_acceleration_proxy") or 0.0))
        score += min(accel / 500.0, 0.2)
        row["height_proxy_score"] = round(min(score, 1.0), 3)
    return features


def extract_features_around_bounce_window(features: list[dict[str, Any]], window: dict[str, Any], radius: int = 1) -> list[dict[str, Any]]:
    """Extract local feature rows around a manual bounce window."""
    center = int(window["center_frame"])
    sorted_features = sorted(features, key=lambda row: abs(int(row["frame_index"]) - center))
    return sorted_features[: max(radius * 2 + 1, 1)]


def summarize_manual_bounce_pattern(features: list[dict[str, Any]], windows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize the weak manual bounce signature from labeled bounce windows."""
    rows: list[dict[str, Any]] = []
    for window in windows:
        rows.extend(extract_features_around_bounce_window(features, window, radius=1))
    if not rows:
        return {"pattern_confidence": "missing", "mean_height_proxy_score": 0.0, "notes": "No manual bounce feature rows available."}
    mean_proxy = sum(float(row.get("height_proxy_score") or 0.0) for row in rows) / len(rows)
    direction_rows = sum(1 for row in rows if row.get("image_y_direction_change") or row.get("projected_y_direction_change"))
    confidence = "weak" if len(windows) == 1 else "medium"
    return {
        "pattern_confidence": confidence,
        "mean_height_proxy_score": round(mean_proxy, 3),
        "direction_change_rows": direction_rows,
        "manual_feature_rows": len(rows),
        "notes": "Only one bounce window is available; propagation is a review aid, not validation." if len(windows) == 1 else "Multiple bounce windows provide a stronger pattern.",
    }


def diff(current: dict[str, Any] | None, previous: dict[str, Any] | None, key: str) -> float | None:
    if current is None or previous is None:
        return None
    a = current.get(key)
    b = previous.get(key)
    if a is None or b is None:
        return None
    return float(a) - float(b)


def sign_change(a: Any, b: Any) -> bool:
    if a in (None, 0) or b in (None, 0):
        return False
    return (float(a) < 0 < float(b)) or (float(a) > 0 > float(b))


def magnitude(x: Any, y: Any) -> float | None:
    if x is None or y is None:
        return None
    return math.sqrt(float(x) ** 2 + float(y) ** 2)


def float_or_none(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def int_or_none(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None
