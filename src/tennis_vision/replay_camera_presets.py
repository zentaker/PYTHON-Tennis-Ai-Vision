"""Deterministic camera profile presets for future replay renderers."""

from __future__ import annotations

from typing import Any


def build_camera_profiles() -> list[dict[str, Any]]:
    """Return renderer camera presets for the replay schema."""
    return [
        {
            "camera_id": "top_tactical",
            "name": "Top Tactical",
            "purpose": "Overhead tactical replay from normalized court coordinates.",
            "view_type": "2d_top_down",
            "coordinate_space": "normalized_court",
            "supported_now": True,
            "renderer_notes": "Best first renderer because Stage 3 homography and Stage 9.1 zones use normalized court coordinates.",
        },
        {
            "camera_id": "sideline_low",
            "name": "Sideline Low",
            "purpose": "Future side-view ball flight interpretation.",
            "view_type": "synthetic_side_view",
            "coordinate_space": "normalized_court_plus_estimated_height",
            "supported_now": False,
            "renderer_notes": "Requires ball height estimation that does not exist yet.",
        },
        {
            "camera_id": "baseline_near",
            "name": "Near Baseline",
            "purpose": "Future baseline replay from near player perspective.",
            "view_type": "synthetic_baseline",
            "coordinate_space": "normalized_court",
            "supported_now": False,
            "renderer_notes": "Renderer hint only; no true near-baseline camera exists.",
        },
        {
            "camera_id": "baseline_far",
            "name": "Far Baseline",
            "purpose": "Future baseline replay from far player perspective.",
            "view_type": "synthetic_baseline",
            "coordinate_space": "normalized_court",
            "supported_now": False,
            "renderer_notes": "Renderer hint only; player identity is independent of side state.",
        },
        {
            "camera_id": "audience_side",
            "name": "Audience Side",
            "purpose": "Future stylized side/audience tactical replay.",
            "view_type": "synthetic_oblique",
            "coordinate_space": "normalized_court",
            "supported_now": False,
            "renderer_notes": "Requires a renderer to map normalized court data into an oblique scene.",
        },
        {
            "camera_id": "mini_court",
            "name": "Mini Court",
            "purpose": "Compact tactical visualization for reports and UI cards.",
            "view_type": "2d_mini_court",
            "coordinate_space": "normalized_court",
            "supported_now": True,
            "renderer_notes": "Can consume replay keyframes and tactical zones immediately.",
        },
    ]
