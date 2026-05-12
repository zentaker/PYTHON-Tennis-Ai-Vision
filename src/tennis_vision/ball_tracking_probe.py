"""Lightweight local ball candidate probe for Stage 4."""

from __future__ import annotations

import csv
import math
import time
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from tennis_vision.video_io import open_video


def resize_frame(frame: Any, resize_width: int | None) -> tuple[Any, float]:
    """Resize a frame and return the scale from original to resized pixels."""
    if not resize_width or resize_width <= 0:
        return frame, 1.0
    height, width = frame.shape[:2]
    if width <= resize_width:
        return frame, 1.0
    scale = resize_width / width
    resized_height = max(1, int(height * scale))
    resized = cv2.resize(frame, (resize_width, resized_height), interpolation=cv2.INTER_AREA)
    return resized, scale


def detect_ball_candidates(frame: Any, frame_index: int) -> list[dict[str, Any]]:
    """Detect yellow/green ball-like blobs with simple OpenCV heuristics."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower = np.array([25, 35, 95], dtype=np.uint8)
    upper = np.array([90, 255, 255], dtype=np.uint8)
    mask = cv2.inRange(hsv, lower, upper)
    mask = cv2.medianBlur(mask, 5)
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates: list[dict[str, Any]] = []
    for contour in contours:
        area = float(cv2.contourArea(contour))
        if area < 6 or area > 900:
            continue
        perimeter = float(cv2.arcLength(contour, True))
        if perimeter <= 0:
            continue
        circularity = 4 * math.pi * area / (perimeter * perimeter)
        if circularity < 0.35:
            continue
        (x_value, y_value), radius = cv2.minEnclosingCircle(contour)
        if radius < 1.5 or radius > 22:
            continue

        x_int = int(round(x_value))
        y_int = int(round(y_value))
        if y_int < 0 or y_int >= hsv.shape[0] or x_int < 0 or x_int >= hsv.shape[1]:
            continue
        hue, saturation, value = hsv[y_int, x_int]
        color_score = min(1.0, float(saturation) / 255.0) * min(1.0, float(value) / 255.0)
        radius_score = 1.0 - min(abs(float(radius) - 5.0) / 18.0, 1.0)
        score = max(0.0, min(1.0, 0.55 * circularity + 0.30 * color_score + 0.15 * radius_score))

        candidates.append(
            {
                "frame_index": frame_index,
                "center_x": round(float(x_value), 2),
                "center_y": round(float(y_value), 2),
                "radius": round(float(radius), 2),
                "area": round(area, 2),
                "circularity": round(float(circularity), 4),
                "score": round(score, 4),
            }
        )

    candidates.sort(key=lambda item: item["score"], reverse=True)
    return candidates[:8]


def draw_candidates(frame: Any, candidates: list[dict[str, Any]], frame_index: int) -> Any:
    """Draw candidate circles and labels on a frame."""
    overlay = frame.copy()
    cv2.putText(
        overlay,
        f"frame {frame_index} | candidates: {len(candidates)}",
        (20, 42),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (0, 0, 0),
        4,
        cv2.LINE_AA,
    )
    cv2.putText(
        overlay,
        f"frame {frame_index} | candidates: {len(candidates)}",
        (20, 42),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    for index, candidate in enumerate(candidates, start=1):
        center = (int(round(candidate["center_x"])), int(round(candidate["center_y"])))
        radius = max(4, int(round(candidate["radius"])))
        cv2.circle(overlay, center, radius + 4, (0, 0, 0), 3)
        cv2.circle(overlay, center, radius + 4, (0, 255, 255), 2)
        cv2.circle(overlay, center, 2, (0, 0, 255), -1)
        cv2.putText(
            overlay,
            f"{index}:{candidate['score']:.2f}",
            (center[0] + 10, center[1] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 0, 0),
            3,
            cv2.LINE_AA,
        )
        cv2.putText(
            overlay,
            f"{index}:{candidate['score']:.2f}",
            (center[0] + 10, center[1] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 255, 255),
            1,
            cv2.LINE_AA,
        )
    return overlay


def write_candidates_csv(csv_path: Path, candidates: list[dict[str, Any]]) -> Path:
    """Write candidate positions to CSV."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "frame_index",
        "center_x",
        "center_y",
        "original_center_x",
        "original_center_y",
        "radius",
        "area",
        "circularity",
        "score",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for candidate in candidates:
            writer.writerow({field: candidate.get(field, "") for field in fields})
    return csv_path


