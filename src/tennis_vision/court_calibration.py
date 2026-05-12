"""Manual court calibration helpers for Stage 3."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from tennis_vision.video_io import open_video


CORNER_ORDER = (
    "near_left_corner",
    "near_right_corner",
    "far_right_corner",
    "far_left_corner",
)
SELECTION_ORDER = (
    "near_left_corner",
    "near_right_corner",
    "far_left_corner",
    "far_right_corner",
)
POINT_LABELS = {
    "near_left_corner": "bottom-left doubles court corner",
    "near_right_corner": "bottom-right doubles court corner",
    "far_left_corner": "top-left doubles court corner",
    "far_right_corner": "top-right doubles court corner",
}
CALIBRATION_BASIS = "doubles court outer boundary"
MINI_COURT_WIDTH = 360
MINI_COURT_HEIGHT = 780


def load_frame_at_index(video_path: Path, frame_index: int) -> tuple[Any | None, str | None]:
    """Load a single frame from a video."""
    if frame_index < 0:
        return None, "frame_index must be zero or greater."

    capture, open_error = open_video(video_path)
    if open_error:
        return None, open_error

    try:
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = capture.read()
        if not ok or frame is None:
            return None, f"Could not load frame at index {frame_index}."
        return frame, None
    finally:
        capture.release()


def save_image(path: Path, image: Any) -> tuple[Path | None, str | None]:
    """Save an image and return an error when OpenCV fails."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        if cv2.imwrite(str(path), image):
            return path, None
        return None, f"OpenCV failed to save image: {path}"
    except Exception as exc:
        return None, f"Could not save image {path}: {exc}"


def read_calibration_config(config_path: Path) -> dict[str, Any]:
    """Read a manual court calibration config."""
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"data": {}, "errors": [f"Config file not found: {config_path}"], "warnings": []}
    except json.JSONDecodeError as exc:
        return {"data": {}, "errors": [f"Config JSON is invalid: {exc}"], "warnings": []}
    except OSError as exc:
        return {"data": {}, "errors": [f"Could not read config file: {exc}"], "warnings": []}

    return {"data": data, "errors": [], "warnings": []}


def validate_points(points: dict[str, Any], frame_shape: tuple[int, int, int] | None = None) -> dict[str, Any]:
    """Validate manual calibration points."""
    height = frame_shape[0] if frame_shape is not None else None
    width = frame_shape[1] if frame_shape is not None else None
    statuses: dict[str, dict[str, Any]] = {}
    usable_points: dict[str, tuple[float, float]] = {}

    for name in CORNER_ORDER:
        raw = points.get(name)
        status = "missing"
        x_value = None
        y_value = None

        if isinstance(raw, list) and len(raw) == 2:
            try:
                x_value = float(raw[0])
                y_value = float(raw[1])
                if x_value == 0 and y_value == 0:
                    status = "placeholder"
                elif x_value < 0 or y_value < 0:
                    status = "invalid"
                elif width is not None and height is not None and (x_value >= width or y_value >= height):
                    status = "invalid"
                else:
                    status = "usable"
                    usable_points[name] = (x_value, y_value)
            except (TypeError, ValueError):
                status = "invalid"
        elif raw is not None:
            status = "invalid"

        statuses[name] = {
            "x": x_value,
            "y": y_value,
            "status": status,
        }

    has_placeholders = any(item["status"] == "placeholder" for item in statuses.values())
    has_missing = any(item["status"] == "missing" for item in statuses.values())
    has_invalid = any(item["status"] == "invalid" for item in statuses.values())
    geometry = validate_corner_geometry(usable_points)
    homography_ready = all(name in usable_points for name in CORNER_ORDER) and geometry["valid"]

    return {
        "points": statuses,
        "usable_points": usable_points,
        "has_placeholders": has_placeholders,
        "has_missing": has_missing,
        "has_invalid": has_invalid,
        "geometry": geometry,
        "homography_ready": homography_ready,
        "usable_count": len(usable_points),
    }


