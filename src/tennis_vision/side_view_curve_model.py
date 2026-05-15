"""Synthetic curved side-view trajectory model for manual full-rally replay."""

from __future__ import annotations

import json
from typing import Any


def curve_profile_for_shot_type(shot_type: str | None) -> dict[str, Any]:
    """Return a visual curve profile for a tennis shot type."""
    text = str(shot_type or "").lower()
    if "serve_topspin" in text:
        return {"name": "serve_topspin", "apex": 155.0, "hit_height": 112.0, "bounce_height": 0.0, "net_clearance": 84.0, "drop_bias": 1.22}
    if "topspin_adjusted" in text:
        return {"name": "topspin_adjusted", "apex": 128.0, "hit_height": 88.0, "bounce_height": 0.0, "net_clearance": 66.0, "drop_bias": 1.12}
    if "topspin" in text:
        return {"name": "topspin", "apex": 138.0, "hit_height": 92.0, "bounce_height": 0.0, "net_clearance": 72.0, "drop_bias": 1.18}
    if "slice" in text:
        return {"name": "slice", "apex": 82.0, "hit_height": 76.0, "bounce_height": 0.0, "net_clearance": 50.0, "drop_bias": 0.82}
    if "flat" in text:
        return {"name": "flat", "apex": 96.0, "hit_height": 86.0, "bounce_height": 0.0, "net_clearance": 58.0, "drop_bias": 0.92}
    return {"name": "default_tennis_arc", "apex": 112.0, "hit_height": 84.0, "bounce_height": 0.0, "net_clearance": 62.0, "drop_bias": 1.0}


def event_height(event: dict[str, Any], profile: dict[str, Any]) -> float:
    """Return synthetic side-view anchor height for an event."""
    event_type = str(event.get("event_type") or "").lower()
    if event_type == "bounce":
        return 0.0
    return float(profile.get("hit_height") or 84.0)


def build_bezier_control_points(start: dict[str, Any], end: dict[str, Any], profile: dict[str, Any]) -> list[dict[str, float]]:
    """Build cubic Bezier control points for one visual tennis arc segment."""
    x0 = float(start["side_x"])
    y0 = float(start["height"])
    x3 = float(end["side_x"])
    y3 = float(end["height"])
    span = x3 - x0
    apex = max(float(profile["apex"]), y0, y3)
    c1 = {"x": x0 + span * 0.33, "height": apex}
    c2 = {"x": x0 + span * 0.67, "height": apex * float(profile.get("drop_bias") or 1.0)}
    return [{"x": x0, "height": y0}, c1, c2, {"x": x3, "height": y3}]


def enforce_net_clearance(control_points: list[dict[str, float]], profile: dict[str, Any], *, net_x: float) -> tuple[list[dict[str, float]], bool]:
    """Raise the curve controls when the sampled net height is visually too low."""
    sampled = sample_curve_points(control_points, samples=31)
    nearest = min(sampled, key=lambda point: abs(point["x"] - net_x), default=None)
    clearance = float(profile.get("net_clearance") or 60.0)
    if nearest is None or nearest["height"] >= clearance:
        return control_points, False
    adjusted = [dict(point) for point in control_points]
    lift = clearance - nearest["height"] + 10.0
    adjusted[1]["height"] += lift
    adjusted[2]["height"] += lift
    return adjusted, True


def sample_curve_points(control_points: list[dict[str, float]], samples: int = 24) -> list[dict[str, float]]:
    """Sample cubic Bezier curve points."""
    if len(control_points) != 4:
        return []
    p0, p1, p2, p3 = control_points
    rows: list[dict[str, float]] = []
    for index in range(samples):
        t = index / max(1, samples - 1)
        omt = 1.0 - t
        x = omt**3 * p0["x"] + 3 * omt**2 * t * p1["x"] + 3 * omt * t**2 * p2["x"] + t**3 * p3["x"]
        height = omt**3 * p0["height"] + 3 * omt**2 * t * p1["height"] + 3 * omt * t**2 * p2["height"] + t**3 * p3["height"]
        rows.append({"x": round(x, 3), "height": round(max(0.0, height), 3), "t": round(t, 4)})
    return rows


def build_side_view_curve_segments(events: list[dict[str, Any]], *, court_height: float = 780.0) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build synthetic curved side-view segments between resolved physical events."""
    physical = [event for event in events if event.get("should_render_as_physical_event") == "yes" and event.get("position_status") == "resolved"]
    segments: list[dict[str, Any]] = []
    sampled_points: list[dict[str, Any]] = []
    net_x = court_height / 2.0
    for index, (start_event, end_event) in enumerate(zip(physical, physical[1:]), start=1):
        shot_type = start_event.get("shot_type") if start_event.get("event_type") == "hit" else ""
        profile = curve_profile_for_shot_type(shot_type)
        start = {
            "side_x": float(start_event.get("projected_y") or 0.0),
            "height": event_height(start_event, profile),
        }
        end = {
            "side_x": float(end_event.get("projected_y") or start["side_x"]),
            "height": event_height(end_event, profile),
        }
        controls = build_bezier_control_points(start, end, profile)
        crosses_net = min(start["side_x"], end["side_x"]) <= net_x <= max(start["side_x"], end["side_x"])
        adjusted = False
        if crosses_net:
            controls, adjusted = enforce_net_clearance(controls, profile, net_x=net_x)
        samples = sample_curve_points(controls, samples=24)
        segment_id = f"curve_{index:03d}"
        for sample_index, point in enumerate(samples):
            ratio = point["t"]
            lateral = _lerp(_float(start_event.get("projected_x")), _float(end_event.get("projected_x")), ratio)
            sampled_points.append(
                {
                    "segment_id": segment_id,
                    "sample_index": sample_index,
                    "x": point["x"],
                    "height": point["height"],
                    "projected_x": lateral,
                    "from_event_id": start_event.get("event_id"),
                    "to_event_id": end_event.get("event_id"),
                    "shot_type": shot_type,
                    "curve_profile": profile["name"],
                }
            )
        segments.append(
            {
                "segment_id": segment_id,
                "from_event_id": start_event.get("event_id"),
                "to_event_id": end_event.get("event_id"),
                "from_event_type": start_event.get("event_type"),
                "to_event_type": end_event.get("event_type"),
                "shot_type": shot_type,
                "curve_profile": profile["name"],
                "curve_type": "cubic_bezier",
                "control_points": json.dumps(controls),
                "synthetic_height_model": "shot_type_weighted_visual_bezier_not_measured_3d",
                "net_clearance_adjusted": "yes" if adjusted else "no",
                "notes": "Synthetic tennis-like side-view curve for interpretability; not measured physics.",
            }
        )
    return segments, sampled_points


def write_side_view_curve_segments(path: Any, rows: list[dict[str, Any]]) -> None:
    """Write side-view curve segments to CSV."""
    import csv
    from pathlib import Path

    fields = [
        "segment_id",
        "from_event_id",
        "to_event_id",
        "from_event_type",
        "to_event_type",
        "shot_type",
        "curve_profile",
        "curve_type",
        "control_points",
        "synthetic_height_model",
        "net_clearance_adjusted",
        "notes",
    ]
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _lerp(a: float | None, b: float | None, t: float) -> float | None:
    if a is None or b is None:
        return None
    return round(a + (b - a) * t, 3)


def _float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
