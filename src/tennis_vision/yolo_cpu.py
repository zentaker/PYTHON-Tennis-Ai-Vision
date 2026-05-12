"""CPU-only YOLO baseline helpers."""

from __future__ import annotations

import statistics
import time
from pathlib import Path
from typing import Any

from tennis_vision.video_io import open_video


DEFAULT_MODEL_CANDIDATES = ("yolo11n.pt", "yolov8n.pt")


def load_yolo_model(model_name: str | None = None) -> dict[str, Any]:
    """Load a small YOLO model with fallback from yolo11n to yolov8n."""
    result: dict[str, Any] = {
        "model": None,
        "model_name": model_name or DEFAULT_MODEL_CANDIDATES[0],
        "attempted_models": [],
        "ultralytics_missing": False,
        "model_download_failed": False,
        "model_load_failed": False,
        "errors": [],
        "warnings": [],
    }

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        result["ultralytics_missing"] = True
        result["model_load_failed"] = True
        result["errors"].append(f"ultralytics import failed: {exc}")
        return result

    candidates = (model_name,) if model_name else DEFAULT_MODEL_CANDIDATES
    for candidate in candidates:
        if not candidate:
            continue
        result["attempted_models"].append(candidate)
        try:
            model = YOLO(candidate)
            result["model"] = model
            result["model_name"] = candidate
            return result
        except Exception as exc:
            message = f"Failed to load YOLO model {candidate}: {exc}"
            result["warnings" if not model_name else "errors"].append(message)

    result["model_load_failed"] = True
    result["model_download_failed"] = True
    if not result["errors"]:
        result["errors"].append("No YOLO model could be loaded from the attempted model list.")
    return result


def resize_frame(frame: Any, resize_width: int | None) -> Any:
    """Resize a frame to the requested width while preserving aspect ratio."""
    if not resize_width or resize_width <= 0:
        return frame

    import cv2

    height, width = frame.shape[:2]
    if width <= resize_width:
        return frame
    ratio = resize_width / width
    new_height = max(1, int(height * ratio))
    return cv2.resize(frame, (resize_width, new_height), interpolation=cv2.INTER_AREA)


def _collect_detections(result: Any, names: dict[int, str]) -> tuple[dict[str, int], list[float]]:
    counts: dict[str, int] = {}
    confidences: list[float] = []
    boxes = getattr(result, "boxes", None)
    if boxes is None:
        return counts, confidences

    classes = getattr(boxes, "cls", None)
    confs = getattr(boxes, "conf", None)
    if classes is None:
        return counts, confidences

    class_values = classes.detach().cpu().tolist() if hasattr(classes, "detach") else list(classes)
    conf_values = confs.detach().cpu().tolist() if confs is not None and hasattr(confs, "detach") else []

    for index, class_id in enumerate(class_values):
        class_index = int(class_id)
        class_name = names.get(class_index, str(class_index))
        counts[class_name] = counts.get(class_name, 0) + 1
        if index < len(conf_values):
            confidences.append(float(conf_values[index]))

    return counts, confidences


