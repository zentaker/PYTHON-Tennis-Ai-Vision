"""Deterministic side-view ball flight replay renderer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from tennis_vision.ball_flight_estimator import build_side_view_keyframes, downgrade_implausible_hits, interpolate_side_view_motion


SIDE_STYLE: dict[str, Any] = {
    "canvas_size": (1200, 700),
    "background": (22, 32, 38),
    "court": (54, 118, 82),
    "court_line": (232, 236, 226),
    "net": (230, 230, 235),
    "ground_emphasis": (95, 205, 145),
    "height_guide": (90, 120, 130),
    "ball": (0, 242, 255),
    "ball_interpolated": (80, 210, 220),
    "anchor": (255, 245, 120),
    "trail": (55, 210, 245),
    "event": (210, 120, 255),
    "hit": (70, 120, 255),
    "bounce": (120, 255, 140),
    "interaction": (220, 95, 220),
    "uncertain": (170, 185, 195),
    "player_a": (255, 120, 70),
    "player_b": (80, 170, 255),
    "text": (245, 245, 240),
    "muted": (190, 205, 195),
    "axis": (210, 220, 210),
    "font": 0,
}


def load_replay_schema(path: Path) -> tuple[dict[str, Any], list[str], list[str]]:
    """Load the Stage 12 replay schema."""
    if not path.exists():
        return {}, [], [f"Replay schema missing: {path}"]
    try:
        return json.loads(path.read_text(encoding="utf-8")), [], []
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [], [f"Could not read replay schema {path}: {exc}"]


def create_side_view_canvas(schema: dict[str, Any]) -> tuple[np.ndarray, dict[str, float]]:
    """Create side-view canvas and depth/height transform."""
    width, height = SIDE_STYLE["canvas_size"]
    canvas = np.full((height, width, 3), SIDE_STYLE["background"], dtype=np.uint8)
    court_height = float(schema.get("court_model", {}).get("normalized_court_height") or 780.0)
    transform = {
        "x0": 95.0,
        "x1": width - 95.0,
        "ground_y": height - 160.0,
        "top_y": 95.0,
        "court_height": court_height,
        "max_synthetic_height": 240.0,
        "timeline_y": height - 70.0,
    }
    return canvas, transform


def map_depth_height_to_canvas(depth: Any, synthetic_height: Any, transform: dict[str, float]) -> tuple[int, int] | None:
    """Map court depth and synthetic height to side-view canvas coordinates."""
    try:
        depth_value = float(depth)
        height_value = float(synthetic_height)
    except (TypeError, ValueError):
        return None
    depth_value = max(0.0, min(transform["court_height"], depth_value))
    height_value = max(0.0, min(transform["max_synthetic_height"], height_value))
    x = transform["x0"] + (depth_value / transform["court_height"]) * (transform["x1"] - transform["x0"])
    y = transform["ground_y"] - (height_value / transform["max_synthetic_height"]) * (transform["ground_y"] - transform["top_y"])
    return int(round(x)), int(round(y))


def render_side_court(canvas: np.ndarray, transform: dict[str, float]) -> np.ndarray:
    """Render side-view court depth axis."""
    x0 = int(transform["x0"])
    x1 = int(transform["x1"])
    ground_y = int(transform["ground_y"])
    cv2.rectangle(canvas, (x0, ground_y), (x1, ground_y + 34), SIDE_STYLE["court"], thickness=-1)
    cv2.line(canvas, (x0, ground_y), (x1, ground_y), SIDE_STYLE["ground_emphasis"], 4)
    cv2.line(canvas, (x0, ground_y + 2), (x1, ground_y + 2), SIDE_STYLE["court_line"], 1)
    for fraction, label in ((0.0, "far baseline"), (0.5, "net"), (1.0, "near baseline")):
        x = int(round(x0 + (x1 - x0) * fraction))
        cv2.line(canvas, (x, ground_y - 8), (x, ground_y + 34), SIDE_STYLE["court_line"], 1)
        cv2.putText(canvas, label, (x - 46, ground_y + 58), SIDE_STYLE["font"], 0.45, SIDE_STYLE["muted"], 1, cv2.LINE_AA)
    cv2.putText(canvas, "Side-view ball flight - synthetic height", (35, 38), SIDE_STYLE["font"], 0.75, SIDE_STYLE["text"], 2, cv2.LINE_AA)
    cv2.putText(canvas, "Synthetic height visualization - not measured 3D height", (35, 66), SIDE_STYLE["font"], 0.52, SIDE_STYLE["muted"], 1, cv2.LINE_AA)
    cv2.putText(canvas, "court surface / bounce floor", (x0, ground_y - 12), SIDE_STYLE["font"], 0.42, SIDE_STYLE["ground_emphasis"], 1, cv2.LINE_AA)
    return canvas


def render_net(canvas: np.ndarray, transform: dict[str, float]) -> np.ndarray:
    """Render approximate net position."""
    net_x = int(round(transform["x0"] + (transform["x1"] - transform["x0"]) * 0.5))
    ground_y = int(transform["ground_y"])
    cv2.line(canvas, (net_x, ground_y), (net_x, ground_y - 95), SIDE_STYLE["net"], 2)
    cv2.line(canvas, (net_x - 18, ground_y - 95), (net_x + 18, ground_y - 95), SIDE_STYLE["net"], 1)
    cv2.line(canvas, (int(transform["x0"]), ground_y - 95), (int(transform["x1"]), ground_y - 95), SIDE_STYLE["height_guide"], 1, cv2.LINE_AA)
    cv2.putText(canvas, "net height reference", (net_x + 24, ground_y - 91), SIDE_STYLE["font"], 0.4, SIDE_STYLE["muted"], 1, cv2.LINE_AA)
    return canvas


def render_ball_arc(canvas: np.ndarray, points: list[dict[str, Any]], transform: dict[str, float], current_index: int) -> np.ndarray:
    """Render previous side-view ball arc."""
    visible = points[: current_index + 1]
    mapped = [map_depth_height_to_canvas(point.get("court_depth"), point.get("synthetic_height"), transform) for point in visible]
    mapped = [point for point in mapped if point is not None]
    for start, end in zip(mapped, mapped[1:]):
        cv2.line(canvas, start, end, SIDE_STYLE["trail"], 2, cv2.LINE_AA)
    for point, mapped_point in zip(visible, mapped):
        color = SIDE_STYLE["ball_interpolated"] if point.get("is_interpolated") else point_color(point)
        radius = 4 if point.get("is_interpolated") else 7
        thickness = 1 if point.get("is_interpolated") else -1
        cv2.circle(canvas, mapped_point, radius, color, thickness=thickness, lineType=cv2.LINE_AA)
    return canvas


def render_ball(canvas: np.ndarray, point: dict[str, Any], transform: dict[str, float]) -> np.ndarray:
    """Render current ball marker."""
    mapped = map_depth_height_to_canvas(point.get("court_depth"), point.get("synthetic_height"), transform)
    if mapped is None:
        return canvas
    cv2.circle(canvas, mapped, 13, SIDE_STYLE["ball"], thickness=2, lineType=cv2.LINE_AA)
    role = str(point.get("height_anchor_type") or "")
    if role == "bounce_grounded":
        label = "bounce grounded"
    elif role == "hit_contact":
        label = "hit estimate"
    elif point.get("is_interpolated"):
        label = "interpolated visual point"
    else:
        label = "side-view keyframe"
    cv2.putText(canvas, label, (mapped[0] + 14, mapped[1] - 12), SIDE_STYLE["font"], 0.45, SIDE_STYLE["text"], 1, cv2.LINE_AA)
    return canvas


def render_event_markers(canvas: np.ndarray, events: list[dict[str, Any]], transform: dict[str, float], current_frame: int) -> np.ndarray:
    """Render possible event markers along the side-view court."""
    for event in events:
        event_frame = _int(event.get("frame_index"))
        if event_frame is None or event_frame > current_frame:
            continue
        projected = event.get("projected_position", {})
        depth = projected.get("y")
        render_role = assign_event_render_role(event)
        if render_role == "bounce_plausible":
            height = 2
        elif render_role == "hit_plausible":
            height = 88
        elif render_role == "player_interaction":
            height = 42
        else:
            height = 58
        mapped = map_depth_height_to_canvas(depth, height, transform)
        if mapped is None:
            continue
        color = render_role_color(render_role)
        marker_type = cv2.MARKER_DIAMOND if render_role == "player_interaction" else cv2.MARKER_TILTED_CROSS
        cv2.drawMarker(canvas, mapped, color, markerType=marker_type, markerSize=18, thickness=2, line_type=cv2.LINE_AA)
        label = render_role_label(event)
        cv2.putText(canvas, label[:22], (mapped[0] + 8, mapped[1] - 8), SIDE_STYLE["font"], 0.42, color, 1, cv2.LINE_AA)
    return canvas


def render_player_depth_markers(canvas: np.ndarray, players: list[dict[str, Any]], transform: dict[str, float], frame_index: int) -> np.ndarray:
    """Render player side/depth markers along the court surface."""
    for player in players:
        state = nearest_player_state(player.get("side_states", []), frame_index)
        if not state:
            continue
        mapped = map_depth_height_to_canvas(state.get("projected_y"), 0, transform)
        if mapped is None:
            continue
        player_id = str(player.get("player_id") or "unknown")
        color = SIDE_STYLE["player_a"] if player_id == "player_a" else SIDE_STYLE["player_b"]
        cv2.circle(canvas, (mapped[0], mapped[1] + 18), 11, color, thickness=-1, lineType=cv2.LINE_AA)
        cv2.putText(canvas, player_id, (mapped[0] + 14, mapped[1] + 22), SIDE_STYLE["font"], 0.45, SIDE_STYLE["text"], 1, cv2.LINE_AA)
    return canvas


def render_timeline_strip(canvas: np.ndarray, points: list[dict[str, Any]], events: list[dict[str, Any]], current_index: int) -> np.ndarray:
    """Render frame-axis timeline strip."""
    x0 = 95
    x1 = canvas.shape[1] - 95
    y = int(SIDE_STYLE.get("timeline_y", canvas.shape[0] - 70))
    frames = [_int(point.get("frame_index")) for point in points if _int(point.get("frame_index")) is not None]
    if not frames:
        return canvas
    min_frame = min(frames)
    max_frame = max(frames)
    cv2.line(canvas, (x0, y), (x1, y), SIDE_STYLE["axis"], 2)
    for point in points:
        frame = _int(point.get("frame_index"))
        if frame is None:
            continue
        x = timeline_x(frame, min_frame, max_frame, x0, x1)
        color = SIDE_STYLE["ball_interpolated"] if point.get("is_interpolated") else SIDE_STYLE["ball"]
        cv2.circle(canvas, (x, y), 4, color, thickness=-1)
    for event in events:
        frame = _int(event.get("frame_index"))
        if frame is None:
            continue
        x = timeline_x(frame, min_frame, max_frame, x0, x1)
        cv2.line(canvas, (x, y - 22), (x, y - 7), render_role_color(assign_event_render_role(event)), 2)
    current_frame = _int(points[current_index].get("frame_index"))
    if current_frame is not None:
        x = timeline_x(current_frame, min_frame, max_frame, x0, x1)
        cv2.line(canvas, (x, y - 34), (x, y + 20), SIDE_STYLE["ball"], 2)
        cv2.putText(canvas, f"Frame {current_frame}", (x0, y + 43), SIDE_STYLE["font"], 0.5, SIDE_STYLE["text"], 1, cv2.LINE_AA)
    return canvas


def render_side_view_frame(
    *,
    schema: dict[str, Any],
    points: list[dict[str, Any]],
    current_index: int,
    players: list[dict[str, Any]],
    events: list[dict[str, Any]],
) -> np.ndarray:
    """Render one side-view ball flight frame."""
    canvas, transform = create_side_view_canvas(schema)
    current = points[current_index]
    current_frame = _int(current.get("frame_index")) or 0
    render_side_court(canvas, transform)
    render_net(canvas, transform)
    render_ball_arc(canvas, points, transform, current_index)
    render_ball(canvas, current, transform)
    render_event_markers(canvas, events, transform, current_frame)
    render_player_depth_markers(canvas, players, transform, current_frame)
    render_timeline_strip(canvas, points, events, current_index)
    height = current.get("synthetic_height")
    cv2.putText(canvas, f"Synthetic height: {height:.1f}" if isinstance(height, (int, float)) else "Synthetic height: n/a", (35, 96), SIDE_STYLE["font"], 0.5, SIDE_STYLE["muted"], 1, cv2.LINE_AA)
    cv2.putText(canvas, f"Height role: {current.get('height_anchor_type') or 'arc_estimate'}", (35, 118), SIDE_STYLE["font"], 0.45, SIDE_STYLE["muted"], 1, cv2.LINE_AA)
    return canvas


def render_side_view_frames(
    *,
    schema: dict[str, Any],
    output_dir: Path,
    interpolate: bool = True,
    interpolation_steps: int = 8,
) -> tuple[list[Path], dict[str, Any], list[str], list[str]]:
    """Render side-view replay frames."""
    warnings: list[str] = []
    errors: list[str] = []
    frames_dir = output_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    keyframes = build_side_view_keyframes(schema)
    if not keyframes:
        return [], {"side_view_keyframes": [], "display_points": [], "players": [], "events": []}, warnings, ["No side-view keyframes could be built."]
    points = interpolate_side_view_motion(keyframes, interpolate=interpolate, interpolation_steps=interpolation_steps)
    players = list(schema.get("players", []))
    events, event_render_role_summary = downgrade_implausible_hits(list(schema.get("event_timeline", [])), players)
    paths: list[Path] = []
    for index in range(len(points)):
        frame = render_side_view_frame(schema=schema, points=points, current_index=index, players=players, events=events)
        path = frames_dir / f"side_view_frame_{index:04d}.jpg"
        if not cv2.imwrite(str(path), frame):
            errors.append(f"Could not write side-view frame: {path}")
        else:
            paths.append(path)
    return paths, {"side_view_keyframes": keyframes, "display_points": points, "players": players, "events": events, "event_render_role_summary": event_render_role_summary}, warnings, errors


def export_side_view_video(frame_paths: list[Path], output_path: Path, fps: int) -> tuple[bool, list[str], list[str]]:
    """Export side-view frames to MP4 using OpenCV VideoWriter."""
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


def create_side_contact_sheet(frame_paths: list[Path], output_path: Path, max_images: int = 9) -> tuple[bool, list[str]]:
    """Create side-view contact sheet."""
    if not frame_paths:
        return False, ["No frames available for contact sheet."]
    selected = evenly_spaced(frame_paths, max_images)
    images = [cv2.imread(str(path)) for path in selected]
    images = [image for image in images if image is not None]
    if not images:
        return False, ["Selected contact sheet frames could not be read."]
    thumb_w = 360
    thumb_h = int(images[0].shape[0] * (thumb_w / images[0].shape[1]))
    thumbs = [cv2.resize(image, (thumb_w, thumb_h), interpolation=cv2.INTER_AREA) for image in images]
    columns = min(3, len(thumbs))
    rows = int(np.ceil(len(thumbs) / columns))
    sheet = np.full((rows * thumb_h, columns * thumb_w, 3), SIDE_STYLE["background"], dtype=np.uint8)
    for index, thumb in enumerate(thumbs):
        row = index // columns
        col = index % columns
        sheet[row * thumb_h : (row + 1) * thumb_h, col * thumb_w : (col + 1) * thumb_w] = thumb
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return bool(cv2.imwrite(str(output_path), sheet)), []


def create_semantic_debug_image(
    *,
    schema: dict[str, Any],
    side_view_keyframes: list[dict[str, Any]],
    display_points: list[dict[str, Any]],
    events: list[dict[str, Any]],
    players: list[dict[str, Any]],
    output_path: Path,
) -> tuple[bool, list[str]]:
    """Create a static side-view semantic debug image."""
    if not display_points:
        return False, ["No display points available for semantic debug image."]
    canvas = render_side_view_frame(
        schema=schema,
        points=display_points,
        current_index=len(display_points) - 1,
        players=players,
        events=events,
    )
    _, transform = create_side_view_canvas(schema)
    for point in side_view_keyframes:
        mapped = map_depth_height_to_canvas(point.get("court_depth"), point.get("synthetic_height"), transform)
        if mapped is None:
            continue
        role = str(point.get("height_anchor_type") or "arc_estimate")
        color = point_color(point)
        cv2.circle(canvas, mapped, 12, color, thickness=2, lineType=cv2.LINE_AA)
        render_role = str(point.get("render_role") or "")
        if role == "bounce_grounded":
            label = "bounce grounded"
        elif role == "hit_contact":
            label = "hit estimate"
        elif render_role == "uncertain_event":
            label = "uncertain event"
        elif role == "interaction_cue":
            label = "near-player cue"
        else:
            label = "arc estimate"
        cv2.putText(canvas, label, (mapped[0] + 10, mapped[1] + 18), SIDE_STYLE["font"], 0.42, color, 1, cv2.LINE_AA)
    for event in events:
        projected = event.get("projected_position", {})
        role = assign_event_render_role(event)
        if role == "bounce_plausible":
            height = 2
        elif role == "hit_plausible":
            height = 88
        elif role == "player_interaction":
            height = 42
        else:
            height = 58
        mapped = map_depth_height_to_canvas(projected.get("y"), height, transform)
        if mapped is None:
            continue
        color = render_role_color(role)
        raw_type = str(event.get("event_type") or "event")
        status = str(event.get("player_aware_plausibility_status") or "not_applicable")
        cv2.putText(canvas, f"raw={raw_type} role={role}", (mapped[0] + 10, mapped[1] + 36), SIDE_STYLE["font"], 0.36, color, 1, cv2.LINE_AA)
        if status != "not_applicable":
            cv2.putText(canvas, f"player check: {status}", (mapped[0] + 10, mapped[1] + 52), SIDE_STYLE["font"], 0.34, color, 1, cv2.LINE_AA)
    cv2.putText(canvas, "Semantic debug: raw events are separated from render roles; implausible hits become uncertain", (35, 145), SIDE_STYLE["font"], 0.46, SIDE_STYLE["text"], 1, cv2.LINE_AA)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return bool(cv2.imwrite(str(output_path), canvas)), []


def write_side_view_manifest(path: Path, manifest: dict[str, Any]) -> Path:
    """Write the Stage 14 side-view renderer manifest."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def nearest_player_state(states: list[dict[str, Any]], frame_index: int) -> dict[str, Any] | None:
    """Return nearest side-state row for a player."""
    if not states:
        return None
    return min(states, key=lambda row: abs((_int(row.get("frame_index")) or frame_index) - frame_index))


