"""Build Stage 12 synthetic rally replay schema data."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from tennis_vision.court_zones import COURT_HEIGHT, COURT_WIDTH
from tennis_vision.replay_camera_presets import build_camera_profiles
from tennis_vision.replay_schema import DEFAULT_SCHEMA_VERSION, SCHEMA_NAME, build_renderer_hints, build_visual_layers


def read_csv_rows(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Read CSV rows with warning return."""
    if not path.exists():
        return [], [f"Missing CSV: {path}"]
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle)), []


def read_json(path: Path) -> tuple[dict[str, Any], list[str]]:
    """Read JSON with warning return."""
    if not path.exists():
        return {}, [f"Missing JSON: {path}"]
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"Could not read JSON {path}: {exc}"]


def read_text(path: Path) -> tuple[str, list[str]]:
    """Read optional text file."""
    if not path.exists():
        return "", [f"Missing text file: {path}"]
    return path.read_text(encoding="utf-8"), []


def load_replay_inputs(paths: dict[str, Path]) -> dict[str, Any]:
    """Load replay schema source data."""
    data: dict[str, Any] = {"warnings": [], "errors": []}
    csv_keys = [
        "tuned_zones",
        "directions",
        "rally_tactical_summary",
        "projected_labels",
        "validated_timeline",
        "expanded_labels",
        "event_timeline",
        "rally_segments",
        "player_event_attribution",
        "main_players",
        "player_side_states",
        "refined_ball_player_distances",
        "smoothed_trajectory",
        "raw_trajectory",
        "trajectory_events",
    ]
    required_csv = {"tuned_zones", "validated_timeline", "rally_segments", "main_players", "smoothed_trajectory"}
    for key in csv_keys:
        rows, warnings = read_csv_rows(paths[key])
        data[key] = rows
        if warnings and key in required_csv:
            data["errors"].extend(warnings)
        else:
            data["warnings"].extend(warnings)
    json_keys = [
        "stage11_manifest",
        "analytical_report_json",
        "confidence_summary",
        "player_identity_profiles",
        "stage3_report",
        "calibration_config",
        "stage1_report",
    ]
    required_json = {"stage11_manifest", "analytical_report_json", "stage3_report"}
    for key in json_keys:
        payload, warnings = read_json(paths[key])
        data[key] = payload
        if warnings and key in required_json:
            data["errors"].extend(warnings)
        else:
            data["warnings"].extend(warnings)
    key_findings, key_warnings = read_text(paths["key_findings"])
    data["key_findings_text"] = key_findings
    data["warnings"].extend(key_warnings)
    return data


def build_source_video(data: dict[str, Any]) -> dict[str, Any]:
    """Build source video section."""
    metadata = data.get("stage1_report", {}).get("metadata", {})
    labels = data.get("expanded_labels", [])
    frames = [_int(row.get("frame_index")) for row in labels if _int(row.get("frame_index")) is not None]
    return {
        "video_path": metadata.get("file_path"),
        "frame_rate": metadata.get("fps"),
        "width": metadata.get("width"),
        "height": metadata.get("height"),
        "analyzed_frame_range": _frame_range(data.get("smoothed_trajectory", [])),
        "label_frame_range": [min(frames), max(frames)] if frames else None,
        "total_labeled_points": len([row for row in labels if str(row.get("visible", "")).lower() in {"true", "1", "yes"}]),
    }


