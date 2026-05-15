"""Resolve manual full-rally event timings to local ball positions."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from tennis_vision.ball_candidate_improvement import generate_hybrid_candidates, load_labeled_frame_bundle
from tennis_vision.court_projection import load_stage_3_calibration, project_image_points
from tennis_vision.court_zones import assign_court_zone


def load_manual_full_rally_annotation(path: Path) -> dict[str, Any]:
    """Load the Product Owner full-rally temporal annotation."""
    return json.loads(path.read_text(encoding="utf-8"))


def timecode_to_frame(timecode: str, fps: int) -> int:
    """Convert HH:MM:SS:FF into a frame index."""
    parts = str(timecode).strip().split(":")
    if len(parts) != 4:
        raise ValueError(f"Expected HH:MM:SS:FF timecode, got {timecode!r}")
    hours, minutes, seconds, frames = [int(part) for part in parts]
    return (((hours * 60) + minutes) * 60 + seconds) * int(fps) + frames


def normalize_manual_events(annotation: dict[str, Any]) -> list[dict[str, Any]]:
    """Return ordered manual events with explicit frame ranges."""
    fps = int(annotation.get("fps") or 60)
    rows: list[dict[str, Any]] = []
    for index, event in enumerate(annotation.get("events", []), start=1):
        start_frame = _int(event.get("start_frame"))
        end_frame = _int(event.get("end_frame"))
        if start_frame is None:
            start_frame = timecode_to_frame(event.get("start_timecode") or event.get("timecode"), fps)
        if end_frame is None:
            end_frame = timecode_to_frame(event.get("end_timecode") or event.get("timecode"), fps)
        start_frame, end_frame = sorted((start_frame, end_frame))
        contact = _int(event.get("contact_frame_estimate") or event.get("center_frame"))
        if contact is None:
            contact = int(round((start_frame + end_frame) / 2))
        rows.append(
            {
                "event_id": event.get("event_id") or f"manual_full_rally_{index:03d}",
                "sequence_index": int(event.get("sequence") or index),
                "event_type": str(event.get("event_type") or "").strip().lower(),
                "start_timecode": event.get("start_timecode") or event.get("timecode") or "",
                "end_timecode": event.get("end_timecode") or event.get("timecode") or "",
                "start_frame": start_frame,
                "end_frame": end_frame,
                "contact_frame_estimate": contact,
                "shot_type": event.get("shot_type") or "",
                "confidence": event.get("confidence") or annotation.get("confidence") or "high",
                "notes": event.get("notes") or "",
            }
        )
    return sorted(rows, key=lambda row: int(row["sequence_index"]))


def build_event_search_window(event: dict[str, Any], *, exact_padding: int = 3, range_padding: int = 2) -> list[int]:
    """Build the local frame search window for one manual event."""
    start = int(event["start_frame"])
    end = int(event["end_frame"])
    if start == end:
        start -= exact_padding
        end += exact_padding
    else:
        start -= range_padding
        end += range_padding
    return list(range(max(0, start), max(start, end) + 1))


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    """Read CSV rows when available."""
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def resolve_manual_event_positions(
    *,
    annotation_path: Path,
    project_root: Path,
    video_path: Path,
    stage3_report_path: Path,
    expanded_labels_path: Path,
    projected_labels_path: Path,
    search_padding: int = 3,
    fallback_tolerance: int = 8,
    resize_width: int = 1280,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Resolve ball image/court positions for every manual full-rally event."""
    annotation = load_manual_full_rally_annotation(annotation_path)
    events = normalize_manual_events(annotation)
    calibration = load_stage_3_calibration(stage3_report_path)
    expanded_labels = read_csv_rows(expanded_labels_path)
    projected_labels = read_csv_rows(projected_labels_path)
    fallback_rows = build_fallback_rows(expanded_labels, projected_labels)
    warnings: list[str] = []
    errors: list[str] = []
    resolved: list[dict[str, Any]] = []

    all_search_frames = sorted({frame for event in events for frame in build_event_search_window(event, exact_padding=search_padding, range_padding=max(1, search_padding - 1))})
    bundles, frame_errors = load_labeled_frame_bundle(video_path=video_path, frame_indices=all_search_frames, resize_width=resize_width, neighbor_offset=2)
    errors.extend(frame_errors)
    candidates_by_frame: dict[int, list[dict[str, Any]]] = {}
    court_polygon = calibration.get("court_polygon") or []
    for frame_index, bundle in bundles.items():
        candidates_by_frame[frame_index] = generate_hybrid_candidates(bundle, court_polygon)

    for event in events:
        row = resolve_ball_position_for_event(
            event,
            candidates_by_frame=candidates_by_frame,
            fallback_rows=fallback_rows,
            calibration=calibration,
            search_padding=search_padding,
            fallback_tolerance=fallback_tolerance,
        )
        if row["event_position_status"] == "unresolved":
            warnings.append(f"{row['event_id']} {row['event_type']} at frame {row['contact_frame_estimate']} could not be spatially resolved.")
        resolved.append(row)

    summary = {
        "manual_events": len(events),
        "positions_resolved": sum(1 for row in resolved if row["event_position_status"] == "resolved"),
        "positions_unresolved": sum(1 for row in resolved if row["event_position_status"] == "unresolved"),
        "projected_positions": sum(1 for row in resolved if row["projection_status"] == "projected"),
        "warnings": warnings,
        "errors": errors,
        "calibration_available": bool(calibration.get("homography_available")),
        "candidate_frames_processed": len(bundles),
        "candidate_count": sum(len(items) for items in candidates_by_frame.values()),
        "project_root": str(project_root),
    }
    return resolved, summary


