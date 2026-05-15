"""Regenerate full-rally replay from manual timing and resolved ball positions."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from tennis_vision.court_zones import COURT_HEIGHT, COURT_WIDTH  # noqa: E402
from tennis_vision.baseline_quarantine import annotate_report_with_failed_baseline_warning, failed_baseline_block_message, print_failed_baseline_warning  # noqa: E402
from tennis_vision.manual_event_position_resolver import (  # noqa: E402
    load_manual_full_rally_annotation,
    normalize_manual_events,
    resolve_manual_event_positions,
    write_resolved_manual_events,
)
from tennis_vision.side_view_curve_model import build_side_view_curve_segments, write_side_view_curve_segments  # noqa: E402
from tennis_vision.tennis_sequence_validator import validate_manual_event_sequence  # noqa: E402


ANNOTATION_PATH = PROJECT_ROOT / "configs" / "manual_annotations" / "video_01_full_rally.json"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "replay" / "manual_full_rally"
REPORT_DIR = PROJECT_ROOT / "outputs" / "reports"
LAB_NOTEBOOK_PATH = PROJECT_ROOT / "docs" / "lab-notebook" / "manual_full_rally_replay.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manual full-rally replay regeneration with resolved positions and curved side-view.")
    parser.add_argument("--annotation", type=Path, default=ANNOTATION_PATH)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--event-position-search-padding", type=int, default=3)
    parser.add_argument("--fallback-tolerance", type=int, default=8)
    parser.add_argument("--resize-width", type=int, default=1280)
    parser.add_argument("--allow-failed-baseline", action="store_true", help="Allow the failed YOLO/HSV/local baseline replay path for explicit research only.")
    return parser.parse_args()


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_sequence_validation_audit(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write tennis-sequence position validation audit rows."""
    fields = [
        "event_id",
        "event_type",
        "shot_type",
        "projected_x",
        "projected_y",
        "court_zone",
        "original_position_source",
        "position_trust",
        "validation_status",
        "validation_reason",
        "render_as_physical_event",
    ]
    audit_rows = [
        {
            "event_id": row.get("event_id", ""),
            "event_type": row.get("event_type", ""),
            "shot_type": row.get("shot_type", ""),
            "projected_x": row.get("projected_x", ""),
            "projected_y": row.get("projected_y", ""),
            "court_zone": row.get("court_zone", ""),
            "original_position_source": row.get("event_position_source", ""),
            "position_trust": row.get("position_trust", ""),
            "validation_status": row.get("position_validation_status", ""),
            "validation_reason": row.get("sequence_validation_reason", ""),
            "render_as_physical_event": row.get("should_render_as_physical_event", "no"),
        }
        for row in rows
    ]
    write_csv(path, audit_rows, fields)


