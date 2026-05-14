"""Projection coverage helpers for Stage 9.1."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from tennis_vision.court_zones import COURT_HEIGHT, COURT_WIDTH, COURT_MARGIN


def load_expanded_ball_labels(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Load visible expanded ball labels from Stage 8.1."""
    if not path.exists():
        return [], [f"Expanded ball labels not found: {path}"]
    rows: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            visible = str(row.get("visible", "")).lower() in {"true", "1", "yes"}
            if not visible:
                continue
            try:
                rows.append(
                    {
                        "frame_index": int(float(row["frame_index"])),
                        "x": float(row["x"]),
                        "y": float(row["y"]),
                        "source": row.get("source") or "stage_8_1_expanded",
                        "notes": row.get("notes", ""),
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
    return rows, []


def load_stage_3_homography(report_path: Path) -> tuple[list[list[float]] | None, dict[str, Any], list[str]]:
    """Load Stage 3 homography matrix and metadata."""
    if not report_path.exists():
        return None, {"homography_available": False}, [f"Stage 3 calibration report not found: {report_path}"]
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, {"homography_available": False}, [f"Could not read Stage 3 calibration report: {exc}"]
    homography = report.get("homography_status") or report.get("calibration_result", {}).get("homography", {})
    matrix = homography.get("matrix")
    if not homography.get("computed") or not matrix:
        return None, {"homography_available": False, "error": homography.get("error")}, ["Stage 3 homography is not available."]
    return matrix, {"homography_available": True, "target_size": homography.get("target_size") or [COURT_WIDTH, COURT_HEIGHT]}, []


def project_labels_to_court(labels: list[dict[str, Any]], matrix: list[list[float]] | None) -> list[dict[str, Any]]:
    """Project expanded label image coordinates into normalized court space."""
    if not labels:
        return []
    if matrix is None:
        return [
            {
                **label,
                "projected_x": None,
                "projected_y": None,
                "projection_status": "missing_homography",
                "notes": "Homography missing; cannot project label.",
            }
            for label in labels
        ]
    transform = np.array(matrix, dtype=np.float64)
    source = np.array([[[float(label["x"]), float(label["y"])]] for label in labels], dtype=np.float64)
    projected = cv2.perspectiveTransform(source, transform)
    rows: list[dict[str, Any]] = []
    for label, projected_point in zip(labels, projected):
        projected_x = round(float(projected_point[0][0]), 3)
        projected_y = round(float(projected_point[0][1]), 3)
        out_of_range = (
            projected_x < -COURT_MARGIN
            or projected_x > COURT_WIDTH + COURT_MARGIN
            or projected_y < -COURT_MARGIN
            or projected_y > COURT_HEIGHT + COURT_MARGIN
        )
        rows.append(
            {
                **label,
                "projected_x": projected_x,
                "projected_y": projected_y,
                "projection_status": "outside_expected_range" if out_of_range else "projected",
                "notes": "Projected with Stage 3 homography." if not out_of_range else "Projected but outside expected normalized court range.",
            }
        )
    return rows


def merge_projected_labels_with_stage_9_assignments(
    projected_labels: list[dict[str, Any]],
    stage_9_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Attach original Stage 9 zone context to projected label rows."""
    by_frame = {int(float(row["frame_index"])): row for row in stage_9_rows if row.get("frame_index")}
    merged: list[dict[str, Any]] = []
    for label in projected_labels:
        original = by_frame.get(int(label["frame_index"]), {})
        merged.append(
            {
                **label,
                "original_zone": original.get("court_zone", "unknown"),
                "original_depth": original.get("depth", "unknown"),
                "original_lateral_lane": original.get("lateral_lane", "unknown"),
                "stage_9_projection_available": bool(original.get("projected_x") and original.get("projected_y")),
            }
        )
    return merged


def calculate_projection_coverage(projected_labels: list[dict[str, Any]], stage_9_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare Stage 9 projection coverage with Stage 9.1 projected labels."""
    stage_9_projected = sum(1 for row in stage_9_rows if row.get("projected_x") not in (None, "") and row.get("projected_y") not in (None, ""))
    stage_9_unknown = sum(1 for row in stage_9_rows if row.get("court_zone") == "unknown")
    stage_9_1_projected = sum(1 for row in projected_labels if row.get("projected_x") is not None and row.get("projected_y") is not None)
    projection_failed = sum(1 for row in projected_labels if row.get("projection_status") in {"projection_failed", "missing_homography"})
    return {
        "stage_9_projected_points": stage_9_projected,
        "stage_9_unknown_zones": stage_9_unknown,
        "stage_9_1_projected_points": stage_9_1_projected,
        "projection_success_count": stage_9_1_projected,
        "projection_failed_count": projection_failed,
        "projection_coverage_improvement": stage_9_1_projected - stage_9_projected,
    }


def read_csv_rows(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Read CSV rows with a warning on missing files."""
    if not path.exists():
        return [], [f"CSV not found: {path}"]
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle)), []


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> Path:
    """Write rows to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    return path
