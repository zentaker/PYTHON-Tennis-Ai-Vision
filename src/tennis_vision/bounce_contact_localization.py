"""Precise bounce contact localization helpers for Stage 8.5."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any

import cv2
import numpy as np

from tennis_vision.ball_labeling import load_frame_at_index
from tennis_vision.ball_tracking_probe import resize_frame


CONTACT_POINT_FIELDS = [
    "bounce_id",
    "source_window_id",
    "window_start_frame",
    "window_end_frame",
    "window_center_frame",
    "contact_frame",
    "contact_x",
    "contact_y",
    "contact_projected_x",
    "contact_projected_y",
    "contact_status",
    "confidence_level",
    "uncertainty_frames",
    "uncertainty_px",
    "uncertainty_projected",
    "line_call_ready",
    "line_call_readiness_reason",
    "method",
    "notes",
]

CANDIDATE_FIELDS = [
    "bounce_id",
    "frame_index",
    "x",
    "y",
    "projected_x",
    "projected_y",
    "score",
    "score_reason",
    "selected_contact",
]


def int_or_none(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def float_or_none(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def normalize_window_label(value: Any) -> str:
    label = str(value or "").strip().lower()
    return label[:-7] if label.endswith("_window") else label


def read_bounce_windows(primary_path: Path, fallback_path: Path) -> tuple[list[dict[str, Any]], str, list[str]]:
    """Read manually supported bounce windows, preferring Stage 8.2 windows."""
    warnings: list[str] = []
    primary_rows = read_csv_rows(primary_path)
    fallback_rows = read_csv_rows(fallback_path)
    rows = primary_rows if primary_rows else fallback_rows
    source = str(primary_path if primary_rows else fallback_path)
    if not primary_rows and fallback_rows:
        warnings.append("Stage 8.2 manual_event_windows.csv had no bounce windows; Stage 8.5 used Stage 8.3 manual_event_windows.csv as fallback.")
    windows: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        label = normalize_window_label(row.get("event_label"))
        manual_support = bool(row.get("window_id") or row.get("source_frames") or row.get("frame_indices"))
        if label not in {"bounce", "validated_bounce", "possible_bounce"}:
            continue
        if label == "possible_bounce" and not manual_support:
            continue
        start = int_or_none(row.get("start_frame"))
        end = int_or_none(row.get("end_frame"))
        if start is None or end is None:
            continue
        start, end = min(start, end), max(start, end)
        windows.append(
            {
                "bounce_id": f"bounce_contact_{len(windows) + 1:03d}",
                "source_window_id": row.get("window_id") or f"source_window_{index:03d}",
                "start_frame": start,
                "end_frame": end,
                "center_frame": int_or_none(row.get("center_frame")) or int(round((start + end) / 2)),
                "event_label": label,
                "confidence": row.get("confidence") or "medium",
                "source": source,
                "notes": row.get("notes") or "",
            }
        )
    return windows, source, warnings


def read_ball_positions(label_path: Path, projected_path: Path) -> tuple[dict[int, dict[str, Any]], list[str]]:
    """Load image-space and projected ball positions keyed by frame."""
    warnings: list[str] = []
    positions: dict[int, dict[str, Any]] = {}
    label_rows = read_csv_rows(label_path)
    if not label_rows:
        warnings.append(f"No expanded ball label rows found: {label_path}")
    for row in label_rows:
        frame = int_or_none(row.get("frame_index"))
        if frame is None:
            continue
        visible = str(row.get("visible", "true")).lower() in {"true", "1", "yes", ""}
        if not visible:
            continue
        positions.setdefault(frame, {"frame_index": frame})
        positions[frame].update(
            {
                "x": float_or_none(row.get("x")),
                "y": float_or_none(row.get("y")),
                "image_source": row.get("source") or "expanded_ball_labels",
                "image_available": float_or_none(row.get("x")) is not None and float_or_none(row.get("y")) is not None,
            }
        )
    projected_rows = read_csv_rows(projected_path)
    if not projected_rows:
        warnings.append(f"No projected ball label rows found: {projected_path}")
    for row in projected_rows:
        frame = int_or_none(row.get("frame_index"))
        if frame is None:
            continue
        positions.setdefault(frame, {"frame_index": frame})
        positions[frame].update(
            {
                "projected_x": float_or_none(row.get("projected_x")),
                "projected_y": float_or_none(row.get("projected_y")),
                "projection_status": row.get("projection_status") or "",
                "projection_available": float_or_none(row.get("projected_x")) is not None and float_or_none(row.get("projected_y")) is not None,
                "projection_source": row.get("source") or "projected_expanded_labels",
            }
        )
        if "x" not in positions[frame]:
            positions[frame]["x"] = float_or_none(row.get("x"))
            positions[frame]["y"] = float_or_none(row.get("y"))
            positions[frame]["image_available"] = positions[frame]["x"] is not None and positions[frame]["y"] is not None
    return positions, warnings


def interpolate_value(frame: int, positions: dict[int, dict[str, Any]], key: str) -> tuple[float | None, bool]:
    if frame in positions and positions[frame].get(key) is not None:
        return float(positions[frame][key]), False
    before = [idx for idx, row in positions.items() if idx < frame and row.get(key) is not None]
    after = [idx for idx, row in positions.items() if idx > frame and row.get(key) is not None]
    if not before or not after:
        return None, False
    lo, hi = max(before), min(after)
    if hi == lo:
        return float(positions[lo][key]), True
    ratio = (frame - lo) / (hi - lo)
    value = float(positions[lo][key]) + (float(positions[hi][key]) - float(positions[lo][key])) * ratio
    return value, True


def build_contact_candidates(window: dict[str, Any], positions: dict[int, dict[str, Any]], *, padding: int) -> list[dict[str, Any]]:
    """Build candidate frames around a bounce window with tentative interpolation."""
    start = int(window["start_frame"]) - padding
    end = int(window["end_frame"]) + padding
    rows: list[dict[str, Any]] = []
    for frame in range(start, end + 1):
        x, interp_x = interpolate_value(frame, positions, "x")
        y, interp_y = interpolate_value(frame, positions, "y")
        px, interp_px = interpolate_value(frame, positions, "projected_x")
        py, interp_py = interpolate_value(frame, positions, "projected_y")
        exact = positions.get(frame, {})
        rows.append(
            {
                "frame_index": frame,
                "x": x,
                "y": y,
                "projected_x": px,
                "projected_y": py,
                "image_available": bool(exact.get("image_available")),
                "projection_available": bool(exact.get("projection_available")),
                "interpolated": bool(interp_x or interp_y or interp_px or interp_py),
                "inside_window": int(window["start_frame"]) <= frame <= int(window["end_frame"]),
            }
        )
    return rows


def local_motion_change(candidates: list[dict[str, Any]], index: int) -> float:
    if index <= 0 or index >= len(candidates) - 1:
        return 0.0
    prev_row, row, next_row = candidates[index - 1], candidates[index], candidates[index + 1]
    if None in (prev_row.get("x"), prev_row.get("y"), row.get("x"), row.get("y"), next_row.get("x"), next_row.get("y")):
        return 0.0
    v1 = np.array([float(row["x"]) - float(prev_row["x"]), float(row["y"]) - float(prev_row["y"])])
    v2 = np.array([float(next_row["x"]) - float(row["x"]), float(next_row["y"]) - float(row["y"])])
    denom = max(float(np.linalg.norm(v1) * np.linalg.norm(v2)), 1e-6)
    cosine = float(np.dot(v1, v2) / denom)
    return max(0.0, min(1.0, (1.0 - cosine) / 2.0))


def projected_turn_score(candidates: list[dict[str, Any]], index: int) -> float:
    if index <= 0 or index >= len(candidates) - 1:
        return 0.0
    prev_row, row, next_row = candidates[index - 1], candidates[index], candidates[index + 1]
    values = [prev_row.get("projected_y"), row.get("projected_y"), next_row.get("projected_y")]
    if any(value is None for value in values):
        return 0.0
    before = float(row["projected_y"]) - float(prev_row["projected_y"])
    after = float(next_row["projected_y"]) - float(row["projected_y"])
    if before == 0 or after == 0:
        return 0.2
    return 1.0 if before * after < 0 else min(0.4, abs(after - before) / 100.0)


def score_contact_candidates(window: dict[str, Any], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Score candidate contact frames using deterministic evidence."""
    center = int(window["center_frame"])
    span = max(int(window["end_frame"]) - int(window["start_frame"]) + 1, 1)
    max_y = max((float(row["y"]) for row in candidates if row.get("y") is not None), default=None)
    for index, row in enumerate(candidates):
        center_score = max(0.0, 1.0 - abs(int(row["frame_index"]) - center) / max(span + 2, 1))
        y_score = 0.0
        if max_y is not None and row.get("y") is not None:
            y_score = max(0.0, 1.0 - abs(max_y - float(row["y"])) / 80.0)
        motion_score = local_motion_change(candidates, index)
        turn_score = projected_turn_score(candidates, index)
        image_score = 1.0 if row.get("image_available") else (0.35 if row.get("x") is not None and row.get("y") is not None else 0.0)
        projection_score = 1.0 if row.get("projection_available") else (0.35 if row.get("projected_x") is not None and row.get("projected_y") is not None else 0.0)
        inside_score = 0.35 if row.get("inside_window") else 0.0
        score = (
            center_score * 0.25
            + y_score * 0.18
            + motion_score * 0.18
            + turn_score * 0.14
            + image_score * 0.1
            + projection_score * 0.1
            + inside_score * 0.05
        )
        row["score"] = round(score, 4)
        row["score_reason"] = (
            f"center={center_score:.2f}; lowest_image_proxy={y_score:.2f}; "
            f"motion_change={motion_score:.2f}; projected_turn={turn_score:.2f}; "
            f"image_available={image_score:.2f}; projection_available={projection_score:.2f}"
        )
    return candidates


