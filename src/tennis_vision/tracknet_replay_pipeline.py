"""End-to-end TrackNet replay pipeline scaffold."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tennis_vision.court_projection import load_stage_3_calibration, project_image_points
from tennis_vision.court_zones import COURT_HEIGHT, COURT_WIDTH, assign_court_zone
from tennis_vision.manual_event_position_resolver import load_manual_full_rally_annotation, normalize_manual_events
from tennis_vision.model_adapters import tracknet_adapter
from tennis_vision.side_view_curve_model import build_side_view_curve_segments, write_side_view_curve_segments
from tennis_vision.tennis_sequence_validator import validate_manual_event_sequence


BALL_TRACKING_FIELDS = [
    "frame_index",
    "timestamp_seconds",
    "ball_x",
    "ball_y",
    "confidence",
    "source_model",
    "visibility_status",
    "notes",
]

PROJECTED_FIELDS = [
    "frame_index",
    "timestamp_seconds",
    "ball_x",
    "ball_y",
    "projected_x",
    "projected_y",
    "court_zone",
    "depth",
    "lateral_lane",
    "projection_status",
    "confidence",
    "source_model",
    "visibility_status",
    "notes",
]

EVENT_POSITION_FIELDS = [
    "event_id",
    "sequence_index",
    "event_type",
    "shot_type",
    "manual_start_frame",
    "manual_end_frame",
    "manual_contact_frame",
    "resolved_frame",
    "image_x",
    "image_y",
    "projected_x",
    "projected_y",
    "court_zone",
    "depth",
    "lateral_lane",
    "tracknet_confidence",
    "position_status",
    "position_trust",
    "validation_status",
    "validation_reason",
    "should_render_as_physical_event",
    "should_render_as_annotation",
]


def run_tracknet_replay_pipeline(
    *,
    project_root: Path,
    video_path: Path,
    annotation_path: Path,
    output_dir: Path,
    fps: int = 60,
    rally_padding: int = 15,
    event_search_padding: int = 5,
    tracknet_weights: Path | None = None,
    generate_replays: bool = True,
) -> dict[str, Any]:
    """Run the integrated TrackNet replay pipeline or write a blocked report."""
    output_dir.mkdir(parents=True, exist_ok=True)
    annotation = load_manual_full_rally_annotation(annotation_path)
    events = normalize_manual_events(annotation)
    hits = [event for event in events if event["event_type"] == "hit"]
    bounces = [event for event in events if event["event_type"] == "bounce"]
    rally_start = max(0, min(int(event["start_frame"]) for event in events) - rally_padding) if events else 0
    rally_end = max(int(event["end_frame"]) for event in events) + rally_padding if events else 0

    availability = tracknet_adapter.check_availability(project_root, weights_path=tracknet_weights)
    tracking_result = tracknet_adapter.track_video_segment(
        video_path=video_path,
        start_frame=rally_start,
        end_frame=rally_end,
        weights_path=tracknet_weights,
        project_root=project_root,
        fps=fps,
    )
    tracked_rows = normalize_tracking_rows(tracking_result.get("tracked_frames", []), fps=fps)
    write_csv(output_dir / "ball_tracking_results.csv", tracked_rows, BALL_TRACKING_FIELDS)

    calibration = load_stage_3_calibration(project_root / "outputs" / "reports" / "stage_3_court_calibration_probe_report.json")
    projected_rows = project_tracking_rows(tracked_rows, calibration)
    write_csv(output_dir / "projected_ball_positions.csv", projected_rows, PROJECTED_FIELDS)

    event_rows = resolve_events_from_tracknet(
        events=events,
        projected_rows=projected_rows,
        event_search_padding=event_search_padding,
        blocked_status=str(tracking_result.get("status") or availability.get("status") or ""),
        blocked_reason=str(tracking_result.get("reason") or availability.get("reason") or ""),
    )
    write_csv(output_dir / "event_position_results.csv", event_rows, EVENT_POSITION_FIELDS)

    schema = build_replay_schema(
        annotation=annotation,
        annotation_path=annotation_path,
        video_path=video_path,
        output_dir=output_dir,
        availability=availability,
        tracked_rows=tracked_rows,
        projected_rows=projected_rows,
        event_rows=event_rows,
    )
    write_json(output_dir / "replay_schema.json", schema)
    (output_dir / "replay_schema_pretty.md").write_text(schema_markdown(schema), encoding="utf-8")

    render_results = maybe_render_replays(event_rows, output_dir=output_dir, fps=12, enabled=generate_replays)

    report = build_report(
        availability=availability,
        tracking_result=tracking_result,
        video_path=video_path,
        annotation_path=annotation_path,
        events=events,
        hits=hits,
        bounces=bounces,
        tracked_rows=tracked_rows,
        projected_rows=projected_rows,
        event_rows=event_rows,
        output_dir=output_dir,
        render_results=render_results,
    )
    write_json(output_dir / "tracknet_replay_report.json", report)
    (output_dir / "tracknet_replay_report.md").write_text(report_markdown(report), encoding="utf-8")
    return report


def maybe_render_replays(
    event_rows: list[dict[str, Any]],
    *,
    output_dir: Path,
    fps: int,
    enabled: bool,
) -> dict[str, Any]:
    """Render TrackNet replays only when enough valid physical anchors exist."""
    if not enabled:
        return {"top_view_generated": False, "side_view_generated": False, "reason": "Replay generation disabled."}
    timeline = build_render_timeline(event_rows)
    physical = [row for row in timeline if row.get("should_render_as_physical_event") == "yes"]
    if len(physical) < 2:
        return {
            "top_view_generated": False,
            "side_view_generated": False,
            "reason": "Too few valid TrackNet physical anchors to render replay without fake geometry.",
            "physical_anchors": len(physical),
        }
    top = render_top_view(timeline, output_dir, fps=fps)
    side = render_side_view(timeline, output_dir, fps=fps)
    return {
        "top_view_generated": bool(top.get("video_generated")),
        "side_view_generated": bool(side.get("video_generated")),
        "top_view": top,
        "side_view": side,
        "physical_anchors": len(physical),
        "curve_segments_count": side.get("curve_segments", 0),
        "net_clearance_adjustments": side.get("net_clearance_adjustments", 0),
    }


def build_render_timeline(event_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert validated TrackNet event rows into renderer-facing timeline rows."""
    rows: list[dict[str, Any]] = []
    for row in event_rows:
        frame = row.get("manual_contact_frame", "")
        rows.append(
            {
                "event_id": row.get("event_id", ""),
                "sequence_index": row.get("sequence_index", ""),
                "event_type": row.get("event_type", ""),
                "validated_event_type": "validated_hit" if row.get("event_type") == "hit" else "validated_bounce",
                "shot_type": row.get("shot_type", ""),
                "frame_index": frame,
                "start_frame": row.get("manual_start_frame", ""),
                "end_frame": row.get("manual_end_frame", ""),
                "image_x": row.get("image_x", ""),
                "image_y": row.get("image_y", ""),
                "projected_x": row.get("projected_x", ""),
                "projected_y": row.get("projected_y", ""),
                "court_zone": row.get("court_zone", "unknown"),
                "depth": row.get("depth", "unknown"),
                "lateral_lane": row.get("lateral_lane", "unknown"),
                "position_status": row.get("position_status", ""),
                "position_trust": row.get("position_trust", "unresolved"),
                "confidence": row.get("tracknet_confidence", ""),
                "render_role": "physical_anchor" if row.get("should_render_as_physical_event") == "yes" else "annotation_only",
                "should_render_as_physical_event": row.get("should_render_as_physical_event", "no"),
                "should_render_as_annotation": row.get("should_render_as_annotation", "yes"),
                "notes": row.get("validation_reason", ""),
            }
        )
    return rows


