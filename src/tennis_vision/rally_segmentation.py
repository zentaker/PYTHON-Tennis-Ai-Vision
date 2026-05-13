"""Rally segmentation helpers for Stage 8."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def build_rally_segments(
    trajectory_rows: list[dict[str, Any]],
    timeline_events: list[dict[str, Any]],
    *,
    fps: float | None = None,
    gap_threshold_frames: int = 60,
) -> list[dict[str, Any]]:
    """Build conservative rally segments from trajectory anchors."""
    anchors = [row for row in sorted(trajectory_rows, key=lambda item: item["frame_index"]) if not row.get("is_interpolated")]
    if not anchors:
        return []

    segments: list[tuple[int, int]] = []
    start = anchors[0]["frame_index"]
    previous = anchors[0]["frame_index"]
    for row in anchors[1:]:
        frame_index = row["frame_index"]
        if frame_index - previous > gap_threshold_frames:
            segments.append((start, previous))
            start = frame_index
        previous = frame_index
    segments.append((start, previous))

    rows: list[dict[str, Any]] = []
    for index, (start_frame, end_frame) in enumerate(segments, start=1):
        segment_events = [event for event in timeline_events if start_frame <= int(event["frame_index"]) <= end_frame]
        possible_hit_count = sum(1 for event in segment_events if event.get("event_type") == "possible_hit")
        possible_bounce_count = sum(1 for event in segment_events if event.get("event_type") == "possible_bounce")
        players = sorted({str(event.get("player_id")) for event in segment_events if event.get("player_id")})
        duration = ((end_frame - start_frame) / fps) if fps else None
        confidence = min(1.0, 0.35 + len(segment_events) * 0.04 + possible_hit_count * 0.08)
        rows.append(
            {
                "rally_id": f"rally_{index:03d}",
                "start_frame": start_frame,
                "end_frame": end_frame,
                "start_time_seconds": round(start_frame / fps, 3) if fps else None,
                "end_time_seconds": round(end_frame / fps, 3) if fps else None,
                "duration_seconds": round(duration, 3) if duration is not None else None,
                "event_count": len(segment_events),
                "possible_hit_count": possible_hit_count,
                "possible_bounce_count": possible_bounce_count,
                "players_involved": ",".join(players) if players else "unknown",
                "confidence_like_score": round(confidence, 3),
                "segmentation_reason": "First prototype segment from first to last high-confidence trajectory anchor.",
            }
        )
    return rows


def write_rally_segments_csv(path: Path, rows: list[dict[str, Any]]) -> Path:
    """Write rally segment rows to CSV."""
    fields = [
        "rally_id",
        "start_frame",
        "end_frame",
        "start_time_seconds",
        "end_time_seconds",
        "duration_seconds",
        "event_count",
        "possible_hit_count",
        "possible_bounce_count",
        "players_involved",
        "confidence_like_score",
        "segmentation_reason",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    return path
