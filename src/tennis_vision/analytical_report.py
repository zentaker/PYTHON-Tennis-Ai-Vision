"""Deterministic analytical report helpers for Stage 10."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


def read_csv_rows(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Read CSV rows and return warnings instead of raising on missing files."""
    if not path.exists():
        return [], [f"Missing CSV: {path}"]
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle)), []


def read_text_if_exists(path: Path) -> tuple[str, list[str]]:
    """Read optional text input."""
    if not path.exists():
        return "", [f"Missing text file: {path}"]
    return path.read_text(encoding="utf-8"), []


def read_stage_inputs(paths: dict[str, Path]) -> dict[str, Any]:
    """Load Stage 10 input files from prior stages."""
    data: dict[str, Any] = {"warnings": [], "errors": []}
    required = {"tactical_zones", "directions", "rally_summary"}
    csv_keys = [
        "tactical_zones",
        "directions",
        "rally_summary",
        "validated_timeline",
        "expanded_labels",
        "expanded_candidate_validation",
        "event_timeline",
        "rally_segments",
        "player_event_attribution",
        "main_players",
        "player_side_states",
        "refined_player_distances",
        "smoothed_trajectory",
        "trajectory_events",
    ]
    for key in csv_keys:
        rows, warnings = read_csv_rows(paths[key])
        data[key] = rows
        if warnings and key in required:
            data["errors"].extend(warnings)
        else:
            data["warnings"].extend(warnings)
    tactical_summary, summary_warnings = read_text_if_exists(paths["stage_9_tactical_summary"])
    data["stage_9_tactical_summary"] = tactical_summary
    data["warnings"].extend(summary_warnings)
    return data


