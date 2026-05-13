"""Lightweight clothing-color identity profiles for Stage 7.1."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import cv2
import numpy as np


def build_identity_profiles(
    *,
    video_path: Path,
    filtered_rows: list[dict[str, Any]],
    output_path: Path,
    max_crops_per_player: int = 8,
) -> tuple[dict[str, Any], list[str]]:
    """Build compact appearance profiles from kept player crops."""
    warnings: list[str] = []
    kept = [row for row in filtered_rows if row.get("keep")]
    if not kept:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("{}", encoding="utf-8")
        return {}, ["No kept player rows were available for identity profiles."]
    if not video_path.exists():
        return {}, [f"Video file not found for identity profiles: {video_path}"]

    capture = cv2.VideoCapture(str(video_path))
    profiles: dict[str, Any] = {}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in kept:
        grouped[row["filtered_track_id"]].append(row)
    try:
        for player_id, rows in grouped.items():
            histograms: list[list[float]] = []
            dominant_colors: list[str] = []
            upper_colors: list[str] = []
            lower_colors: list[str] = []
            for row in rows[:max_crops_per_player]:
                capture.set(cv2.CAP_PROP_POS_FRAMES, int(row["frame_index"]))
                ok, frame = capture.read()
                if not ok:
                    continue
                crop = crop_player(frame, row)
                if crop is None:
                    continue
                histograms.append(color_histogram(crop))
                dominant_colors.append(dominant_color_hex(crop))
                height = crop.shape[0]
                upper_colors.append(dominant_color_hex(crop[: max(1, height // 2), :]))
                lower_colors.append(dominant_color_hex(crop[max(1, height // 2) :, :]))
            if not histograms:
                warnings.append(f"No valid crops were available for {player_id}.")
                continue
            average_hist = np.mean(np.array(histograms, dtype=np.float32), axis=0).tolist()
            top_colors = [color for color, _count in Counter(dominant_colors).most_common(3)]
            top_upper = [color for color, _count in Counter(upper_colors).most_common(2)]
            top_lower = [color for color, _count in Counter(lower_colors).most_common(2)]
            profiles[player_id] = {
                "source_track_ids": sorted({row["original_track_id"] for row in rows}),
                "frames_seen": len(rows),
                "histogram": [round(float(value), 6) for value in average_hist],
                "dominant_colors": top_colors,
                "upper_body_colors": top_upper,
                "lower_body_colors": top_lower,
                "dominant_colors_summary": f"upper {', '.join(top_upper) or 'unknown'}; lower {', '.join(top_lower) or 'unknown'}",
            }
    finally:
        capture.release()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(profiles, indent=2, sort_keys=True), encoding="utf-8")
    return profiles, warnings


def compare_identity_profiles(profiles: dict[str, Any]) -> list[dict[str, Any]]:
    """Compare player appearance profiles with a simple histogram distance."""
    rows: list[dict[str, Any]] = []
    player_ids = sorted(profiles)
    for index, first in enumerate(player_ids):
        for second in player_ids[index + 1 :]:
            distance = histogram_distance(profiles[first].get("histogram", []), profiles[second].get("histogram", []))
            rows.append(
                {
                    "player_id_a": first,
                    "player_id_b": second,
                    "appearance_distance": round(distance, 4) if distance is not None else "",
                    "likely_same_identity": bool(distance is not None and distance < 0.18),
                    "notes": "Clothing-color heuristic only; not biometric re-identification.",
                }
            )
    return rows


def crop_player(frame: Any, row: dict[str, Any]) -> Any | None:
    """Crop a player bbox from a frame."""
    height, width = frame.shape[:2]
    x1 = max(0, int(round(float(row["bbox_x1"]))))
    y1 = max(0, int(round(float(row["bbox_y1"]))))
    x2 = min(width, int(round(float(row["bbox_x2"]))))
    y2 = min(height, int(round(float(row["bbox_y2"]))))
    if x2 <= x1 or y2 <= y1:
        return None
    return frame[y1:y2, x1:x2]


def color_histogram(crop: Any) -> list[float]:
    """Compute compact HSV histogram."""
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [12, 8], [0, 180, 0, 256])
    hist = cv2.normalize(hist, hist).flatten()
    return [float(value) for value in hist]


def histogram_distance(first: list[float], second: list[float]) -> float | None:
    """Return Euclidean distance between normalized histograms."""
    if not first or not second or len(first) != len(second):
        return None
    return math.sqrt(sum((float(a) - float(b)) ** 2 for a, b in zip(first, second)))


def dominant_color_hex(crop: Any) -> str:
    """Approximate dominant color as a hex string."""
    if crop is None or crop.size == 0:
        return "unknown"
    small = cv2.resize(crop, (1, 1), interpolation=cv2.INTER_AREA)
    b, g, r = [int(value) for value in small[0, 0]]
    return f"#{r:02x}{g:02x}{b:02x}"


def save_identity_preview(
    *,
    video_path: Path,
    filtered_rows: list[dict[str, Any]],
    output_path: Path,
) -> str | None:
    """Save representative crops for each selected identity."""
    kept = [row for row in filtered_rows if row.get("keep")]
    if not kept or not video_path.exists():
        return None
    by_player: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in kept:
        by_player[row["filtered_track_id"]].append(row)
    capture = cv2.VideoCapture(str(video_path))
    crops: list[Any] = []
    try:
        for player_id, rows in sorted(by_player.items()):
            row = rows[0]
            capture.set(cv2.CAP_PROP_POS_FRAMES, int(row["frame_index"]))
            ok, frame = capture.read()
            if not ok:
                continue
            crop = crop_player(frame, row)
            if crop is None:
                continue
            crop = cv2.resize(crop, (180, 360), interpolation=cv2.INTER_AREA)
            cv2.putText(crop, player_id, (12, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            crops.append(crop)
    finally:
        capture.release()
    if not crops:
        return None
    preview = np.hstack(crops)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if cv2.imwrite(str(output_path), preview):
        return str(output_path)
    return None


def write_matches_csv(path: Path, rows: list[dict[str, Any]]) -> Path:
    """Write identity comparison rows."""
    import csv

    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["player_id_a", "player_id_b", "appearance_distance", "likely_same_identity", "notes"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    return path
