"""Candidate-to-label filtering helpers for Stage 5."""

from __future__ import annotations

import csv
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any

import cv2
import numpy as np

from tennis_vision.court_projection import point_inside_or_near_polygon, project_image_points


DISTANCE_THRESHOLDS = (10, 25, 50, 100, 200)


def read_ball_candidates(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Read Stage 4 automatic candidates."""
    if not path.exists():
        return [], [f"Candidate CSV not found: {path}"]
    candidates: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                x_value = float(row.get("original_center_x") or row.get("center_x") or 0)
                y_value = float(row.get("original_center_y") or row.get("center_y") or 0)
                candidates.append(
                    {
                        "frame_index": int(float(row["frame_index"])),
                        "x": x_value,
                        "y": y_value,
                        "radius": _float_or_none(row.get("radius")),
                        "area": _float_or_none(row.get("area")),
                        "score": _float_or_none(row.get("score")) or 0.0,
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
    return candidates, []


def read_manual_labels(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Read Stage 4.1 visible manual labels."""
    if not path.exists():
        return [], [f"Manual labels CSV not found: {path}"]
    labels: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            visible = str(row.get("visible", "")).lower() == "true"
            if not visible:
                continue
            try:
                labels.append(
                    {
                        "frame_index": int(float(row["frame_index"])),
                        "x": float(row["x"]),
                        "y": float(row["y"]),
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
    return labels, []


def _float_or_none(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def compare_candidates_to_labels(
    candidates: list[dict[str, Any]],
    labels: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Rank candidates by distance to visible manual labels in the same frame."""
    candidates_by_frame: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        candidates_by_frame[int(candidate["frame_index"])].append(candidate)

    rows: list[dict[str, Any]] = []
    nearest_distances: list[float] = []
    frames_with_nearest = 0
    for label in labels:
        frame_candidates = candidates_by_frame.get(int(label["frame_index"]), [])
        ranked: list[tuple[float, dict[str, Any]]] = []
        for candidate in frame_candidates:
            distance = math.dist((label["x"], label["y"]), (candidate["x"], candidate["y"]))
            ranked.append((distance, candidate))
        ranked.sort(key=lambda item: item[0])
        if ranked:
            frames_with_nearest += 1
            nearest_distances.append(ranked[0][0])
        for rank, (distance, candidate) in enumerate(ranked, start=1):
            rows.append(
                {
                    "frame_index": label["frame_index"],
                    "manual_x": round(label["x"], 3),
                    "manual_y": round(label["y"], 3),
                    "candidate_x": round(candidate["x"], 3),
                    "candidate_y": round(candidate["y"], 3),
                    "distance_px": round(distance, 3),
                    "candidate_rank": rank,
                    "within_10_px": distance <= 10,
                    "within_25_px": distance <= 25,
                    "within_50_px": distance <= 50,
                    "within_100_px": distance <= 100,
                    "within_200_px": distance <= 200,
                }
            )

    summary = {
        "manual_labels_count": len(labels),
        "automatic_candidates_count": len(candidates),
        "labeled_frames_compared": frames_with_nearest,
        "nearest_candidate_average_distance": round(sum(nearest_distances) / len(nearest_distances), 3)
        if nearest_distances
        else None,
        "nearest_candidate_median_distance": round(median(nearest_distances), 3) if nearest_distances else None,
        "frames_within_10_px": sum(1 for distance in nearest_distances if distance <= 10),
        "frames_within_25_px": sum(1 for distance in nearest_distances if distance <= 25),
        "frames_within_50_px": sum(1 for distance in nearest_distances if distance <= 50),
        "frames_within_100_px": sum(1 for distance in nearest_distances if distance <= 100),
        "frames_within_200_px": sum(1 for distance in nearest_distances if distance <= 200),
    }
    return rows, summary


def filter_candidates(
    candidates: list[dict[str, Any]],
    labels: list[dict[str, Any]],
    court_polygon: list[list[float]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Apply a simple baseline filter using labels, court geometry, and temporal consistency."""
    labels_by_frame = {int(label["frame_index"]): label for label in labels}
    candidates_by_frame: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        candidates_by_frame[int(candidate["frame_index"])].append(candidate)

    selected_by_frame: dict[int, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []

    # Labeled frames: select nearest candidate only if it is close enough to the manual label.
    for frame_index, frame_candidates in sorted(candidates_by_frame.items()):
        label = labels_by_frame.get(frame_index)
        if label:
            ranked = sorted(
                frame_candidates,
                key=lambda candidate: math.dist((label["x"], label["y"]), (candidate["x"], candidate["y"])),
            )
            nearest = ranked[0] if ranked else None
            for candidate in frame_candidates:
                distance = math.dist((label["x"], label["y"]), (candidate["x"], candidate["y"]))
                court_check = point_inside_or_near_polygon(candidate["x"], candidate["y"], court_polygon)
                selected = candidate is nearest and distance <= 200
                reason = "nearest_to_manual_label_within_200px" if selected else "rejected_by_manual_label_distance"
                row = candidate_row(candidate, selected, reason, distance, court_check)
                rows.append(row)
                if selected:
                    selected_by_frame[frame_index] = row

    anchors = sorted(selected_by_frame.values(), key=lambda item: item["frame_index"])

    # Unlabeled frames: choose at most one candidate when it fits court and temporal interpolation.
    for frame_index, frame_candidates in sorted(candidates_by_frame.items()):
        if frame_index in labels_by_frame:
            continue
        expected = interpolate_expected_point(frame_index, anchors)
        best_candidate = None
        best_distance = None
        for candidate in frame_candidates:
            court_check = point_inside_or_near_polygon(candidate["x"], candidate["y"], court_polygon)
            if not court_check["inside_or_near"]:
                continue
            if expected is not None:
                temporal_distance = math.dist(expected, (candidate["x"], candidate["y"]))
                if temporal_distance > 450:
                    continue
            else:
                temporal_distance = 0.0
            weighted = temporal_distance - (candidate.get("score") or 0.0) * 40
            if best_distance is None or weighted < best_distance:
                best_distance = weighted
                best_candidate = candidate

        for candidate in frame_candidates:
            court_check = point_inside_or_near_polygon(candidate["x"], candidate["y"], court_polygon)
            selected = candidate is best_candidate
            reason = "temporal_court_consistent_candidate" if selected else "rejected_by_temporal_or_court_filter"
            distance = math.dist(expected, (candidate["x"], candidate["y"])) if expected is not None else None
            row = candidate_row(candidate, selected, reason, distance, court_check)
            rows.append(row)
            if selected:
                selected_by_frame[frame_index] = row

    rows.sort(key=lambda item: (item["frame_index"], not item["selected"], item["score"]))
    reasons = Counter(row["filter_reason"] for row in rows if not row["selected"])
    summary = {
        "selected_candidates": sum(1 for row in rows if row["selected"]),
        "rejected_candidates": sum(1 for row in rows if not row["selected"]),
        "main_rejection_reasons": dict(reasons.most_common(5)),
    }
    return rows, summary


def interpolate_expected_point(frame_index: int, anchors: list[dict[str, Any]]) -> tuple[float, float] | None:
    """Estimate an expected ball point from nearby selected labeled anchors."""
    previous = None
    next_item = None
    for anchor in anchors:
        if anchor["frame_index"] < frame_index:
            previous = anchor
        elif anchor["frame_index"] > frame_index and next_item is None:
            next_item = anchor
            break
    if previous and next_item:
        span = next_item["frame_index"] - previous["frame_index"]
        if span <= 0:
            return None
        ratio = (frame_index - previous["frame_index"]) / span
        return (
            previous["x"] + (next_item["x"] - previous["x"]) * ratio,
            previous["y"] + (next_item["y"] - previous["y"]) * ratio,
        )
    return None


def candidate_row(
    candidate: dict[str, Any],
    selected: bool,
    reason: str,
    distance: float | None,
    court_check: dict[str, Any],
) -> dict[str, Any]:
    """Build a filtered candidate output row."""
    base_score = float(candidate.get("score") or 0.0)
    distance_penalty = min((distance or 0.0) / 500.0, 1.0) if distance is not None else 0.2
    court_bonus = 0.1 if court_check.get("inside_or_near") else -0.3
    score = max(0.0, min(1.0, base_score * 0.65 + (1.0 - distance_penalty) * 0.25 + court_bonus))
    return {
        "frame_index": int(candidate["frame_index"]),
        "x": round(float(candidate["x"]), 3),
        "y": round(float(candidate["y"]), 3),
        "selected": bool(selected),
        "filter_reason": reason,
        "score": round(score, 4),
        "source_score": round(base_score, 4),
        "distance_reference_px": round(distance, 3) if distance is not None else None,
        "inside_or_near_court": court_check.get("inside_or_near"),
        "court_signed_distance": court_check.get("signed_distance"),
        "projected_x": None,
        "projected_y": None,
    }


def add_projection_to_rows(rows: list[dict[str, Any]], matrix: list[list[float]] | None) -> tuple[list[dict[str, Any]], int]:
    """Project selected candidates and merge projected coordinates back into rows."""
    selected_points = [{"x": row["x"], "y": row["y"], "frame_index": row["frame_index"]} for row in rows if row["selected"]]
    projected = project_image_points(selected_points, matrix)
    projected_by_key = {(item["frame_index"], item["x"], item["y"]): item for item in projected}
    projected_count = 0
    for row in rows:
        key = (row["frame_index"], row["x"], row["y"])
        item = projected_by_key.get(key)
        if item:
            row["projected_x"] = item["projected_x"]
            row["projected_y"] = item["projected_y"]
            projected_count += 1
    return rows, projected_count


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> Path:
    """Write rows to CSV with a stable field order."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    return path


def save_filtered_trajectory_preview(rows: list[dict[str, Any]], output_path: Path, size: tuple[int, int] = (1280, 720)) -> str | None:
    """Save a simple image-space trajectory preview for selected candidates."""
    selected = [row for row in sorted(rows, key=lambda item: item["frame_index"]) if row["selected"]]
    if not selected:
        return None
    canvas = 255 * np.ones((size[1], size[0], 3), dtype=np.uint8)
    points: list[tuple[int, int]] = []
    for row in selected:
        # Source coordinates are 4K; scale to preview canvas.
        x_value = int(round(row["x"] / 3840 * size[0]))
        y_value = int(round(row["y"] / 2160 * size[1]))
        points.append((x_value, y_value))
        cv2.circle(canvas, (x_value, y_value), 6, (0, 0, 255), -1)
        cv2.putText(canvas, str(row["frame_index"]), (x_value + 8, y_value - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)
    for start, end in zip(points, points[1:]):
        cv2.line(canvas, start, end, (0, 180, 255), 2)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if cv2.imwrite(str(output_path), canvas):
        return str(output_path)
    return None
