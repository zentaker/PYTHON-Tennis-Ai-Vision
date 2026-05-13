"""Court-aware player filtering for Stage 7.1."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from tennis_vision.court_projection import point_inside_or_near_polygon


def read_player_tracks(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Read Stage 7 player track rows."""
    if not path.exists():
        return [], [f"Player tracks CSV not found: {path}"]
    rows: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                x1 = float(row["bbox_x1"])
                y1 = float(row["bbox_y1"])
                x2 = float(row["bbox_x2"])
                y2 = float(row["bbox_y2"])
                rows.append(
                    {
                        "frame_index": int(float(row["frame_index"])),
                        "original_track_id": row["track_id"],
                        "bbox_x1": x1,
                        "bbox_y1": y1,
                        "bbox_x2": x2,
                        "bbox_y2": y2,
                        "bbox_center_x": float(row["bbox_center_x"]),
                        "bbox_center_y": float(row["bbox_center_y"]),
                        "bottom_center_x": (x1 + x2) / 2,
                        "bottom_center_y": y2,
                        "confidence": _float_or_none(row.get("confidence")) or 0.0,
                        "player_side_guess": row.get("player_side_guess") or "unknown",
                        "projected_x": _float_or_none(row.get("projected_x")),
                        "projected_y": _float_or_none(row.get("projected_y")),
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
    return rows, []


def score_track_rows(
    rows: list[dict[str, Any]],
    court_polygon: list[list[float]],
    *,
    court_margin: float,
    min_track_frames: int,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Score detections and aggregate track-level quality."""
    counts = defaultdict(int)
    for row in rows:
        counts[row["original_track_id"]] += 1
    scored: list[dict[str, Any]] = []
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        width = max(1.0, row["bbox_x2"] - row["bbox_x1"])
        height = max(1.0, row["bbox_y2"] - row["bbox_y1"])
        area_ratio = (width * height) / (3840 * 2160)
        court_region_score = court_score(row["bottom_center_x"], row["bottom_center_y"], court_polygon, court_margin)
        size_score = max(0.0, min(1.0, area_ratio / 0.008))
        if height < 80:
            size_score *= 0.45
        duration_score = min(1.0, counts[row["original_track_id"]] / max(float(min_track_frames), 1.0))
        confidence_score = min(1.0, row["confidence"] / 0.75)
        final_score = round(0.38 * court_region_score + 0.24 * confidence_score + 0.18 * size_score + 0.20 * duration_score, 4)
        scored_row = {
            **row,
            "court_region_score": round(court_region_score, 4),
            "size_score": round(size_score, 4),
            "duration_score": round(duration_score, 4),
            "final_player_score": final_score,
            "keep": False,
            "filtered_track_id": "",
            "rejection_reason": "not_selected_as_main_player",
        }
        grouped[row["original_track_id"]].append(scored_row)
        scored.append(scored_row)

    summaries: dict[str, dict[str, Any]] = {}
    for track_id, track_rows in grouped.items():
        summaries[track_id] = {
            "track_id": track_id,
            "frames_seen": len(track_rows),
            "average_confidence": round(mean(row["confidence"] for row in track_rows), 4),
            "average_court_score": round(mean(row["court_region_score"] for row in track_rows), 4),
            "average_size_score": round(mean(row["size_score"] for row in track_rows), 4),
            "average_player_score": round(mean(row["final_player_score"] for row in track_rows), 4),
            "initial_side_state": side_state(track_rows[0]),
        }
    return scored, summaries


def select_main_tracks(track_summaries: dict[str, dict[str, Any]], max_players: int) -> list[str]:
    """Select likely main-player source tracks."""
    ranked = sorted(
        track_summaries.values(),
        key=lambda item: (
            item["average_player_score"],
            item["frames_seen"],
            item["average_confidence"],
        ),
        reverse=True,
    )
    return [item["track_id"] for item in ranked[:max_players]]


def apply_player_identities(scored_rows: list[dict[str, Any]], selected_tracks: list[str]) -> list[dict[str, Any]]:
    """Assign stable player_a/player_b identities to selected source tracks."""
    identity_map = {track_id: f"player_{chr(ord('a') + index)}" for index, track_id in enumerate(selected_tracks)}
    output: list[dict[str, Any]] = []
    for row in scored_rows:
        track_id = row["original_track_id"]
        item = dict(row)
        if track_id in identity_map:
            item["keep"] = True
            item["filtered_track_id"] = identity_map[track_id]
            item["rejection_reason"] = ""
        elif row["court_region_score"] < 0.25:
            item["rejection_reason"] = "far_outside_court_region"
        elif row["size_score"] < 0.08:
            item["rejection_reason"] = "small_background_detection"
        else:
            item["rejection_reason"] = "lower_ranked_player_candidate"
        output.append(item)
    return output


def build_main_players(
    selected_tracks: list[str],
    track_summaries: dict[str, dict[str, Any]],
    identity_profiles: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build main player summary rows."""
    rows: list[dict[str, Any]] = []
    for index, source_track in enumerate(selected_tracks):
        player_id = f"player_{chr(ord('a') + index)}"
        summary = track_summaries[source_track]
        profile = identity_profiles.get(player_id, {})
        rows.append(
            {
                "player_id": player_id,
                "source_track_ids": source_track,
                "frames_seen": summary["frames_seen"],
                "dominant_colors_summary": profile.get("dominant_colors_summary", "Not available"),
                "average_confidence": summary["average_confidence"],
                "average_court_score": summary["average_court_score"],
                "initial_side_state": summary["initial_side_state"],
                "notes": "Identity is appearance/track based; side is a mutable state.",
            }
        )
    return rows


def build_side_states(filtered_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build side-state rows for kept player identities."""
    rows: list[dict[str, Any]] = []
    for row in filtered_rows:
        if not row["keep"]:
            continue
        rows.append(
            {
                "frame_index": row["frame_index"],
                "player_id": row["filtered_track_id"],
                "side_state": side_state(row),
                "x": round(row["bbox_center_x"], 3),
                "y": round(row["bbox_center_y"], 3),
                "projected_x": row.get("projected_x"),
                "projected_y": row.get("projected_y"),
                "source_track_id": row["original_track_id"],
            }
        )
    return rows


def court_score(x_value: float, y_value: float, court_polygon: list[list[float]], margin: float) -> float:
    """Score bottom-center position relative to the calibrated court polygon."""
    check = point_inside_or_near_polygon(x_value, y_value, court_polygon, margin_px=margin)
    if not check.get("available"):
        return 0.5
    distance = check.get("signed_distance")
    if distance is None:
        return 0.5
    if distance >= 0:
        return 1.0
    if distance >= -margin * 0.35:
        return 0.75
    if distance >= -margin:
        return 0.45
    return 0.05


def side_state(row: dict[str, Any]) -> str:
    """Estimate mutable court side state; this is not identity."""
    projected_y = row.get("projected_y")
    if projected_y not in (None, ""):
        try:
            return "near_side" if float(projected_y) > 390 else "far_side"
        except (TypeError, ValueError):
            pass
    return "near_side" if float(row.get("bottom_center_y", row.get("bbox_center_y", 0))) > 1080 else "far_side"


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> Path:
    """Write rows to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    return path


def _float_or_none(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