def estimate_uncertainty(window: dict[str, Any], candidates: list[dict[str, Any]], selected: dict[str, Any]) -> dict[str, Any]:
    frame_count = int(window["end_frame"]) - int(window["start_frame"]) + 1
    available = [row for row in candidates if row.get("image_available")]
    projection_available = bool(selected.get("projected_x") is not None and selected.get("projected_y") is not None)
    uncertainty_frames = max(1.0, frame_count / 2.0)
    if not selected.get("image_available"):
        uncertainty_frames += 1.0
    if len(available) <= 1:
        uncertainty_frames += 1.0
    distances: list[float] = []
    for left, right in zip(candidates, candidates[1:]):
        if None not in (left.get("x"), left.get("y"), right.get("x"), right.get("y")):
            distances.append(math.hypot(float(right["x"]) - float(left["x"]), float(right["y"]) - float(left["y"])))
    uncertainty_px = max(8.0, mean(distances) if distances else 50.0)
    if selected.get("interpolated"):
        uncertainty_px += 15.0
    if len(available) <= 1:
        uncertainty_px += 25.0
    projected_distances: list[float] = []
    for left, right in zip(candidates, candidates[1:]):
        if None not in (left.get("projected_x"), left.get("projected_y"), right.get("projected_x"), right.get("projected_y")):
            projected_distances.append(math.hypot(float(right["projected_x"]) - float(left["projected_x"]), float(right["projected_y"]) - float(left["projected_y"])))
    uncertainty_projected = max(2.0, mean(projected_distances) if projected_distances else 25.0)
    if not projection_available:
        uncertainty_projected += 50.0
    criteria_scores = [float(selected.get("score") or 0)]
    confidence_level = "high"
    if uncertainty_frames > 2.0 or uncertainty_px > 35 or not projection_available:
        confidence_level = "medium"
    if uncertainty_frames > 3.0 or uncertainty_px > 60 or not selected.get("image_available"):
        confidence_level = "low"
    if not selected.get("image_available") and not selected.get("projection_available"):
        contact_status = "insufficient_data"
    elif selected.get("image_available") and not selected.get("interpolated") and len(available) >= 2:
        contact_status = "localized"
    elif selected.get("x") is not None and selected.get("y") is not None:
        contact_status = "estimated"
    else:
        contact_status = "ambiguous"
    if len(available) <= 1:
        contact_status = "estimated" if contact_status == "localized" else contact_status
    return {
        "uncertainty_frames": round(uncertainty_frames, 2),
        "uncertainty_px": round(uncertainty_px, 2),
        "uncertainty_projected": round(uncertainty_projected, 2),
        "confidence_level": confidence_level,
        "contact_status": contact_status,
        "criteria_disagreement": round(1.0 - max(criteria_scores), 3),
    }