def run_yolo_cpu_baseline(
    *,
    video_path: Path,
    output_folder: Path,
    model_name: str | None = None,
    max_frames: int = 10,
    interval: int = 60,
    resize_width: int = 1280,
    confidence: float = 0.25,
) -> dict[str, Any]:
    """Run a limited CPU-only YOLO baseline on sampled video frames."""
    started = time.perf_counter()
    errors: list[str] = []
    warnings: list[str] = []
    saved_files: list[str] = []
    inference_times: list[float] = []
    detection_counts: dict[str, int] = {}
    confidences: list[float] = []

    if max_frames <= 0:
        errors.append("max_frames must be greater than zero.")
    if interval <= 0:
        errors.append("interval must be greater than zero.")
    if confidence < 0 or confidence > 1:
        errors.append("confidence must be between 0 and 1.")
    if errors:
        return _result(
            started=started,
            model_name=model_name,
            output_folder=output_folder,
            frames_processed=0,
            annotated_frames_saved=0,
            saved_files=saved_files,
            detection_counts=detection_counts,
            confidences=confidences,
            inference_times=inference_times,
            errors=errors,
            warnings=warnings,
            model_status={},
        )

    model_status = load_yolo_model(model_name)
    errors.extend(model_status["errors"])
    warnings.extend(model_status["warnings"])
    model = model_status["model"]
    if model is None:
        return _result(
            started=started,
            model_name=model_status.get("model_name", model_name),
            output_folder=output_folder,
            frames_processed=0,
            annotated_frames_saved=0,
            saved_files=saved_files,
            detection_counts=detection_counts,
            confidences=confidences,
            inference_times=inference_times,
            errors=errors,
            warnings=warnings,
            model_status=model_status,
        )

    capture, open_error = open_video(video_path)
    if open_error:
        errors.append(open_error)
        return _result(
            started=started,
            model_name=model_status["model_name"],
            output_folder=output_folder,
            frames_processed=0,
            annotated_frames_saved=0,
            saved_files=saved_files,
            detection_counts=detection_counts,
            confidences=confidences,
            inference_times=inference_times,
            errors=errors,
            warnings=warnings,
            model_status=model_status,
        )

    try:
        import cv2

        output_folder.mkdir(parents=True, exist_ok=True)
        total_frames_read = 0
        frames_processed = 0
        names = getattr(model, "names", {}) or {}

        while frames_processed < max_frames:
            ok, frame = capture.read()
            if not ok:
                break
            total_frames_read += 1
            if total_frames_read != 1 and total_frames_read % interval != 0:
                continue

            resized = resize_frame(frame, resize_width)
            inference_started = time.perf_counter()
            predictions = model.predict(
                source=resized,
                conf=confidence,
                device="cpu",
                verbose=False,
            )
            inference_times.append(time.perf_counter() - inference_started)
            if not predictions:
                warnings.append(f"No prediction object returned for frame {total_frames_read}.")
                continue

            prediction = predictions[0]
            frame_counts, frame_confidences = _collect_detections(prediction, names)
            for class_name, count in frame_counts.items():
                detection_counts[class_name] = detection_counts.get(class_name, 0) + count
            confidences.extend(frame_confidences)

            annotated = prediction.plot()
            frame_path = output_folder / f"yolo_frame_{total_frames_read:06d}.jpg"
            if cv2.imwrite(str(frame_path), annotated):
                saved_files.append(str(frame_path))
            else:
                errors.append(f"OpenCV failed to save {frame_path.name}.")
            frames_processed += 1
    except Exception as exc:
        errors.append(f"YOLO CPU inference failed: {exc}")
    finally:
        capture.release()

    if not inference_times:
        warnings.append("No frames were processed by YOLO.")
    if not detection_counts and inference_times:
        warnings.append("YOLO ran, but no objects were detected in the sampled frames.")

    return _result(
        started=started,
        model_name=model_status["model_name"],
        output_folder=output_folder,
        frames_processed=len(inference_times),
        annotated_frames_saved=len(saved_files),
        saved_files=saved_files,
        detection_counts=detection_counts,
        confidences=confidences,
        inference_times=inference_times,
        errors=errors,
        warnings=warnings,
        model_status=model_status,
    )


def _result(
    *,
    started: float,
    model_name: str | None,
    output_folder: Path,
    frames_processed: int,
    annotated_frames_saved: int,
    saved_files: list[str],
    detection_counts: dict[str, int],
    confidences: list[float],
    inference_times: list[float],
    errors: list[str],
    warnings: list[str],
    model_status: dict[str, Any],
) -> dict[str, Any]:
    confidence_stats = {
        "count": len(confidences),
        "min": round(min(confidences), 4) if confidences else None,
        "max": round(max(confidences), 4) if confidences else None,
        "mean": round(statistics.mean(confidences), 4) if confidences else None,
    }
    total_runtime = time.perf_counter() - started
    return {
        "model_name": model_name,
        "device": "cpu",
        "frames_processed": frames_processed,
        "annotated_frames_saved": annotated_frames_saved,
        "annotated_files": saved_files,
        "output_folder": str(output_folder),
        "total_runtime_seconds": round(total_runtime, 3),
        "average_inference_time_seconds": round(statistics.mean(inference_times), 3)
        if inference_times
        else None,
        "detection_counts_by_class": dict(sorted(detection_counts.items())),
        "confidence_stats": confidence_stats,
        "model_status": {
            key: value
            for key, value in model_status.items()
            if key != "model"
        },
        "errors": errors,
        "warnings": warnings,
    }
