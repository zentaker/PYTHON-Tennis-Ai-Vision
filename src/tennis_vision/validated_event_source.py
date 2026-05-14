"""Validated event source loading for side-view replay rendering."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


EVENT_SOURCE_PRIORITY = [
    ("stage_8_3_validated_event_timeline", Path("outputs/timeline/stage_8_3_event_validation/validated_event_timeline.csv")),
    ("stage_8_1_validated_event_timeline", Path("outputs/timeline/stage_8_1_timeline_validation/validated_event_timeline.csv")),
    ("stage_8_event_timeline", Path("outputs/timeline/stage_8_event_timeline/event_timeline.csv")),
    ("stage_6_trajectory_events", Path("outputs/ball_tracking/stage_6_trajectory_smoothing/trajectory_events.csv")),
]


def load_validated_event_source(project_root: Path, schema: dict[str, Any], preferred_path: Path | None = None) -> dict[str, Any]:
    """Load Stage 8.3 validated events as the preferred side-view event source."""
    priority = list(EVENT_SOURCE_PRIORITY)
    if preferred_path is not None:
        priority[0] = ("stage_8_3_validated_event_timeline", preferred_path)
    warnings: list[str] = []
    errors: list[str] = []
    for source_name, relative_path in priority:
        path = relative_path if relative_path.is_absolute() else project_root / relative_path
        rows, read_warnings = read_event_rows(path)
        warnings.extend(read_warnings)
        if not rows:
            continue
        events = [
            map_validated_event_to_render_role(row, source_name=source_name, schema=schema, sequence=index)
            for index, row in enumerate(rows, start=1)
        ]
        validated_available = source_name == "stage_8_3_validated_event_timeline"
        if not validated_available:
            warnings.append(f"Stage 8.3 validated event source was not available; using fallback source {source_name}.")
        return {
            "events": events,
            "event_source_used": source_name,
            "event_source_path": str(path),
            "event_source_priority": [name for name, _path in priority],
            "validated_event_source_available": validated_available,
            "fallback_used": not validated_available,
            "warnings": warnings,
            "errors": errors,
            "summary": summarize_validated_render_events(events),
        }
    errors.append("No event source could be loaded for side-view replay.")
    return {
        "events": [],
        "event_source_used": "missing",
        "event_source_path": "",
        "event_source_priority": [name for name, _path in priority],
        "validated_event_source_available": False,
        "fallback_used": False,
        "warnings": warnings,
        "errors": errors,
        "summary": summarize_validated_render_events([]),
    }


def read_event_rows(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Read event rows from a CSV file."""
    if not path.exists():
        return [], []
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle)), []
    except OSError as exc:
        return [], [f"Could not read event source {path}: {exc}"]


def map_validated_event_to_render_role(row: dict[str, Any], *, source_name: str, schema: dict[str, Any], sequence: int = 0) -> dict[str, Any]:
    """Convert validated/reclassified event labels into physical or annotation render roles."""
    frame = _int(row.get("frame_index"))
    original_type = str(row.get("original_event_type") or row.get("event_type") or "").strip()
    validated_type = str(row.get("validated_event_type") or row.get("event_type") or original_type).strip()
    source_role = str(row.get("render_role") or "").strip()
    role, physical, annotation, ignored = classify_render_role(
        original_type=original_type,
        validated_type=validated_type,
        source_role=source_role,
        should_render_as_physical_event=row.get("should_render_as_physical_event"),
        should_render_as_annotation=row.get("should_render_as_annotation"),
        source_name=source_name,
    )
    projected = projected_position_for_frame(schema, frame, row)
    event_id = str(row.get("event_id") or f"{source_name}_{sequence:03d}")
    confidence = _float(row.get("confidence_adjusted"))
    if confidence is None:
        confidence = _float(row.get("adjusted_confidence_like_score"))
    if confidence is None:
        confidence = _float(row.get("confidence_like_score"))
    event_type_for_render = "possible_bounce" if role == "bounce_plausible" else "possible_hit" if role == "hit_plausible" else role
    mapped = {
        "event_id": event_id,
        "frame_index": frame,
        "event_type": validated_type or original_type,
        "raw_event_type": original_type,
        "validated_event_type": validated_type,
        "source_render_role": source_role,
        "render_role": role,
        "event_type_for_render": event_type_for_render,
        "validation_status": row.get("validation_status") or "",
        "player_id": row.get("player_id") or "",
        "confidence_like_score": confidence,
        "confidence_adjusted": confidence,
        "reason": row.get("reason") or "",
        "source": source_name,
        "manual_support": row.get("manual_support") or "",
        "projected_position": projected,
        "side_view_physical_event": physical,
        "annotation_only": annotation and not physical,
        "ignored_event": ignored,
        "main_path_contact_marker": physical,
        "player_aware_plausibility_status": "validated" if role in {"bounce_plausible", "hit_plausible"} else "not_physical",
        "semantic_note": semantic_note_for_role(role, original_type, validated_type),
    }
    return mapped


