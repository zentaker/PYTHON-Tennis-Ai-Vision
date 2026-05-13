"""Court projection helpers for calibrated tennis-court coordinates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np


def load_stage_3_calibration(report_path: Path) -> dict[str, Any]:
    """Load homography and court polygon data from the Stage 3 report."""
    if not report_path.exists():
        return {
            "available": False,
            "homography_available": False,
            "matrix": None,
            "target_size": None,
            "court_polygon": [],
            "error": f"Stage 3 report not found: {report_path}",
            "warnings": [],
        }

    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "available": False,
            "homography_available": False,
            "matrix": None,
            "target_size": None,
            "court_polygon": [],
            "error": f"Could not read Stage 3 report: {exc}",
            "warnings": [],
        }

    homography = report.get("homography_status", {})
    matrix = homography.get("matrix")
    points_status = report.get("points_status", {})
    points = points_status.get("usable_points") or points_status.get("points", {})
    polygon_names = ("near_left_corner", "near_right_corner", "far_right_corner", "far_left_corner")
    polygon = []
    for name in polygon_names:
        point = points.get(name)
        if isinstance(point, dict):
            if point.get("status") == "usable" and "x" in point and "y" in point:
                polygon.append([float(point["x"]), float(point["y"])])
        elif isinstance(point, (list, tuple)) and len(point) >= 2:
            polygon.append([float(point[0]), float(point[1])])
    return {
        "available": True,
        "homography_available": bool(homography.get("computed") and matrix),
        "matrix": matrix,
        "target_size": homography.get("target_size") or [360, 780],
        "court_polygon": polygon,
        "error": None if homography.get("computed") and matrix else homography.get("error") or "Homography unavailable.",
        "warnings": [],
        "stage_3_verdict": report.get("final_verdict"),
    }


def project_image_points(points: list[dict[str, Any]], matrix: list[list[float]] | None) -> list[dict[str, Any]]:
    """Project image-space points into the normalized court plane."""
    if not matrix or not points:
        return []
    transform = np.array(matrix, dtype=np.float64)
    source = np.array([[[float(point["x"]), float(point["y"])]] for point in points], dtype=np.float64)
    projected = cv2.perspectiveTransform(source, transform)
    rows: list[dict[str, Any]] = []
    for point, projected_point in zip(points, projected):
        rows.append(
            {
                **point,
                "projected_x": round(float(projected_point[0][0]), 3),
                "projected_y": round(float(projected_point[0][1]), 3),
            }
        )
    return rows


def point_inside_or_near_polygon(
    x_value: float,
    y_value: float,
    polygon: list[list[float]] | list[tuple[float, float]],
    margin_px: float = 150.0,
) -> dict[str, Any]:
    """Check whether a point is inside or near the calibrated court polygon."""
    if len(polygon) < 4:
        return {"available": False, "inside_or_near": True, "signed_distance": None}
    contour = np.array(polygon, dtype=np.float32)
    distance = float(cv2.pointPolygonTest(contour, (float(x_value), float(y_value)), True))
    return {
        "available": True,
        "inside_or_near": distance >= -margin_px,
        "signed_distance": round(distance, 3),
    }


def save_court_projection_preview(
    projected_candidates: list[dict[str, Any]],
    output_path: Path,
    target_size: list[int] | tuple[int, int] | None,
) -> str | None:
    """Save a mini-court preview with projected candidate points."""
    if not projected_candidates:
        return None
    width, height = target_size or [360, 780]
    canvas = np.zeros((int(height), int(width), 3), dtype=np.uint8)
    canvas[:] = (34, 105, 55)
    cv2.rectangle(canvas, (0, 0), (int(width) - 1, int(height) - 1), (255, 255, 255), 2)
    points: list[tuple[int, int]] = []
    for candidate in projected_candidates:
        x_value = int(round(candidate["projected_x"]))
        y_value = int(round(candidate["projected_y"]))
        points.append((x_value, y_value))
        cv2.circle(canvas, (x_value, y_value), 6, (0, 255, 255), -1)
        cv2.putText(
            canvas,
            str(candidate.get("frame_index", "")),
            (x_value + 7, y_value - 7),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
    for start, end in zip(points, points[1:]):
        cv2.line(canvas, start, end, (0, 255, 255), 1)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if cv2.imwrite(str(output_path), canvas):
        return str(output_path)
    return None
