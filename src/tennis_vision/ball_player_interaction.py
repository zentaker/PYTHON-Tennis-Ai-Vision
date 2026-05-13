"""Ball-player association and interaction hypotheses for Stage 7."""

from __future__ import annotations

import csv
import math
from collections import Counter
from pathlib import Path
from typing import Any


def read_stage_6_events(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Read Stage 6 event hypotheses."""
    if not path.exists():
        return [], [f"Stage 6 events CSV not found: {path}"]
    events: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                events.append({"frame_index": int(float(row["frame_index"])), "event_type": row.get("event_type", "")})
            except (KeyError, TypeError, ValueError):
                continue
    return events, []


def associate_ball_to_players(
    *,
    ball_rows: list[dict[str, Any]],
    player_tracks: list[dict[str, Any]],
    stage_6_events: list[dict[str, Any]],
    frame_tolerance: int = 5,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    """Associate each non-interpolated ball point to the nearest player track."""
    associations: list[dict[str, Any]] = []
    event_by_frame = {int(event["frame_index"]): event["event_type"] for event in stage_6_events}
    non_interpolated = [row for row in ball_rows if not row.get("is_interpolated")]
    for ball in non_interpolated:
        candidates = [
            track
            for track in player_tracks
            if abs(int(track["frame_index"]) - int(ball["frame_index"])) <= frame_tolerance
        ]
        nearest = min(
            candidates,
            key=lambda track: math.dist((ball["x"], ball["y"]), (track["bbox_center_x"], track["bbox_center_y"])),
            default=None,
        )
        if nearest is None:
            associations.append(_empty_association(ball))
            continue
        image_distance = math.dist((ball["x"], ball["y"]), (nearest["bbox_center_x"], nearest["bbox_center_y"]))
        edge_distance = bbox_edge_distance(ball["x"], ball["y"], nearest)
        near_bbox = edge_distance <= 180
        projected_distance = None
        if ball.get("projected_x") is not None and nearest.get("projected_x") not in (None, ""):
            projected_distance = math.dist(
                (float(ball["projected_x"]), float(ball["projected_y"])),
                (float(nearest["projected_x"]), float(nearest["projected_y"])),
            )
        interaction_score = score_interaction(image_distance, edge_distance, projected_distance)
        related_event = event_by_frame.get(int(ball["frame_index"]), "")
        reason = "nearest player within frame tolerance"
        if near_bbox:
            reason = "ball is inside or near expanded player bbox"
        associations.append(
            {
                "frame_index": int(ball["frame_index"]),
                "ball_x": round(float(ball["x"]), 3),
                "ball_y": round(float(ball["y"]), 3),
                "ball_projected_x": _round_or_none(ball.get("projected_x")),
                "ball_projected_y": _round_or_none(ball.get("projected_y")),
                "nearest_track_id": nearest["track_id"],
                "nearest_player_center_x": nearest["bbox_center_x"],
                "nearest_player_center_y": nearest["bbox_center_y"],
                "image_distance_px": round(image_distance, 3),
                "projected_distance": round(projected_distance, 3) if projected_distance is not None else None,
                "near_player_bbox": near_bbox,
                "interaction_score": interaction_score,
                "interaction_reason": reason,
                "related_stage_6_event": related_event,
            }
        )

    interactions = build_interactions(associations)
    return associations, interactions, dict(Counter(item["interaction_type"] for item in interactions))


def bbox_edge_distance(x_value: float, y_value: float, track: dict[str, Any]) -> float:
    """Distance from point to bbox edge; zero if inside."""
    dx = max(float(track["bbox_x1"]) - x_value, 0.0, x_value - float(track["bbox_x2"]))
    dy = max(float(track["bbox_y1"]) - y_value, 0.0, y_value - float(track["bbox_y2"]))
    return math.hypot(dx, dy)


def score_interaction(image_distance: float, edge_distance: float, projected_distance: float | None) -> float:
    """Score ball-player proximity as a hypothesis strength."""
    center_score = max(0.0, 1.0 - image_distance / 900.0)
    edge_score = max(0.0, 1.0 - edge_distance / 240.0)
    projected_score = 0.0 if projected_distance is None else max(0.0, 1.0 - projected_distance / 180.0)
    return round(min(1.0, 0.45 * center_score + 0.40 * edge_score + 0.15 * projected_score), 4)


def build_interactions(associations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create hypothesis rows from ball-player association distances and Stage 6 events."""
    interactions: list[dict[str, Any]] = []
    previous_distance = None
    for association in associations:
        if not association.get("nearest_track_id"):
            interactions.append(_interaction(association, "insufficient_data", 0.1, "No player track was close enough in time."))
            previous_distance = None
            continue
        distance = association.get("image_distance_px")
        related_event = association.get("related_stage_6_event") or ""
        if association.get("near_player_bbox") or (distance is not None and distance <= 450):
            interactions.append(_interaction(association, "ball_near_player", association["interaction_score"], "Ball is near the expanded player bbox or close to player center."))
        if related_event in {"possible_hit", "direction_change", "speed_drop", "speed_spike"} and distance is not None and distance <= 650:
            interactions.append(_interaction(association, "possible_hit_window", max(association["interaction_score"], 0.45), f"Stage 6 event `{related_event}` occurs near a player."))
        if previous_distance is not None and distance is not None:
            if distance < previous_distance - 80:
                interactions.append(_interaction(association, "ball_approaching_player", 0.35, "Ball-player distance decreased between trajectory points."))
            elif distance > previous_distance + 80:
                interactions.append(_interaction(association, "ball_leaving_player", 0.35, "Ball-player distance increased between trajectory points."))
        previous_distance = distance
    return interactions


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> Path:
    """Write rows to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    return path


def _empty_association(ball: dict[str, Any]) -> dict[str, Any]:
    return {
        "frame_index": int(ball["frame_index"]),
        "ball_x": round(float(ball["x"]), 3),
        "ball_y": round(float(ball["y"]), 3),
        "ball_projected_x": _round_or_none(ball.get("projected_x")),
        "ball_projected_y": _round_or_none(ball.get("projected_y")),
        "nearest_track_id": "",
        "nearest_player_center_x": "",
        "nearest_player_center_y": "",
        "image_distance_px": None,
        "projected_distance": None,
        "near_player_bbox": False,
        "interaction_score": 0.0,
        "interaction_reason": "No player track within frame tolerance.",
        "related_stage_6_event": "",
    }


def _interaction(association: dict[str, Any], interaction_type: str, score: float, reason: str) -> dict[str, Any]:
    return {
        "frame_index": association["frame_index"],
        "interaction_type": interaction_type,
        "confidence_like_score": round(max(0.0, min(float(score), 1.0)), 3),
        "reason": reason,
        "nearest_track_id": association.get("nearest_track_id"),
        "image_distance_px": association.get("image_distance_px"),
        "projected_distance": association.get("projected_distance"),
        "related_stage_6_event": association.get("related_stage_6_event"),
    }


def _round_or_none(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return round(float(value), 3)
    except (TypeError, ValueError):
        return None