def normalize_tracking_rows(rows: list[dict[str, Any]], *, fps: int) -> list[dict[str, Any]]:
    """Normalize TrackNet coordinate rows to the pipeline contract."""
    normalized: list[dict[str, Any]] = []
    for row in rows:
        frame = _int(row.get("frame_index"))
        if frame is None:
            continue
        normalized.append(
            {
                "frame_index": frame,
                "timestamp_seconds": round(frame / float(fps), 4),
                "ball_x": row.get("ball_x", row.get("x", "")),
                "ball_y": row.get("ball_y", row.get("y", "")),
                "confidence": row.get("confidence", ""),
                "source_model": row.get("source_model", "tracknet"),
                "visibility_status": row.get("visibility_status", "visible"),
                "notes": row.get("notes", ""),
            }
        )
    return normalized


def project_tracking_rows(rows: list[dict[str, Any]], calibration: dict[str, Any]) -> list[dict[str, Any]]:
    """Project TrackNet image-space rows to normalized court coordinates."""
    projected_points = project_image_points(
        [{"x": _float(row.get("ball_x")), "y": _float(row.get("ball_y"))} for row in rows],
        calibration.get("matrix"),
    )
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        projected = projected_points[index] if index < len(projected_points) else {}
        px = _float(projected.get("projected_x"))
        py = _float(projected.get("projected_y"))
        zone = assign_court_zone(px, py)
        output.append(
            {
                **row,
                "projected_x": round(px, 3) if px is not None else "",
                "projected_y": round(py, 3) if py is not None else "",
                "court_zone": zone["zone_id"],
                "depth": zone["depth"],
                "lateral_lane": zone["lateral_lane"],
                "projection_status": "projected" if px is not None and py is not None else "failed",
            }
        )
    return output