def save_trajectory_preview(
    *,
    base_frame: Any | None,
    best_candidates_by_frame: list[dict[str, Any]],
    output_path: Path,
) -> str | None:
    """Save a rough trajectory preview using the best candidate per frame."""
    if base_frame is None or len(best_candidates_by_frame) < 2:
        return None
    preview = base_frame.copy()
    points: list[tuple[int, int]] = []
    for candidate in best_candidates_by_frame:
        point = (int(round(candidate["center_x"])), int(round(candidate["center_y"])))
        points.append(point)
        cv2.circle(preview, point, 7, (0, 0, 255), -1)
    for start, end in zip(points, points[1:]):
        cv2.line(preview, start, end, (0, 255, 255), 2)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if cv2.imwrite(str(output_path), preview):
        return str(output_path)
    return None


def run_yolo_reference(
    *,
    sampled_frames: list[tuple[int, Any]],
    output_folder: Path,
    confidence: float,
    max_yolo_frames: int = 5,
) -> dict[str, Any]:
    """Run an optional tiny YOLO reference pass on sampled frames."""
    started = time.perf_counter()
    result: dict[str, Any] = {
        "enabled": True,
        "frames_processed": 0,
        "sports_ball_like_detections": 0,
        "detection_counts_by_class": {},
        "runtime_seconds": 0.0,
        "average_seconds_per_frame": None,
        "warnings": [],
        "errors": [],
    }
    try:
        from tennis_vision.yolo_cpu import load_yolo_model
    except Exception as exc:
        result["warnings"].append(f"YOLO utilities were unavailable: {exc}")
        result["runtime_seconds"] = round(time.perf_counter() - started, 3)
        return result

    model_status = load_yolo_model(None)
    if model_status.get("errors"):
        result["warnings"].extend(model_status["errors"])
    if model_status.get("warnings"):
        result["warnings"].extend(model_status["warnings"])
    model = model_status.get("model")
    if model is None:
        result["runtime_seconds"] = round(time.perf_counter() - started, 3)
        return result

    output_folder.mkdir(parents=True, exist_ok=True)
    inference_times: list[float] = []
    names = getattr(model, "names", {}) or {}
    try:
        for frame_index, frame in sampled_frames[:max_yolo_frames]:
            frame_started = time.perf_counter()
            predictions = model.predict(source=frame, conf=confidence, device="cpu", verbose=False)
            inference_times.append(time.perf_counter() - frame_started)
            result["frames_processed"] += 1
            if not predictions:
                continue
            prediction = predictions[0]
            boxes = getattr(prediction, "boxes", None)
            classes = getattr(boxes, "cls", None) if boxes is not None else None
            if classes is None:
                continue
            class_values = classes.detach().cpu().tolist() if hasattr(classes, "detach") else list(classes)
            for class_id in class_values:
                class_name = names.get(int(class_id), str(int(class_id)))
                result["detection_counts_by_class"][class_name] = result["detection_counts_by_class"].get(class_name, 0) + 1
                if "ball" in class_name.lower() or class_name.lower() in {"sports ball", "tennis ball"}:
                    result["sports_ball_like_detections"] += 1
            annotated = prediction.plot()
            cv2.imwrite(str(output_folder / f"yolo_reference_{frame_index:06d}.jpg"), annotated)
    except Exception as exc:
        result["warnings"].append(f"YOLO reference pass failed: {exc}")

    total_runtime = time.perf_counter() - started
    result["runtime_seconds"] = round(total_runtime, 3)
    if inference_times:
        result["average_seconds_per_frame"] = round(sum(inference_times) / len(inference_times), 3)
    return result


