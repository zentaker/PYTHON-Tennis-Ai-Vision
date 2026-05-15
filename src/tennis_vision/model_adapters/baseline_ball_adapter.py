"""Baseline local color/motion ball candidate adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tennis_vision.ball_candidate_improvement import generate_hybrid_candidates, load_labeled_frame_bundle
from tennis_vision.manual_event_position_resolver import confidence_from_score


MODEL_NAME = "baseline_current"


def check_availability(project_root: Path) -> dict[str, Any]:
    """Return availability for the existing local candidate generator."""
    return {
        "model_name": MODEL_NAME,
        "available": True,
        "status": "available",
        "reason": "Uses existing Stage 5.1 HSV/motion hybrid local candidate generator.",
    }


def prepare_context(
    *,
    video_path: Path,
    search_windows: dict[str, list[int]],
    calibration: dict[str, Any],
    resize_width: int = 1280,
    **_: Any,
) -> dict[str, Any]:
    """Precompute local candidates for all event search windows."""
    all_frames = sorted({frame for frames in search_windows.values() for frame in frames})
    bundles, errors = load_labeled_frame_bundle(
        video_path=video_path,
        frame_indices=all_frames,
        resize_width=resize_width,
        neighbor_offset=2,
    )
    court_polygon = calibration.get("court_polygon") or []
    candidates_by_frame: dict[int, list[dict[str, Any]]] = {}
    for frame_index, bundle in bundles.items():
        candidates_by_frame[frame_index] = generate_hybrid_candidates(bundle, court_polygon)
    return {
        "available": True,
        "errors": errors,
        "candidate_frames_processed": len(bundles),
        "candidate_count": sum(len(items) for items in candidates_by_frame.values()),
        "candidates_by_frame": candidates_by_frame,
    }


def resolve_event_position(
    video_path: Path,
    event: dict[str, Any],
    search_window: list[int],
    context: dict[str, Any],
) -> dict[str, Any]:
    """Resolve one event using the current local candidate scoring logic."""
    del video_path
    contact = int(event["contact_frame_estimate"])
    scored: list[dict[str, Any]] = []
    for frame in search_window:
        for candidate in context.get("candidates_by_frame", {}).get(frame, []):
            time_score = 1.0 - min(abs(frame - contact) / max(1.0, len(search_window)), 1.0)
            combined = 0.78 * float(candidate.get("score") or 0.0) + 0.22 * time_score
            scored.append({**candidate, "combined_score": round(combined, 4)})

    best = max(scored, key=lambda item: float(item.get("combined_score") or 0.0), default=None)
    if not best or float(best.get("combined_score") or 0.0) < 0.28:
        return _base_result(
            event,
            search_window,
            position_status="unresolved",
            debug_reason="No baseline local candidate exceeded the minimum combined score.",
        )

    score = float(best.get("combined_score") or 0.0)
    return {
        **_base_result(
            event,
            search_window,
            position_status="resolved",
            debug_reason=f"Resolved from Stage 5.1 hybrid candidate near manual event time; strategy={best.get('strategy', 'hybrid')}.",
        ),
        "resolved_frame": int(best["frame_index"]),
        "image_x": best.get("x", ""),
        "image_y": best.get("y", ""),
        "raw_score": round(score, 4),
        "confidence": confidence_from_score(score),
    }


def _base_result(event: dict[str, Any], search_window: list[int], *, position_status: str, debug_reason: str) -> dict[str, Any]:
    return {
        "model_name": MODEL_NAME,
        "event_id": event["event_id"],
        "event_type": event["event_type"],
        "shot_type": event.get("shot_type", ""),
        "manual_frame": event["contact_frame_estimate"],
        "search_start_frame": min(search_window) if search_window else "",
        "search_end_frame": max(search_window) if search_window else "",
        "resolved_frame": "",
        "image_x": "",
        "image_y": "",
        "raw_score": "",
        "confidence": "low",
        "position_status": position_status,
        "debug_reason": debug_reason,
    }
