"""Manual tennis ball labeling helpers for Stage 4.1."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from statistics import median
from typing import Any

import cv2

from tennis_vision.ball_tracking_probe import resize_frame
from tennis_vision.video_io import open_video


DEFAULT_FRAME_INDICES = [30, 60, 90, 120, 150, 180, 210, 240]


def parse_frame_indices(value: str | None) -> list[int]:
    """Parse a comma-separated frame list."""
    if not value:
        return []
    indices: list[int] = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        indices.append(int(item))
    return indices


def build_frame_indices(
    *,
    frames: str | None,
    start_frame: int | None,
    interval: int,
    max_frames: int,
) -> list[int]:
    """Build the selected frame list from CLI choices."""
    parsed = parse_frame_indices(frames)
    if parsed:
        return sorted(dict.fromkeys(index for index in parsed if index >= 0))
    if start_frame is not None:
        return [start_frame + interval * offset for offset in range(max_frames) if start_frame + interval * offset >= 0]
    return DEFAULT_FRAME_INDICES[:max_frames]


def load_frame_at_index(video_path: Path, frame_index: int) -> tuple[Any | None, str | None]:
    """Load one frame from a video."""
    capture, open_error = open_video(video_path)
    if open_error:
        return None, open_error
    try:
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = capture.read()
        if not ok or frame is None:
            return None, f"Could not load frame {frame_index}."
        return frame, None
    finally:
        capture.release()


def draw_label_overlay(frame: Any, label: dict[str, Any]) -> Any:
    """Draw a manual label marker onto a display frame."""
    overlay = frame.copy()
    frame_index = label["frame_index"]
    text = f"frame {frame_index}"
    if label.get("visible"):
        point = (int(round(label["display_x"])), int(round(label["display_y"])))
        cv2.circle(overlay, point, 18, (0, 0, 0), 4)
        cv2.circle(overlay, point, 16, (0, 255, 255), 3)
        cv2.circle(overlay, point, 3, (0, 0, 255), -1)
        text += f" | ball ({label['x']:.1f}, {label['y']:.1f})"
    else:
        text += " | skipped"
    cv2.putText(overlay, text, (20, 44), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 4, cv2.LINE_AA)
    cv2.putText(overlay, text, (20, 44), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
    return overlay


def write_labels_csv(path: Path, labels: list[dict[str, Any]]) -> Path:
    """Write manual labels to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "frame_index",
        "visible",
        "x",
        "y",
        "display_x",
        "display_y",
        "original_width",
        "original_height",
        "display_width",
        "display_height",
        "notes",
        "overlay_path",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for label in labels:
            writer.writerow({field: label.get(field, "") for field in fields})
    return path