def validate_corner_geometry(usable_points: dict[str, tuple[float, float]]) -> dict[str, Any]:
    """Validate manual corner ordering and polygon shape."""
    required_available = all(name in usable_points for name in CORNER_ORDER)
    order_checks = {
        "near_left_before_near_right": None,
        "far_left_before_far_right": None,
    }
    warnings: list[str] = []
    self_intersects = None

    if not required_available:
        return {
            "valid": False,
            "required_points_available": False,
            "point_order_valid": False,
            "polygon_self_intersects": None,
            "order_checks": order_checks,
            "warnings": warnings,
        }

    near_left = usable_points["near_left_corner"]
    near_right = usable_points["near_right_corner"]
    far_left = usable_points["far_left_corner"]
    far_right = usable_points["far_right_corner"]
    order_checks["near_left_before_near_right"] = near_left[0] < near_right[0]
    order_checks["far_left_before_far_right"] = far_left[0] < far_right[0]
    point_order_valid = all(bool(value) for value in order_checks.values())

    if not point_order_valid:
        warnings.append("Court point left/right order is suspicious or inverted.")

    polygon = [near_left, near_right, far_right, far_left]
    self_intersects = quadrilateral_self_intersects(polygon)
    if self_intersects:
        warnings.append("Court point polygon self-intersects.")

    valid = point_order_valid and not self_intersects
    return {
        "valid": valid,
        "required_points_available": True,
        "point_order_valid": point_order_valid,
        "polygon_self_intersects": self_intersects,
        "order_checks": order_checks,
        "warnings": warnings,
    }


def quadrilateral_self_intersects(points: list[tuple[float, float]]) -> bool:
    """Return True when a four-point polygon crosses itself."""
    if len(points) != 4:
        return False
    p0, p1, p2, p3 = points
    return segments_intersect(p0, p1, p2, p3) or segments_intersect(p1, p2, p3, p0)


def segments_intersect(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
    d: tuple[float, float],
) -> bool:
    """Check whether two 2D line segments intersect."""

    def orientation(p: tuple[float, float], q: tuple[float, float], r: tuple[float, float]) -> float:
        return (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])

    def on_segment(p: tuple[float, float], q: tuple[float, float], r: tuple[float, float]) -> bool:
        return (
            min(p[0], r[0]) <= q[0] <= max(p[0], r[0])
            and min(p[1], r[1]) <= q[1] <= max(p[1], r[1])
        )

    o1 = orientation(a, b, c)
    o2 = orientation(a, b, d)
    o3 = orientation(c, d, a)
    o4 = orientation(c, d, b)

    if (o1 > 0 > o2 or o1 < 0 < o2) and (o3 > 0 > o4 or o3 < 0 < o4):
        return True
    epsilon = 1e-9
    if abs(o1) < epsilon and on_segment(a, c, b):
        return True
    if abs(o2) < epsilon and on_segment(a, d, b):
        return True
    if abs(o3) < epsilon and on_segment(c, a, d):
        return True
    if abs(o4) < epsilon and on_segment(c, b, d):
        return True
    return False


def draw_points_overlay(frame: Any, validation: dict[str, Any]) -> Any:
    """Draw calibration point markers, labels, and polygon when possible."""
    overlay = frame.copy()
    colors = {
        "usable": (40, 220, 40),
        "placeholder": (0, 215, 255),
        "missing": (60, 60, 255),
        "invalid": (0, 0, 255),
    }

    for name, details in validation["points"].items():
        x_value = details["x"]
        y_value = details["y"]
        status = details["status"]
        if x_value is None or y_value is None:
            continue
        point = (int(round(x_value)), int(round(y_value)))
        cv2.circle(overlay, point, 12, colors.get(status, (255, 255, 255)), -1)
        cv2.putText(
            overlay,
            f"{name} - {POINT_LABELS.get(name, 'court point')} ({status})",
            (point[0] + 14, point[1] - 14),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            colors.get(status, (255, 255, 255)),
            2,
            cv2.LINE_AA,
        )

    if validation["homography_ready"]:
        polygon = np.array(
            [[validation["usable_points"][name] for name in CORNER_ORDER]],
            dtype=np.int32,
        )
        cv2.polylines(overlay, polygon, isClosed=True, color=(255, 255, 0), thickness=4)

    return overlay


def compute_homography(validation: dict[str, Any]) -> dict[str, Any]:
    """Compute a basic court homography from four manual corner points."""
    if not validation["homography_ready"]:
        geometry = validation.get("geometry", {})
        if geometry.get("required_points_available") and not geometry.get("valid"):
            return {
                "computed": False,
                "matrix": None,
                "error": "Court points appear crossed, inverted, or geometrically invalid.",
            }
        return {
            "computed": False,
            "matrix": None,
            "error": "Four usable court corner points are required.",
        }

    src = np.array([validation["usable_points"][name] for name in CORNER_ORDER], dtype=np.float32)
    dst = np.array(
        [
            [0, MINI_COURT_HEIGHT],
            [MINI_COURT_WIDTH, MINI_COURT_HEIGHT],
            [MINI_COURT_WIDTH, 0],
            [0, 0],
        ],
        dtype=np.float32,
    )
    matrix, _ = cv2.findHomography(src, dst)
    if matrix is None:
        return {"computed": False, "matrix": None, "error": "OpenCV could not compute homography."}

    return {
        "computed": True,
        "matrix": matrix.tolist(),
        "error": None,
        "target_size": [MINI_COURT_WIDTH, MINI_COURT_HEIGHT],
    }