def build_court_model(data: dict[str, Any]) -> dict[str, Any]:
    """Build court model section."""
    stage3 = data.get("stage3_report", {})
    calibration = stage3.get("calibration_result", {})
    homography = calibration.get("homography", {})
    points = calibration.get("config", {}).get("points") or data.get("calibration_config", {}).get("points", {})
    zones = sorted(set(row.get("tuned_zone") or "unknown" for row in data.get("tuned_zones", [])))
    zone_definitions = {
        "side": ["near", "far", "unknown"],
        "depth": ["short", "mid", "deep", "unknown"],
        "lateral_lane": ["left", "center", "right", "unknown"],
        "special": ["out_of_bounds"],
    }
    return {
        "calibration_basis": "doubles court outer boundary",
        "calibration_type": "full_doubles_boundary_homography",
        "homography_status": {"computed": bool(homography.get("computed")), "target_size": homography.get("target_size"), "error": homography.get("error")},
        "normalized_court_width": COURT_WIDTH,
        "normalized_court_height": COURT_HEIGHT,
        "court_zone_model": "simple_normalized_doubles_court_zones_v0",
        "available_zones": zones,
        "zone_definitions": zone_definitions,
        "calibration_points": points,
        "limitations": [
            "Tennis has singles and doubles lines; this calibration uses the doubles outer boundary.",
            "Singles and service-box geometry may be derived later.",
            "This is not official line calling.",
        ],
    }


