"""Deterministic 2D tactical replay renderer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from tennis_vision.replay_visual_styles import STYLE


def load_replay_schema(path: Path) -> tuple[dict[str, Any], list[str], list[str]]:
    """Load the Stage 12 replay schema."""
    if not path.exists():
        return {}, [], [f"Replay schema missing: {path}"]
    try:
        return json.loads(path.read_text(encoding="utf-8")), [], []
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [], [f"Could not read replay schema {path}: {exc}"]


def extract_court_model(schema: dict[str, Any]) -> dict[str, Any]:
    """Extract court model data from the replay schema."""
    return schema.get("court_model", {})


def extract_replay_keyframes(schema: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract replay keyframes from the replay schema."""
    return list(schema.get("ball_trajectory", {}).get("replay_keyframes", []))


def extract_players(schema: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract player records from the replay schema."""
    return list(schema.get("players", []))


def extract_events(schema: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract replay event records from the replay schema."""
    return list(schema.get("event_timeline", []))


def create_court_canvas(court_model: dict[str, Any]) -> tuple[np.ndarray, dict[str, float]]:
    """Create a base canvas and court-to-canvas transform."""
    width, height = STYLE["canvas_size"]
    canvas = np.full((height, width, 3), STYLE["background"], dtype=np.uint8)
    court_width = float(court_model.get("normalized_court_width") or 360.0)
    court_height = float(court_model.get("normalized_court_height") or 780.0)
    available_w = width - (2 * STYLE["court_margin_x"])
    available_h = height - STYLE["timeline_height"] - STYLE["court_margin_top"] - 70
    scale = min(available_w / court_width, available_h / court_height)
    court_px_w = court_width * scale
    court_px_h = court_height * scale
    origin_x = (width - court_px_w) / 2
    origin_y = STYLE["court_margin_top"]
    transform = {
        "origin_x": origin_x,
        "origin_y": origin_y,
        "scale": scale,
        "court_width": court_width,
        "court_height": court_height,
        "court_px_w": court_px_w,
        "court_px_h": court_px_h,
    }
    return canvas, transform


def map_court_to_canvas(x: Any, y: Any, transform: dict[str, float], *, clamp: bool = True) -> tuple[int, int] | None:
    """Map normalized court coordinates to canvas pixels."""
    try:
        court_x = float(x)
        court_y = float(y)
    except (TypeError, ValueError):
        return None
    if clamp:
        court_x = max(0.0, min(transform["court_width"], court_x))
        court_y = max(0.0, min(transform["court_height"], court_y))
    px = int(round(transform["origin_x"] + court_x * transform["scale"]))
    py = int(round(transform["origin_y"] + court_y * transform["scale"]))
    return px, py


def render_static_court(canvas: np.ndarray, court_model: dict[str, Any], transform: dict[str, float]) -> np.ndarray:
    """Render court boundary and simple zone grid."""
    top_left = (int(transform["origin_x"]), int(transform["origin_y"]))
    bottom_right = (
        int(transform["origin_x"] + transform["court_px_w"]),
        int(transform["origin_y"] + transform["court_px_h"]),
    )
    cv2.rectangle(canvas, top_left, bottom_right, STYLE["court_fill"], thickness=-1)
    cv2.rectangle(canvas, top_left, bottom_right, STYLE["court_line"], thickness=2)

    for fraction in (1 / 3, 2 / 3):
        x = int(transform["origin_x"] + transform["court_px_w"] * fraction)
        cv2.line(canvas, (x, top_left[1]), (x, bottom_right[1]), STYLE["court_zone_line"], 1)
    for fraction in (1 / 3, 2 / 3, 0.5):
        y = int(transform["origin_y"] + transform["court_px_h"] * fraction)
        color = STYLE["court_line"] if fraction == 0.5 else STYLE["court_zone_line"]
        cv2.line(canvas, (top_left[0], y), (bottom_right[0], y), color, 1)

    cv2.putText(canvas, "2D tactical replay - normalized doubles court", (30, 38), STYLE["font"], 0.72, STYLE["text"], 2, cv2.LINE_AA)
    cv2.putText(canvas, "possible_* events are hypotheses", (30, 64), STYLE["font"], 0.5, STYLE["muted_text"], 1, cv2.LINE_AA)
    return canvas


def render_ball_trajectory(canvas: np.ndarray, points: list[dict[str, Any]], transform: dict[str, float], current_index: int) -> np.ndarray:
    """Render trajectory trail and current ball."""
    visible = points[: current_index + 1]
    mapped = [map_court_to_canvas(point.get("projected_x"), point.get("projected_y"), transform) for point in visible]
    mapped = [point for point in mapped if point is not None]
    for start, end in zip(mapped, mapped[1:]):
        cv2.line(canvas, start, end, STYLE["ball_trail"], 2, cv2.LINE_AA)
    for point, mapped_point in zip(visible, mapped):
        radius = 4 if point.get("is_visual_interpolation") else 5
        color = STYLE["ball_interpolated"] if point.get("is_visual_interpolation") else STYLE["ball"]
        cv2.circle(canvas, mapped_point, radius, color, thickness=-1, lineType=cv2.LINE_AA)
    if mapped:
        cv2.circle(canvas, mapped[-1], 10, STYLE["ball"], thickness=2, lineType=cv2.LINE_AA)
    return canvas


def render_players(canvas: np.ndarray, players: list[dict[str, Any]], transform: dict[str, float], frame_index: int) -> np.ndarray:
    """Render approximate player positions using nearest side state."""
    for player in players:
        state = nearest_player_state(player.get("side_states", []), frame_index)
        if not state:
            continue
        mapped = map_court_to_canvas(state.get("projected_x"), state.get("projected_y"), transform)
        if mapped is None:
            continue
        player_id = str(player.get("player_id") or "unknown")
        color = STYLE["player_a"] if player_id == "player_a" else STYLE["player_b"] if player_id == "player_b" else STYLE["unknown_player"]
        cv2.circle(canvas, mapped, 13, color, thickness=-1, lineType=cv2.LINE_AA)
        cv2.circle(canvas, mapped, 16, STYLE["court_line"], thickness=1, lineType=cv2.LINE_AA)
        label = f"{player_id} {state.get('side_state') or 'unknown'}"
        cv2.putText(canvas, label, (mapped[0] + 18, mapped[1] + 5), STYLE["font"], STYLE["small_font_scale"], STYLE["text"], 1, cv2.LINE_AA)
    return canvas


def render_event_markers(canvas: np.ndarray, events: list[dict[str, Any]], transform: dict[str, float], current_frame: int) -> np.ndarray:
    """Render event markers up to the current frame."""
    for event in events:
        event_frame = _int(event.get("frame_index"))
        if event_frame is None or event_frame > current_frame:
            continue
        pos = event.get("projected_position", {})
        mapped = map_court_to_canvas(pos.get("x"), pos.get("y"), transform)
        if mapped is None:
            continue
        color = event_color(event.get("event_type"))
        cv2.drawMarker(canvas, mapped, color, markerType=cv2.MARKER_TILTED_CROSS, markerSize=18, thickness=2, line_type=cv2.LINE_AA)
        label = str(event.get("event_type") or "possible_event").replace("possible_", "?")
        cv2.putText(canvas, label[:22], (mapped[0] + 8, mapped[1] - 10), STYLE["font"], STYLE["small_font_scale"], color, 1, cv2.LINE_AA)
    return canvas


def render_timeline_strip(canvas: np.ndarray, points: list[dict[str, Any]], events: list[dict[str, Any]], current_index: int) -> np.ndarray:
    """Render a simple frame-axis timeline strip."""
    height, width = canvas.shape[:2]
    y = height - 85
    x0 = 80
    x1 = width - 80
    frames = [_int(point.get("frame_index")) for point in points if _int(point.get("frame_index")) is not None]
    if not frames:
        return canvas
    min_frame = min(frames)
    max_frame = max(frames)
    cv2.line(canvas, (x0, y), (x1, y), STYLE["timeline_axis"], 2)
    for point in points:
        frame = _int(point.get("frame_index"))
        if frame is None:
            continue
        x = timeline_x(frame, min_frame, max_frame, x0, x1)
        color = STYLE["ball_interpolated"] if point.get("is_visual_interpolation") else STYLE["ball"]
        cv2.circle(canvas, (x, y), 4, color, thickness=-1)
    for event in events:
        frame = _int(event.get("frame_index"))
        if frame is None:
            continue
        x = timeline_x(frame, min_frame, max_frame, x0, x1)
        cv2.line(canvas, (x, y - 22), (x, y - 7), event_color(event.get("event_type")), 2)
    current_frame = _int(points[current_index].get("frame_index")) if points else None
    if current_frame is not None:
        x = timeline_x(current_frame, min_frame, max_frame, x0, x1)
        cv2.line(canvas, (x, y - 35), (x, y + 22), STYLE["timeline_current"], 2)
        cv2.putText(canvas, f"Frame {current_frame}", (x0, y + 45), STYLE["font"], 0.55, STYLE["text"], 1, cv2.LINE_AA)
    cv2.putText(canvas, f"{min_frame}", (x0 - 12, y + 24), STYLE["font"], STYLE["small_font_scale"], STYLE["muted_text"], 1, cv2.LINE_AA)
    cv2.putText(canvas, f"{max_frame}", (x1 - 26, y + 24), STYLE["font"], STYLE["small_font_scale"], STYLE["muted_text"], 1, cv2.LINE_AA)
    return canvas


def render_replay_frame(
    *,
    schema: dict[str, Any],
    points: list[dict[str, Any]],
    current_index: int,
    players: list[dict[str, Any]],
    events: list[dict[str, Any]],
) -> np.ndarray:
    """Render one deterministic 2D tactical replay frame from court, ball, player and event data."""
    court_model = extract_court_model(schema)
    canvas, transform = create_court_canvas(court_model)
    render_static_court(canvas, court_model, transform)
    current = points[current_index]
    current_frame = _int(current.get("frame_index")) or 0
    render_ball_trajectory(canvas, points, transform, current_index)
    render_players(canvas, players, transform, current_frame)
    render_event_markers(canvas, events, transform, current_frame)
    render_timeline_strip(canvas, points, events, current_index)
    note = "interpolated visual point" if current.get("is_visual_interpolation") else "measured replay keyframe"
    zone = current.get("zone") or "unknown"
    cv2.putText(canvas, f"{note} | zone: {zone}", (30, 95), STYLE["font"], 0.5, STYLE["muted_text"], 1, cv2.LINE_AA)
    return canvas


def render_replay_frames(
    *,
    schema: dict[str, Any],
    output_dir: Path,
    interpolate: bool = True,
    interpolation_steps: int = 5,
) -> tuple[list[Path], dict[str, Any], list[str], list[str]]:
    """Render all replay frames."""
    warnings: list[str] = []
    errors: list[str] = []
    frames_dir = output_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    keyframes = extract_replay_keyframes(schema)
    if not keyframes:
        return [], {"display_points": [], "players": [], "events": []}, warnings, ["Replay schema has no replay keyframes."]
    points = build_display_points(keyframes, interpolate=interpolate, interpolation_steps=interpolation_steps)
    players = extract_players(schema)
    events = extract_events(schema)
    paths: list[Path] = []
    for index in range(len(points)):
        frame = render_replay_frame(schema=schema, points=points, current_index=index, players=players, events=events)
        path = frames_dir / f"replay_frame_{index:04d}.jpg"
        if not cv2.imwrite(str(path), frame):
            errors.append(f"Could not write replay frame: {path}")
        else:
            paths.append(path)
    return paths, {"display_points": points, "players": players, "events": events}, warnings, errors


def export_replay_video(frame_paths: list[Path], output_path: Path, fps: int) -> tuple[bool, list[str], list[str]]:
    """Export replay frames to MP4 using OpenCV VideoWriter."""
    warnings: list[str] = []
    errors: list[str] = []
    if not frame_paths:
        return False, warnings, ["No frames available for video export."]
    first = cv2.imread(str(frame_paths[0]))
    if first is None:
        return False, warnings, [f"Could not read first frame for video export: {frame_paths[0]}"]
    height, width = first.shape[:2]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(output_path), cv2.VideoWriter_fourcc(*"mp4v"), float(fps), (width, height))
    if not writer.isOpened():
        return False, ["OpenCV VideoWriter could not open MP4 output. Frames are still available."], errors
    try:
        for frame_path in frame_paths:
            frame = cv2.imread(str(frame_path))
            if frame is None:
                warnings.append(f"Skipped unreadable frame during video export: {frame_path}")
                continue
            writer.write(frame)
    finally:
        writer.release()
    if not output_path.exists() or output_path.stat().st_size == 0:
        warnings.append("MP4 export completed but output file is missing or empty. Frames are still available.")
        return False, warnings, errors
    return True, warnings, errors


