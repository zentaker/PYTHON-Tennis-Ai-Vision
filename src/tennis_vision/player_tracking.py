"""Local player detection and lightweight tracking helpers for Stage 7."""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any

import cv2

from tennis_vision.court_projection import project_image_points
from tennis_vision.video_io import open_video
from tennis_vision.yolo_cpu import load_yolo_model, resize_frame


def read_smoothed_trajectory(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Read Stage 6 smoothed ball trajectory rows."""
    if not path.exists():
        return [], [f"Smoothed trajectory CSV not found: {path}"]
    rows: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                rows.append(
                    {
                        "frame_index": int(float(row["frame_index"])),
                        "x": float(row["smooth_x"]),
                        "y": float(row["smooth_y"]),
                        "projected_x": _float_or_none(row.get("smooth_projected_x")),
                        "projected_y": _float_or_none(row.get("smooth_projected_y")),
                        "is_interpolated": str(row.get("is_interpolated", "")).lower() == "true",
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
    rows.sort(key=lambda item: item["frame_index"])
    return rows, []


def select_analysis_frames(trajectory_rows: list[dict[str, Any]], event_frames: list[int], max_frames: int) -> list[int]:
    """Select a small set of frames from trajectory and event hypotheses."""
    selected: list[int] = []
    anchors = [row["frame_index"] for row in trajectory_rows if not row.get("is_interpolated")]
    for frame_index in anchors + event_frames:
        if frame_index not in selected:
            selected.append(frame_index)
    if len(selected) < max_frames:
        for row in trajectory_rows:
            frame_index = row["frame_index"]
            if frame_index not in selected:
                selected.append(frame_index)
            if len(selected) >= max_frames:
                break
    return sorted(selected[:max_frames])


def detect_players(
    *,
    video_path: Path,
    frame_indices: list[int],
    model_name: str | None,
    resize_width: int,
    confidence: float,
    homography_matrix: list[list[float]] | None = None,
) -> dict[str, Any]:
    """Run YOLO person detection on selected frames using CPU."""
    result: dict[str, Any] = {
        "detections": [],
        "frames_analyzed": [],
        "model_name": model_name,
        "device": "cpu",
        "warnings": [],
        "errors": [],
        "model_status": {},
    }
    if not video_path.exists():
        result["errors"].append(f"Video file not found: {video_path}")
        return result
    model_status = load_yolo_model(model_name)
    result["model_status"] = {key: value for key, value in model_status.items() if key != "model"}
    result["warnings"].extend(model_status.get("warnings", []))
    result["errors"].extend(model_status.get("errors", []))
    model = model_status.get("model")
    result["model_name"] = model_status.get("model_name", model_name)
    if model is None:
        return result

    capture, open_error = open_video(video_path)
    if open_error:
        result["errors"].append(open_error)
        return result

    try:
        names = getattr(model, "names", {}) or {}
        for frame_index in frame_indices:
            capture.set(cv2.CAP_PROP_POS_FRAMES, int(frame_index))
            ok, frame = capture.read()
            if not ok:
                result["warnings"].append(f"Could not read frame {frame_index}.")
                continue
            original_height, original_width = frame.shape[:2]
            resized = resize_frame(frame, resize_width)
            resized_height, resized_width = resized.shape[:2]
            scale_x = original_width / resized_width
            scale_y = original_height / resized_height
            predictions = model.predict(source=resized, conf=confidence, device="cpu", verbose=False)
            result["frames_analyzed"].append(frame_index)
            if not predictions:
                continue
            boxes = getattr(predictions[0], "boxes", None)
            if boxes is None:
                continue
            xyxy = getattr(boxes, "xyxy", None)
            classes = getattr(boxes, "cls", None)
            confs = getattr(boxes, "conf", None)
            if xyxy is None or classes is None:
                continue
            box_values = xyxy.detach().cpu().tolist() if hasattr(xyxy, "detach") else list(xyxy)
            class_values = classes.detach().cpu().tolist() if hasattr(classes, "detach") else list(classes)
            conf_values = confs.detach().cpu().tolist() if confs is not None and hasattr(confs, "detach") else []
            for index, box in enumerate(box_values):
                class_id = int(class_values[index])
                class_name = names.get(class_id, str(class_id))
                if str(class_name).lower() != "person":
                    continue
                x1, y1, x2, y2 = [float(value) for value in box]
                detection = {
                    "frame_index": frame_index,
                    "bbox_x1": round(x1 * scale_x, 3),
                    "bbox_y1": round(y1 * scale_y, 3),
                    "bbox_x2": round(x2 * scale_x, 3),
                    "bbox_y2": round(y2 * scale_y, 3),
                    "bbox_center_x": round(((x1 + x2) / 2) * scale_x, 3),
                    "bbox_center_y": round(((y1 + y2) / 2) * scale_y, 3),
                    "confidence": round(float(conf_values[index]), 4) if index < len(conf_values) else None,
                    "class_name": str(class_name),
                    "player_side_guess": "near_player" if ((y1 + y2) / 2) * scale_y > original_height * 0.52 else "far_player",
                    "projected_x": None,
                    "projected_y": None,
                }
                if homography_matrix:
                    projected = project_image_points(
                        [{"frame_index": frame_index, "x": detection["bbox_center_x"], "y": detection["bbox_y2"]}],
                        homography_matrix,
                    )
                    if projected:
                        detection["projected_x"] = projected[0]["projected_x"]
                        detection["projected_y"] = projected[0]["projected_y"]
                result["detections"].append(detection)
    except Exception as exc:
        result["errors"].append(f"Player detection failed: {exc}")
    finally:
        capture.release()
    return result


def track_players(detections: list[dict[str, Any]], max_match_distance: float = 550.0) -> list[dict[str, Any]]:
    """Assign simple nearest-center track IDs across frames."""
    tracks: dict[str, dict[str, Any]] = {}
    next_id = 1
    tracked_rows: list[dict[str, Any]] = []
    for detection in sorted(detections, key=lambda item: (item["frame_index"], -(item.get("confidence") or 0))):
        best_track_id = None
        best_distance = None
        for track_id, last in tracks.items():
            if detection["frame_index"] <= last["frame_index"]:
                continue
            distance = math.dist((detection["bbox_center_x"], detection["bbox_center_y"]), (last["bbox_center_x"], last["bbox_center_y"]))
            if distance <= max_match_distance and (best_distance is None or distance < best_distance):
                best_track_id = track_id
                best_distance = distance
        if best_track_id is None:
            best_track_id = f"player_{next_id}" if next_id <= 2 else f"unknown_{next_id}"
            next_id += 1
        row = {**detection, "track_id": best_track_id}
        tracks[best_track_id] = row
        tracked_rows.append(row)
    return tracked_rows


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> Path:
    """Write rows to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    return path


def _float_or_none(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