def build_players(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Build player schema section."""
    side_states = data.get("player_side_states", [])
    states_by_player: dict[str, list[dict[str, Any]]] = {}
    for row in side_states:
        states_by_player.setdefault(str(row.get("player_id") or "unknown"), []).append(
            {
                "frame_index": _int(row.get("frame_index")),
                "side_state": row.get("side_state") or "unknown",
                "x": _float(row.get("x")),
                "y": _float(row.get("y")),
                "projected_x": _float(row.get("projected_x")),
                "projected_y": _float(row.get("projected_y")),
            }
        )
    players: list[dict[str, Any]] = []
    for row in data.get("main_players", []):
        player_id = str(row.get("player_id") or "unknown")
        players.append(
            {
                "player_id": player_id,
                "source_track_ids": row.get("source_track_ids"),
                "identity_basis": "clothing_color_heuristic / track_filtering",
                "dominant_colors_summary": row.get("dominant_colors_summary"),
                "initial_side_state": row.get("initial_side_state") or "unknown",
                "side_states": states_by_player.get(player_id, []),
                "confidence": _float(row.get("average_confidence")),
                "limitations": ["Near/far side is a state, not identity.", "Identity is not biometric re-identification."],
            }
        )
    return players


def build_ball_trajectory(data: dict[str, Any]) -> dict[str, Any]:
    """Build ball trajectory section."""
    tuned_by_frame = {_int(row.get("frame_index")): row for row in data.get("tuned_zones", []) if _int(row.get("frame_index")) is not None}
    raw_points = []
    for row in data.get("raw_trajectory", []):
        raw_points.append(_ball_point_from_row(row, tuned_by_frame.get(_int(row.get("frame_index")), {}), raw=True))
    smoothed_points = []
    for row in data.get("smoothed_trajectory", []):
        smoothed_points.append(_ball_point_from_row(row, tuned_by_frame.get(_int(row.get("frame_index")), {}), raw=False))
    replay_keyframes = [_ball_point_from_tuned(row) for row in data.get("tuned_zones", []) if row.get("projected_x") not in (None, "")]
    return {
        "raw_ball_points": raw_points,
        "smoothed_ball_points": smoothed_points,
        "replay_keyframes": replay_keyframes,
    }


def build_projected_trajectory(data: dict[str, Any]) -> dict[str, Any]:
    """Build projected trajectory summary."""
    rows = data.get("tuned_zones", [])
    projected = [row for row in rows if row.get("projected_x") not in (None, "") and row.get("projected_y") not in (None, "")]
    xs = [_float(row.get("projected_x")) for row in projected]
    ys = [_float(row.get("projected_y")) for row in projected]
    xs = [value for value in xs if value is not None]
    ys = [value for value in ys if value is not None]
    return {
        "projected_points_count": len(projected),
        "unknown_zone_count": sum(1 for row in rows if row.get("tuned_zone") == "unknown"),
        "trajectory_bounds": {"min_x": min(xs) if xs else None, "max_x": max(xs) if xs else None, "min_y": min(ys) if ys else None, "max_y": max(ys) if ys else None},
        "projection_status_summary": dict(Counter(row.get("projection_status") or "unknown" for row in rows)),
        "court_zone_sequence": [row.get("tuned_zone") for row in rows],
        "depth_sequence": [row.get("tuned_depth") for row in rows],
        "lateral_sequence": [row.get("tuned_lateral_lane") for row in rows],
    }


def build_event_timeline(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Build replay event timeline section."""
    events = []
    for row in data.get("validated_timeline", []) or data.get("event_timeline", []):
        events.append(
            {
                "event_id": row.get("event_id"),
                "frame_index": _int(row.get("frame_index")),
                "timestamp_seconds": _float(row.get("timestamp_seconds")),
                "event_type": row.get("event_type") or "unknown",
                "possible_event": True,
                "source": row.get("event_source") or row.get("source") or "timeline",
                "confidence_like_score": _float(row.get("adjusted_confidence_like_score") or row.get("confidence_like_score")),
                "player_id": row.get("player_id") or "unknown",
                "side_state": row.get("player_side_state") or "unknown",
                "ball_position": {"x": _float(row.get("ball_x")), "y": _float(row.get("ball_y"))},
                "projected_position": {"x": _float(row.get("ball_projected_x")), "y": _float(row.get("ball_projected_y"))},
                "validation_status": row.get("validation_status") or "unknown",
                "reason": row.get("reason") or "",
                "limitations": ["Hypothesis only; not a confirmed tennis event."],
            }
        )
    return events


def build_rally_segments(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Build replay rally segment section."""
    attribution = data.get("player_event_attribution", [])
    players = sorted(set(row.get("player_id") for row in attribution if row.get("player_id")))
    segments = []
    for row in data.get("rally_segments", []):
        segments.append(
            {
                "rally_id": row.get("rally_id"),
                "start_frame": _int(row.get("start_frame")),
                "end_frame": _int(row.get("end_frame")),
                "duration_seconds": _float(row.get("duration_seconds")),
                "event_count": _int(row.get("event_count")),
                "possible_hit_count": _int(row.get("possible_hit_count")),
                "possible_bounce_count": _int(row.get("possible_bounce_count")),
                "players_involved": players,
                "confidence_like_score": _float(row.get("confidence_like_score")),
                "segmentation_reason": row.get("segmentation_reason") or "Conservative segment from first to last valid ball trajectory point.",
            }
        )
    return segments


def build_tactical_metrics(data: dict[str, Any]) -> dict[str, Any]:
    """Build tactical metrics section."""
    zones = data.get("tuned_zones", [])
    directions = data.get("directions", [])
    rally_summary = data.get("rally_tactical_summary", [])
    return {
        "depth_distribution": dict(Counter(row.get("tuned_depth") or "unknown" for row in zones)),
        "lateral_distribution": dict(Counter(row.get("tuned_lateral_lane") or "unknown" for row in zones)),
        "zone_distribution": dict(Counter(row.get("tuned_zone") or "unknown" for row in zones)),
        "direction_estimates": directions,
        "dominant_depth": _most_common(row.get("tuned_depth") for row in zones),
        "dominant_lateral_lane": _most_common(row.get("tuned_lateral_lane") for row in zones),
        "dominant_zone": _most_common(row.get("tuned_zone") for row in zones),
        "tactical_summary": rally_summary,
        "key_findings": [line[2:].strip() for line in data.get("key_findings_text", "").splitlines() if line.startswith("- ")],
    }


def build_confidence(data: dict[str, Any]) -> dict[str, Any]:
    """Build confidence section."""
    confidence = data.get("confidence_summary", {})
    return {
        "confidence_level": confidence.get("confidence_level") or "unknown",
        "confidence_reasons": confidence.get("confidence_reasons", []),
        "limiting_factors": confidence.get("limiting_factors", []),
        "recommended_validation_steps": confidence.get("recommended_validation_steps", []),
        "upstream_friction_notes": ["Stage 11 package friction was low."],
    }


def build_replay_schema(*, data: dict[str, Any], paths: dict[str, Path], generated_at: str, schema_version: str = DEFAULT_SCHEMA_VERSION) -> dict[str, Any]:
    """Build the replay data contract from court, trajectory, player, timeline and tactical outputs."""
    source_artifacts = {key: str(value) for key, value in paths.items()}
    camera_profiles = build_camera_profiles()
    visual_layers = build_visual_layers()
    return {
        "metadata": {
            "generated_at": generated_at,
            "project_name": "Tennis AI Vision",
            "stage": "stage_12_replay_schema",
            "schema_version": schema_version,
            "schema_name": SCHEMA_NAME,
            "input_package": str(paths["stage11_manifest"]),
            "source_pipeline_stage": "stage_11_report_package",
            "intended_use": "Data contract for deterministic analytical replay renderers.",
            "non_goals": ["photorealistic video generation", "official scoring", "official line calling", "confirmed coaching analysis"],
        },
        "source_video": build_source_video(data),
        "court_model": build_court_model(data),
        "camera_profiles": camera_profiles,
        "players": build_players(data),
        "ball_trajectory": build_ball_trajectory(data),
        "projected_trajectory": build_projected_trajectory(data),
        "event_timeline": build_event_timeline(data),
        "rally_segments": build_rally_segments(data),
        "tactical_metrics": build_tactical_metrics(data),
        "confidence": build_confidence(data),
        "visual_layers": visual_layers,
        "renderer_hints": build_renderer_hints(),
        "limitations": [
            "limited sample video",
            "limited labels",
            "possible_* events are hypotheses",
            "player identity is clothing/track heuristic",
            "no official line calling",
            "no official scoring",
            "no verified ball height",
            "no real 3D reconstruction yet",
            "no multi-angle camera support yet",
            "no real-time support yet",
        ],
        "source_artifacts": source_artifacts,
    }


def replay_keyframe_rows(schema: dict[str, Any]) -> list[dict[str, Any]]:
    """Return replay keyframes as flat CSV rows."""
    return schema["ball_trajectory"]["replay_keyframes"]


def replay_event_rows(schema: dict[str, Any]) -> list[dict[str, Any]]:
    """Return replay events as flat CSV rows."""
    rows = []
    for event in schema["event_timeline"]:
        rows.append(
            {
                "event_id": event.get("event_id"),
                "frame_index": event.get("frame_index"),
                "timestamp_seconds": event.get("timestamp_seconds"),
                "event_type": event.get("event_type"),
                "possible_event": event.get("possible_event"),
                "player_id": event.get("player_id"),
                "side_state": event.get("side_state"),
                "ball_x": event.get("ball_position", {}).get("x"),
                "ball_y": event.get("ball_position", {}).get("y"),
                "projected_x": event.get("projected_position", {}).get("x"),
                "projected_y": event.get("projected_position", {}).get("y"),
                "validation_status": event.get("validation_status"),
                "confidence_like_score": event.get("confidence_like_score"),
                "reason": event.get("reason"),
            }
        )
    return rows


def build_pretty_markdown(*, schema: dict[str, Any], verdict: str, friction: dict[str, Any], next_step: str) -> str:
    """Build plain-text-friendly replay schema markdown."""
    metadata = schema["metadata"]
    projected = schema["projected_trajectory"]
    lines = [
        "# Stage 12 Synthetic Rally Replay Data Schema",
        "",
        "SCHEMA STATUS",
        f"  Verdict: {verdict}",
        f"  Schema version: {metadata['schema_version']}",
        f"  Generated at: {metadata['generated_at']}",
        f"  Confidence level: {schema['confidence']['confidence_level']}",
        f"  Friction: {friction['score']} ({friction['band']})",
        "",
        "WHAT THIS IS",
        "  This is a data contract for future deterministic replay renderers.",
        "  It packages court, player, ball, event, tactical, confidence, and renderer hint data.",
        "",
        "WHAT THIS IS NOT",
        "  - not generated video",
        "  - not photorealistic rendering",
        "  - not official scoring",
        "  - not line calling",
        "",
        "REPLAY DATA INCLUDED",
        f"  Court model: {'available' if schema['court_model']['homography_status']['computed'] else 'limited'}",
        f"  Players: {len(schema['players'])}",
        f"  Ball trajectory points: {len(schema['ball_trajectory']['smoothed_ball_points'])}",
        f"  Projected points: {projected['projected_points_count']}",
        f"  Events: {len(schema['event_timeline'])}",
        f"  Rally segments: {len(schema['rally_segments'])}",
        f"  Tactical metrics: {'available' if schema['tactical_metrics'] else 'missing'}",
        f"  Camera presets: {len(schema['camera_profiles'])}",
        f"  Visual layers: {len(schema['visual_layers'])}",
        "",
        "RENDERER-READY DATA",
        "  A future renderer can consume normalized court keyframes, player identities,",
        "  possible_* event markers, rally segments, tactical zones, and camera profile hints.",
        "",
        "FIRST RECOMMENDED RENDERER",
        "  2D tactical replay renderer.",
        "",
        "FUTURE RENDERERS",
        "  - side-view ball flight",
        "  - baseline view",
        "  - multi-camera analytical replay",
        "  - synthetic stylized replay",
        "",
        "LIMITATIONS",
    ]
    lines.extend(f"  - {item}" for item in schema["limitations"])
    lines.extend(["", "NEXT STEP", f"  {next_step}"])
    return "\n".join(lines).rstrip() + "\n"


def _ball_point_from_row(row: dict[str, Any], tuned: dict[str, Any], *, raw: bool) -> dict[str, Any]:
    frame = _int(row.get("frame_index"))
    return {
        "frame_index": frame,
        "timestamp_seconds": _float(row.get("timestamp_seconds")),
        "image_x": _float(row.get("x") if raw else row.get("smooth_x") or row.get("raw_x")),
        "image_y": _float(row.get("y") if raw else row.get("smooth_y") or row.get("raw_y")),
        "projected_x": _float(row.get("projected_x") if raw else row.get("smooth_projected_x") or row.get("raw_projected_x")),
        "projected_y": _float(row.get("projected_y") if raw else row.get("smooth_projected_y") or row.get("raw_projected_y")),
        "zone": tuned.get("tuned_zone") or "unknown",
        "depth": tuned.get("tuned_depth") or "unknown",
        "lateral_lane": tuned.get("tuned_lateral_lane") or "unknown",
        "source": "raw_trajectory" if raw else "smoothed_trajectory",
        "confidence_like_score": _float(tuned.get("zone_confidence")),
        "is_interpolated": str(row.get("is_interpolated", "")).lower() == "true",
        "notes": tuned.get("notes") or "",
    }


def _ball_point_from_tuned(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "frame_index": _int(row.get("frame_index")),
        "timestamp_seconds": None,
        "image_x": _float(row.get("x")),
        "image_y": _float(row.get("y")),
        "projected_x": _float(row.get("projected_x")),
        "projected_y": _float(row.get("projected_y")),
        "zone": row.get("tuned_zone") or "unknown",
        "depth": row.get("tuned_depth") or "unknown",
        "lateral_lane": row.get("tuned_lateral_lane") or "unknown",
        "source": row.get("source") or "tuned_zone_assignment",
        "confidence_like_score": _float(row.get("zone_confidence")),
        "is_interpolated": False,
        "notes": row.get("notes") or "",
    }


def _frame_range(rows: list[dict[str, Any]]) -> list[int] | None:
    frames = [_int(row.get("frame_index")) for row in rows if _int(row.get("frame_index")) is not None]
    return [min(frames), max(frames)] if frames else None


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


def _most_common(values: Any) -> str:
    filtered = [str(value) for value in values if value not in (None, "")]
    if not filtered:
        return "unknown"
    return Counter(filtered).most_common(1)[0][0]
