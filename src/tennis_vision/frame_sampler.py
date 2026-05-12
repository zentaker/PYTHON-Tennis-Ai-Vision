"""Frame extraction helpers for local video probes."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from tennis_vision.video_io import open_video


def extract_frames(
    video_path: Path,
    output_folder: Path,
    *,
    interval: int = 30,
    max_frames: int = 25,
) -> dict[str, Any]:
    """Extract JPG frames from a video at a fixed frame interval."""
    started = time.perf_counter()
    errors: list[str] = []
    warnings: list[str] = []
    saved_files: list[str] = []
    frames_attempted = 0
    total_frames_read = 0

    if interval <= 0:
        errors.append("Extraction interval must be greater than zero.")
    if max_frames <= 0:
        errors.append("max_frames must be greater than zero.")
    if errors:
        return {
            "frames_attempted": frames_attempted,
            "frames_saved": 0,
            "total_frames_read": total_frames_read,
            "extraction_interval": interval,
            "max_frames": max_frames,
            "output_folder": str(output_folder),
            "saved_files": saved_files,
            "extraction_time_seconds": round(time.perf_counter() - started, 3),
            "errors": errors,
            "warnings": warnings,
        }

    capture, open_error = open_video(video_path)
    if open_error:
        errors.append(open_error)
        return {
            "frames_attempted": frames_attempted,
            "frames_saved": 0,
            "total_frames_read": total_frames_read,
            "extraction_interval": interval,
            "max_frames": max_frames,
            "output_folder": str(output_folder),
            "saved_files": saved_files,
            "extraction_time_seconds": round(time.perf_counter() - started, 3),
            "errors": errors,
            "warnings": warnings,
        }

    try:
        import cv2
    except ImportError as exc:
        capture.release()
        errors.append(f"OpenCV import failed: {exc}")
        return {
            "frames_attempted": frames_attempted,
            "frames_saved": 0,
            "total_frames_read": total_frames_read,
            "extraction_interval": interval,
            "max_frames": max_frames,
            "output_folder": str(output_folder),
            "saved_files": saved_files,
            "extraction_time_seconds": round(time.perf_counter() - started, 3),
            "errors": errors,
            "warnings": warnings,
        }

    output_folder.mkdir(parents=True, exist_ok=True)

    try:
        while len(saved_files) < max_frames:
            ok, frame = capture.read()
            if not ok:
                break

            total_frames_read += 1
            frame_number = total_frames_read
            should_save = frame_number == 1 or frame_number % interval == 0
            if not should_save:
                continue

            frames_attempted += 1
            frame_path = output_folder / f"frame_{frame_number:06d}.jpg"
            try:
                saved = cv2.imwrite(str(frame_path), frame)
            except Exception as exc:
                errors.append(f"Failed to save {frame_path.name}: {exc}")
                continue

            if saved:
                saved_files.append(str(frame_path))
            else:
                errors.append(f"OpenCV failed to save {frame_path.name}.")
    except Exception as exc:
        errors.append(f"Frame extraction failed: {exc}")
    finally:
        capture.release()

    if total_frames_read == 0:
        warnings.append("No frames were read from the video.")
    if frames_attempted > 0 and not saved_files:
        warnings.append("Frames were selected for extraction, but none were saved.")

    return {
        "frames_attempted": frames_attempted,
        "frames_saved": len(saved_files),
        "total_frames_read": total_frames_read,
        "extraction_interval": interval,
        "max_frames": max_frames,
        "output_folder": str(output_folder),
        "saved_files": saved_files,
        "extraction_time_seconds": round(time.perf_counter() - started, 3),
        "errors": errors,
        "warnings": warnings,
    }
