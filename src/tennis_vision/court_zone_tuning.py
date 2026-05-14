"""Court zone tuning helpers for Stage 9.1."""

from __future__ import annotations

from collections import Counter
from typing import Any

from tennis_vision.court_zones import COURT_HEIGHT, COURT_WIDTH, classify_depth, classify_lateral_lane, infer_side


TUNING_MARGIN = 120.0


def validate_zone_bounds(projected_x: float | None, projected_y: float | None, margin: float = TUNING_MARGIN) -> dict[str, Any]:
    """Validate whether projected coordinates are inside or near the expected court range."""
    if projected_x is None or projected_y is None:
        return {"status": "missing_projection", "inside_or_near": False}
    x_value = float(projected_x)
    y_value = float(projected_y)
    inside = 0 <= x_value <= COURT_WIDTH and 0 <= y_value <= COURT_HEIGHT
    near = -margin <= x_value <= COURT_WIDTH + margin and -margin <= y_value <= COURT_HEIGHT + margin
    if inside:
        status = "inside_bounds"
    elif near:
        status = "near_bounds"
    else:
        status = "out_of_bounds"
    return {"status": status, "inside_or_near": near, "inside": inside}


def classify_tuned_lateral_lane(projected_x: float | None) -> str:
    """Classify tuned lateral lane with a slightly wider tolerance."""
    if projected_x is None:
        return "unknown"
    x_value = min(max(float(projected_x), 0.0), COURT_WIDTH)
    return classify_lateral_lane(x_value)


def classify_tuned_depth(projected_y: float | None) -> str:
    """Classify tuned depth with a slightly wider tolerance."""
    if projected_y is None:
        return "unknown"
    y_value = min(max(float(projected_y), 0.0), COURT_HEIGHT)
    return classify_depth(y_value)


def assign_tuned_court_zone(projected_x: float | None, projected_y: float | None, config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Assign a tuned zone while keeping out-of-bounds uncertainty visible."""
    bounds = validate_zone_bounds(projected_x, projected_y, float((config or {}).get("margin", TUNING_MARGIN)))
    if bounds["status"] == "missing_projection":
        return {
            "tuned_zone": "unknown",
            "tuned_depth": "unknown",
            "tuned_lateral_lane": "unknown",
            "side": "unknown",
            "zone_confidence": 0.2,
            "notes": "Missing projection; cannot tune zone.",
        }
    lane = classify_tuned_lateral_lane(projected_x)
    depth = classify_tuned_depth(projected_y)
    side = infer_side(min(max(float(projected_y), 0.0), COURT_HEIGHT))
    if bounds["status"] == "out_of_bounds":
        return {
            "tuned_zone": "out_of_bounds",
            "tuned_depth": depth,
            "tuned_lateral_lane": lane,
            "side": side,
            "zone_confidence": 0.35,
            "notes": "Projected point is outside the tuned court tolerance; not a confident tactical zone.",
        }
    zone = f"{side}_{depth}_{lane}"
    confidence = 0.85 if bounds["status"] == "inside_bounds" else 0.65
    return {
        "tuned_zone": zone,
        "tuned_depth": depth,
        "tuned_lateral_lane": lane,
        "side": side,
        "zone_confidence": confidence,
        "notes": "Tuned approximate court zone; not official line calling.",
    }


def tune_zone_assignments(merged_rows: list[dict[str, Any]], config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Apply tuned zone assignment to projected expanded labels."""
    rows: list[dict[str, Any]] = []
    for row in merged_rows:
        projected_x = _float_or_none(row.get("projected_x"))
        projected_y = _float_or_none(row.get("projected_y"))
        tuned = assign_tuned_court_zone(projected_x, projected_y, config)
        rows.append(
            {
                "frame_index": row.get("frame_index"),
                "x": row.get("x"),
                "y": row.get("y"),
                "projected_x": row.get("projected_x"),
                "projected_y": row.get("projected_y"),
                "original_zone": row.get("original_zone", "unknown"),
                "tuned_zone": tuned["tuned_zone"],
                "original_depth": row.get("original_depth", "unknown"),
                "tuned_depth": tuned["tuned_depth"],
                "original_lateral_lane": row.get("original_lateral_lane", "unknown"),
                "tuned_lateral_lane": tuned["tuned_lateral_lane"],
                "projection_status": row.get("projection_status"),
                "zone_confidence": tuned["zone_confidence"],
                "notes": tuned["notes"],
            }
        )
    return rows


def summarize_zone_coverage(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize tuned zone coverage."""
    tuned_zones = Counter(str(row.get("tuned_zone") or "unknown") for row in rows)
    depths = Counter(str(row.get("tuned_depth") or "unknown") for row in rows)
    lanes = Counter(str(row.get("tuned_lateral_lane") or "unknown") for row in rows)
    unknown = tuned_zones.get("unknown", 0)
    return {
        "tuned_zone_distribution": dict(sorted(tuned_zones.items())),
        "tuned_depth_distribution": dict(sorted(depths.items())),
        "tuned_lateral_distribution": dict(sorted(lanes.items())),
        "stage_9_1_unknown_zones": unknown,
    }


def compare_stage_9_to_9_1(stage_9_rows: list[dict[str, Any]], tuned_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build before/after zone comparison rows."""
    stage_9_by_frame = {int(float(row["frame_index"])): row for row in stage_9_rows if row.get("frame_index")}
    rows: list[dict[str, Any]] = []
    for tuned in tuned_rows:
        frame = int(float(tuned["frame_index"]))
        original = stage_9_by_frame.get(frame, {})
        stage_9_projection = bool(original.get("projected_x") and original.get("projected_y"))
        stage_9_1_projection = bool(tuned.get("projected_x") not in (None, "") and tuned.get("projected_y") not in (None, ""))
        if original.get("court_zone") == "unknown" and tuned.get("tuned_zone") != "unknown":
            status = "improved_from_unknown"
        elif stage_9_1_projection and not stage_9_projection:
            status = "projection_added"
        elif tuned.get("tuned_zone") == original.get("court_zone"):
            status = "unchanged"
        else:
            status = "changed"
        rows.append(
            {
                "frame_index": frame,
                "stage_9_zone": original.get("court_zone", "unknown"),
                "stage_9_1_zone": tuned.get("tuned_zone", "unknown"),
                "stage_9_depth": original.get("depth", "unknown"),
                "stage_9_1_depth": tuned.get("tuned_depth", "unknown"),
                "stage_9_projection_available": stage_9_projection,
                "stage_9_1_projection_available": stage_9_1_projection,
                "improvement_status": status,
            }
        )
    return rows


def _float_or_none(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