def event_color(event_type: Any) -> tuple[int, int, int]:
    """Return BGR color for event marker."""
    text = str(event_type or "").lower()
    if "hit" in text:
        return SIDE_STYLE["hit"]
    if "bounce" in text:
        return SIDE_STYLE["bounce"]
    return SIDE_STYLE["event"]


def assign_event_render_role(event: dict[str, Any]) -> str:
    """Separate raw event labels from the final side-view render role."""
    role = str(event.get("render_role") or "").lower()
    if role:
        return role
    text = str(event.get("event_type") or "").lower()
    if "bounce" in text:
        return "bounce_plausible"
    if "ball_near_player" in text or "near_player" in text:
        return "player_interaction"
    if "hit" in text:
        return "uncertain_event"
    if event.get("is_interpolated"):
        return "interpolation_only"
    return "uncertain_event"


def render_role_color(render_role: str) -> tuple[int, int, int]:
    """Return BGR color for the final event render role."""
    if render_role == "hit_plausible":
        return SIDE_STYLE["hit"]
    if render_role == "bounce_plausible":
        return SIDE_STYLE["bounce"]
    if render_role == "player_interaction":
        return SIDE_STYLE["interaction"]
    if render_role == "interpolation_only":
        return SIDE_STYLE["ball_interpolated"]
    if render_role == "uncertain_event":
        return SIDE_STYLE["uncertain"]
    return SIDE_STYLE["event"]


def render_role_label(event: dict[str, Any]) -> str:
    """Return short label for side-view event rendering."""
    role = assign_event_render_role(event)
    if role == "hit_plausible":
        return "?hit plausible"
    if role == "bounce_plausible":
        return "?bounce grounded"
    if role == "player_interaction":
        return "near player cue"
    if role == "interpolation_only":
        return "interpolated"
    return "uncertain"


def point_color(point: dict[str, Any]) -> tuple[int, int, int]:
    """Return BGR color for a side-view point role."""
    role = str(point.get("height_anchor_type") or "")
    render_role = str(point.get("render_role") or "")
    if role == "bounce_grounded":
        return SIDE_STYLE["bounce"]
    if role == "hit_contact":
        return SIDE_STYLE["hit"]
    if render_role == "uncertain_event":
        return SIDE_STYLE["uncertain"]
    if render_role == "player_interaction":
        return SIDE_STYLE["interaction"]
    if role == "visual_interpolation":
        return SIDE_STYLE["ball_interpolated"]
    return SIDE_STYLE["ball"]


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


def _int(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None