def resolve_events_from_tracknet(
    *,
    events: list[dict[str, Any]],
    projected_rows: list[dict[str, Any]],
    event_search_padding: int,
    blocked_status: str,
    blocked_reason: str,
) -> list[dict[str, Any]]:
    """Resolve manual event positions from TrackNet trajectory rows."""
    by_frame = {int(row["frame_index"]): row for row in projected_rows if _int(row.get("frame_index")) is not None}
    raw_events: list[dict[str, Any]] = []
    for event in events:
        search_start, search_end = event_search_range(event, event_search_padding)
        candidates = [row for frame, row in by_frame.items() if search_start <= frame <= search_end]
        best = max(candidates, key=lambda row: (_float(row.get("confidence")) or 0.0, -abs(int(row["frame_index"]) - int(event["contact_frame_estimate"]))), default=None)
        if not best:
            raw_events.append(unresolved_event_row(event, blocked_status=blocked_status, blocked_reason=blocked_reason))
            continue
        raw_events.append(
            {
                **event,
                "manual_start_frame": event["start_frame"],
                "manual_end_frame": event["end_frame"],
                "manual_contact_frame": event["contact_frame_estimate"],
                "resolved_frame": best["frame_index"],
                "image_x": best.get("ball_x", ""),
                "image_y": best.get("ball_y", ""),
                "projected_x": best.get("projected_x", ""),
                "projected_y": best.get("projected_y", ""),
                "court_zone": best.get("court_zone", "unknown"),
                "depth": best.get("depth", "unknown"),
                "lateral_lane": best.get("lateral_lane", "unknown"),
                "tracknet_confidence": best.get("confidence", ""),
                "event_position_status": "resolved",
                "event_position_source": "tracknet",
                "event_position_confidence": confidence_from_value(best.get("confidence")),
                "projection_status": best.get("projection_status", ""),
                "position_status": "resolved",
            }
        )
    validated = validate_manual_event_sequence(raw_events)
    return [flatten_event_row(row) for row in validated]


def unresolved_event_row(event: dict[str, Any], *, blocked_status: str, blocked_reason: str) -> dict[str, Any]:
    """Create an unresolved event position row."""
    reason = blocked_reason or "No TrackNet trajectory point was available near this manual event."
    return {
        **event,
        "manual_start_frame": event["start_frame"],
        "manual_end_frame": event["end_frame"],
        "manual_contact_frame": event["contact_frame_estimate"],
        "resolved_frame": "",
        "image_x": "",
        "image_y": "",
        "projected_x": "",
        "projected_y": "",
        "court_zone": "unknown",
        "depth": "unknown",
        "lateral_lane": "unknown",
        "tracknet_confidence": "",
        "event_position_status": "unresolved",
        "event_position_source": "tracknet",
        "event_position_confidence": "low",
        "projection_status": "not_attempted",
        "position_status": blocked_status or "unresolved",
        "position_notes": reason,
    }


def flatten_event_row(row: dict[str, Any]) -> dict[str, Any]:
    """Flatten a validated event row to CSV contract."""
    return {
        "event_id": row.get("event_id", ""),
        "sequence_index": row.get("sequence_index", ""),
        "event_type": row.get("event_type", ""),
        "shot_type": row.get("shot_type", ""),
        "manual_start_frame": row.get("manual_start_frame", row.get("start_frame", "")),
        "manual_end_frame": row.get("manual_end_frame", row.get("end_frame", "")),
        "manual_contact_frame": row.get("manual_contact_frame", row.get("contact_frame_estimate", "")),
        "resolved_frame": row.get("resolved_frame", ""),
        "image_x": row.get("image_x", ""),
        "image_y": row.get("image_y", ""),
        "projected_x": row.get("projected_x", ""),
        "projected_y": row.get("projected_y", ""),
        "court_zone": row.get("court_zone", "unknown"),
        "depth": row.get("depth", "unknown"),
        "lateral_lane": row.get("lateral_lane", "unknown"),
        "tracknet_confidence": row.get("tracknet_confidence", ""),
        "position_status": row.get("position_status", row.get("event_position_status", "")),
        "position_trust": row.get("position_trust", "unresolved"),
        "validation_status": row.get("position_validation_status", ""),
        "validation_reason": row.get("sequence_validation_reason", ""),
        "should_render_as_physical_event": row.get("should_render_as_physical_event", "no"),
        "should_render_as_annotation": row.get("should_render_as_annotation", "yes"),
    }


def event_search_range(event: dict[str, Any], padding: int) -> tuple[int, int]:
    """Return event search range."""
    start = int(event["start_frame"])
    end = int(event["end_frame"])
    return max(0, start - padding), end + padding