def line_call_readiness(
    contact_status: str,
    confidence: str,
    projected_available: bool,
    uncertainty_projected: float,
    uncertainty_frames: float,
    uncertainty_px: float,
) -> tuple[bool, str]:
    """Decide whether a localized contact is ready for future line-call logic."""
    if contact_status not in {"localized", "estimated"}:
        return False, f"contact status is {contact_status}"
    if confidence not in {"high", "medium"}:
        return False, "confidence is low"
    if not projected_available:
        return False, "projected court coordinates are missing"
    if uncertainty_frames > 2:
        return False, "bounce contact frame uncertainty too high"
    if uncertainty_px > 25:
        return False, "bounce contact image-space uncertainty too high"
    if uncertainty_projected > 18:
        return False, "bounce contact point uncertainty too high"
    return True, "contact point has projected coordinates and acceptable uncertainty"


def localize_bounce_contact(window: dict[str, Any], positions: dict[int, dict[str, Any]], *, padding: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    candidates = score_contact_candidates(window, build_contact_candidates(window, positions, padding=padding))
    valid_candidates = [row for row in candidates if row.get("x") is not None or row.get("projected_x") is not None]
    selected = max(valid_candidates or candidates, key=lambda row: (float(row.get("score") or 0), bool(row.get("inside_window"))))
    uncertainty = estimate_uncertainty(window, candidates, selected)
    projected_available = selected.get("projected_x") is not None and selected.get("projected_y") is not None
    ready, ready_reason = line_call_readiness(
        uncertainty["contact_status"],
        uncertainty["confidence_level"],
        projected_available,
        float(uncertainty["uncertainty_projected"]),
        float(uncertainty["uncertainty_frames"]),
        float(uncertainty["uncertainty_px"]),
    )
    contact = {
        "bounce_id": window["bounce_id"],
        "source_window_id": window["source_window_id"],
        "window_start_frame": window["start_frame"],
        "window_end_frame": window["end_frame"],
        "window_center_frame": window["center_frame"],
        "contact_frame": selected.get("frame_index"),
        "contact_x": round(float(selected["x"]), 3) if selected.get("x") is not None else None,
        "contact_y": round(float(selected["y"]), 3) if selected.get("y") is not None else None,
        "contact_projected_x": round(float(selected["projected_x"]), 3) if selected.get("projected_x") is not None else None,
        "contact_projected_y": round(float(selected["projected_y"]), 3) if selected.get("projected_y") is not None else None,
        "contact_status": uncertainty["contact_status"],
        "confidence_level": uncertainty["confidence_level"],
        "uncertainty_frames": uncertainty["uncertainty_frames"],
        "uncertainty_px": uncertainty["uncertainty_px"],
        "uncertainty_projected": uncertainty["uncertainty_projected"],
        "line_call_ready": "yes" if ready else "no",
        "line_call_readiness_reason": ready_reason,
        "method": "deterministic_window_scoring",
        "notes": f"contact estimate, not official line call; window_source={window.get('source')}; criteria_disagreement={uncertainty['criteria_disagreement']}",
    }
    candidate_rows = []
    for row in candidates:
        candidate_rows.append(
            {
                "bounce_id": window["bounce_id"],
                "frame_index": row.get("frame_index"),
                "x": round(float(row["x"]), 3) if row.get("x") is not None else None,
                "y": round(float(row["y"]), 3) if row.get("y") is not None else None,
                "projected_x": round(float(row["projected_x"]), 3) if row.get("projected_x") is not None else None,
                "projected_y": round(float(row["projected_y"]), 3) if row.get("projected_y") is not None else None,
                "score": row.get("score"),
                "score_reason": row.get("score_reason"),
                "selected_contact": "yes" if row.get("frame_index") == selected.get("frame_index") else "no",
            }
        )
    return contact, candidate_rows


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def save_contact_overlay(video_path: Path, contact: dict[str, Any], output_path: Path, *, resize_width: int = 1280) -> bool:
    frame_index = int(contact["contact_frame"])
    frame, error = load_frame_at_index(video_path, frame_index)
    if error or frame is None:
        return False
    display, scale = resize_frame(frame, resize_width)
    x, y = contact.get("contact_x"), contact.get("contact_y")
    if x is not None and y is not None:
        point = (int(round(float(x) * scale)), int(round(float(y) * scale)))
        cv2.circle(display, point, 18, (0, 220, 255), 2)
        cv2.drawMarker(display, point, (0, 80, 255), cv2.MARKER_CROSS, 28, 2)
    cv2.rectangle(display, (0, 0), (display.shape[1], 76), (0, 0, 0), -1)
    cv2.putText(display, f"{contact['bounce_id']} frame {frame_index} | {contact['contact_status']} | {contact['confidence_level']}", (18, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (255, 255, 255), 2)
    cv2.putText(display, "contact estimate, not official line call", (18, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 220, 255), 2)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return bool(cv2.imwrite(str(output_path), display))


def save_timeline_preview(contacts: list[dict[str, Any]], output_path: Path) -> bool:
    if not contacts:
        return False
    frames = [int(row["contact_frame"]) for row in contacts if row.get("contact_frame") is not None]
    if not frames:
        return False
    width, height = 1200, 360
    canvas = np.full((height, width, 3), 246, dtype=np.uint8)
    left, right, axis_y = 80, width - 80, 180
    min_frame, max_frame = min(frames), max(frames)
    span = max(max_frame - min_frame, 1)

    def x_for(frame: int) -> int:
        return left + int(round(((frame - min_frame) / span) * (right - left)))

    cv2.putText(canvas, "Stage 8.5 bounce contact localization", (35, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.82, (25, 25, 25), 2)
    cv2.putText(canvas, "gold=contact estimate  green=line-call-ready  gray=inconclusive", (35, 72), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (80, 80, 80), 1)
    cv2.line(canvas, (left, axis_y), (right, axis_y), (45, 45, 45), 2)
    for contact in contacts:
        frame = int(contact["contact_frame"])
        x = x_for(frame)
        color = (80, 190, 80) if contact.get("line_call_ready") == "yes" else ((40, 170, 245) if contact.get("contact_status") in {"localized", "estimated"} else (140, 140, 140))
        cv2.drawMarker(canvas, (x, axis_y), color, cv2.MARKER_TRIANGLE_UP, 24, 2)
        cv2.putText(canvas, f"{contact['bounce_id']} f{frame} {contact['confidence_level']}", (max(20, x - 70), axis_y + 44), cv2.FONT_HERSHEY_SIMPLEX, 0.42, color, 1)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return bool(cv2.imwrite(str(output_path), canvas))