def build_fallback_rows(expanded_labels: list[dict[str, Any]], projected_labels: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Combine existing Stage 8.1 labels and Stage 9.1 projections for fallback lookup."""
    projected_by_frame = {_int(row.get("frame_index")): row for row in projected_labels if _int(row.get("frame_index")) is not None}
    rows: list[dict[str, Any]] = []
    for row in expanded_labels:
        frame = _int(row.get("frame_index"))
        if frame is None:
            continue
        projected = projected_by_frame.get(frame, {})
        x = _float(row.get("x"))
        y = _float(row.get("y"))
        if x is None or y is None:
            continue
        rows.append(
            {
                "frame_index": frame,
                "x": x,
                "y": y,
                "projected_x": _float(projected.get("projected_x")),
                "projected_y": _float(projected.get("projected_y")),
                "projection_status": projected.get("projection_status") or "",
                "source": row.get("source") or "stage_8_1_expanded_label",
            }
        )
    return rows


def resolve_ball_position_for_event(
    event: dict[str, Any],
    *,
    candidates_by_frame: dict[int, list[dict[str, Any]]],
    fallback_rows: list[dict[str, Any]],
    calibration: dict[str, Any],
    search_padding: int,
    fallback_tolerance: int,
) -> dict[str, Any]:
    """Resolve one manual event to a best local ball position."""
    search_frames = build_event_search_window(event, exact_padding=search_padding, range_padding=max(1, search_padding - 1))
    contact = int(event["contact_frame_estimate"])
    scored: list[dict[str, Any]] = []
    for frame in search_frames:
        for candidate in candidates_by_frame.get(frame, []):
            time_score = 1.0 - min(abs(frame - contact) / max(1.0, len(search_frames)), 1.0)
            combined = 0.78 * float(candidate.get("score") or 0.0) + 0.22 * time_score
            scored.append({**candidate, "combined_score": round(combined, 4)})
    best = max(scored, key=lambda item: float(item.get("combined_score") or 0.0), default=None)
    if best and float(best.get("combined_score") or 0.0) >= 0.28:
        base = {
            **event,
            "resolved_frame": int(best["frame_index"]),
            "image_x": _float(best.get("x")),
            "image_y": _float(best.get("y")),
            "event_position_status": "resolved",
            "event_position_source": "local_ball_detection",
            "event_position_confidence": confidence_from_score(float(best.get("combined_score") or 0.0)),
            "detection_score": round(float(best.get("combined_score") or 0.0), 4),
            "position_notes": f"Resolved from local {best.get('strategy', 'hybrid')} candidate search near manual event timing.",
        }
        return project_event_position_to_court(base, calibration)

    fallback = nearest_fallback(event, fallback_rows, fallback_tolerance)
    if fallback:
        base = {
            **event,
            "resolved_frame": int(fallback["frame_index"]),
            "image_x": _float(fallback.get("x")),
            "image_y": _float(fallback.get("y")),
            "projected_x": _float(fallback.get("projected_x")),
            "projected_y": _float(fallback.get("projected_y")),
            "event_position_status": "resolved",
            "event_position_source": "nearest_existing_ball_label",
            "event_position_confidence": "medium" if abs(int(fallback["frame_index"]) - contact) <= 4 else "low",
            "detection_score": "",
            "position_notes": f"Resolved from nearest existing ball label at frame {fallback['frame_index']}.",
        }
        return project_event_position_to_court(base, calibration)

    return {
        **event,
        "resolved_frame": "",
        "image_x": "",
        "image_y": "",
        "projected_x": "",
        "projected_y": "",
        "court_zone": "unknown",
        "depth": "unknown",
        "lateral_lane": "unknown",
        "event_position_status": "unresolved",
        "event_position_source": "",
        "event_position_confidence": "low",
        "detection_score": "",
        "projection_status": "not_attempted",
        "position_notes": "No local ball candidate or nearby existing label could resolve this event position.",
    }


def nearest_fallback(event: dict[str, Any], fallback_rows: list[dict[str, Any]], tolerance: int) -> dict[str, Any] | None:
    """Return nearest existing manual/projected label inside tolerance."""
    contact = int(event["contact_frame_estimate"])
    candidates = [(abs(int(row["frame_index"]) - contact), row) for row in fallback_rows if abs(int(row["frame_index"]) - contact) <= tolerance]
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: item[0])[0][1]


def project_event_position_to_court(row: dict[str, Any], calibration: dict[str, Any]) -> dict[str, Any]:
    """Project an image-space event position into normalized court coordinates."""
    x = _float(row.get("image_x"))
    y = _float(row.get("image_y"))
    projected_x = _float(row.get("projected_x"))
    projected_y = _float(row.get("projected_y"))
    projection_status = "not_attempted"
    if x is not None and y is not None and (projected_x is None or projected_y is None):
        projected = project_image_points([{"x": x, "y": y}], calibration.get("matrix"))
        if projected:
            projected_x = _float(projected[0].get("projected_x"))
            projected_y = _float(projected[0].get("projected_y"))
            projection_status = "projected"
        else:
            projection_status = "failed"
    elif projected_x is not None and projected_y is not None:
        projection_status = "projected"
    zone = assign_court_zone(projected_x, projected_y)
    return {
        **row,
        "projected_x": round(projected_x, 3) if projected_x is not None else "",
        "projected_y": round(projected_y, 3) if projected_y is not None else "",
        "court_zone": zone["zone_id"],
        "depth": zone["depth"],
        "lateral_lane": zone["lateral_lane"],
        "projection_status": projection_status,
    }


def write_resolved_manual_events(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write resolved manual event rows to CSV."""
    fields = [
        "event_id",
        "sequence_index",
        "event_type",
        "shot_type",
        "start_frame",
        "end_frame",
        "contact_frame_estimate",
        "resolved_frame",
        "image_x",
        "image_y",
        "projected_x",
        "projected_y",
        "court_zone",
        "depth",
        "lateral_lane",
        "event_position_status",
        "event_position_source",
        "event_position_confidence",
        "detection_score",
        "projection_status",
        "position_trust",
        "position_validation_status",
        "sequence_validation_reason",
        "should_render_as_physical_event",
        "should_render_as_annotation",
        "position_notes",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def confidence_from_score(score: float) -> str:
    """Convert detector score into coarse confidence."""
    if score >= 0.58:
        return "high"
    if score >= 0.40:
        return "medium"
    return "low"


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
