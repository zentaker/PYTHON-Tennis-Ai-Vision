"""Improved local ball candidate generation for Stage 5.1."""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Any

import cv2
import numpy as np

from tennis_vision.ball_candidate_filtering import read_manual_labels
from tennis_vision.court_projection import point_inside_or_near_polygon, project_image_points
from tennis_vision.video_io import open_video


DISTANCE_THRESHOLDS = (10, 25, 50, 100, 200)


def load_labeled_frame_bundle(
    *,
    video_path: Path,
    frame_indices: list[int],
    resize_width: int = 1280,
    neighbor_offset: int = 2,
) -> tuple[dict[int, dict[str, Any]], list[str]]:
    """Load labeled frames plus nearby frames for motion comparison."""
    capture, open_error = open_video(video_path)
    if open_error:
        return {}, [open_error]

    bundles: dict[int, dict[str, Any]] = {}
    errors: list[str] = []
    try:
        for frame_index in frame_indices:
            current = _read_frame(capture, frame_index)
            if current is None:
                errors.append(f"Could not load frame {frame_index}.")
                continue
            previous = _read_frame(capture, max(0, frame_index - neighbor_offset))
            next_frame = _read_frame(capture, frame_index + neighbor_offset)
            display, scale = resize_frame(current, resize_width)
            previous_display, _ = resize_frame(previous, resize_width) if previous is not None else (None, scale)
            next_display, _ = resize_frame(next_frame, resize_width) if next_frame is not None else (None, scale)
            bundles[frame_index] = {
                "frame_index": frame_index,
                "original": current,
                "display": display,
                "previous": previous_display,
                "next": next_display,
                "scale": scale,
                "original_width": current.shape[1],
                "original_height": current.shape[0],
                "display_width": display.shape[1],
                "display_height": display.shape[0],
            }
    finally:
        capture.release()

    return bundles, errors


def _read_frame(capture: Any, frame_index: int) -> Any | None:
    capture.set(cv2.CAP_PROP_POS_FRAMES, int(frame_index))
    ok, frame = capture.read()
    return frame if ok else None


def resize_frame(frame: Any, resize_width: int | None) -> tuple[Any, float]:
    """Resize a frame and return display/original scale."""
    if frame is None:
        return None, 1.0
    if not resize_width or resize_width <= 0:
        return frame, 1.0
    height, width = frame.shape[:2]
    if width <= resize_width:
        return frame, 1.0
    scale = resize_width / width
    resized_height = max(1, int(round(height * scale)))
    return cv2.resize(frame, (resize_width, resized_height), interpolation=cv2.INTER_AREA), scale


def generate_hsv_candidates(bundle: dict[str, Any], court_polygon: list[list[float]]) -> list[dict[str, Any]]:
    """Generate yellow/green ball candidates with HSV color thresholding."""
    frame = bundle["display"]
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower = np.array([20, 30, 80], dtype=np.uint8)
    upper = np.array([95, 255, 255], dtype=np.uint8)
    mask = cv2.inRange(hsv, lower, upper)
    mask = cv2.medianBlur(mask, 3)
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    return _contour_candidates(
        mask=mask,
        frame=frame,
        hsv=hsv,
        bundle=bundle,
        strategy="hsv_color",
        court_polygon=court_polygon,
        min_area=2.0,
        max_area=1200.0,
        min_circularity=0.2,
    )


def generate_motion_candidates(bundle: dict[str, Any], court_polygon: list[list[float]]) -> list[dict[str, Any]]:
    """Generate candidates from frame-to-frame motion differences."""
    frame = bundle["display"]
    previous = bundle.get("previous")
    next_frame = bundle.get("next")
    if previous is None and next_frame is None:
        return []

    gray = cv2.GaussianBlur(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (5, 5), 0)
    motion_mask = np.zeros(gray.shape, dtype=np.uint8)
    for neighbor in (previous, next_frame):
        if neighbor is None:
            continue
        neighbor_gray = cv2.GaussianBlur(cv2.cvtColor(neighbor, cv2.COLOR_BGR2GRAY), (5, 5), 0)
        diff = cv2.absdiff(gray, neighbor_gray)
        _, threshold = cv2.threshold(diff, 18, 255, cv2.THRESH_BINARY)
        motion_mask = cv2.bitwise_or(motion_mask, threshold)

    kernel = np.ones((3, 3), np.uint8)
    motion_mask = cv2.morphologyEx(motion_mask, cv2.MORPH_OPEN, kernel, iterations=1)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    return _contour_candidates(
        mask=motion_mask,
        frame=frame,
        hsv=hsv,
        bundle=bundle,
        strategy="motion_difference",
        court_polygon=court_polygon,
        min_area=2.0,
        max_area=900.0,
        min_circularity=0.12,
    )


