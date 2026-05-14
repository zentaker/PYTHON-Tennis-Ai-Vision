"""Schema constants and writers for Stage 12 replay data."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


SCHEMA_NAME = "tennis_ai_vision.synthetic_rally_replay"
DEFAULT_SCHEMA_VERSION = "0.1.0"


def build_visual_layers() -> list[dict[str, Any]]:
    """Return future renderer visual layer definitions."""
    return [
        {
            "layer_id": "court_layer",
            "purpose": "Draw normalized doubles court boundary and optional zone grid.",
            "required_data": ["court_model"],
            "optional_data": ["court_zone_model"],
            "supported_now": True,
            "notes": "Uses doubles court outer boundary as the current calibration baseline.",
        },
        {
            "layer_id": "player_layer",
            "purpose": "Render approximate player identity markers and side states.",
            "required_data": ["players"],
            "optional_data": ["side_states"],
            "supported_now": True,
            "notes": "Player identity is clothing/track heuristic, not biometric re-identification.",
        },
        {
            "layer_id": "ball_layer",
            "purpose": "Render ball positions at replay keyframes.",
            "required_data": ["ball_trajectory.replay_keyframes"],
            "optional_data": ["confidence_like_score"],
            "supported_now": True,
            "notes": "No verified 3D ball height yet.",
        },
        {
            "layer_id": "trajectory_layer",
            "purpose": "Draw trajectory sequence through projected points.",
            "required_data": ["projected_trajectory"],
            "optional_data": ["is_interpolated"],
            "supported_now": True,
            "notes": "Interpolated points should be dashed or visually distinct.",
        },
        {
            "layer_id": "event_marker_layer",
            "purpose": "Display possible_* event markers.",
            "required_data": ["event_timeline"],
            "optional_data": ["player_id", "validation_status"],
            "supported_now": True,
            "notes": "Use question markers for hypotheses.",
        },
        {
            "layer_id": "tactical_zone_layer",
            "purpose": "Display tactical zone assignments and depth/lane context.",
            "required_data": ["tactical_metrics"],
            "optional_data": ["zone_confidence"],
            "supported_now": True,
            "notes": "Not official line calling.",
        },
        {
            "layer_id": "timeline_layer",
            "purpose": "Show event sequence along frame/time axis.",
            "required_data": ["event_timeline", "rally_segments"],
            "optional_data": ["confidence_like_score"],
            "supported_now": True,
            "notes": "Useful for 2D replay controls.",
        },
        {
            "layer_id": "confidence_overlay_layer",
            "purpose": "Expose uncertainty and confidence labels.",
            "required_data": ["confidence"],
            "optional_data": ["limitations"],
            "supported_now": True,
            "notes": "Should remain visible in early renderers.",
        },
    ]


def build_renderer_hints() -> dict[str, Any]:
    """Return deterministic renderer policy hints."""
    return {
        "recommended_first_renderer": "2d_tactical_replay",
        "preferred_initial_rendering": "deterministic_code_generated",
        "avoid_initial_generation_ai": True,
        "future_generation_ai_layer": "optional_later",
        "suggested_animation_fps": 30,
        "suggested_output_duration_seconds": None,
        "interpolation_policy": "Use interpolated points for visualization only; mark them clearly.",
        "uncertainty_display_policy": [
            "show dashed lines for interpolated points",
            "show possible events with question markers",
            "show confidence labels",
            "avoid hiding uncertainty",
        ],
    }


def write_json(path: Path, data: dict[str, Any] | list[dict[str, Any]]) -> Path:
    """Write JSON output."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> Path:
    """Write CSV rows."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    return path