def run_ball_tracking_probe(
    *,
    video_path: Path,
    output_folder: Path,
    max_frames: int = 20,
    interval: int = 15,
    resize_width: int = 1280,
    use_yolo: bool = False,
    confidence: float = 0.25,
) -> dict[str, Any]:
    """Run a limited local ball candidate probe."""
    started = time.perf_counter()
    errors: list[str] = []
    warnings: list[str] = []
    all_candidates: list[dict[str, Any]] = []
    candidate_count_by_frame: dict[str, int] = {}
    sampled_frames: list[tuple[int, Any]] = []
    best_candidates: list[dict[str, Any]] = []
    overlay_folder = output_folder / "ball_candidates_overlay"
    csv_path = output_folder / "ball_candidates.csv"
    trajectory_path = output_folder / "trajectory_preview.jpg"

    if max_frames <= 0:
        errors.append("max_frames must be greater than zero.")
    if interval <= 0:
        errors.append("interval must be greater than zero.")
    if resize_width <= 0:
        warnings.append("resize_width must be positive; using original frame size.")
        resize_width = 0
    if errors:
        return _result(
            started=started,
            video_path=video_path,
            overlay_folder=overlay_folder,
            csv_path=csv_path,
            trajectory_path=None,
            frames_processed=0,
            all_candidates=[],
            candidate_count_by_frame={},
            warnings=warnings,
            errors=errors,
            yolo_result={"enabled": use_yolo},
        )

    capture, open_error = open_video(video_path)
    if open_error:
        errors.append(open_error)
        return _result(
            started=started,
            video_path=video_path,
            overlay_folder=overlay_folder,
            csv_path=csv_path,
            trajectory_path=None,
            frames_processed=0,
            all_candidates=[],
            candidate_count_by_frame={},
            warnings=warnings,
            errors=errors,
            yolo_result={"enabled": use_yolo},
        )

    output_folder.mkdir(parents=True, exist_ok=True)
    overlay_folder.mkdir(parents=True, exist_ok=True)
    for old_file in overlay_folder.glob("*.jpg"):
        old_file.unlink()

    frames_read = 0
    frames_processed = 0
    first_overlay_frame = None
    try:
        while frames_processed < max_frames:
            ok, frame = capture.read()
            if not ok:
                break
            frame_index = frames_read
            frames_read += 1
            if frame_index != 0 and frame_index % interval != 0:
                continue

            resized, scale = resize_frame(frame, resize_width)
            frame_candidates = detect_ball_candidates(resized, frame_index)
            for candidate in frame_candidates:
                candidate["original_center_x"] = round(candidate["center_x"] / scale, 2) if scale else candidate["center_x"]
                candidate["original_center_y"] = round(candidate["center_y"] / scale, 2) if scale else candidate["center_y"]
            all_candidates.extend(frame_candidates)
            candidate_count_by_frame[str(frame_index)] = len(frame_candidates)

            overlay = draw_candidates(resized, frame_candidates, frame_index)
            if first_overlay_frame is None:
                first_overlay_frame = overlay.copy()
            if frame_candidates:
                best_candidates.append(frame_candidates[0])
            overlay_path = overlay_folder / f"ball_candidates_frame_{frame_index:06d}.jpg"
            if not cv2.imwrite(str(overlay_path), overlay):
                errors.append(f"OpenCV failed to save overlay frame: {overlay_path}")
            sampled_frames.append((frame_index, resized))
            frames_processed += 1
    except Exception as exc:
        errors.append(f"Ball candidate probe failed: {exc}")
    finally:
        capture.release()

    if frames_processed == 0 and not errors:
        warnings.append("No frames were processed. Try a smaller interval or check the video length.")
    if not all_candidates and frames_processed > 0:
        warnings.append("No ball candidates were detected by the simple color/blob heuristic.")

    write_candidates_csv(csv_path, all_candidates)
    trajectory_preview = save_trajectory_preview(
        base_frame=first_overlay_frame,
        best_candidates_by_frame=best_candidates,
        output_path=trajectory_path,
    )
    if all_candidates and trajectory_preview is None:
        warnings.append("Trajectory preview was not created because candidates did not span enough frames.")

    yolo_result: dict[str, Any] = {"enabled": False}
    if use_yolo:
        yolo_result = run_yolo_reference(
            sampled_frames=sampled_frames,
            output_folder=output_folder / "yolo_reference",
            confidence=confidence,
        )
        warnings.extend(yolo_result.get("warnings", []))
        errors.extend(yolo_result.get("errors", []))

    return _result(
        started=started,
        video_path=video_path,
        overlay_folder=overlay_folder,
        csv_path=csv_path,
        trajectory_path=Path(trajectory_preview) if trajectory_preview else None,
        frames_processed=frames_processed,
        all_candidates=all_candidates,
        candidate_count_by_frame=candidate_count_by_frame,
        warnings=warnings,
        errors=errors,
        yolo_result=yolo_result,
    )


def _result(
    *,
    started: float,
    video_path: Path,
    overlay_folder: Path,
    csv_path: Path,
    trajectory_path: Path | None,
    frames_processed: int,
    all_candidates: list[dict[str, Any]],
    candidate_count_by_frame: dict[str, int],
    warnings: list[str],
    errors: list[str],
    yolo_result: dict[str, Any],
) -> dict[str, Any]:
    candidate_count = len(all_candidates)
    frames_with_candidates = sum(1 for count in candidate_count_by_frame.values() if count > 0)
    average = round(candidate_count / frames_processed, 3) if frames_processed else 0.0
    return {
        "video_path": str(video_path),
        "frames_processed": frames_processed,
        "candidate_count": candidate_count,
        "candidate_count_by_frame": candidate_count_by_frame,
        "frames_with_candidates": frames_with_candidates,
        "average_candidates_per_frame": average,
        "candidates": all_candidates,
        "csv_path": str(csv_path),
        "overlay_folder": str(overlay_folder),
        "trajectory_preview_path": str(trajectory_path) if trajectory_path else None,
        "total_runtime_seconds": round(time.perf_counter() - started, 3),
        "yolo_reference": yolo_result,
        "warnings": warnings,
        "errors": errors,
    }