def generate_hybrid_candidates(bundle: dict[str, Any], court_polygon: list[list[float]]) -> list[dict[str, Any]]:
    """Generate hybrid candidates by merging color and motion signals."""
    hsv_candidates = generate_hsv_candidates(bundle, court_polygon)
    motion_candidates = generate_motion_candidates(bundle, court_polygon)
    merged: list[dict[str, Any]] = []
    for candidate in hsv_candidates + motion_candidates:
        existing = _find_nearby_candidate(merged, candidate, max_distance=35.0)
        if existing is None:
            merged.append({**candidate, "strategy": "hybrid"})
            continue
        existing["motion_score"] = max(existing.get("motion_score", 0.0), candidate.get("motion_score", 0.0))
        existing["color_score"] = max(existing.get("color_score", 0.0), candidate.get("color_score", 0.0))
        existing["circularity"] = max(existing.get("circularity", 0.0), candidate.get("circularity", 0.0))
        existing["score"] = score_candidate(existing)

    for candidate in merged:
        candidate["score"] = score_candidate(candidate)
    merged.sort(key=lambda item: item["score"], reverse=True)
    return merged[:12]


def _find_nearby_candidate(candidates: list[dict[str, Any]], candidate: dict[str, Any], max_distance: float) -> dict[str, Any] | None:
    for existing in candidates:
        if math.dist((existing["x"], existing["y"]), (candidate["x"], candidate["y"])) <= max_distance:
            return existing
    return None


def _contour_candidates(
    *,
    mask: Any,
    frame: Any,
    hsv: Any,
    bundle: dict[str, Any],
    strategy: str,
    court_polygon: list[list[float]],
    min_area: float,
    max_area: float,
    min_circularity: float,
) -> list[dict[str, Any]]:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates: list[dict[str, Any]] = []
    scale = float(bundle["scale"]) or 1.0
    for contour in contours:
        area = float(cv2.contourArea(contour))
        if area < min_area or area > max_area:
            continue
        perimeter = float(cv2.arcLength(contour, True))
        if perimeter <= 0:
            continue
        circularity = 4 * math.pi * area / (perimeter * perimeter)
        if circularity < min_circularity:
            continue
        (display_x, display_y), radius = cv2.minEnclosingCircle(contour)
        if radius < 1.0 or radius > 28.0:
            continue
        x_value = float(display_x) / scale
        y_value = float(display_y) / scale
        color_score = color_quality(hsv, int(round(display_x)), int(round(display_y)))
        motion_score = motion_quality(mask, int(round(display_x)), int(round(display_y)), int(max(3, round(radius * 2))))
        court_score = court_quality(x_value, y_value, court_polygon)
        candidate = {
            "frame_index": int(bundle["frame_index"]),
            "x": round(x_value, 3),
            "y": round(y_value, 3),
            "display_x": round(float(display_x), 3),
            "display_y": round(float(display_y), 3),
            "radius": round(float(radius) / scale, 3),
            "area": round(area / (scale * scale), 3),
            "strategy": strategy,
            "color_score": round(color_score, 4),
            "motion_score": round(motion_score, 4),
            "court_score": round(court_score, 4),
            "circularity": round(float(circularity), 4),
        }
        candidate["score"] = score_candidate(candidate)
        candidates.append(candidate)
    candidates.sort(key=lambda item: item["score"], reverse=True)
    return candidates[:12]


def color_quality(hsv: Any, x_value: int, y_value: int) -> float:
    """Score local yellow/green tennis-ball color quality."""
    height, width = hsv.shape[:2]
    if x_value < 0 or y_value < 0 or x_value >= width or y_value >= height:
        return 0.0
    hue, saturation, value = hsv[y_value, x_value]
    hue_score = 1.0 - min(abs(float(hue) - 55.0) / 45.0, 1.0)
    saturation_score = min(float(saturation) / 160.0, 1.0)
    value_score = min(float(value) / 180.0, 1.0)
    return max(0.0, min(1.0, 0.45 * hue_score + 0.30 * saturation_score + 0.25 * value_score))


def motion_quality(mask: Any, x_value: int, y_value: int, radius: int) -> float:
    """Score how much motion-mask energy exists near a candidate."""
    height, width = mask.shape[:2]
    left = max(0, x_value - radius)
    right = min(width, x_value + radius + 1)
    top = max(0, y_value - radius)
    bottom = min(height, y_value + radius + 1)
    patch = mask[top:bottom, left:right]
    if patch.size == 0:
        return 0.0
    return float(np.count_nonzero(patch)) / float(patch.size)