def write_labels_json(path: Path, labels: list[dict[str, Any]]) -> Path:
    """Write manual labels to JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(labels, indent=2) + "\n", encoding="utf-8")
    return path


def label_frames_interactively(
    *,
    video_path: Path,
    frame_indices: list[int],
    output_dir: Path,
    resize_width: int = 1280,
    stage_4_overlay_dir: Path | None = None,
) -> dict[str, Any]:
    """Open selected frames and collect manual ball clicks."""
    labels: list[dict[str, Any]] = []
    errors: list[str] = []
    warnings: list[str] = []
    overlay_dir = output_dir / "label_overlays"
    overlay_dir.mkdir(parents=True, exist_ok=True)

    window_name = "Stage 4.1 Manual Ball Labeling"
    quit_requested = False
    try:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    except cv2.error as exc:
        return {
            "labels": labels,
            "frames_shown": 0,
            "quit_requested": False,
            "errors": [f"OpenCV GUI is unavailable or failed: {exc}"],
            "warnings": warnings,
            "overlay_dir": str(overlay_dir),
        }

    frames_shown = 0
    try:
        for frame_index in frame_indices:
            frame, frame_error = load_frame_at_index(video_path, frame_index)
            if frame_error:
                errors.append(frame_error)
                continue
            original_height, original_width = frame.shape[:2]
            display, scale = resize_frame(frame, resize_width)
            display = load_stage_4_display_frame(stage_4_overlay_dir, frame_index, display)
            display_height, display_width = display.shape[:2]
            current: dict[str, Any] | None = None

            def on_mouse(event: int, x_value: int, y_value: int, _flags: int, _param: Any) -> None:
                nonlocal current
                if event != cv2.EVENT_LBUTTONDOWN:
                    return
                original_x = x_value / scale if scale else x_value
                original_y = y_value / scale if scale else y_value
                current = {
                    "frame_index": frame_index,
                    "visible": True,
                    "x": round(float(original_x), 2),
                    "y": round(float(original_y), 2),
                    "display_x": int(x_value),
                    "display_y": int(y_value),
                    "original_width": original_width,
                    "original_height": original_height,
                    "display_width": display_width,
                    "display_height": display_height,
                    "notes": "",
                }
                print(f"Selected frame {frame_index}: x={original_x:.1f}, y={original_y:.1f}")

            cv2.setMouseCallback(window_name, on_mouse)
            frames_shown += 1
            while True:
                shown = draw_label_overlay(display, current or {"frame_index": frame_index, "visible": False})
                cv2.setWindowTitle(window_name, f"Frame {frame_index} | click ball | u=undo s=save n=skip q=quit")
                cv2.imshow(window_name, shown)
                key = cv2.waitKey(30) & 0xFF
                if key == ord("u"):
                    current = None
                elif key == ord("s"):
                    if current is None:
                        warnings.append(f"Frame {frame_index} save requested without a selected ball; frame skipped.")
                        current = skipped_label(frame_index, original_width, original_height, display_width, display_height)
                    overlay_path = overlay_dir / f"manual_ball_label_frame_{frame_index:06d}.jpg"
                    current["overlay_path"] = str(overlay_path)
                    cv2.imwrite(str(overlay_path), draw_label_overlay(display, current))
                    labels.append(current)
                    break
                elif key == ord("n"):
                    labels.append(skipped_label(frame_index, original_width, original_height, display_width, display_height))
                    break
                elif key == ord("q"):
                    quit_requested = True
                    break
            if quit_requested:
                break
    finally:
        try:
            cv2.destroyWindow(window_name)
        except cv2.error:
            pass

    return {
        "labels": labels,
        "frames_shown": frames_shown,
        "quit_requested": quit_requested,
        "errors": errors,
        "warnings": warnings,
        "overlay_dir": str(overlay_dir),
    }


def load_stage_4_display_frame(stage_4_overlay_dir: Path | None, frame_index: int, fallback: Any) -> Any:
    """Use a Stage 4 overlay frame for display when it matches the sampled frame size."""
    if stage_4_overlay_dir is None:
        return fallback
    overlay_path = stage_4_overlay_dir / f"ball_candidates_frame_{frame_index:06d}.jpg"
    if not overlay_path.exists():
        return fallback
    overlay = cv2.imread(str(overlay_path))
    if overlay is None or overlay.shape[:2] != fallback.shape[:2]:
        return fallback
    return overlay


def skipped_label(
    frame_index: int,
    original_width: int,
    original_height: int,
    display_width: int,
    display_height: int,
) -> dict[str, Any]:
    """Return a skipped-frame label row."""
    return {
        "frame_index": frame_index,
        "visible": False,
        "x": None,
        "y": None,
        "display_x": None,
        "display_y": None,
        "original_width": original_width,
        "original_height": original_height,
        "display_width": display_width,
        "display_height": display_height,
        "notes": "ball not visible or frame skipped",
    }


def load_candidate_csv(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Load Stage 4 candidate CSV rows."""
    if not path.exists():
        return [], [f"Stage 4 candidate CSV not found: {path}"]
    rows: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                rows.append(
                    {
                        "frame_index": int(float(row["frame_index"])),
                        "x": float(row.get("original_center_x") or row.get("center_x") or 0),
                        "y": float(row.get("original_center_y") or row.get("center_y") or 0),
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
    return rows, []


def compare_candidates_to_labels(
    *,
    labels: list[dict[str, Any]],
    candidate_csv_path: Path,
    output_csv_path: Path,
) -> dict[str, Any]:
    """Compare manual labels to nearest Stage 4 candidates."""
    candidates, warnings = load_candidate_csv(candidate_csv_path)
    if warnings:
        return {
            "available": False,
            "comparison_csv_path": None,
            "summary": {},
            "rows": [],
            "warnings": warnings,
            "errors": [],
        }

    rows: list[dict[str, Any]] = []
    distances: list[float] = []
    by_frame: dict[int, list[dict[str, Any]]] = {}
    for candidate in candidates:
        by_frame.setdefault(candidate["frame_index"], []).append(candidate)

    for label in labels:
        if not label.get("visible"):
            continue
        frame_index = int(label["frame_index"])
        frame_candidates = by_frame.get(frame_index, [])
        nearest = None
        nearest_distance = None
        for candidate in frame_candidates:
            distance = math.dist((float(label["x"]), float(label["y"])), (candidate["x"], candidate["y"]))
            if nearest_distance is None or distance < nearest_distance:
                nearest_distance = distance
                nearest = candidate
        row = {
            "frame_index": frame_index,
            "label_x": label["x"],
            "label_y": label["y"],
            "nearest_candidate_x": nearest["x"] if nearest else None,
            "nearest_candidate_y": nearest["y"] if nearest else None,
            "nearest_distance_px": round(nearest_distance, 2) if nearest_distance is not None else None,
            "within_10_px": bool(nearest_distance is not None and nearest_distance <= 10),
            "within_25_px": bool(nearest_distance is not None and nearest_distance <= 25),
            "within_50_px": bool(nearest_distance is not None and nearest_distance <= 50),
            "within_100_px": bool(nearest_distance is not None and nearest_distance <= 100),
        }
        if nearest_distance is not None:
            distances.append(nearest_distance)
        rows.append(row)

    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "frame_index",
        "label_x",
        "label_y",
        "nearest_candidate_x",
        "nearest_candidate_y",
        "nearest_distance_px",
        "within_10_px",
        "within_25_px",
        "within_50_px",
        "within_100_px",
    ]
    with output_csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    summary = {
        "labeled_frames_compared": len(rows),
        "within_10_px": sum(1 for row in rows if row["within_10_px"]),
        "within_25_px": sum(1 for row in rows if row["within_25_px"]),
        "within_50_px": sum(1 for row in rows if row["within_50_px"]),
        "within_100_px": sum(1 for row in rows if row["within_100_px"]),
        "average_nearest_distance": round(sum(distances) / len(distances), 2) if distances else None,
        "median_nearest_distance": round(median(distances), 2) if distances else None,
    }
    return {
        "available": True,
        "comparison_csv_path": str(output_csv_path),
        "summary": summary,
        "rows": rows,
        "warnings": [],
        "errors": [],
    }