def build_replay_schema(
    *,
    annotation: dict[str, Any],
    annotation_path: Path,
    video_path: Path,
    output_dir: Path,
    availability: dict[str, Any],
    tracked_rows: list[dict[str, Any]],
    projected_rows: list[dict[str, Any]],
    event_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build TrackNet replay schema, even when blocked."""
    physical = [row for row in event_rows if row["should_render_as_physical_event"] == "yes"]
    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "schema_version": "tracknet_replay.v1",
            "pipeline": "tracknet_replay_pipeline",
            "model_source": "TrackNet-style temporal tracker",
            "model_status": availability.get("status", ""),
            "model_weights_path": availability.get("weights_path", ""),
            "manual_annotation_source": str(annotation_path),
            "side_view_height_is_synthetic": True,
        },
        "source_video": str(video_path),
        "fps": annotation.get("fps", 60),
        "court_model": {
            "normalized_court_width": COURT_WIDTH,
            "normalized_court_height": COURT_HEIGHT,
            "calibration_basis": "Stage 3 doubles court homography",
        },
        "ball_tracking_results": {
            "path": str(output_dir / "ball_tracking_results.csv"),
            "tracked_frames_count": len(tracked_rows),
        },
        "projected_ball_positions": {
            "path": str(output_dir / "projected_ball_positions.csv"),
            "projected_positions_count": len([row for row in projected_rows if row.get("projection_status") == "projected"]),
        },
        "event_positions": event_rows,
        "ball_trajectory": {
            "replay_keyframes": [
                {
                    "frame_index": row["manual_contact_frame"],
                    "projected_x": row["projected_x"],
                    "projected_y": row["projected_y"],
                    "event_id": row["event_id"],
                    "event_type": row["event_type"],
                    "shot_type": row["shot_type"],
                    "source": "tracknet_event_position",
                }
                for row in physical
            ]
        },
        "limitations": [
            "TrackNet results are required for physical replay anchors.",
            "Manual annotation supplies event timing only.",
            "Suspicious, invalid, or unresolved events are annotations only.",
            "Side-view height is synthetic and not measured 3D physics.",
        ],
    }


def top_view_transform() -> dict[str, float]:
    """Return a deterministic top-view court transform."""
    width, height = 1100, 900
    margin_x, margin_y = 210, 70
    scale = min((width - margin_x * 2) / COURT_WIDTH, (height - 170 - margin_y) / COURT_HEIGHT)
    return {"width": width, "height": height, "origin_x": (width - COURT_WIDTH * scale) / 2, "origin_y": margin_y, "scale": scale}


def map_top(point_x: Any, point_y: Any, transform: dict[str, float]) -> tuple[int, int] | None:
    """Map normalized court coordinates to top-view pixels."""
    x = _float(point_x)
    y = _float(point_y)
    if x is None or y is None:
        return None
    x = max(0.0, min(COURT_WIDTH, x))
    y = max(0.0, min(COURT_HEIGHT, y))
    return int(round(transform["origin_x"] + x * transform["scale"])), int(round(transform["origin_y"] + y * transform["scale"]))


def render_top_view(timeline: list[dict[str, Any]], output_dir: Path, fps: int) -> dict[str, Any]:
    """Render a compact top-view replay from validated TrackNet anchors."""
    import cv2
    import numpy as np

    transform = top_view_transform()
    physical = [row for row in timeline if row.get("should_render_as_physical_event") == "yes"]
    frames_dir = output_dir / "top_view_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    frame_paths: list[Path] = []
    for index in range(len(physical)):
        canvas = draw_top_court(transform)
        mapped = [(row, map_top(row.get("projected_x"), row.get("projected_y"), transform)) for row in physical[: index + 1]]
        mapped = [(row, point) for row, point in mapped if point is not None]
        for (_row_a, point_a), (_row_b, point_b) in zip(mapped, mapped[1:]):
            cv2.line(canvas, point_a, point_b, (90, 230, 255), 2, cv2.LINE_AA)
        for row, point in mapped:
            is_hit = row.get("event_type") == "hit"
            color = (0, 150, 255) if is_hit else (60, 240, 80)
            cv2.circle(canvas, point, 8, color, -1, cv2.LINE_AA)
            label = f"{'H' if is_hit else 'B'}{row.get('sequence_index', '')}"
            cv2.putText(canvas, label, (point[0] + 9, point[1] - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)
        current = physical[index]
        shot = f" | {current.get('shot_type')}" if current.get("shot_type") else ""
        cv2.putText(canvas, f"{current.get('event_id')} {current.get('event_type')}{shot}", (30, 805), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (245, 245, 245), 1, cv2.LINE_AA)
        path = frames_dir / f"top_view_frame_{index:04d}.jpg"
        cv2.imwrite(str(path), canvas)
        frame_paths.append(path)
    video_path = output_dir / "top_view_replay.mp4"
    video_generated = export_video(frame_paths, video_path, fps)
    contact_sheet = output_dir / "top_view_contact_sheet.jpg"
    create_contact_sheet(frame_paths, contact_sheet)
    final_frame = output_dir / "top_view_final_frame.jpg"
    if frame_paths:
        final_frame.write_bytes(frame_paths[-1].read_bytes())
    return {"video_path": str(video_path), "video_generated": video_generated, "contact_sheet": str(contact_sheet), "final_frame": str(final_frame), "frames": len(frame_paths)}


def draw_top_court(transform: dict[str, float]) -> Any:
    """Draw a tennis court background for top-view TrackNet replay."""
    import cv2
    import numpy as np

    canvas = np.full((int(transform["height"]), int(transform["width"]), 3), (24, 72, 44), dtype=np.uint8)
    left, top = int(transform["origin_x"]), int(transform["origin_y"])
    right = int(transform["origin_x"] + COURT_WIDTH * transform["scale"])
    bottom = int(transform["origin_y"] + COURT_HEIGHT * transform["scale"])
    cv2.rectangle(canvas, (left, top), (right, bottom), (55, 128, 72), -1)
    cv2.rectangle(canvas, (left, top), (right, bottom), (245, 245, 245), 2)
    cv2.line(canvas, (left, (top + bottom) // 2), (right, (top + bottom) // 2), (245, 245, 245), 2)
    for fraction in (1 / 3, 2 / 3):
        x = int(left + (right - left) * fraction)
        cv2.line(canvas, (x, top), (x, bottom), (180, 220, 185), 1)
    cv2.putText(canvas, "TrackNet top view - validated ball anchors only", (30, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (245, 245, 245), 2)
    cv2.putText(canvas, "Manual timing; TrackNet positions. Suspicious/unresolved events are not physical anchors.", (30, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (220, 220, 220), 1)
    return canvas


def render_side_view(timeline: list[dict[str, Any]], output_dir: Path, fps: int) -> dict[str, Any]:
    """Render a synthetic curved side-view replay from validated TrackNet anchors."""
    import cv2

    segments, samples = build_side_view_curve_segments(timeline, court_height=COURT_HEIGHT)
    write_side_view_curve_segments(output_dir / "side_view_curve_segments.csv", segments)
    write_json(output_dir / "side_view_curve_segments.json", segments)
    physical = [row for row in timeline if row.get("should_render_as_physical_event") == "yes"]
    samples_by_segment: dict[str, list[dict[str, Any]]] = {}
    for sample in samples:
        samples_by_segment.setdefault(sample["segment_id"], []).append(sample)
    frames_dir = output_dir / "side_view_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    frame_paths: list[Path] = []
    transform = side_transform()
    step_counter = 0
    for segment_index, segment in enumerate(segments):
        segment_samples = samples_by_segment.get(segment["segment_id"], [])
        for sample_index in range(max(1, len(segment_samples))):
            canvas = draw_side_base()
            for draw_index, draw_segment in enumerate(segments):
                draw_samples = samples_by_segment.get(draw_segment["segment_id"], [])
                if draw_index < segment_index:
                    visible_samples = draw_samples
                elif draw_segment["segment_id"] == segment["segment_id"]:
                    visible_samples = draw_samples[: sample_index + 1]
                else:
                    visible_samples = []
                points = [map_side(item.get("x"), item.get("height"), transform) for item in visible_samples]
                points = [point for point in points if point is not None]
                for point_a, point_b in zip(points, points[1:]):
                    cv2.line(canvas, point_a, point_b, (90, 225, 255), 2, cv2.LINE_AA)
            for row in physical:
                height = 0 if row.get("event_type") == "bounce" else 88
                point = map_side(row.get("projected_y"), height, transform)
                if point is None:
                    continue
                color = (0, 150, 255) if row.get("event_type") == "hit" else (60, 240, 80)
                cv2.circle(canvas, point, 7, color, -1, cv2.LINE_AA)
                label = f"{'H' if row.get('event_type') == 'hit' else 'B'}{row.get('sequence_index', '')}"
                cv2.putText(canvas, label, (point[0] + 8, point[1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.43, color, 1, cv2.LINE_AA)
            cv2.putText(canvas, f"{segment.get('from_event_id')} -> {segment.get('to_event_id')} | {segment.get('curve_profile')}", (32, 665), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (245, 245, 245), 1, cv2.LINE_AA)
            path = frames_dir / f"side_view_frame_{step_counter:04d}.jpg"
            cv2.imwrite(str(path), canvas)
            frame_paths.append(path)
            step_counter += 1
    video_path = output_dir / "side_view_replay.mp4"
    video_generated = export_video(frame_paths, video_path, fps)
    contact_sheet = output_dir / "side_view_contact_sheet.jpg"
    create_contact_sheet(frame_paths, contact_sheet)
    final_frame = output_dir / "side_view_final_frame.jpg"
    arc_preview = output_dir / "side_view_arc_preview.jpg"
    if frame_paths:
        final_frame.write_bytes(frame_paths[-1].read_bytes())
        arc_preview.write_bytes(frame_paths[-1].read_bytes())
    return {
        "video_path": str(video_path),
        "video_generated": video_generated,
        "contact_sheet": str(contact_sheet),
        "final_frame": str(final_frame),
        "arc_preview": str(arc_preview),
        "frames": len(frame_paths),
        "curve_segments": len(segments),
        "net_clearance_adjustments": sum(1 for row in segments if row.get("net_clearance_adjusted") == "yes"),
    }


def side_transform() -> dict[str, float]:
    """Return side-view transform."""
    return {"width": 1200, "height": 720, "left": 90, "right": 1110, "floor": 585, "top": 80, "height_scale": 2.3}


def map_side(depth: Any, height: Any, transform: dict[str, float]) -> tuple[int, int] | None:
    """Map court depth and synthetic height to side-view pixels."""
    d = _float(depth)
    h = _float(height)
    if d is None or h is None:
        return None
    d = max(0.0, min(COURT_HEIGHT, d))
    x = transform["left"] + (d / COURT_HEIGHT) * (transform["right"] - transform["left"])
    y = transform["floor"] - h * transform["height_scale"]
    return int(round(x)), int(round(max(transform["top"], min(transform["floor"], y))))


def draw_side_base() -> Any:
    """Draw side-view court base."""
    import cv2
    import numpy as np

    transform = side_transform()
    canvas = np.full((int(transform["height"]), int(transform["width"]), 3), (18, 18, 18), dtype=np.uint8)
    cv2.line(canvas, (int(transform["left"]), int(transform["floor"])), (int(transform["right"]), int(transform["floor"])), (235, 235, 235), 2)
    net_x = int(transform["left"] + 0.5 * (transform["right"] - transform["left"]))
    cv2.line(canvas, (net_x, int(transform["floor"])), (net_x, int(transform["floor"] - 92)), (220, 220, 220), 3)
    cv2.putText(canvas, "TrackNet side view - synthetic curved tennis arcs", (32, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (245, 245, 245), 2)
    cv2.putText(canvas, "Curves use shot metadata for visual plausibility; not measured 3D height.", (32, 66), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (210, 210, 210), 1)
    return canvas


def export_video(frame_paths: list[Path], output_path: Path, fps: int) -> bool:
    """Export frames to MP4."""
    import cv2

    if not frame_paths:
        return False
    first = cv2.imread(str(frame_paths[0]))
    if first is None:
        return False
    height, width = first.shape[:2]
    writer = cv2.VideoWriter(str(output_path), cv2.VideoWriter_fourcc(*"mp4v"), float(fps), (width, height))
    if not writer.isOpened():
        return False
    for path in frame_paths:
        frame = cv2.imread(str(path))
        if frame is not None:
            writer.write(frame)
    writer.release()
    return output_path.exists()


def create_contact_sheet(frame_paths: list[Path], output_path: Path, max_items: int = 12) -> bool:
    """Create a simple contact sheet for rendered replay frames."""
    import cv2
    import numpy as np

    if not frame_paths:
        return False
    indices = np.linspace(0, len(frame_paths) - 1, min(max_items, len(frame_paths))).round().astype(int)
    images = [cv2.imread(str(frame_paths[int(index)])) for index in indices]
    images = [image for image in images if image is not None]
    if not images:
        return False
    thumb_width = 260
    thumbs = []
    for image in images:
        scale = thumb_width / image.shape[1]
        thumbs.append(cv2.resize(image, (thumb_width, int(image.shape[0] * scale)), interpolation=cv2.INTER_AREA))
    max_height = max(image.shape[0] for image in thumbs)
    padded = []
    for thumb in thumbs:
        if thumb.shape[0] < max_height:
            pad = np.full((max_height - thumb.shape[0], thumb.shape[1], 3), (20, 20, 20), dtype=np.uint8)
            thumb = np.vstack([thumb, pad])
        padded.append(thumb)
    sheet = np.hstack(padded)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), sheet)
    return output_path.exists()


def build_report(
    *,
    availability: dict[str, Any],
    tracking_result: dict[str, Any],
    video_path: Path,
    annotation_path: Path,
    events: list[dict[str, Any]],
    hits: list[dict[str, Any]],
    bounces: list[dict[str, Any]],
    tracked_rows: list[dict[str, Any]],
    projected_rows: list[dict[str, Any]],
    event_rows: list[dict[str, Any]],
    output_dir: Path,
    render_results: dict[str, Any],
) -> dict[str, Any]:
    """Build TrackNet replay pipeline report."""
    valid = [row for row in event_rows if row["position_trust"] == "valid"]
    suspicious = [row for row in event_rows if row["position_trust"] == "suspicious"]
    invalid = [row for row in event_rows if row["position_trust"] == "invalid"]
    unresolved = [row for row in event_rows if row["position_trust"] == "unresolved"]
    projected_count = sum(1 for row in projected_rows if row.get("projection_status") == "projected")
    top_view_generated = bool(render_results.get("top_view_generated")) and (output_dir / "top_view_replay.mp4").exists()
    side_view_generated = bool(render_results.get("side_view_generated")) and (output_dir / "side_view_replay.mp4").exists()
    verdict, failure_reason = classify_verdict(availability, event_rows, top_view_generated, side_view_generated)
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stage": "tracknet_replay_pipeline",
        "model_available": bool(availability.get("available")),
        "weights_found": bool(availability.get("weights_found")),
        "dependencies_available": bool(availability.get("dependencies_available")),
        "model_name": "tracknet",
        "model_weights_path": availability.get("weights_path", ""),
        "weight_type": availability.get("weight_type", "missing"),
        "architecture_available": bool(availability.get("architecture_available")),
        "architecture_modules_found": int(availability.get("architecture_modules_found") or 0),
        "architecture_status": availability.get("architecture_status", "missing"),
        "weights_status": availability.get("weights_status", "missing"),
        "inference_implementation_status": availability.get("inference_implementation_status", "not_ready"),
        "ready_for_inference": bool(availability.get("ready_for_inference")),
        "video_path": str(video_path),
        "manual_annotation_source": str(annotation_path),
        "manual_events_count": len(events),
        "hits_count": len(hits),
        "bounces_count": len(bounces),
        "tracked_frames_count": len(tracked_rows),
        "event_positions_resolved": sum(1 for row in event_rows if row["position_status"] == "resolved"),
        "event_positions_valid": len(valid),
        "event_positions_suspicious": len(suspicious),
        "event_positions_invalid": len(invalid),
        "event_positions_unresolved": len(unresolved),
        "projected_positions_count": projected_count,
        "top_view_generated": top_view_generated,
        "side_view_generated": side_view_generated,
        "curve_segments_count": int(render_results.get("curve_segments_count") or 0),
        "net_clearance_adjustments": int(render_results.get("net_clearance_adjustments") or 0),
        "replay_trustworthy": verdict == "ready_for_review",
        "failure_reason": failure_reason or render_results.get("reason", ""),
        "recommended_next_step": recommended_next_step(verdict, availability),
        "exact_next_action": availability.get("exact_next_action", ""),
        "final_verdict": verdict,
        "tracknet_status": tracking_result.get("status", availability.get("status", "")),
        "warnings": [],
        "errors": [] if verdict.startswith("blocked") else [],
        "output_folder": str(output_dir),
        "output_paths": {
            "ball_tracking_results": str(output_dir / "ball_tracking_results.csv"),
            "projected_ball_positions": str(output_dir / "projected_ball_positions.csv"),
            "event_position_results": str(output_dir / "event_position_results.csv"),
            "replay_schema": str(output_dir / "replay_schema.json"),
            "top_view_replay": str(output_dir / "top_view_replay.mp4"),
            "side_view_replay": str(output_dir / "side_view_replay.mp4"),
            "report_json": str(output_dir / "tracknet_replay_report.json"),
            "report_md": str(output_dir / "tracknet_replay_report.md"),
        },
    }


def classify_verdict(availability: dict[str, Any], event_rows: list[dict[str, Any]], top: bool, side: bool) -> tuple[str, str]:
    """Classify pipeline result."""
    status = availability.get("status")
    if status == "weights_missing":
        return "blocked_weights_missing", availability.get("reason", "TrackNet weights are missing.")
    if status == "dependency_missing":
        return "blocked_dependency_missing", availability.get("reason", "TrackNet dependencies are missing.")
    if status == "architecture_missing":
        return "blocked_architecture_missing", availability.get("reason", "TrackNet architecture is missing.")
    if status == "model_unavailable":
        return "needs_better_tracknet_integration", availability.get("reason", "TrackNet inference is not wired.")
    if status in {"unsupported_weight_format", "model_load_failed", "inference_not_implemented"}:
        return "needs_better_tracknet_integration", availability.get("reason", "TrackNet inference is not ready.")
    valid = sum(1 for row in event_rows if row["position_trust"] == "valid")
    unresolved = sum(1 for row in event_rows if row["position_trust"] == "unresolved")
    if valid >= 10 and top and side:
        return "ready_for_review", ""
    if unresolved >= len(event_rows) / 2:
        return "needs_better_tracknet_integration", "TrackNet did not resolve enough event positions."
    if top or side:
        return "ready_with_warnings", "Replay generated with validation warnings."
    return "failed", "Replay would require fake anchors, so it was not generated."


def recommended_next_step(verdict: str, availability: dict[str, Any]) -> str:
    """Return recommended next step."""
    if verdict == "blocked_weights_missing":
        return "TrackNet cannot run yet because architecture modules found=0 and weights found=false. Next required artifact: TrackNet architecture plus matching pretrained weights. Place weights in models/tracknet/weights/ or pass --tracknet-weights, then rerun python scripts/check_tracknet_integration.py."
    if verdict == "blocked_dependency_missing":
        return f"Install missing local dependencies: {', '.join(availability.get('missing_dependencies', []))}."
    if verdict == "blocked_architecture_missing":
        return "Wire the TrackNet architecture class that matches the local checkpoint/state_dict, or use a full PyTorch model file with its architecture serialized."
    if verdict == "needs_better_tracknet_integration":
        status = availability.get("status")
        if status == "architecture_missing":
            return "Wire the TrackNet architecture class that matches the local checkpoint/state_dict."
        if status == "inference_not_implemented":
            return "Implement load_model/infer_clip for the local TrackNet architecture."
        if status == "unsupported_weight_format":
            return "Use a compatible .pt or .pth TrackNet weight file."
        return "Wire a concrete TrackNet inference implementation to load local weights and return per-frame ball coordinates."
    return "Review TrackNet replay outputs."


def report_markdown(report: dict[str, Any]) -> str:
    """Render report Markdown."""
    return f"""# TrackNet Replay Pipeline Report

VERDICT
  Final verdict: {report["final_verdict"]}
  Replay trustworthy: {report["replay_trustworthy"]}

MODEL
  Model available: {report["model_available"]}
  Weights found: {report["weights_found"]}
  Architecture available: {report["architecture_available"]}
  Architecture modules found: {report["architecture_modules_found"]}
  Architecture status: {report["architecture_status"]}
  Weights status: {report["weights_status"]}
  Inference implementation status: {report["inference_implementation_status"]}
  Ready for inference: {report["ready_for_inference"]}
  Dependencies available: {report["dependencies_available"]}
  Model weights path: {report["model_weights_path"] or "None"}
  Weight type: {report.get("weight_type", "unknown")}

SUMMARY
  Manual events: {report["manual_events_count"]}
  Hits: {report["hits_count"]}
  Bounces: {report["bounces_count"]}
  Tracked frames: {report["tracked_frames_count"]}
  Projected positions: {report["projected_positions_count"]}
  Valid event positions: {report["event_positions_valid"]}
  Suspicious event positions: {report["event_positions_suspicious"]}
  Invalid event positions: {report["event_positions_invalid"]}
  Unresolved event positions: {report["event_positions_unresolved"]}

REPLAY OUTPUTS
  Top-view generated: {report["top_view_generated"]}
  Side-view generated: {report["side_view_generated"]}
  Curve segments: {report["curve_segments_count"]}
  Net clearance adjustments: {report["net_clearance_adjustments"]}

FAILURE REASON
  {report["failure_reason"] or "None"}

WHY TRACKNET CANNOT RUN YET
  Architecture modules found: {report["architecture_modules_found"]}
  Weights found: {report["weights_found"]}
  Ready for inference: {report["ready_for_inference"]}
  Next required artifact: TrackNet architecture plus matching pretrained weights.

EXPECTED WEIGHT LOCATIONS
  models/tracknet/weights/tracknet.pt
  models/tracknet/weights/tracknet.pth
  models/tracknet/weights/tracknetv2.pt
  models/tracknet/weights/tracknetv2.pth
  models/tracknet/weights/tracknetv3.pt
  models/tracknet/weights/tracknetv3.pth
  models/tracknet/weights/tracknetv4.pt
  models/tracknet/weights/tracknetv4.pth

NEXT CHECK COMMAND
  python scripts/check_tracknet_integration.py

RECOMMENDED NEXT STEP
  {report["recommended_next_step"]}

EXACT NEXT ACTION
  {report.get("exact_next_action") or report["recommended_next_step"]}

OUTPUTS
  Ball tracking: {report["output_paths"]["ball_tracking_results"]}
  Projected positions: {report["output_paths"]["projected_ball_positions"]}
  Event positions: {report["output_paths"]["event_position_results"]}
  Replay schema: {report["output_paths"]["replay_schema"]}
"""


def schema_markdown(schema: dict[str, Any]) -> str:
    """Render schema summary Markdown."""
    return f"""# TrackNet Replay Schema

Pipeline:
  {schema["metadata"]["pipeline"]}

Model status:
  {schema["metadata"]["model_status"]}

Tracked frames:
  {schema["ball_tracking_results"]["tracked_frames_count"]}

Event positions:
  {len(schema["event_positions"])}

Limitations:
  - TrackNet results are required for physical replay anchors.
  - Manual annotation supplies event timing only.
  - Side-view height is synthetic, not measured 3D.
"""


def confidence_from_value(value: Any) -> str:
    """Convert numeric confidence into a coarse label."""
    score = _float(value)
    if score is None:
        return "low"
    if score >= 0.75:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    """Write CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    """Write JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