def court_quality(x_value: float, y_value: float, court_polygon: list[list[float]]) -> float:
    """Score whether a candidate is inside or near the calibrated play area."""
    check = point_inside_or_near_polygon(x_value, y_value, court_polygon, margin_px=350.0)
    if not check.get("available"):
        return 0.5
    distance = check.get("signed_distance")
    if distance is None:
        return 0.5
    if distance >= 0:
        return 1.0
    if distance >= -150:
        return 0.75
    if distance >= -350:
        return 0.45
    return 0.1


def score_candidate(candidate: dict[str, Any]) -> float:
    """Score a candidate using local handcrafted signals."""
    area = float(candidate.get("area") or 0.0)
    radius = float(candidate.get("radius") or 0.0)
    area_score = 1.0 - min(abs(area - 120.0) / 900.0, 1.0)
    radius_score = 1.0 - min(abs(radius - 9.0) / 35.0, 1.0)
    score = (
        0.24 * float(candidate.get("color_score") or 0.0)
        + 0.24 * float(candidate.get("motion_score") or 0.0)
        + 0.20 * float(candidate.get("court_score") or 0.0)
        + 0.16 * float(candidate.get("circularity") or 0.0)
        + 0.08 * area_score
        + 0.08 * radius_score
    )
    return round(max(0.0, min(1.0, score)), 4)


def generate_candidates_for_labels(
    *,
    video_path: Path,
    labels: list[dict[str, Any]],
    court_polygon: list[list[float]],
    resize_width: int = 1280,
) -> dict[str, Any]:
    """Generate candidates for all labeled frames across all Stage 5.1 strategies."""
    frame_indices = sorted({int(label["frame_index"]) for label in labels})
    bundles, errors = load_labeled_frame_bundle(video_path=video_path, frame_indices=frame_indices, resize_width=resize_width)
    strategies = {
        "hsv_color": generate_hsv_candidates,
        "motion_difference": generate_motion_candidates,
        "hybrid": generate_hybrid_candidates,
    }
    by_strategy: dict[str, list[dict[str, Any]]] = {name: [] for name in strategies}
    for bundle in bundles.values():
        for name, function in strategies.items():
            by_strategy[name].extend(function(bundle, court_polygon))
    return {
        "bundles": bundles,
        "candidates_by_strategy": by_strategy,
        "strategies": list(strategies),
        "errors": errors,
    }


def evaluate_strategies(
    candidates_by_strategy: dict[str, list[dict[str, Any]]],
    labels: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any] | None]:
    """Compare every candidate strategy against manual labels."""
    comparison_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    labels_by_frame = {int(label["frame_index"]): label for label in labels}
    for strategy, candidates in candidates_by_strategy.items():
        by_frame: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for candidate in candidates:
            by_frame[int(candidate["frame_index"])].append(candidate)
        distances: list[float] = []
        total_candidates = 0
        best_frame = None
        best_distance = None
        for frame_index, label in labels_by_frame.items():
            frame_candidates = by_frame.get(frame_index, [])
            total_candidates += len(frame_candidates)
            nearest = min(
                frame_candidates,
                key=lambda item: math.dist((label["x"], label["y"]), (item["x"], item["y"])),
                default=None,
            )
            distance = math.dist((label["x"], label["y"]), (nearest["x"], nearest["y"])) if nearest else None
            if distance is not None:
                distances.append(distance)
                if best_distance is None or distance < best_distance:
                    best_distance = distance
                    best_frame = frame_index
            comparison_rows.append(
                {
                    "strategy": strategy,
                    "frame_index": frame_index,
                    "manual_x": round(label["x"], 3),
                    "manual_y": round(label["y"], 3),
                    "nearest_candidate_x": round(nearest["x"], 3) if nearest else "",
                    "nearest_candidate_y": round(nearest["y"], 3) if nearest else "",
                    "nearest_distance_px": round(distance, 3) if distance is not None else "",
                    "candidate_count": len(frame_candidates),
                    "within_10_px": bool(distance is not None and distance <= 10),
                    "within_25_px": bool(distance is not None and distance <= 25),
                    "within_50_px": bool(distance is not None and distance <= 50),
                    "within_100_px": bool(distance is not None and distance <= 100),
                    "within_200_px": bool(distance is not None and distance <= 200),
                }
            )
        summary = {
            "strategy": strategy,
            "average_distance": round(sum(distances) / len(distances), 3) if distances else None,
            "median_distance": round(median(distances), 3) if distances else None,
            "best_frame": best_frame,
            "best_distance": round(best_distance, 3) if best_distance is not None else None,
            "frames_within_10_px": sum(1 for distance in distances if distance <= 10),
            "frames_within_25_px": sum(1 for distance in distances if distance <= 25),
            "frames_within_50_px": sum(1 for distance in distances if distance <= 50),
            "frames_within_100_px": sum(1 for distance in distances if distance <= 100),
            "frames_within_200_px": sum(1 for distance in distances if distance <= 200),
            "candidate_count": total_candidates,
        }
        summary_rows.append(summary)

    best_summary = min(
        (row for row in summary_rows if row.get("average_distance") is not None),
        key=lambda row: float(row["average_distance"]),
        default=None,
    )
    return comparison_rows, summary_rows, best_summary