def build_full_rally_event_timeline(resolved_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build renderer-facing full-rally event timeline from resolved manual events."""
    rows: list[dict[str, Any]] = []
    for row in resolved_rows:
        trust = row.get("position_trust") or "unresolved"
        resolved = (
            row["event_position_status"] == "resolved"
            and row["projection_status"] == "projected"
            and trust == "valid"
        )
        event_type = row["event_type"]
        rows.append(
            {
                "event_id": row["event_id"],
                "sequence_index": row["sequence_index"],
                "event_type": event_type,
                "validated_event_type": "validated_hit" if event_type == "hit" else "validated_bounce",
                "shot_type": row.get("shot_type") or "",
                "frame_index": row["contact_frame_estimate"],
                "start_frame": row["start_frame"],
                "end_frame": row["end_frame"],
                "image_x": row.get("image_x", ""),
                "image_y": row.get("image_y", ""),
                "projected_x": row.get("projected_x", ""),
                "projected_y": row.get("projected_y", ""),
                "court_zone": row.get("court_zone", "unknown"),
                "depth": row.get("depth", "unknown"),
                "lateral_lane": row.get("lateral_lane", "unknown"),
                "position_status": row["event_position_status"],
                "position_trust": trust,
                "position_validation_status": row.get("position_validation_status", ""),
                "sequence_validation_reason": row.get("sequence_validation_reason", ""),
                "confidence": row["confidence"],
                "render_role": "validated_hit" if event_type == "hit" and resolved else "validated_bounce" if event_type == "bounce" and resolved else "unresolved_annotation",
                "should_render_as_physical_event": row.get("should_render_as_physical_event", "yes" if resolved else "no") if resolved else "no",
                "should_render_as_annotation": row.get("should_render_as_annotation", "yes"),
                "notes": row.get("position_notes") or row.get("notes") or "",
            }
        )
    return rows


def build_replay_schema(annotation: dict[str, Any], timeline: list[dict[str, Any]], summary: dict[str, Any]) -> dict[str, Any]:
    """Build manual full-rally replay schema."""
    physical = [row for row in timeline if row["should_render_as_physical_event"] == "yes"]
    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "project_name": "Tennis AI Vision",
            "stage": "manual_full_rally_replay",
            "schema_version": "manual_full_rally.v1",
            "manual_annotation_source": str(ANNOTATION_PATH),
            "event_times_are_manual": True,
            "positions_are_automatically_resolved": True,
            "side_view_height_is_synthetic": True,
        },
        "source_video": {
            "video_path": annotation.get("source_video") or annotation.get("source_video_path"),
            "fps": annotation.get("fps"),
        },
        "court_model": {
            "normalized_court_width": COURT_WIDTH,
            "normalized_court_height": COURT_HEIGHT,
            "calibration_basis": "Stage 3 doubles court homography",
        },
        "event_timeline": timeline,
        "ball_trajectory": {
            "replay_keyframes": [
                {
                    "frame_index": row["frame_index"],
                    "timestamp_seconds": round(int(row["frame_index"]) / float(annotation.get("fps") or 60), 3),
                    "projected_x": row["projected_x"],
                    "projected_y": row["projected_y"],
                    "source": "manual_timing_resolved_ball_position",
                    "event_id": row["event_id"],
                    "event_type": row["event_type"],
                    "shot_type": row["shot_type"],
                    "is_interpolated": False,
                    "notes": "Position resolved automatically near manual event time.",
                }
                for row in physical
            ]
        },
        "manual_resolution_summary": summary,
        "limitations": [
            "Product Owner provides event timing and shot type only.",
            "Ball positions are resolved automatically from local video/candidate/fallback data.",
            "Unresolved positions are not rendered as known physical court points.",
            "Side-view arcs are synthetic visual approximations, not measured 3D physics.",
            "Future line calling requires contact localization and uncertainty.",
        ],
    }


def top_view_transform() -> dict[str, float]:
    width, height = 1100, 900
    margin_x, margin_y = 210, 70
    scale = min((width - margin_x * 2) / COURT_WIDTH, (height - 170 - margin_y) / COURT_HEIGHT)
    return {"width": width, "height": height, "origin_x": (width - COURT_WIDTH * scale) / 2, "origin_y": margin_y, "scale": scale}


def map_top(point_x: Any, point_y: Any, transform: dict[str, float]) -> tuple[int, int] | None:
    x = to_float(point_x)
    y = to_float(point_y)
    if x is None or y is None:
        return None
    x = max(0.0, min(COURT_WIDTH, x))
    y = max(0.0, min(COURT_HEIGHT, y))
    return int(round(transform["origin_x"] + x * transform["scale"])), int(round(transform["origin_y"] + y * transform["scale"]))


def draw_top_court(transform: dict[str, float]) -> np.ndarray:
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
    cv2.putText(canvas, "Manual full-rally top view - resolved ball positions", (30, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (245, 245, 245), 2)
    cv2.putText(canvas, "Timing is manual; positions are automatically resolved. Unresolved events are not physical anchors.", (30, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (220, 220, 220), 1)
    return canvas


def render_top_view(timeline: list[dict[str, Any]], output_dir: Path, fps: int) -> dict[str, Any]:
    """Render manual full-rally top-view replay."""
    transform = top_view_transform()
    physical = [row for row in timeline if row["should_render_as_physical_event"] == "yes"]
    frames_dir = output_dir / "top_view_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    frame_paths: list[Path] = []
    for index in range(len(physical)):
        canvas = draw_top_court(transform)
        visible = physical[: index + 1]
        mapped = [(row, map_top(row["projected_x"], row["projected_y"], transform)) for row in visible]
        mapped = [(row, point) for row, point in mapped if point is not None]
        for (_row_a, point_a), (_row_b, point_b) in zip(mapped, mapped[1:]):
            cv2.line(canvas, point_a, point_b, (90, 230, 255), 2, cv2.LINE_AA)
        for row, point in mapped:
            is_hit = row["event_type"] == "hit"
            color = (0, 150, 255) if is_hit else (60, 240, 80)
            cv2.circle(canvas, point, 8, color, -1, cv2.LINE_AA)
            label = f"{'H' if is_hit else 'B'}{row['sequence_index']}"
            cv2.putText(canvas, label, (point[0] + 9, point[1] - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)
        current = physical[index]
        shot = f" | {current['shot_type']}" if current.get("shot_type") else ""
        cv2.putText(canvas, f"{current['event_id']} {current['event_type']}{shot}", (30, 805), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (245, 245, 245), 1, cv2.LINE_AA)
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


def side_transform() -> dict[str, float]:
    return {"width": 1200, "height": 720, "left": 90, "right": 1110, "floor": 585, "top": 80, "height_scale": 2.3}


def map_side(depth: Any, height: Any, transform: dict[str, float]) -> tuple[int, int] | None:
    d = to_float(depth)
    h = to_float(height)
    if d is None or h is None:
        return None
    d = max(0.0, min(COURT_HEIGHT, d))
    x = transform["left"] + (d / COURT_HEIGHT) * (transform["right"] - transform["left"])
    y = transform["floor"] - h * transform["height_scale"]
    return int(round(x)), int(round(max(transform["top"], min(transform["floor"], y))))


def draw_side_base() -> np.ndarray:
    t = side_transform()
    canvas = np.full((int(t["height"]), int(t["width"]), 3), (18, 18, 18), dtype=np.uint8)
    cv2.line(canvas, (int(t["left"]), int(t["floor"])), (int(t["right"]), int(t["floor"])), (235, 235, 235), 2)
    net_x = int(t["left"] + 0.5 * (t["right"] - t["left"]))
    cv2.line(canvas, (net_x, int(t["floor"])), (net_x, int(t["floor"] - 92)), (220, 220, 220), 3)
    cv2.putText(canvas, "Manual full-rally side view - synthetic curved tennis arcs", (32, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (245, 245, 245), 2)
    cv2.putText(canvas, "Curves are visual approximations from shot type; not measured 3D height.", (32, 66), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (210, 210, 210), 1)
    return canvas


def render_side_view(timeline: list[dict[str, Any]], output_dir: Path, fps: int) -> dict[str, Any]:
    """Render curved synthetic side-view replay."""
    segments, samples = build_side_view_curve_segments(timeline, court_height=COURT_HEIGHT)
    write_side_view_curve_segments(output_dir / "side_view_curve_segments.csv", segments)
    write_json(output_dir / "side_view_curve_segments.json", segments)
    physical = [row for row in timeline if row["should_render_as_physical_event"] == "yes"]
    samples_by_segment: dict[str, list[dict[str, Any]]] = {}
    for sample in samples:
        samples_by_segment.setdefault(sample["segment_id"], []).append(sample)
    frames_dir = output_dir / "side_view_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    frame_paths: list[Path] = []
    t = side_transform()
    total_steps = sum(max(1, len(samples_by_segment.get(segment["segment_id"], []))) for segment in segments)
    step_counter = 0
    for segment in segments:
        segment_samples = samples_by_segment.get(segment["segment_id"], [])
        for sample_index in range(max(1, len(segment_samples))):
            canvas = draw_side_base()
            completed_ids = {item["segment_id"] for item in segments[: max(0, int(segment["segment_id"].split("_")[-1]) - 1)]}
            for draw_segment in segments:
                draw_samples = samples_by_segment.get(draw_segment["segment_id"], [])
                if draw_segment["segment_id"] in completed_ids:
                    visible_samples = draw_samples
                elif draw_segment["segment_id"] == segment["segment_id"]:
                    visible_samples = draw_samples[: sample_index + 1]
                else:
                    visible_samples = []
                points = [map_side(item["x"], item["height"], t) for item in visible_samples]
                points = [point for point in points if point is not None]
                for point_a, point_b in zip(points, points[1:]):
                    cv2.line(canvas, point_a, point_b, (90, 225, 255), 2, cv2.LINE_AA)
            for row in physical:
                profile_height = 0 if row["event_type"] == "bounce" else 88
                point = map_side(row.get("projected_y"), profile_height, t)
                if point is None:
                    continue
                color = (0, 150, 255) if row["event_type"] == "hit" else (60, 240, 80)
                cv2.circle(canvas, point, 7, color, -1, cv2.LINE_AA)
                cv2.putText(canvas, f"{'H' if row['event_type']=='hit' else 'B'}{row['sequence_index']}", (point[0] + 8, point[1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.43, color, 1, cv2.LINE_AA)
            cv2.putText(canvas, f"{segment['from_event_id']} -> {segment['to_event_id']} | {segment['curve_profile']}", (32, 665), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (245, 245, 245), 1, cv2.LINE_AA)
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
        "straight_segments_used": 0,
        "net_clearance_adjustments": sum(1 for row in segments if row["net_clearance_adjusted"] == "yes"),
    }


def export_video(frame_paths: list[Path], output_path: Path, fps: int) -> bool:
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
    if not frame_paths:
        return False
    indices = np.linspace(0, len(frame_paths) - 1, min(max_items, len(frame_paths))).round().astype(int)
    images = [cv2.imread(str(frame_paths[int(index)])) for index in indices]
    images = [image for image in images if image is not None]
    if not images:
        return False
    thumb_w = 260
    thumbs = []
    for image in images:
        h, w = image.shape[:2]
        thumb_h = int(round(h * (thumb_w / w)))
        thumbs.append(cv2.resize(image, (thumb_w, thumb_h), interpolation=cv2.INTER_AREA))
    columns = 4
    rows = int(np.ceil(len(thumbs) / columns))
    cell_h = max(image.shape[0] for image in thumbs)
    sheet = np.zeros((rows * cell_h, columns * thumb_w, 3), dtype=np.uint8)
    for index, image in enumerate(thumbs):
        y = (index // columns) * cell_h
        x = (index % columns) * thumb_w
        sheet[y : y + image.shape[0], x : x + image.shape[1]] = image
    return cv2.imwrite(str(output_path), sheet)


def build_report(
    *,
    annotation_path: Path,
    annotation: dict[str, Any],
    resolved: list[dict[str, Any]],
    timeline: list[dict[str, Any]],
    top_result: dict[str, Any],
    side_result: dict[str, Any],
    summary: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    hits = [row for row in timeline if row["event_type"] == "hit"]
    bounces = [row for row in timeline if row["event_type"] == "bounce"]
    unresolved = [row["event_id"] for row in timeline if row["position_status"] != "resolved"]
    valid_positions = [row for row in timeline if row.get("position_trust") == "valid"]
    suspicious_positions = [row for row in timeline if row.get("position_trust") == "suspicious"]
    invalid_positions = [row for row in timeline if row.get("position_trust") == "invalid"]
    unresolved_trust = [row for row in timeline if row.get("position_trust") == "unresolved"]
    physical_anchors = [row for row in timeline if row.get("should_render_as_physical_event") == "yes"]
    annotations = [row for row in timeline if row.get("should_render_as_annotation") == "yes"]
    unsafe_rendered = [
        row
        for row in timeline
        if row.get("position_trust") != "valid" and row.get("should_render_as_physical_event") == "yes"
    ]
    warnings = list(summary.get("warnings", []))
    errors = list(summary.get("errors", []))
    if unresolved:
        warnings.append(f"Unresolved events: {', '.join(unresolved)}")
    if suspicious_positions:
        warnings.append(f"Suspicious positions blocked from physical rendering: {', '.join(row['event_id'] for row in suspicious_positions)}")
    if invalid_positions:
        warnings.append(f"Invalid positions blocked from physical rendering: {', '.join(row['event_id'] for row in invalid_positions)}")
    if unsafe_rendered:
        errors.append(f"Unsafe render gate failure: {', '.join(row['event_id'] for row in unsafe_rendered)}")
    if side_result["straight_segments_used"]:
        warnings.append("Side-view still used straight segments.")
    projected_count = sum(1 for row in resolved if row["projection_status"] == "projected")
    if not top_result["video_generated"]:
        errors.append("Top-view replay was not generated.")
    if not side_result["video_generated"]:
        errors.append("Side-view replay was not generated.")
    if errors:
        verdict = "blocked"
    elif len(physical_anchors) < 6 or (len(suspicious_positions) + len(invalid_positions) + len(unresolved_trust)) >= len(timeline) / 2:
        verdict = "needs_better_ball_position_resolution"
    elif side_result["straight_segments_used"]:
        verdict = "needs_side_view_curve_review"
    elif unresolved or suspicious_positions or invalid_positions:
        verdict = "ready_with_warnings"
    else:
        verdict = "ready_for_review"
    replay_trustworthy = verdict == "ready_for_review" and len(valid_positions) == len(timeline) and not unsafe_rendered
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stage": "manual_full_rally_replay",
        "manual_annotation_source": str(annotation_path),
        "manual_events_count": len(timeline),
        "hits_count": len(hits),
        "bounces_count": len(bounces),
        "shot_types_found": sorted({row["shot_type"] for row in hits if row["shot_type"]}),
        "positions_resolved_count": sum(1 for row in resolved if row["event_position_status"] == "resolved"),
        "positions_unresolved_count": sum(1 for row in resolved if row["event_position_status"] == "unresolved"),
        "sequence_valid_positions_count": len(valid_positions),
        "suspicious_positions_count": len(suspicious_positions),
        "invalid_positions_count": len(invalid_positions),
        "unresolved_positions_count": len(unresolved_trust),
        "physical_anchors_rendered_count": len(physical_anchors),
        "annotations_rendered_count": len(annotations),
        "replay_trustworthy": replay_trustworthy,
        "replay_trust_reason": "All physical anchors passed tennis-sequence validation." if replay_trustworthy else "One or more resolved local detections failed tennis-sequence validation and were blocked from physical rendering.",
        "projected_positions_count": projected_count,
        "unresolved_event_list": unresolved,
        "top_view_generated": bool(top_result["video_generated"]),
        "side_view_generated": bool(side_result["video_generated"]),
        "curved_side_view_enabled": True,
        "straight_side_view_segments_used": side_result["straight_segments_used"],
        "curve_segments_count": side_result["curve_segments"],
        "net_clearance_adjustments_count": side_result["net_clearance_adjustments"],
        "shot_types_preserved": bool({row["shot_type"] for row in hits if row["shot_type"]}),
        "warnings": warnings,
        "errors": errors,
        "final_verdict": verdict,
        "recommended_next_step": "Improve ball position resolution before trusting full-rally spatial replay." if not replay_trustworthy else "Review manual full-rally top-view and curved side-view replay outputs.",
        "output_folder": str(output_dir),
        "output_paths": {
            "resolved_manual_events_csv": str(output_dir / "resolved_manual_events.csv"),
            "full_rally_event_timeline_csv": str(output_dir / "full_rally_event_timeline.csv"),
            "sequence_validation_audit_csv": str(output_dir / "sequence_validation_audit.csv"),
            "replay_schema_json": str(output_dir / "replay_schema.json"),
            "top_view_replay": top_result["video_path"],
            "side_view_replay": side_result["video_path"],
            "side_view_curve_segments_csv": str(output_dir / "side_view_curve_segments.csv"),
            "report_json": str(REPORT_DIR / "manual_full_rally_replay_report.json"),
            "report_md": str(REPORT_DIR / "manual_full_rally_replay_report.md"),
        },
        "source_video": annotation.get("source_video") or annotation.get("source_video_path"),
    }


def report_markdown(report: dict[str, Any]) -> str:
    shot_types = "\n".join(f"  - {item}" for item in report["shot_types_found"]) or "  None"
    unresolved = "\n".join(f"  - {item}" for item in report["unresolved_event_list"]) or "  None"
    warnings = "\n".join(f"  - {item}" for item in report["warnings"]) or "  None"
    errors = "\n".join(f"  - {item}" for item in report["errors"]) or "  None"
    outputs = "\n".join(f"  - {value}" for value in report["output_paths"].values())
    return f"""# Manual Full-Rally Replay Report

VERDICT
  Final verdict: {report["final_verdict"]}
  Source video: {report["source_video"]}
  Manual annotation: {report["manual_annotation_source"]}

SUMMARY
  Manual events: {report["manual_events_count"]}
  Hits: {report["hits_count"]}
  Bounces: {report["bounces_count"]}
  Positions resolved: {report["positions_resolved_count"]}
  Positions unresolved: {report["positions_unresolved_count"]}
  Projected positions: {report["projected_positions_count"]}
  Sequence-valid positions: {report["sequence_valid_positions_count"]}
  Suspicious positions: {report["suspicious_positions_count"]}
  Invalid positions: {report["invalid_positions_count"]}
  Physical anchors rendered: {report["physical_anchors_rendered_count"]}
  Annotation events rendered: {report["annotations_rendered_count"]}
  Replay trustworthy: {report["replay_trustworthy"]}
  Trust reason: {report["replay_trust_reason"]}

SHOT TYPES
{shot_types}

REPLAY OUTPUTS
  Top-view generated: {report["top_view_generated"]}
  Side-view generated: {report["side_view_generated"]}
  Curved side-view enabled: {report["curved_side_view_enabled"]}
  Straight side-view segments used: {report["straight_side_view_segments_used"]}
  Curve segments: {report["curve_segments_count"]}
  Net clearance adjustments: {report["net_clearance_adjustments_count"]}

UNRESOLVED EVENTS
{unresolved}

WARNINGS
{warnings}

ERRORS
{errors}

LIMITATIONS
  Product Owner provides event timing and shot type only.
  The system resolves ball positions automatically near those event times.
  Unresolved events are not rendered as known physical court points.
  Side-view curves are synthetic visual approximations, not measured 3D physics.
  Future line calling requires contact localization and uncertainty.

OUTPUTS
{outputs}
"""


def write_docs(report: dict[str, Any]) -> None:
    LAB_NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    LAB_NOTEBOOK_PATH.write_text(report_markdown(report), encoding="utf-8")
    technical = PROJECT_ROOT / "docs" / "technical" / "manual_full_rally_replay.md"
    technical.write_text(
        """# Manual Full-Rally Replay

PURPOSE
  Uses the Product Owner's full-rally timing annotation as temporal ground
  truth, then resolves ball positions automatically from local video/candidate
  data and renders top-view and curved side-view replays.

IMPORTANT DATA CONTRACT
  The Product Owner labels when events happen.
  The system resolves where the ball is.
  The renderer shows only resolved physical positions as physical events.

SIDE-VIEW MODEL
  Side-view trajectories are synthetic Bezier curves influenced by shot_type.
  They are visual approximations, not measured 3D physics.

OUTPUTS
  outputs/replay/manual_full_rally/resolved_manual_events.csv
  outputs/replay/manual_full_rally/full_rally_event_timeline.csv
  outputs/replay/manual_full_rally/replay_schema.json
  outputs/replay/manual_full_rally/top_view_replay.mp4
  outputs/replay/manual_full_rally/side_view_replay.mp4
""",
        encoding="utf-8",
    )


def print_summary(report: dict[str, Any]) -> None:
    rows = [
        ("Verdict", report["final_verdict"]),
        ("Manual events", report["manual_events_count"]),
        ("Local detections", report["positions_resolved_count"]),
        ("Valid positions", report["sequence_valid_positions_count"]),
        ("Suspicious positions", report["suspicious_positions_count"]),
        ("Invalid positions", report["invalid_positions_count"]),
        ("Unresolved positions", report["unresolved_positions_count"]),
        ("Physical anchors rendered", report["physical_anchors_rendered_count"]),
        ("Annotation events", report["annotations_rendered_count"]),
        ("Replay trustworthy", report["replay_trustworthy"]),
        ("Top-view replay", report["top_view_generated"]),
        ("Side-view replay", report["side_view_generated"]),
        ("Recommended next step", report["recommended_next_step"]),
    ]
    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(title="Manual Full Rally Position Validation")
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")
        for field, value in rows:
            table.add_row(str(field), str(value))
        Console().print(table)
    except ImportError:
        print("Manual Full Rally Position Validation")
        for field, value in rows:
            print(f"{field}: {value}")


def to_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def main() -> int:
    args = parse_args()
    if not args.allow_failed_baseline:
        print(failed_baseline_block_message())
        return 2
    print_failed_baseline_warning()
    annotation_path = resolve(args.annotation)
    output_dir = resolve(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    annotation = load_manual_full_rally_annotation(annotation_path)
    video_path = PROJECT_ROOT / (annotation.get("source_video") or annotation.get("source_video_path"))
    resolved, resolution_summary = resolve_manual_event_positions(
        annotation_path=annotation_path,
        project_root=PROJECT_ROOT,
        video_path=video_path,
        stage3_report_path=PROJECT_ROOT / "outputs" / "reports" / "stage_3_court_calibration_probe_report.json",
        expanded_labels_path=PROJECT_ROOT / "outputs" / "timeline" / "stage_8_1_timeline_validation" / "expanded_ball_labels.csv",
        projected_labels_path=PROJECT_ROOT / "outputs" / "tactical" / "stage_9_1_projection_coverage" / "projected_expanded_labels.csv",
        search_padding=args.event_position_search_padding,
        fallback_tolerance=args.fallback_tolerance,
        resize_width=args.resize_width,
    )
    resolved = validate_manual_event_sequence(resolved)
    write_resolved_manual_events(output_dir / "resolved_manual_events.csv", resolved)
    write_json(output_dir / "resolved_manual_events.json", resolved)
    write_sequence_validation_audit(output_dir / "sequence_validation_audit.csv", resolved)
    timeline = build_full_rally_event_timeline(resolved)
    timeline_fields = [
        "event_id",
        "sequence_index",
        "event_type",
        "validated_event_type",
        "shot_type",
        "frame_index",
        "start_frame",
        "end_frame",
        "image_x",
        "image_y",
        "projected_x",
        "projected_y",
        "court_zone",
        "depth",
        "lateral_lane",
        "position_status",
        "position_trust",
        "position_validation_status",
        "sequence_validation_reason",
        "confidence",
        "render_role",
        "should_render_as_physical_event",
        "should_render_as_annotation",
        "notes",
    ]
    write_csv(output_dir / "full_rally_event_timeline.csv", timeline, timeline_fields)
    write_json(output_dir / "full_rally_event_timeline.json", timeline)
    schema = build_replay_schema(annotation, timeline, resolution_summary)
    write_json(output_dir / "replay_schema.json", schema)
    (output_dir / "replay_schema_pretty.md").write_text(
        f"""# Manual Full-Rally Replay Schema

Source annotation:
  {annotation_path}

Manual events:
  {len(timeline)}

Physical anchors:
  {sum(1 for row in timeline if row["should_render_as_physical_event"] == "yes")}

Schema:
  {output_dir / "replay_schema.json"}

Safety rule:
  Only events with position_trust=valid render as physical replay anchors.
""",
        encoding="utf-8",
    )
    top_result = render_top_view(timeline, output_dir, args.fps)
    side_result = render_side_view(timeline, output_dir, args.fps)
    write_json(output_dir / "replay_manifest.json", {"generated_at": datetime.now(timezone.utc).isoformat(), "manual_annotation": str(annotation_path), "resolution_summary": resolution_summary, "top_view": top_result, "side_view": side_result})
    report = build_report(annotation_path=annotation_path, annotation=annotation, resolved=resolved, timeline=timeline, top_result=top_result, side_result=side_result, summary=resolution_summary, output_dir=output_dir)
    annotate_report_with_failed_baseline_warning(report)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(REPORT_DIR / "manual_full_rally_replay_report.json", report)
    (REPORT_DIR / "manual_full_rally_replay_report.md").write_text(report_markdown(report), encoding="utf-8")
    write_docs(report)
    print_summary(report)
    return 1 if report["final_verdict"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
