"""Tennis-sequence validation for manually timed rally event positions.

Manual full-rally timings are temporal ground truth. Local ball detections are
candidate positions only; this module decides whether those positions are
plausible enough to render as physical replay anchors.
"""

from __future__ import annotations

from typing import Any


COURT_SIDE_SPLIT_Y = 390.0
FAR_BASELINE_MAX_Y = 190.0
NEAR_BASELINE_MIN_Y = 590.0


def validate_manual_event_sequence(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate a full manual rally event sequence against conservative tennis order."""
    ordered = sorted(rows, key=lambda row: int(row.get("sequence_index") or 0))
    expected_sides = _expected_rally_sides(ordered)
    validated: list[dict[str, Any]] = []

    for index, row in enumerate(ordered):
        expected_side = expected_sides.get(str(row.get("event_id") or ""))
        checks = validate_event_position_plausibility(
            row,
            previous_event=ordered[index - 1] if index > 0 else None,
            next_event=ordered[index + 1] if index + 1 < len(ordered) else None,
            expected_side=expected_side,
        )
        merged = {**row, **checks}
        validated.append(merged)

    for index, row in enumerate(validated):
        transition_reason = validate_alternating_court_sides(
            row,
            previous_event=validated[index - 1] if index > 0 else None,
            next_event=validated[index + 1] if index + 1 < len(validated) else None,
        )
        if transition_reason and row["position_trust"] == "valid":
            row["position_trust"] = "suspicious"
            row["position_validation_status"] = "suspicious_transition"
            row["sequence_validation_reason"] = transition_reason

    return apply_render_safety_flags(validated)


def validate_event_position_plausibility(
    row: dict[str, Any],
    *,
    previous_event: dict[str, Any] | None = None,
    next_event: dict[str, Any] | None = None,
    expected_side: str | None = None,
) -> dict[str, Any]:
    """Validate one resolved event position against projection and sequence context."""
    if row.get("event_position_status") != "resolved":
        return classify_position_trust("unresolved_position", "No reliable image/court position was resolved for this manual event.")
    if row.get("projection_status") != "projected":
        return classify_position_trust("projection_missing", "The event has no projected court coordinate, so it cannot be trusted as a physical anchor.")

    event_type = str(row.get("event_type") or "").lower()
    shot_type = str(row.get("shot_type") or "").lower()
    if event_type == "hit" and "serve" in shot_type:
        serve_result = validate_serve_position(row, next_event=next_event, expected_side=expected_side)
        if serve_result["position_trust"] != "valid":
            return serve_result

    if event_type == "bounce":
        bounce_result = validate_bounce_side(row, previous_event=previous_event, expected_side=expected_side)
        if bounce_result["position_trust"] != "valid":
            return bounce_result

    if previous_event and previous_event.get("event_type") == "hit" and event_type == "bounce":
        transition = validate_hit_bounce_side_transition(previous_event, row)
        if transition:
            return classify_position_trust("impossible_hit_bounce_transition", transition)

    side = court_side(row.get("projected_y"))
    if expected_side and side != "unknown" and side != expected_side:
        return classify_position_trust(
            "wrong_side_likely",
            f"Projected to {side} court side, but sequence expects {expected_side} for this rally event.",
        )

    return classify_position_trust("local_detection_sequence_valid", "Local detection survived projection, serve, side, and transition plausibility checks.")


def validate_serve_position(
    row: dict[str, Any],
    *,
    next_event: dict[str, Any] | None = None,
    expected_side: str | None = None,
) -> dict[str, Any]:
    """Validate that the first serve contact is in a plausible serving-side region."""
    side = court_side(row.get("projected_y"))
    y = _float(row.get("projected_y"))
    expected = expected_side or "far"
    if side != expected:
        return classify_position_trust(
            "implausible_serve_position",
            f"Serve contact projected to {side} side; expected {expected} serving side for this manual rally.",
            trust="invalid",
        )
    if y is None or not (y <= FAR_BASELINE_MAX_Y or y >= NEAR_BASELINE_MIN_Y):
        return classify_position_trust(
            "implausible_serve_position",
            "Serve contact is not near a plausible baseline band.",
            trust="invalid",
        )
    if next_event and next_event.get("projection_status") == "projected":
        next_side = court_side(next_event.get("projected_y"))
        if next_side == side:
            return classify_position_trust(
                "wrong_side_likely",
                f"Serve and first bounce both project to {side}; serve-to-bounce should cross court side.",
                trust="invalid",
            )
    return classify_position_trust("serve_position_sequence_valid", "Serve contact is on the expected serving side and near a baseline.")


def validate_hit_bounce_side_transition(hit_event: dict[str, Any], bounce_event: dict[str, Any]) -> str:
    """Return a failure reason when a hit-to-bounce pair does not cross sides."""
    hit_side = court_side(hit_event.get("projected_y"))
    bounce_side = court_side(bounce_event.get("projected_y"))
    if "unknown" in {hit_side, bounce_side}:
        return ""
    if hit_side == bounce_side:
        return f"Hit-to-bounce pair stays on {hit_side} side; expected the ball to cross the net before the next bounce."
    return ""


def validate_bounce_side(
    row: dict[str, Any],
    *,
    previous_event: dict[str, Any] | None = None,
    expected_side: str | None = None,
) -> dict[str, Any]:
    """Validate a bounce side with expected rally order and previous hit context."""
    side = court_side(row.get("projected_y"))
    if expected_side and side != "unknown" and side != expected_side:
        return classify_position_trust(
            "wrong_side_likely",
            f"Bounce projected to {side} court side, but sequence expects {expected_side}.",
        )
    if previous_event and previous_event.get("event_type") == "hit":
        reason = validate_hit_bounce_side_transition(previous_event, row)
        if reason:
            return classify_position_trust("impossible_hit_bounce_transition", reason)
    return classify_position_trust("bounce_side_sequence_valid", "Bounce side is plausible for this event sequence.")


def validate_alternating_court_sides(
    row: dict[str, Any],
    *,
    previous_event: dict[str, Any] | None = None,
    next_event: dict[str, Any] | None = None,
) -> str:
    """Validate local neighbor transitions without forcing corrections."""
    event_type = str(row.get("event_type") or "").lower()
    side = court_side(row.get("projected_y"))
    if side == "unknown":
        return "Court side is unknown after projection."

    if event_type == "hit" and next_event and next_event.get("event_type") == "bounce":
        return validate_hit_bounce_side_transition(row, next_event)

    if event_type == "hit" and previous_event and previous_event.get("event_type") == "bounce":
        previous_side = court_side(previous_event.get("projected_y"))
        if previous_side != "unknown" and previous_side != side:
            return f"Bounce-to-hit pair switches from {previous_side} to {side}; receiver hit should normally occur on the bounce side."

    return ""


def classify_position_trust(status: str, reason: str, *, trust: str | None = None) -> dict[str, str]:
    """Classify validation status into renderable trust levels."""
    if trust is None:
        if status in {"local_detection_sequence_valid", "serve_position_sequence_valid", "bounce_side_sequence_valid"}:
            trust = "valid"
        elif status in {"unresolved_position"}:
            trust = "unresolved"
        elif status in {"projection_missing", "implausible_serve_position"}:
            trust = "invalid"
        else:
            trust = "suspicious"
    return {
        "position_trust": trust,
        "position_validation_status": status,
        "sequence_validation_reason": reason,
    }


def apply_render_safety_flags(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Allow only valid positions to become physical replay anchors."""
    output: list[dict[str, Any]] = []
    for row in rows:
        trust = str(row.get("position_trust") or "unresolved")
        physical = trust == "valid"
        output.append(
            {
                **row,
                "should_render_as_physical_event": "yes" if physical else "no",
                "should_render_as_annotation": "yes",
            }
        )
    return output


def court_side(projected_y: Any) -> str:
    """Classify normalized court depth into near/far halves."""
    y = _float(projected_y)
    if y is None:
        return "unknown"
    return "far" if y < COURT_SIDE_SPLIT_Y else "near"


def _expected_rally_sides(rows: list[dict[str, Any]]) -> dict[str, str]:
    """Derive conservative expected sides for a serve rally: hit/bounce pairs alternate."""
    expected: dict[str, str] = {}
    pair_sides = [("far", "near"), ("near", "far")]
    pair_index = 0
    current_pair = pair_sides[pair_index]
    for index, row in enumerate(rows):
        event_id = str(row.get("event_id") or "")
        event_type = str(row.get("event_type") or "").lower()
        if event_type == "hit":
            expected[event_id] = current_pair[0]
        elif event_type == "bounce":
            expected[event_id] = current_pair[1]
            pair_index += 1
            current_pair = pair_sides[pair_index % 2]
        else:
            expected[event_id] = "unknown"
    return expected


def _float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
