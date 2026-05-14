"""Synthetic side-view ball flight estimation for replay rendering."""

from __future__ import annotations

import math
from typing import Any


BOUNCE_FLOOR_HEIGHT = 2.0
HIT_CONTACT_MIN_HEIGHT = 62.0
HIT_CONTACT_MAX_HEIGHT = 118.0
DEFAULT_ARC_MIN_HEIGHT = 34.0
DEFAULT_ARC_PEAK_HEIGHT = 155.0
PLAYER_CONTACT_DEPTH_TOLERANCE = 140.0


def load_replay_keyframes(schema: dict[str, Any]) -> list[dict[str, Any]]:
    """Load replay keyframes from the Stage 12 schema dictionary."""
    return list(schema.get("ball_trajectory", {}).get("replay_keyframes", []))


def extract_projected_ball_sequence(schema: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract replay keyframes that have projected court coordinates."""
    keyframes = load_replay_keyframes(schema)
    sequence = [row for row in keyframes if _float(row.get("projected_y")) is not None]
    return sorted(sequence, key=lambda row: (_int(row.get("frame_index")) is None, _int(row.get("frame_index")) or 0))


def estimate_side_view_depth(point: dict[str, Any], court_height: float) -> float | None:
    """Estimate side-view depth from projected court y coordinate."""
    projected_y = _float(point.get("projected_y"))
    if projected_y is None:
        return None
    return max(0.0, min(court_height, projected_y))


def estimate_synthetic_height(*, sequence_index: int, total_points: int, event_type: str | None = None) -> float:
    """Create a synthetic height profile when measured 3D ball height is unavailable."""
    role = classify_height_anchor_type(event_type)
    if role == "bounce_grounded":
        return enforce_bounce_floor_contact(DEFAULT_ARC_MIN_HEIGHT)
    if role == "hit_contact":
        return enforce_hit_contact_band(95.0)
    if total_points <= 1:
        return 45.0
    phase = sequence_index / max(total_points - 1, 1)
    return DEFAULT_ARC_MIN_HEIGHT + DEFAULT_ARC_PEAK_HEIGHT * abs(math.sin(phase * math.pi * 2.5))


def classify_height_anchor_type(event_type: str | None) -> str:
    """Classify an event into a synthetic side-view height role."""
    text = (event_type or "").lower()
    if "bounce" in text:
        return "bounce_grounded"
    if "hit" in text:
        return "hit_contact"
    if "ball_near_player" in text or "near_player" in text:
        return "interaction_cue"
    return "arc_estimate"


def classify_event_semantic_role(event: dict[str, Any], players: list[dict[str, Any]] | None = None) -> str:
    """Classify a raw event into a player-aware semantic role."""
    event_type = str(event.get("event_type") or "").lower()
    if "bounce" in event_type:
        return "bounce_plausible"
    if "hit" in event_type:
        return "hit_plausible" if is_hit_plausible_for_player(event, players or []) else "uncertain_event"
    if "ball_near_player" in event_type or "near_player" in event_type:
        return "player_interaction"
    return "uncertain_event"


def estimate_player_contact_window(player: dict[str, Any], frame_index: int | None, tolerance: float = PLAYER_CONTACT_DEPTH_TOLERANCE) -> dict[str, Any]:
    """Estimate a conservative court-depth contact window for one player."""
    state = nearest_player_state(player.get("side_states", []), frame_index)
    depth = _float(state.get("projected_y")) if state else None
    if depth is None:
        return {
            "player_id": player.get("player_id"),
            "player_depth": None,
            "min_depth": None,
            "max_depth": None,
            "side_state": state.get("side_state") if state else "unknown",
            "available": False,
        }
    return {
        "player_id": player.get("player_id"),
        "player_depth": depth,
        "min_depth": depth - tolerance,
        "max_depth": depth + tolerance,
        "side_state": state.get("side_state") or "unknown",
        "available": True,
    }


def score_hit_plausibility(event: dict[str, Any], players: list[dict[str, Any]], tolerance: float = PLAYER_CONTACT_DEPTH_TOLERANCE) -> dict[str, Any]:
    """Score whether a possible_hit is plausible relative to player depth."""
    event_frame = _int(event.get("frame_index"))
    player_id = str(event.get("player_id") or "")
    projected = event.get("projected_position", {})
    ball_depth = _float(projected.get("y"))
    player = next((item for item in players if str(item.get("player_id")) == player_id), None)
    if player is None or ball_depth is None:
        return {
            "plausible": False,
            "score": 0.0,
            "reason": "Missing player identity or projected ball depth.",
            "ball_depth": ball_depth,
            "player_depth": None,
            "depth_delta": None,
        }
    window = estimate_player_contact_window(player, event_frame, tolerance=tolerance)
    player_depth = window.get("player_depth")
    if player_depth is None:
        return {
            "plausible": False,
            "score": 0.0,
            "reason": "Missing player projected depth near event frame.",
            "ball_depth": ball_depth,
            "player_depth": None,
            "depth_delta": None,
        }
    depth_delta = abs(ball_depth - float(player_depth))
    score = max(0.0, 1.0 - (depth_delta / max(tolerance, 1.0)))
    plausible = depth_delta <= tolerance
    return {
        "plausible": plausible,
        "score": round(score, 3),
        "reason": "Ball depth is within player contact window." if plausible else "Ball depth is too far from attributed player depth.",
        "ball_depth": ball_depth,
        "player_depth": player_depth,
        "depth_delta": round(depth_delta, 3),
        "contact_window": window,
    }


def is_hit_plausible_for_player(event: dict[str, Any], players: list[dict[str, Any]], tolerance: float = PLAYER_CONTACT_DEPTH_TOLERANCE) -> bool:
    """Test whether a candidate hit is plausible relative to player position and court depth."""
    return bool(score_hit_plausibility(event, players, tolerance=tolerance).get("plausible"))


def downgrade_implausible_hits(events: list[dict[str, Any]], players: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Assign render roles and downgrade implausible possible_hit events."""
    summary = {
        "implausible_hits_downgraded_count": 0,
        "plausible_hits_count": 0,
        "plausible_bounces_count": 0,
        "uncertain_events_count": 0,
        "player_interactions_count": 0,
    }
    updated_events: list[dict[str, Any]] = []
    for event in events:
        updated = dict(event)
        raw_type = str(updated.get("event_type") or "").lower()
        plausibility = score_hit_plausibility(updated, players) if "hit" in raw_type else {}
        role = classify_event_semantic_role(updated, players)
        updated["render_role"] = role
        updated["hit_plausibility"] = plausibility
        updated["player_aware_plausibility_status"] = "plausible" if plausibility.get("plausible") else "not_applicable" if "hit" not in raw_type else "implausible"
        if raw_type and "hit" in raw_type and role != "hit_plausible":
            updated["event_type_for_render"] = "uncertain_event"
            updated["semantic_note"] = "Raw possible_hit downgraded because player depth does not support contact location."
            summary["implausible_hits_downgraded_count"] += 1
            summary["uncertain_events_count"] += 1
        elif role == "hit_plausible":
            updated["event_type_for_render"] = "possible_hit"
            summary["plausible_hits_count"] += 1
        elif role == "bounce_plausible":
            updated["event_type_for_render"] = "possible_bounce"
            summary["plausible_bounces_count"] += 1
        elif role == "player_interaction":
            updated["event_type_for_render"] = "ball_near_player"
            summary["player_interactions_count"] += 1
        else:
            updated["event_type_for_render"] = "uncertain_event"
            summary["uncertain_events_count"] += 1
        updated_events.append(updated)
    return updated_events, summary


def apply_event_grounding_rules(height: float, event_type: str | None) -> float:
    """Apply event-specific height constraints."""
    role = classify_height_anchor_type(event_type)
    if role == "bounce_grounded":
        return enforce_bounce_floor_contact(height)
    if role == "hit_contact":
        return enforce_hit_contact_band(height)
    return height


def estimate_semantic_height_profile(points: list[dict[str, Any]]) -> list[float]:
    """Create a semantically constrained synthetic height profile."""
    total = len(points)
    heights: list[float] = []
    for index, point in enumerate(points):
        event_type = str(point.get("event_type") or "")
        role = classify_height_anchor_type(event_type)
        if role == "bounce_grounded":
            height = enforce_bounce_floor_contact(0.0)
        elif role == "hit_contact":
            side_bias = 8.0 if str(point.get("player_side_state") or "").lower() == "near_side" else 0.0
            height = enforce_hit_contact_band(88.0 + side_bias)
        else:
            phase = index / max(total - 1, 1)
            height = DEFAULT_ARC_MIN_HEIGHT + DEFAULT_ARC_PEAK_HEIGHT * abs(math.sin(phase * math.pi * 2.5))
        heights.append(height)
    return smooth_height_segments(heights, points)


def smooth_height_segments(heights: list[float], points: list[dict[str, Any]]) -> list[float]:
    """Smooth non-anchored synthetic heights while preserving semantic anchors."""
    if len(heights) <= 2:
        return heights
    smoothed = list(heights)
    for index in range(1, len(heights) - 1):
        role = classify_height_anchor_type(points[index].get("event_type"))
        if role in {"bounce_grounded", "hit_contact"}:
            continue
        previous_role = classify_height_anchor_type(points[index - 1].get("event_type"))
        next_role = classify_height_anchor_type(points[index + 1].get("event_type"))
        local_average = (heights[index - 1] + heights[index] + heights[index + 1]) / 3.0
        if previous_role == "bounce_grounded" or next_role == "bounce_grounded":
            smoothed[index] = max(DEFAULT_ARC_MIN_HEIGHT, min(local_average, DEFAULT_ARC_PEAK_HEIGHT))
        else:
            smoothed[index] = local_average
    return [apply_event_grounding_rules(value, point.get("event_type")) for value, point in zip(smoothed, points)]


def enforce_bounce_floor_contact(height: float) -> float:
    """Force bounce-like events to visually ground near court surface."""
    return min(max(0.0, height), BOUNCE_FLOOR_HEIGHT)


def enforce_hit_contact_band(height: float) -> float:
    """Force hit-like events into a plausible synthetic contact-height band."""
    return max(HIT_CONTACT_MIN_HEIGHT, min(HIT_CONTACT_MAX_HEIGHT, height))


def annotate_interpolated_height_points(points: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Mark interpolated side-view points as visual estimates."""
    annotated: list[dict[str, Any]] = []
    for point in points:
        updated = dict(point)
        if updated.get("is_interpolated"):
            updated["height_anchor_type"] = "visual_interpolation"
            updated["event_semantic_role"] = "interpolated_visual_point"
            updated["grounded_event"] = False
            updated["notes"] = "Interpolated visual point with synthetic height; not measured data."
        annotated.append(updated)
    return annotated


def build_side_view_keyframes(schema: dict[str, Any]) -> list[dict[str, Any]]:
    """Build side-view keyframes with synthetic height annotations."""
    court_height = float(schema.get("court_model", {}).get("normalized_court_height") or 780.0)
    sequence = extract_projected_ball_sequence(schema)
    events, _summary = downgrade_implausible_hits(schema.get("event_timeline", []), schema.get("players", []))
    raw_keyframes: list[dict[str, Any]] = []
    for index, point in enumerate(sequence):
        frame = _int(point.get("frame_index"))
        event = nearest_event(events, frame)
        event_type = event.get("event_type_for_render") if event else ""
        render_role = event.get("render_role") if event else ""
        role = "hit_contact" if render_role == "hit_plausible" else "bounce_grounded" if render_role == "bounce_plausible" else classify_height_anchor_type(event_type)
        depth = estimate_side_view_depth(point, court_height)
        raw_keyframes.append(
            {
                "frame_index": frame,
                "timestamp_seconds": _float(point.get("timestamp_seconds")),
                "court_depth": depth,
                "lateral_reference": _float(point.get("projected_x")),
                "synthetic_height": None,
                "projected_x": _float(point.get("projected_x")),
                "projected_y": _float(point.get("projected_y")),
                "event_type": event_type,
                "raw_event_type": event.get("event_type") if event else "",
                "render_role": render_role or role,
                "player_aware_plausibility_status": event.get("player_aware_plausibility_status") if event else "not_applicable",
                "hit_plausibility": event.get("hit_plausibility") if event else {},
                "height_anchor_type": role,
                "event_semantic_role": role,
                "grounded_event": role == "bounce_grounded",
                "is_interpolated": False,
                "height_is_estimated": True,
                "confidence_like_score": _float(point.get("confidence_like_score")),
                "notes": "Synthetic side-view height; not measured 3D ball height.",
            }
        )
    heights = estimate_semantic_height_profile(raw_keyframes)
    keyframes: list[dict[str, Any]] = []
    for point, height in zip(raw_keyframes, heights):
        updated = dict(point)
        updated["synthetic_height"] = height
        if updated["height_anchor_type"] == "bounce_grounded":
            updated["notes"] = "Bounce-like event visually grounded near court surface; synthetic height only."
        elif updated["height_anchor_type"] == "hit_contact":
            updated["notes"] = "Hit-like event placed in plausible synthetic contact band; not measured height."
        elif updated["height_anchor_type"] == "interaction_cue":
            updated["notes"] = "Ball-near-player interaction cue; height remains arc estimate."
        keyframes.append(updated)
    return keyframes


def interpolate_side_view_motion(keyframes: list[dict[str, Any]], *, interpolate: bool = True, interpolation_steps: int = 8) -> list[dict[str, Any]]:
    """Interpolate side-view points for animation only."""
    if not interpolate or interpolation_steps <= 0 or len(keyframes) <= 1:
        return [dict(point, is_interpolated=False, height_is_estimated=True) for point in keyframes]
    points: list[dict[str, Any]] = []
    for start, end in zip(keyframes, keyframes[1:]):
        points.append(dict(start, is_interpolated=False, height_is_estimated=True))
        for step in range(1, interpolation_steps + 1):
            t = step / (interpolation_steps + 1)
            points.append(interpolate_side_view_point(start, end, t))
    points.append(dict(keyframes[-1], is_interpolated=False, height_is_estimated=True))
    return annotate_interpolated_height_points(points)


def interpolate_side_view_point(start: dict[str, Any], end: dict[str, Any], t: float) -> dict[str, Any]:
    """Create one visual-only side-view interpolation point."""
    result = dict(start)
    for key in ("court_depth", "lateral_reference", "synthetic_height", "projected_x", "projected_y", "confidence_like_score"):
        result[key] = _lerp(_float(start.get(key)), _float(end.get(key)), t)
    frame_a = _float(start.get("frame_index"))
    frame_b = _float(end.get("frame_index"))
    result["frame_index"] = None if frame_a is None or frame_b is None else int(round(_lerp(frame_a, frame_b, t) or frame_a))
    time_a = _float(start.get("timestamp_seconds"))
    time_b = _float(end.get("timestamp_seconds"))
    result["timestamp_seconds"] = _lerp(time_a, time_b, t)
    result["event_type"] = ""
    result["raw_event_type"] = ""
    result["render_role"] = "interpolation_only"
    result["player_aware_plausibility_status"] = "not_applicable"
    result["hit_plausibility"] = {}
    result["height_anchor_type"] = "visual_interpolation"
    result["event_semantic_role"] = "interpolated_visual_point"
    result["grounded_event"] = False
    result["is_interpolated"] = True
    result["height_is_estimated"] = True
    result["notes"] = "Visual interpolation with synthetic height; not measured data."
    return result


def nearest_event(events: list[dict[str, Any]], frame_index: int | None, tolerance: int = 3) -> dict[str, Any] | None:
    """Find a nearby event for a side-view keyframe."""
    if frame_index is None:
        return None
    candidates = []
    for event in events:
        event_frame = _int(event.get("frame_index"))
        if event_frame is None:
            continue
        delta = abs(event_frame - frame_index)
        if delta <= tolerance:
            candidates.append((delta, event))
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: item[0])[0][1]


def nearest_player_state(states: list[dict[str, Any]], frame_index: int | None) -> dict[str, Any] | None:
    """Find the nearest player side-state row for an event frame."""
    if frame_index is None or not states:
        return None
    return min(states, key=lambda row: abs((_int(row.get("frame_index")) or frame_index) - frame_index))


def _lerp(start: float | None, end: float | None, t: float) -> float | None:
    if start is None or end is None:
        return None
    return start + ((end - start) * t)


def _float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None