def classify_render_role(
    *,
    original_type: str,
    validated_type: str,
    source_role: str,
    should_render_as_physical_event: Any,
    should_render_as_annotation: Any,
    source_name: str,
) -> tuple[str, bool, bool, bool]:
    """Classify a row into a side-view render role and render policy."""
    text = " ".join([original_type, validated_type, source_role]).lower()
    physical_flag = _yes(should_render_as_physical_event)
    annotation_flag = _yes(should_render_as_annotation)
    if source_name == "stage_8_3_validated_event_timeline":
        if any(token in text for token in ("bounce_validated", "validated_possible_bounce", "validated_bounce", "possible_bounce_candidate")):
            return "bounce_plausible", True, True, False
        if any(token in text for token in ("hit_validated", "validated_possible_hit", "validated_hit")):
            return "hit_plausible", True, True, False
        if "rejected_event" in text:
            return "rejected_event", False, False, True
        if "interaction_cue" in text or "ball_near_player" in text:
            return "player_interaction", False, True, False
        if "hit_unvalidated" in text or "possible_hit_unvalidated" in text or "downgraded_hit" in text or "uncertain_event" in text:
            return "uncertain_event", False, True, False
        if physical_flag and "bounce" in text:
            return "bounce_plausible", True, annotation_flag, False
        if physical_flag and "hit" in text:
            return "hit_plausible", True, annotation_flag, False
        return "uncertain_event", False, annotation_flag or True, False
    if "bounce" in text:
        return "bounce_plausible", True, True, False
    if "hit" in text:
        return "uncertain_event", False, True, False
    if "near_player" in text or "ball_near_player" in text:
        return "player_interaction", False, True, False
    return "uncertain_event", False, True, False


def summarize_validated_render_events(events: list[dict[str, Any]]) -> dict[str, int]:
    """Summarize how validated events will be rendered by the side-view stage."""
    summary = {
        "validated_bounces_rendered_count": 0,
        "validated_hits_rendered_count": 0,
        "downgraded_hits_annotation_count": 0,
        "rejected_events_ignored_count": 0,
        "unvalidated_events_annotation_count": 0,
        "physical_events_count": 0,
        "annotation_events_count": 0,
    }
    for event in events:
        role = str(event.get("render_role") or "")
        original = str(event.get("raw_event_type") or event.get("event_type") or "").lower()
        validated = str(event.get("validated_event_type") or "").lower()
        if event.get("side_view_physical_event"):
            summary["physical_events_count"] += 1
        if event.get("annotation_only"):
            summary["annotation_events_count"] += 1
        if role == "bounce_plausible" and event.get("side_view_physical_event"):
            summary["validated_bounces_rendered_count"] += 1
        if role == "hit_plausible" and event.get("side_view_physical_event"):
            summary["validated_hits_rendered_count"] += 1
        if "hit" in original and role != "hit_plausible":
            summary["downgraded_hits_annotation_count"] += 1
        if role == "rejected_event" or event.get("ignored_event"):
            summary["rejected_events_ignored_count"] += 1
        if event.get("annotation_only") and role != "rejected_event":
            summary["unvalidated_events_annotation_count"] += 1
        if "hit_unvalidated" in validated and role == "uncertain_event":
            summary["unvalidated_events_annotation_count"] = max(summary["unvalidated_events_annotation_count"], summary["unvalidated_events_annotation_count"])
    return summary


def projected_position_for_frame(schema: dict[str, Any], frame_index: int | None, row: dict[str, Any]) -> dict[str, float | None]:
    """Attach projected court coordinates to an event using row data or nearest replay keyframe."""
    x = _float(row.get("ball_projected_x") or row.get("projected_x"))
    y = _float(row.get("ball_projected_y") or row.get("projected_y"))
    if x is not None or y is not None:
        return {"x": x, "y": y}
    keyframes = schema.get("ball_trajectory", {}).get("replay_keyframes", []) if schema else []
    nearest = nearest_frame_row(keyframes, frame_index)
    if nearest:
        return {"x": _float(nearest.get("projected_x")), "y": _float(nearest.get("projected_y"))}
    return {"x": None, "y": None}


def nearest_frame_row(rows: list[dict[str, Any]], frame_index: int | None) -> dict[str, Any] | None:
    """Find the nearest row by frame index."""
    if frame_index is None or not rows:
        return None
    candidates = []
    for row in rows:
        other = _int(row.get("frame_index"))
        if other is None:
            continue
        candidates.append((abs(other - frame_index), row))
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: item[0])[0][1]


def semantic_note_for_role(role: str, original_type: str, validated_type: str) -> str:
    """Explain the render policy for a normalized event."""
    if role == "bounce_plausible":
        return "Validated bounce rendered as a grounded physical event."
    if role == "hit_plausible":
        return "Validated hit rendered as a physical contact event."
    if role == "player_interaction":
        return "Player interaction cue rendered as annotation only."
    if role == "rejected_event":
        return "Rejected event ignored for physical side-view trajectory."
    if "hit" in original_type.lower() or "hit" in validated_type.lower():
        return "Unvalidated or downgraded hit rendered as annotation only."
    return "Uncertain event rendered as annotation only."


def _yes(value: Any) -> bool:
    return str(value or "").strip().lower() in {"yes", "true", "1", "y"}


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
