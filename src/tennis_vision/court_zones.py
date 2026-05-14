"""Simple normalized court zones for tactical prototypes."""

from __future__ import annotations

from typing import Any


COURT_WIDTH = 360.0
COURT_HEIGHT = 780.0
COURT_MARGIN = 80.0


def classify_lateral_lane(projected_x: float | None) -> str:
    """Classify normalized court x position into left, center, or right."""
    if projected_x is None:
        return "unknown"
    x_value = float(projected_x)
    if x_value < -COURT_MARGIN or x_value > COURT_WIDTH + COURT_MARGIN:
        return "unknown"
    clamped = min(max(x_value, 0.0), COURT_WIDTH)
    if clamped < COURT_WIDTH / 3:
        return "left"
    if clamped < (COURT_WIDTH * 2) / 3:
        return "center"
    return "right"


def infer_side(projected_y: float | None) -> str:
    """Infer near or far court side from normalized y position."""
    if projected_y is None:
        return "unknown"
    y_value = float(projected_y)
    if y_value < -COURT_MARGIN or y_value > COURT_HEIGHT + COURT_MARGIN:
        return "unknown"
    return "far" if y_value < COURT_HEIGHT / 2 else "near"


def classify_depth(projected_y: float | None) -> str:
    """Classify normalized court y position as short, mid, or deep."""
    side = infer_side(projected_y)
    if side == "unknown" or projected_y is None:
        return "unknown"
    y_value = min(max(float(projected_y), 0.0), COURT_HEIGHT)
    half = COURT_HEIGHT / 2
    if side == "far":
        if y_value < half / 3:
            return "deep"
        if y_value < (half * 2) / 3:
            return "mid"
        return "short"
    distance_from_near_baseline = COURT_HEIGHT - y_value
    if distance_from_near_baseline < half / 3:
        return "deep"
    if distance_from_near_baseline < (half * 2) / 3:
        return "mid"
    return "short"


def assign_court_zone(projected_x: float | None, projected_y: float | None) -> dict[str, Any]:
    """Assign a projected ball point to an approximate tactical court zone."""
    lane = classify_lateral_lane(projected_x)
    depth = classify_depth(projected_y)
    side = infer_side(projected_y)
    if "unknown" in {lane, depth, side}:
        return {
            "zone_id": "unknown",
            "depth": depth,
            "lateral_lane": lane,
            "side": side,
            "confidence_like_score": 0.25,
            "notes": "Projection was missing or outside the expected normalized court range.",
        }
    zone_id = f"{side}_{depth}_{lane}"
    y_value = float(projected_y)
    x_value = float(projected_x)
    near_edge = (
        x_value < 0
        or x_value > COURT_WIDTH
        or y_value < 0
        or y_value > COURT_HEIGHT
    )
    return {
        "zone_id": zone_id,
        "depth": depth,
        "lateral_lane": lane,
        "side": side,
        "confidence_like_score": 0.7 if near_edge else 0.9,
        "notes": "Approximate zone from normalized court coordinates; not official line calling.",
    }


def describe_zone(zone_id: str) -> str:
    """Return a plain-language description for a court zone id."""
    if zone_id == "unknown":
        return "Unknown court zone."
    parts = zone_id.split("_")
    if len(parts) != 3:
        return "Approximate court zone."
    side, depth, lane = parts
    return f"{side} side, {depth} court, {lane} lane."