def generate_mini_court_preview(frame: Any, homography: dict[str, Any]) -> tuple[Any | None, str | None]:
    """Generate a normalized mini-court preview when homography exists."""
    if not homography["computed"] or not homography["matrix"]:
        return None, homography.get("error") or "Homography was not computed."

    matrix = np.array(homography["matrix"], dtype=np.float64)
    preview = cv2.warpPerspective(frame, matrix, (MINI_COURT_WIDTH, MINI_COURT_HEIGHT))
    cv2.rectangle(preview, (0, 0), (MINI_COURT_WIDTH - 1, MINI_COURT_HEIGHT - 1), (255, 255, 255), 2)
    return preview, None


def run_court_calibration_probe(
    *,
    config_path: Path,
    output_folder: Path,
    project_root: Path,
    video_override: Path | None = None,
    frame_index_override: int | None = None,
) -> dict[str, Any]:
    """Run the Stage 3 manual court calibration probe."""
    errors: list[str] = []
    warnings: list[str] = []
    config_result = read_calibration_config(config_path)
    errors.extend(config_result["errors"])
    warnings.extend(config_result["warnings"])
    config = config_result["data"]

    config_video = Path(config.get("video", "samples/video_01.mov"))
    video_path = video_override or config_video
    if not video_path.is_absolute():
        video_path = project_root / video_path
    frame_index = frame_index_override if frame_index_override is not None else int(config.get("frame_index", 120))

    reference_path = output_folder / "calibration_reference_frame.jpg"
    overlay_path = output_folder / "court_points_overlay.jpg"
    preview_path = output_folder / "mini_court_preview.jpg"
    frame, frame_error = load_frame_at_index(video_path, frame_index)
    if frame_error:
        errors.append(frame_error)
        return {
            "config": config,
            "video_path": str(video_path),
            "frame_index": frame_index,
            "reference_frame_path": None,
            "overlay_path": None,
            "mini_court_preview_path": None,
            "points_status": {},
            "homography": {"computed": False, "matrix": None, "error": "Frame load failed."},
            "errors": errors,
            "warnings": warnings,
        }

    saved_reference, reference_error = save_image(reference_path, frame)
    if reference_error:
        errors.append(reference_error)

    points = config.get("points", {})
    if not isinstance(points, dict) or not points:
        warnings.append("Calibration points are missing from the config.")
        points = {}
    validation = validate_points(points, frame.shape)
    if validation["has_placeholders"]:
        warnings.append("Placeholder court points detected. Fill coordinates from the reference frame.")
    if validation["has_invalid"]:
        warnings.append("Invalid court points detected.")
    if validation["has_missing"]:
        warnings.append("Some required court points are missing.")
    geometry = validation.get("geometry", {})
    if geometry.get("required_points_available") and not geometry.get("valid"):
        warnings.append(
            "Court points appear crossed, inverted, or geometrically invalid. "
            "Rerun Stage 3.1 and select points in this exact order: "
            "near_left_corner, near_right_corner, far_left_corner, far_right_corner."
        )

    overlay = draw_points_overlay(frame, validation)
    saved_overlay, overlay_error = save_image(overlay_path, overlay)
    if overlay_error:
        errors.append(overlay_error)

    homography = compute_homography(validation)
    saved_preview = None
    if homography["computed"]:
        preview, preview_error = generate_mini_court_preview(frame, homography)
        if preview_error:
            warnings.append(preview_error)
        elif preview is not None:
            saved_preview, preview_save_error = save_image(preview_path, preview)
            if preview_save_error:
                errors.append(preview_save_error)
    else:
        if validation["homography_ready"]:
            warnings.append(f"Homography not computed: {homography['error']}")

    return {
        "config": config,
        "video_path": str(video_path),
        "frame_index": frame_index,
        "reference_frame_path": str(saved_reference) if saved_reference else None,
        "overlay_path": str(saved_overlay) if saved_overlay else None,
        "mini_court_preview_path": str(saved_preview) if saved_preview else None,
        "points_status": {
            "points": validation["points"],
            "usable_count": validation["usable_count"],
            "has_placeholders": validation["has_placeholders"],
            "has_missing": validation["has_missing"],
            "has_invalid": validation["has_invalid"],
            "homography_ready": validation["homography_ready"],
            "geometry": validation["geometry"],
            "calibration_basis": CALIBRATION_BASIS,
            "point_labels": POINT_LABELS,
        },
        "homography": homography,
        "errors": errors,
        "warnings": warnings,
    }