def create_contact_sheet(frame_paths: list[Path], output_path: Path, max_images: int = 9) -> tuple[bool, list[str]]:
    """Create a contact sheet from selected replay frames."""
    if not frame_paths:
        return False, ["No frames available for contact sheet."]
    selected = evenly_spaced(frame_paths, max_images)
    images = [cv2.imread(str(path)) for path in selected]
    images = [image for image in images if image is not None]
    if not images:
        return False, ["Selected contact sheet frames could not be read."]
    thumb_w = 300
    thumb_h = int(images[0].shape[0] * (thumb_w / images[0].shape[1]))
    thumbs = [cv2.resize(image, (thumb_w, thumb_h), interpolation=cv2.INTER_AREA) for image in images]
    columns = min(3, len(thumbs))
    rows = int(np.ceil(len(thumbs) / columns))
    sheet = np.full((rows * thumb_h, columns * thumb_w, 3), STYLE["background"], dtype=np.uint8)
    for index, thumb in enumerate(thumbs):
        row = index // columns
        col = index % columns
        sheet[row * thumb_h : (row + 1) * thumb_h, col * thumb_w : (col + 1) * thumb_w] = thumb
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return bool(cv2.imwrite(str(output_path), sheet)), []


def write_renderer_manifest(path: Path, manifest: dict[str, Any]) -> Path:
    """Write the Stage 13 renderer manifest."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def build_display_points(keyframes: list[dict[str, Any]], *, interpolate: bool, interpolation_steps: int) -> list[dict[str, Any]]:
    """Create display points, including visual-only interpolation when requested."""
    if not interpolate or interpolation_steps <= 0 or len(keyframes) <= 1:
        return [dict(point, is_visual_interpolation=False) for point in keyframes]
    points: list[dict[str, Any]] = []
    for start, end in zip(keyframes, keyframes[1:]):
        points.append(dict(start, is_visual_interpolation=False))
        for step in range(1, interpolation_steps + 1):
            t = step / (interpolation_steps + 1)
            points.append(interpolate_point(start, end, t))
    points.append(dict(keyframes[-1], is_visual_interpolation=False))
    return points


def interpolate_point(start: dict[str, Any], end: dict[str, Any], t: float) -> dict[str, Any]:
    """Build one visual-only interpolated ball point."""
    result = dict(start)
    for key in ("projected_x", "projected_y", "image_x", "image_y", "confidence_like_score"):
        a = _float(start.get(key))
        b = _float(end.get(key))
        result[key] = None if a is None or b is None else a + ((b - a) * t)
    frame_a = _float(start.get("frame_index"))
    frame_b = _float(end.get("frame_index"))
    result["frame_index"] = None if frame_a is None or frame_b is None else int(round(frame_a + ((frame_b - frame_a) * t)))
    result["source"] = "visual_interpolation"
    result["is_interpolated"] = True
    result["is_visual_interpolation"] = True
    result["notes"] = "Visual interpolation only; not a measured detection."
    return result


def nearest_player_state(states: list[dict[str, Any]], frame_index: int) -> dict[str, Any] | None:
    """Return nearest side-state row for a player."""
    if not states:
        return None
    return min(states, key=lambda row: abs((_int(row.get("frame_index")) or frame_index) - frame_index))


def event_color(event_type: Any) -> tuple[int, int, int]:
    """Return a BGR event marker color."""
    text = str(event_type or "")
    if "hit" in text:
        return STYLE["event_hit"]
    if "bounce" in text:
        return STYLE["event_bounce"]
    return STYLE["event_default"]


def timeline_x(frame: int, min_frame: int, max_frame: int, x0: int, x1: int) -> int:
    """Map frame index to timeline x coordinate."""
    if max_frame == min_frame:
        return x0
    return int(round(x0 + ((frame - min_frame) / (max_frame - min_frame)) * (x1 - x0)))


def evenly_spaced(items: list[Path], max_items: int) -> list[Path]:
    """Select evenly spaced items."""
    if len(items) <= max_items:
        return items
    indices = np.linspace(0, len(items) - 1, max_items).round().astype(int)
    return [items[int(index)] for index in indices]


def _float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None
