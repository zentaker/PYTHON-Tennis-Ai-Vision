"""Friction scoring for local experiment readiness."""

from __future__ import annotations

from typing import Any


def friction_band(score: int) -> str:
    """Return the friction band for a 0 to 100 score."""
    if score <= 20:
        return "low friction"
    if score <= 50:
        return "medium friction"
    if score <= 80:
        return "high friction"
    return "blocking friction"


def calculate_friction_score(
    *,
    missing_packages: list[str] | None = None,
    missing_folders: list[str] | None = None,
    ffmpeg_missing: bool = False,
    errors_count: int = 0,
    manual_action_required: bool = False,
) -> dict[str, Any]:
    """Calculate a basic Stage 0 friction score from 0 to 100."""
    missing_packages = missing_packages or []
    missing_folders = missing_folders or []

    score = 0
    score += min(len(missing_packages) * 15, 45)
    score += min(len(missing_folders) * 10, 40)
    score += 15 if ffmpeg_missing else 0
    score += min(errors_count * 10, 30)
    score += 20 if manual_action_required else 0
    score = max(0, min(score, 100))

    return {
        "score": score,
        "band": friction_band(score),
        "inputs": {
            "missing_packages": missing_packages,
            "missing_folders": missing_folders,
            "ffmpeg_missing": ffmpeg_missing,
            "errors_count": errors_count,
            "manual_action_required": manual_action_required,
        },
    }


def calculate_stage_1_friction_score(
    *,
    video_missing: bool = False,
    video_open_failed: bool = False,
    metadata_read_failed: bool = False,
    zero_frames_detected: bool = False,
    frames_not_saved: bool = False,
    errors_count: int = 0,
    warnings_count: int = 0,
    manual_action_required: bool = False,
) -> dict[str, Any]:
    """Calculate Stage 1 video loading and frame extraction friction."""
    score = 0
    score += 35 if video_missing else 0
    score += 35 if video_open_failed else 0
    score += 25 if metadata_read_failed else 0
    score += 20 if zero_frames_detected else 0
    score += 35 if frames_not_saved else 0
    score += min(errors_count * 10, 30)
    score += min(warnings_count * 3, 15)
    score += 20 if manual_action_required else 0
    score = max(0, min(score, 100))

    return {
        "score": score,
        "band": friction_band(score),
        "inputs": {
            "video_missing": video_missing,
            "video_open_failed": video_open_failed,
            "metadata_read_failed": metadata_read_failed,
            "zero_frames_detected": zero_frames_detected,
            "frames_not_saved": frames_not_saved,
            "errors_count": errors_count,
            "warnings_count": warnings_count,
            "manual_action_required": manual_action_required,
        },
    }


def calculate_stage_2_friction_score(
    *,
    ultralytics_missing: bool = False,
    model_download_failed: bool = False,
    model_load_failed: bool = False,
    video_open_failed: bool = False,
    no_frames_processed: bool = False,
    no_detections: bool = False,
    inference_too_slow: bool = False,
    errors_count: int = 0,
    warnings_count: int = 0,
    manual_action_required: bool = False,
) -> dict[str, Any]:
    """Calculate Stage 2 YOLO CPU baseline friction."""
    score = 0
    score += 45 if ultralytics_missing else 0
    score += 25 if model_download_failed else 0
    score += 35 if model_load_failed else 0
    score += 35 if video_open_failed else 0
    score += 35 if no_frames_processed else 0
    score += 10 if no_detections else 0
    score += 20 if inference_too_slow else 0
    score += min(errors_count * 10, 30)
    score += min(warnings_count * 3, 15)
    score += 20 if manual_action_required else 0
    score = max(0, min(score, 100))

    return {
        "score": score,
        "band": friction_band(score),
        "inputs": {
            "ultralytics_missing": ultralytics_missing,
            "model_download_failed": model_download_failed,
            "model_load_failed": model_load_failed,
            "video_open_failed": video_open_failed,
            "no_frames_processed": no_frames_processed,
            "no_detections": no_detections,
            "inference_too_slow": inference_too_slow,
            "errors_count": errors_count,
            "warnings_count": warnings_count,
            "manual_action_required": manual_action_required,
        },
    }