def distribution(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    """Count values in a row field."""
    return dict(sorted(Counter(str(row.get(key) or "unknown") for row in rows).items()))


def top_values(values: dict[str, int], limit: int = 3) -> list[str]:
    """Return top distribution values in readable form."""
    return [f"{key}: {value}" for key, value in sorted(values.items(), key=lambda item: (-item[1], item[0]))[:limit]]


def summarize_ball_placement(tactical_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize tuned ball placement rows."""
    projected = [row for row in tactical_rows if row.get("projected_x") not in (None, "") and row.get("projected_y") not in (None, "")]
    unknown = [row for row in tactical_rows if row.get("tuned_zone") == "unknown"]
    depth = {"short": 0, "mid": 0, "deep": 0, "unknown": 0, **distribution(tactical_rows, "tuned_depth")}
    lateral = {"left": 0, "center": 0, "right": 0, "unknown": 0, **distribution(tactical_rows, "tuned_lateral_lane")}
    zones = distribution(tactical_rows, "tuned_zone")
    return {
        "label_count": len(tactical_rows),
        "projected_points_count": len(projected),
        "unknown_zone_count": len(unknown),
        "projection_coverage": round(len(projected) / len(tactical_rows), 3) if tactical_rows else 0,
        "depth_distribution": depth,
        "lateral_distribution": lateral,
        "zone_distribution": zones,
        "dominant_zones": top_values(zones),
    }


def summarize_direction_patterns(direction_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize approximate shot direction rows."""
    directions = {"crosscourt_like": 0, "down_the_line_like": 0, "center_like": 0, "unknown": 0, **distribution(direction_rows, "direction_type")}
    return {
        "direction_estimates_count": len(direction_rows),
        "direction_distribution": directions,
    }


def summarize_player_context(main_players: list[dict[str, Any]], refined_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize player identities and refined ball-player associations."""
    counts = Counter(row.get("nearest_player_id") or "unknown" for row in refined_rows)
    return {
        "player_identities_count": len(main_players),
        "player_a": {
            "associated_events": counts.get("player_a", 0),
            "notes": "Identity is appearance/track based; near/far side remains a state.",
        },
        "player_b": {
            "associated_events": counts.get("player_b", 0),
            "notes": "Identity is appearance/track based; near/far side remains a state.",
        },
        "unknown": {
            "associated_events": counts.get("unknown", 0) + counts.get("", 0),
            "notes": "Unknown means player attribution was weak or unavailable.",
        },
    }


def summarize_event_timeline(timeline_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize validated event timeline rows."""
    supported = [row for row in timeline_rows if str(row.get("validation_status")) == "supported_by_label" or str(row.get("label_support")).lower() == "true"]
    return {
        "timeline_events_count": len(timeline_rows),
        "supported_events_count": len(supported),
        "events_by_type": distribution(timeline_rows, "event_type"),
    }


def summarize_rally(rally_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize rally rows."""
    return {
        "rally_segments_count": len(rally_rows),
        "possible_hit_count": sum(_int(row.get("possible_hit_count")) for row in rally_rows),
        "possible_bounce_count": sum(_int(row.get("possible_bounce_count")) for row in rally_rows),
    }


def build_analysis_summary(data: dict[str, Any]) -> dict[str, Any]:
    """Build one structured summary from all Stage 10 inputs."""
    placement = summarize_ball_placement(data["tactical_zones"])
    directions = summarize_direction_patterns(data["directions"])
    players = summarize_player_context(data["main_players"], data["refined_player_distances"])
    events = summarize_event_timeline(data["validated_timeline"])
    rally = summarize_rally(data["rally_summary"])
    return {**placement, **directions, "player_context": players, "event_summary": events, **rally}


def build_plain_language_report(
    *,
    summary: dict[str, Any],
    key_findings: list[str],
    coaching_observations: list[dict[str, Any]],
    confidence: dict[str, Any],
    input_paths: dict[str, str],
    output_paths: dict[str, str],
    verdict: str,
    friction: dict[str, Any],
    timestamp: str,
    recommended_next_step: str,
) -> str:
    """Build the plain-text-friendly analytical report Markdown."""
    lines = [
        "# Stage 10 Analytical Rally Report",
        "",
        "REPORT STATUS",
        f"  Verdict: {verdict}",
        f"  Confidence level: {confidence['confidence_level']}",
        f"  Friction: {friction['score']} ({friction['band']})",
        "  Data source: Stage 9.1 tuned tactical outputs and validated timeline data.",
        f"  Generated at: {timestamp}",
        "",
        "EXECUTIVE SUMMARY",
    ]
    lines.extend(f"  - {finding}" for finding in key_findings[:6])
    lines.extend(
        [
            "",
            "WHAT THE SYSTEM ANALYZED",
            f"  - Number of ball labels: {summary['label_count']}",
            f"  - Number of projected ball points: {summary['projected_points_count']}",
            f"  - Number of rally segments: {summary['rally_segments_count']}",
            f"  - Number of timeline events: {summary['event_summary']['timeline_events_count']}",
            f"  - Number of player identities: {summary['player_context']['player_identities_count']}",
            f"  - Projection coverage: {summary['projection_coverage']}",
            f"  - Unknown zones: {summary['unknown_zone_count']}",
            "",
            "TACTICAL PLACEMENT SUMMARY",
            "  Depth:",
        ]
    )
    lines.extend(f"    - {key}: {value}" for key, value in summary["depth_distribution"].items())
    lines.append("")
    lines.append("  Lateral placement:")
    lines.extend(f"    - {key}: {value}" for key, value in summary["lateral_distribution"].items())
    lines.extend(["", "  Dominant zones:"])
    lines.extend(f"    - {zone}" for zone in summary["dominant_zones"])
    lines.extend(["", "SHOT DIRECTION SUMMARY", "  Direction estimates:"])
    lines.extend(f"    - {key}: {value}" for key, value in summary["direction_distribution"].items())
    lines.extend(
        [
            "",
            "  Interpretation:",
            "    Direction estimates are approximate and should be read as movement hypotheses.",
            "",
            "PLAYER / INTERACTION SUMMARY",
        ]
    )
    for player_id in ("player_a", "player_b", "unknown"):
        player = summary["player_context"][player_id]
        lines.extend([f"  {player_id}:", f"    - associated events: {player['associated_events']}", f"    - notes: {player['notes']}"])
    lines.extend(["", "EVENT TIMELINE SUMMARY"])
    for event_type, count in summary["event_summary"]["events_by_type"].items():
        lines.append(f"  - {event_type}: {count}")
    lines.extend(["", "COACHING-STYLE OBSERVATIONS"])
    for index, observation in enumerate(coaching_observations, start=1):
        lines.extend(
            [
                f"  Observation {index}:",
                f"    What it suggests: {observation['what_it_suggests']}",
                f"    Confidence: {observation['confidence']}",
                f"    Limitation: {observation['limitation']}",
            ]
        )
    lines.extend(["", "CONFIDENCE AND LIMITATIONS", f"  Confidence level: {confidence['confidence_level']}", "  Reasons:"])
    lines.extend(f"    - {reason}" for reason in confidence["confidence_reasons"])
    lines.extend(["", "  Limitations:"])
    lines.extend(f"    - {factor}" for factor in confidence["limiting_factors"])
    lines.extend(["", "NEXT RECOMMENDED STEP", f"  {recommended_next_step}", "", "VISUAL REFERENCES"])
    for key in ("tuned_ball_placement_map", "projection_coverage_map", "timeline_preview", "court_timeline_preview", "player_interaction_preview"):
        value = output_paths.get(key) or input_paths.get(key)
        if value:
            lines.append(f"  - {key}: {value}")
    return "\n".join(lines).rstrip() + "\n"


def write_report_markdown(path: Path, content: str) -> Path:
    """Write the final analytical report Markdown."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def write_report_json(path: Path, content: dict[str, Any]) -> Path:
    """Write the final analytical report JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _int(value: Any) -> int:
    try:
        if value in (None, ""):
            return 0
        return int(float(value))
    except (TypeError, ValueError):
        return 0
