"""Visual style constants for deterministic 2D replay rendering."""

from __future__ import annotations

from typing import Any


CANVAS_WIDTH = 900
CANVAS_HEIGHT = 1200
COURT_MARGIN_X = 170
COURT_MARGIN_TOP = 80
TIMELINE_HEIGHT = 150

STYLE: dict[str, Any] = {
    "canvas_size": (CANVAS_WIDTH, CANVAS_HEIGHT),
    "court_margin_x": COURT_MARGIN_X,
    "court_margin_top": COURT_MARGIN_TOP,
    "timeline_height": TIMELINE_HEIGHT,
    "background": (25, 45, 38),
    "court_fill": (40, 95, 74),
    "court_line": (235, 238, 229),
    "court_zone_line": (90, 140, 115),
    "text": (245, 245, 240),
    "muted_text": (190, 205, 195),
    "ball": (0, 242, 255),
    "ball_interpolated": (80, 210, 220),
    "ball_trail": (50, 210, 245),
    "player_a": (255, 120, 70),
    "player_b": (80, 170, 255),
    "unknown_player": (190, 190, 190),
    "event_default": (210, 120, 255),
    "event_hit": (70, 120, 255),
    "event_bounce": (120, 255, 140),
    "timeline_axis": (210, 220, 210),
    "timeline_current": (0, 242, 255),
    "out_of_bounds": (120, 120, 120),
    "font": 0,
    "font_scale": 0.55,
    "small_font_scale": 0.45,
    "line_thickness": 2,
}
