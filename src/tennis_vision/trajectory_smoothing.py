"""Trajectory construction and smoothing helpers for Stage 6."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any


def read_improved_candidates(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Read Stage 5.1 improved candidate rows."""
    if not path.exists():
        return [], [f"Improved candidates CSV not found: {path}"]
    rows: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                rows.append(
                    {
                        "frame_index": int(float(row["frame_index"])),
                        "x": float(row["x"]),
                        "y": float(row["y"]),
                        "projected_x": _float_or_none(row.get("projected_x")),
                        "projected_y": _float_or_none(row.get("projected_y")),
                        "source_strategy": row.get("strategy") or row.get("source_strategy") or "unknown",
                        "score": _float_or_none(row.get("score")),
                        "distance_to_manual_label": _float_or_none(row.get("distance_to_manual_label")),
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
    rows.sort(key=lambda item: item["frame_index"])
    return rows, []


def read_projected_candidates(path: Path) -> tuple[dict[int, dict[str, float]], list[str]]:
    """Read projected candidate coordinates keyed by frame index."""
    if not path.exists():
        return {}, [f"Projected candidates CSV not found: {path}"]
    projected: dict[int, dict[str, float]] = {}
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                projected[int(float(row["frame_index"]))] = {
                    "projected_x": float(row["projected_x"]),
                    "projected_y": float(row["projected_y"]),
                }
            except (KeyError, TypeError, ValueError):
                continue
    return projected, []


def enrich_with_projected_candidates(
    candidates: list[dict[str, Any]],
    projected_by_frame: dict[int, dict[str, float]],
) -> list[dict[str, Any]]:
    """Fill missing projected coordinates from projected CSV rows."""
    enriched: list[dict[str, Any]] = []
    for candidate in candidates:
        row = dict(candidate)
        projected = projected_by_frame.get(int(row["frame_index"]))
        if projected and row.get("projected_x") is None:
            row["projected_x"] = projected["projected_x"]
            row["projected_y"] = projected["projected_y"]
        enriched.append(row)
    return enriched


def read_manual_labels(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Read visible manual labels for visual comparison."""
    if not path.exists():
        return [], [f"Manual labels CSV not found: {path}"]
    labels: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if str(row.get("visible", "")).lower() != "true":
                continue
            try:
                labels.append({"frame_index": int(float(row["frame_index"])), "x": float(row["x"]), "y": float(row["y"])})
            except (KeyError, TypeError, ValueError):
                continue
    return labels, []


def read_fps(stage_1_report: Path) -> float | None:
    """Read FPS from the Stage 1 report when available."""
    try:
        report = json.loads(stage_1_report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    fps = report.get("metadata", {}).get("fps")
    try:
        return float(fps) if fps else None
    except (TypeError, ValueError):
        return None


def build_raw_trajectory(candidates: list[dict[str, Any]], fps: float | None = None) -> list[dict[str, Any]]:
    """Build a trajectory table with deltas and speeds."""
    rows: list[dict[str, Any]] = []
    previous: dict[str, Any] | None = None
    for candidate in sorted(candidates, key=lambda item: item["frame_index"]):
        row = {
            "frame_index": candidate["frame_index"],
            "x": candidate["x"],
            "y": candidate["y"],
            "projected_x": candidate.get("projected_x"),
            "projected_y": candidate.get("projected_y"),
            "source_strategy": candidate.get("source_strategy"),
            "score": candidate.get("score"),
            "distance_to_manual_label": candidate.get("distance_to_manual_label"),
            "delta_frame": None,
            "delta_x": None,
            "delta_y": None,
            "image_velocity_px_per_frame": None,
            "image_speed_px_per_second": None,
            "projected_delta_x": None,
            "projected_delta_y": None,
            "projected_speed": None,
        }
        if previous is not None:
            delta_frame = row["frame_index"] - previous["frame_index"]
            delta_x = row["x"] - previous["x"]
            delta_y = row["y"] - previous["y"]
            velocity = math.hypot(delta_x, delta_y) / delta_frame if delta_frame else None
            row.update(
                {
                    "delta_frame": delta_frame,
                    "delta_x": round(delta_x, 3),
                    "delta_y": round(delta_y, 3),
                    "image_velocity_px_per_frame": round(velocity, 4) if velocity is not None else None,
                    "image_speed_px_per_second": round(velocity * fps, 3) if velocity is not None and fps else None,
                }
            )
            if row.get("projected_x") is not None and previous.get("projected_x") is not None:
                projected_delta_x = float(row["projected_x"]) - float(previous["projected_x"])
                projected_delta_y = float(row["projected_y"]) - float(previous["projected_y"])
                projected_speed = math.hypot(projected_delta_x, projected_delta_y) / delta_frame if delta_frame else None
                row.update(
                    {
                        "projected_delta_x": round(projected_delta_x, 3),
                        "projected_delta_y": round(projected_delta_y, 3),
                        "projected_speed": round(projected_speed, 4) if projected_speed is not None else None,
                    }
                )
        rows.append(row)
        previous = row
    return rows


def interpolate_trajectory(raw_rows: list[dict[str, Any]], enabled: bool = True) -> list[dict[str, Any]]:
    """Interpolate between known points for visualization only."""
    if not enabled or len(raw_rows) < 2:
        return [{**row, "is_interpolated": False} for row in raw_rows]
    expanded: list[dict[str, Any]] = []
    for current, next_row in zip(raw_rows, raw_rows[1:]):
        expanded.append({**current, "is_interpolated": False})
        gap = int(next_row["frame_index"] - current["frame_index"])
        if gap <= 1:
            continue
        for offset in range(1, gap):
            ratio = offset / gap
            expanded.append(_interpolated_row(current, next_row, ratio, current["frame_index"] + offset))
    expanded.append({**raw_rows[-1], "is_interpolated": False})
    return expanded


def _interpolated_row(current: dict[str, Any], next_row: dict[str, Any], ratio: float, frame_index: int) -> dict[str, Any]:
    row = {
        "frame_index": frame_index,
        "x": current["x"] + (next_row["x"] - current["x"]) * ratio,
        "y": current["y"] + (next_row["y"] - current["y"]) * ratio,
        "projected_x": None,
        "projected_y": None,
        "source_strategy": "interpolated",
        "score": None,
        "distance_to_manual_label": None,
        "is_interpolated": True,
    }
    if current.get("projected_x") is not None and next_row.get("projected_x") is not None:
        row["projected_x"] = float(current["projected_x"]) + (float(next_row["projected_x"]) - float(current["projected_x"])) * ratio
        row["projected_y"] = float(current["projected_y"]) + (float(next_row["projected_y"]) - float(current["projected_y"])) * ratio
    return row


def moving_average_smooth(rows: list[dict[str, Any]], window_size: int = 3) -> list[dict[str, Any]]:
    """Apply centered moving-average smoothing to image and projected coordinates."""
    if not rows:
        return []
    window_size = max(1, int(window_size))
    half_window = window_size // 2
    smoothed: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        start = max(0, index - half_window)
        end = min(len(rows), index + half_window + 1)
        window = rows[start:end]
        smooth_x = _mean([item.get("x") for item in window])
        smooth_y = _mean([item.get("y") for item in window])
        smooth_projected_x = _mean([item.get("projected_x") for item in window])
        smooth_projected_y = _mean([item.get("projected_y") for item in window])
        smoothed.append(
            {
                "frame_index": row["frame_index"],
                "raw_x": round(float(row["x"]), 3),
                "raw_y": round(float(row["y"]), 3),
                "smooth_x": round(smooth_x, 3) if smooth_x is not None else None,
                "smooth_y": round(smooth_y, 3) if smooth_y is not None else None,
                "raw_projected_x": _round_or_none(row.get("projected_x")),
                "raw_projected_y": _round_or_none(row.get("projected_y")),
                "smooth_projected_x": round(smooth_projected_x, 3) if smooth_projected_x is not None else None,
                "smooth_projected_y": round(smooth_projected_y, 3) if smooth_projected_y is not None else None,
                "is_interpolated": bool(row.get("is_interpolated")),
                "smoothing_method": f"moving_average_{window_size}",
            }
        )
    return smoothed


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> Path:
    """Write rows to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    return path


def _mean(values: list[Any]) -> float | None:
    numbers = [float(value) for value in values if value is not None and value != ""]
    if not numbers:
        return None
    return sum(numbers) / len(numbers)


def _float_or_none(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _round_or_none(value: Any) -> float | None:
    number = _float_or_none(value)
    return round(number, 3) if number is not None else None