def select_best_candidates(
    candidates: list[dict[str, Any]],
    labels: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Select the nearest candidate for each manual-label frame."""
    by_frame: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        by_frame[int(candidate["frame_index"])].append(candidate)
    selected: list[dict[str, Any]] = []
    for label in labels:
        frame_candidates = by_frame.get(int(label["frame_index"]), [])
        nearest = min(
            frame_candidates,
            key=lambda item: math.dist((label["x"], label["y"]), (item["x"], item["y"])),
            default=None,
        )
        if nearest is None:
            continue
        distance = math.dist((label["x"], label["y"]), (nearest["x"], nearest["y"]))
        selected.append({**nearest, "distance_to_manual_label": round(distance, 3)})
    return selected


def add_projection(candidates: list[dict[str, Any]], matrix: list[list[float]] | None) -> tuple[list[dict[str, Any]], int]:
    """Project improved candidates when homography is available."""
    projected = project_image_points(candidates, matrix)
    by_key = {(item["frame_index"], item["x"], item["y"]): item for item in projected}
    projected_count = 0
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        item = by_key.get((candidate["frame_index"], candidate["x"], candidate["y"]))
        row = {**candidate, "projected_x": None, "projected_y": None}
        if item:
            row["projected_x"] = item["projected_x"]
            row["projected_y"] = item["projected_y"]
            projected_count += 1
        rows.append(row)
    return rows, projected_count


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> Path:
    """Write dictionaries to CSV with stable field order."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    return path


def save_strategy_overlays(
    *,
    bundles: dict[int, dict[str, Any]],
    labels: list[dict[str, Any]],
    best_candidates: list[dict[str, Any]],
    output_dir: Path,
) -> list[str]:
    """Save review overlays showing manual label and best candidate."""
    output_dir.mkdir(parents=True, exist_ok=True)
    labels_by_frame = {int(label["frame_index"]): label for label in labels}
    candidates_by_frame = {int(candidate["frame_index"]): candidate for candidate in best_candidates}
    saved: list[str] = []
    for frame_index, bundle in bundles.items():
        frame = bundle["display"].copy()
        scale = float(bundle["scale"]) or 1.0
        label = labels_by_frame.get(frame_index)
        candidate = candidates_by_frame.get(frame_index)
        if label:
            lx = int(round(label["x"] * scale))
            ly = int(round(label["y"] * scale))
            cv2.circle(frame, (lx, ly), 9, (0, 0, 255), -1)
            cv2.putText(frame, "manual", (lx + 10, ly - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
        if candidate:
            cx = int(round(candidate["x"] * scale))
            cy = int(round(candidate["y"] * scale))
            cv2.circle(frame, (cx, cy), 12, (0, 255, 255), 2)
            cv2.putText(
                frame,
                f"{candidate['strategy']} {candidate['score']:.2f}",
                (cx + 10, cy + 18),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 255),
                2,
            )
            if label:
                cv2.line(frame, (lx, ly), (cx, cy), (255, 255, 255), 2)
                cv2.putText(
                    frame,
                    f"{candidate['distance_to_manual_label']:.1f}px",
                    (min(lx, cx), max(20, min(ly, cy) - 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2,
                )
        cv2.putText(frame, f"frame {frame_index}", (24, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        path = output_dir / f"stage_5_1_frame_{frame_index:06d}.jpg"
        if cv2.imwrite(str(path), frame):
            saved.append(str(path))
    return saved


def save_strategy_preview(overlay_paths: list[str], output_path: Path) -> str | None:
    """Save a simple contact sheet from overlay images."""
    images = [cv2.imread(path) for path in overlay_paths]
    images = [image for image in images if image is not None]
    if not images:
        return None
    thumb_width = 480
    thumbs = []
    for image in images:
        height, width = image.shape[:2]
        scale = thumb_width / width
        thumbs.append(cv2.resize(image, (thumb_width, int(height * scale)), interpolation=cv2.INTER_AREA))
    max_height = max(image.shape[0] for image in thumbs)
    padded = []
    for image in thumbs:
        if image.shape[0] < max_height:
            pad = np.full((max_height - image.shape[0], image.shape[1], 3), 30, dtype=np.uint8)
            image = np.vstack([image, pad])
        padded.append(image)
    sheet = np.hstack(padded)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if cv2.imwrite(str(output_path), sheet):
        return str(output_path)
    return None
