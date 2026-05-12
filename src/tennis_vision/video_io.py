"""Video loading and metadata helpers for local probes."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def validate_video_path(video_path: Path) -> dict[str, Any]:
    """Validate that a video path exists and points to a file."""
    path = video_path.expanduser()
    return {
        "path": str(path),
        "exists": path.exists(),
        "is_file": path.is_file() if path.exists() else False,
        "error": None
        if path.exists() and path.is_file()
        else f"Video file was not found: {path}",
    }


def _load_cv2() -> tuple[Any | None, str | None]:
    try:
        import cv2
    except ImportError as exc:
        return None, f"OpenCV import failed: {exc}"
    return cv2, None


def open_video(video_path: Path) -> tuple[Any | None, str | None]:
    """Open a video with OpenCV and return the capture object or an error."""
    cv2, import_error = _load_cv2()
    if import_error:
        return None, import_error

    try:
        capture = cv2.VideoCapture(str(video_path))
    except Exception as exc:
        return None, f"OpenCV could not create a VideoCapture: {exc}"

    if not capture.isOpened():
        capture.release()
        return None, f"OpenCV could not open the video file: {video_path}"

    return capture, None


def _decode_fourcc(value: float) -> str | None:
    """Decode OpenCV FOURCC codec information when available."""
    try:
        code = int(value)
        chars = "".join(chr((code >> 8 * index) & 0xFF) for index in range(4))
        cleaned = chars.strip().strip("\x00")
        return cleaned or None
    except (TypeError, ValueError):
        return None


def read_video_metadata(video_path: Path) -> dict[str, Any]:
    """Read basic video metadata with OpenCV."""
    path = video_path.expanduser()
    validation = validate_video_path(path)
    metadata: dict[str, Any] = {
        "file_path": str(path),
        "file_extension": path.suffix,
        "file_size_mb": None,
        "frame_count": None,
        "fps": None,
        "duration_seconds": None,
        "width": None,
        "height": None,
        "codec": None,
        "exists": validation["exists"],
        "opened": False,
        "metadata_readable": False,
        "errors": [],
        "warnings": [],
    }

    if validation["error"]:
        metadata["errors"].append(validation["error"])
        return metadata

    try:
        metadata["file_size_mb"] = round(path.stat().st_size / (1024 * 1024), 3)
    except OSError as exc:
        metadata["warnings"].append(f"Could not read file size: {exc}")

    capture, open_error = open_video(path)
    if open_error:
        metadata["errors"].append(open_error)
        return metadata

    cv2, import_error = _load_cv2()
    if import_error:
        metadata["errors"].append(import_error)
        if capture is not None:
            capture.release()
        return metadata

    try:
        metadata["opened"] = True
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        codec = _decode_fourcc(capture.get(cv2.CAP_PROP_FOURCC))

        metadata["frame_count"] = frame_count
        metadata["fps"] = round(fps, 3) if fps else 0.0
        metadata["duration_seconds"] = round(frame_count / fps, 3) if fps > 0 else None
        metadata["width"] = width
        metadata["height"] = height
        metadata["codec"] = codec
        metadata["metadata_readable"] = frame_count > 0 and width > 0 and height > 0

        if frame_count <= 0:
            metadata["warnings"].append("OpenCV reported zero frames.")
        if fps <= 0:
            metadata["warnings"].append("OpenCV reported missing or zero FPS.")
        if width <= 0 or height <= 0:
            metadata["warnings"].append("OpenCV reported missing or zero resolution.")
        if codec is None:
            metadata["warnings"].append("OpenCV did not expose codec information.")
    except Exception as exc:
        metadata["errors"].append(f"Metadata read failed: {exc}")
    finally:
        capture.release()

    return metadata
