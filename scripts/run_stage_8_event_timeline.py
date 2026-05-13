"""Run Stage 8 shot/event timeline and rally segmentation prototype."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import cv2
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from tennis_vision.event_timeline import (  # noqa: E402
    attach_player_side_states,
    build_player_event_attribution,
    events_by_type,
    make_trajectory_events,
    merge_timeline_events,
    read_fps,
    read_interactions,
    read_player_side_states,
    read_refined_associations,
    read_smoothed_trajectory,
    read_stage_events,
    write_player_event_attribution_csv,
    write_timeline_csv,
    write_timeline_json,
)
from tennis_vision.friction import calculate_stage_8_friction_score  # noqa: E402
from tennis_vision.rally_segmentation import build_rally_segments, write_rally_segments_csv  # noqa: E402
from tennis_vision.report import ensure_output_folders, utc_timestamp, write_json_report, write_markdown_report, write_timestamped_log  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 8 shot/event timeline and rally segmentation prototype.")
    parser.add_argument("--merge-window", type=int, default=5)
    parser.add_argument(
        "--trajectory",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "ball_tracking" / "stage_6_trajectory_smoothing" / "smoothed_trajectory.csv",
    )
    parser.add_argument(
        "--events",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "ball_tracking" / "stage_6_trajectory_smoothing" / "trajectory_events.csv",
    )
    parser.add_argument(
        "--interactions",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "player_tracking" / "stage_7_player_interaction" / "ball_player_interactions.csv",
    )
    parser.add_argument(
        "--player-identities",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "player_tracking" / "stage_7_1_player_filtering" / "main_players.csv",
    )
    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def determine_verdict(report: dict[str, Any]) -> str:
    flags = report["flags"]
    if flags["trajectory_missing"] or flags["no_timeline_events"] or flags["no_rally_segments"]:
        return "blocked"
    if flags["too_few_points"]:
        return "ready_with_warnings"
    if flags["player_attribution_failed"] or flags["source_events_missing"]:
        return "ready_with_warnings"
    return "ready_for_stage_9"


def recommended_next_step(report: dict[str, Any]) -> str:
    if report["final_verdict"] == "ready_for_stage_9":
        return "Proceed to Stage 9: tactical metrics and shot zone prototype."
    if report["flags"]["too_few_points"]:
        return "Proceed to Stage 8.1: expand labels and timeline validation before tactical metrics."
    if report["flags"]["player_attribution_failed"]:
        return "Proceed to Stage 8.2: event validation and manual event labeling helper."
    if report["final_verdict"] == "blocked":
        return "Fix missing Stage 6 trajectory inputs, then rerun Stage 8."
    return "Review warnings, then decide between Stage 8.1 validation and Stage 9 prototype work."


def save_timeline_preview(timeline_rows: list[dict[str, Any]], rally_segments: list[dict[str, Any]], output_path: Path) -> str | None:
    """Save a simple frame-axis event timeline chart."""
    if not timeline_rows:
        return None
    width, height = 1280, 420
    canvas = np.full((height, width, 3), 247, dtype=np.uint8)
    frames = [int(row["frame_index"]) for row in timeline_rows]
    min_frame, max_frame = min(frames), max(frames)
    span = max(max_frame - min_frame, 1)
    left, right, axis_y = 80, width - 80, 220
    colors = {
        "trajectory_point": (120, 120, 120),
        "possible_hit": (0, 80, 255),
        "possible_bounce": (0, 180, 255),
        "ball_near_player": (80, 160, 40),
        "ball_approaching_player": (180, 120, 20),
        "ball_leaving_player": (180, 80, 120),
        "possible_direction_change": (180, 80, 180),
        "possible_speed_spike": (255, 120, 0),
        "possible_speed_drop": (90, 90, 220),
    }
    cv2.line(canvas, (left, axis_y), (right, axis_y), (40, 40, 40), 2)
    for segment in rally_segments:
        start_x = left + int((int(segment["start_frame"]) - min_frame) / span * (right - left))
        end_x = left + int((int(segment["end_frame"]) - min_frame) / span * (right - left))
        cv2.rectangle(canvas, (start_x, axis_y - 60), (end_x, axis_y + 60), (220, 240, 230), -1)
        cv2.rectangle(canvas, (start_x, axis_y - 60), (end_x, axis_y + 60), (90, 140, 100), 1)
    cv2.line(canvas, (left, axis_y), (right, axis_y), (40, 40, 40), 2)
    for row in timeline_rows:
        x = left + int((int(row["frame_index"]) - min_frame) / span * (right - left))
        color = colors.get(str(row["event_type"]), (0, 0, 0))
        cv2.drawMarker(canvas, (x, axis_y), color, cv2.MARKER_TRIANGLE_UP, 22, 2)
        label = f"{row['frame_index']} {row['event_type']}"
        if row.get("player_id"):
            label += f" {row['player_id']}"
        cv2.putText(canvas, label, (max(8, x - 70), axis_y - 78), cv2.FONT_HERSHEY_SIMPLEX, 0.42, color, 1)
    cv2.putText(canvas, "Stage 8 prototype timeline: events are hypotheses", (32, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (20, 20, 20), 2)
    cv2.putText(canvas, f"frames {min_frame}-{max_frame}", (32, height - 32), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (20, 20, 20), 1)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return str(output_path) if cv2.imwrite(str(output_path), canvas) else None


def save_court_timeline_preview(timeline_rows: list[dict[str, Any]], output_path: Path) -> str | None:
    """Save projected event locations on a mini-court style canvas."""
    projected = [row for row in timeline_rows if row.get("ball_projected_x") is not None and row.get("ball_projected_y") is not None]
    if not projected:
        return None
    width, height = 420, 760
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    canvas[:] = (38, 112, 62)
    cv2.rectangle(canvas, (30, 30), (width - 30, height - 30), (255, 255, 255), 2)
    cv2.line(canvas, (30, height // 2), (width - 30, height // 2), (255, 255, 255), 1)
    xs = [float(row["ball_projected_x"]) for row in projected]
    ys = [float(row["ball_projected_y"]) for row in projected]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max(max_x - min_x, 1.0)
    span_y = max(max_y - min_y, 1.0)

    def map_point(row: dict[str, Any]) -> tuple[int, int]:
        x = 50 + int((float(row["ball_projected_x"]) - min_x) / span_x * (width - 100))
        y = 60 + int((float(row["ball_projected_y"]) - min_y) / span_y * (height - 120))
        return x, y

    points = [map_point(row) for row in projected]
    for start, end in zip(points, points[1:]):
        cv2.line(canvas, start, end, (0, 255, 255), 2)
    for row, point in zip(projected, points):
        color = (0, 90, 255) if row.get("event_type") == "possible_hit" else (0, 255, 255)
        cv2.circle(canvas, point, 6, color, -1)
        cv2.putText(canvas, str(row["frame_index"]), (point[0] + 8, point[1] - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    cv2.putText(canvas, "Projected timeline preview", (34, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return str(output_path) if cv2.imwrite(str(output_path), canvas) else None


def write_timeline_summary(path: Path, timeline_rows: list[dict[str, Any]], rally_segments: list[dict[str, Any]]) -> str:
    """Write a compact human-readable event timeline."""
    lines = ["# Stage 8 Timeline Summary", ""]
    for row in timeline_rows:
        player = f" near {row['player_id']}" if row.get("player_id") else ""
        lines.append(f"- Frame {row['frame_index']} - {row['event_type']}{player} - {row.get('reason') or 'hypothesis'}")
    lines.extend(["", "## Rally Segments", ""])
    for row in rally_segments:
        lines.append(f"- {row['rally_id']}: frames {row['start_frame']} to {row['end_frame']}, {row['event_count']} events.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return str(path)


def _metric_table(rows: list[tuple[str, Any]]) -> str:
    lines = ["| Metric | Value |", "|---|---:|"]
    for key, value in rows:
        lines.append(f"| {key} | {value if value is not None else 'Not available'} |")
    return "\n".join(lines)


def _event_table(counts: dict[str, int]) -> str:
    lines = ["| Event type | Count |", "|---|---:|"]
    if not counts:
        lines.append("| None | 0 |")
    for event_type, count in sorted(counts.items()):
        lines.append(f"| {event_type} | {count} |")
    return "\n".join(lines)


def _rally_table(rows: list[dict[str, Any]]) -> str:
    lines = ["| Rally ID | Start frame | End frame | Events | Possible hits | Possible bounces | Confidence |", "|---|---:|---:|---:|---:|---:|---:|"]
    if not rows:
        lines.append("| None | 0 | 0 | 0 | 0 | 0 | 0 |")
    for row in rows:
        lines.append(f"| {row['rally_id']} | {row['start_frame']} | {row['end_frame']} | {row['event_count']} | {row['possible_hit_count']} | {row['possible_bounce_count']} | {row['confidence_like_score']} |")
    return "\n".join(lines)


def _bullet_list(items: list[str], empty_text: str) -> str:
    return empty_text if not items else "\n".join(f"- {item}" for item in items)


def build_markdown_sections(report: dict[str, Any]) -> list[tuple[str, str]]:
    interpretation = (
        "Stage 8 creates a first structured timeline by merging ball trajectory anchors, Stage 6 event hypotheses, "
        "Stage 7 ball-player hypotheses, and Stage 7.1 stabilized player identities. "
        "The result is useful as a prototype evidence map, but it is not official scoring, line calling, or confirmed shot classification. "
    )
    if report["flags"]["too_few_points"]:
        interpretation += "The current timeline is sparse, so more labels are needed before treating rally segmentation as meaningful."
    else:
        interpretation += "The current inputs are sufficient for a cautious Stage 9 tactical prototype."
    return [
        ("Verdict", f"- Final verdict: {report['final_verdict']}\n- Friction score: {report['friction']['score']}\n- Friction level: {report['friction']['band']}"),
        ("Inputs", "\n".join(f"- {name}: `{path}`" for name, path in report["inputs_used"].items() if path)),
        (
            "Timeline summary",
            _metric_table(
                [
                    ("trajectory points", report["trajectory_points_count"]),
                    ("source events", report["source_event_count"]),
                    ("merged timeline events", report["merged_timeline_event_count"]),
                    ("rally segments", report["rally_segments_count"]),
                    ("player-attributed events", report["player_attributed_events_count"]),
                    ("merge window", report["merge_window"]),
                ]
            ),
        ),
        ("Events by type", _event_table(report["events_by_type"])),
        ("Rally segments", _rally_table(report["rally_segments"])),
        (
            "Player attribution",
            "Events are attributed to `player_a` / `player_b` when Stage 7.1 identity evidence exists near the event frame. Near/far side remains a side state, not permanent identity.",
        ),
        (
            "Visual outputs",
            f"- Timeline preview: `{report['output_paths']['timeline_preview']}`\n- Court timeline preview: `{report['output_paths']['court_timeline_preview']}`\n- Timeline summary markdown: `{report['output_paths']['timeline_summary']}`",
        ),
        ("Product Owner interpretation", interpretation),
        ("Warnings", _bullet_list(report["warnings"], "No warnings.")),
        ("Errors", _bullet_list(report["errors"], "No errors.")),
        ("Next step", report["recommended_next_step"]),
    ]


def update_lab_notebook_safely() -> tuple[dict[str, Path], str | None]:
    try:
        from tennis_vision.lab_notebook import lab_notebook_paths, update_lab_notebook

        update_lab_notebook(PROJECT_ROOT)
        return lab_notebook_paths(PROJECT_ROOT, "stage_8"), None
    except Exception as exc:
        try:
            from tennis_vision.lab_notebook import lab_notebook_paths

            return lab_notebook_paths(PROJECT_ROOT, "stage_8"), f"Lab notebook update failed: {exc}"
        except Exception:
            return {
                "stage_page": PROJECT_ROOT / "docs" / "lab-notebook" / "stage_8_event_timeline.md",
                "experiment_index": PROJECT_ROOT / "docs" / "lab-notebook" / "experiment_index.md",
            }, f"Lab notebook update failed: {exc}"


def print_summary(report: dict[str, Any], lab_paths: dict[str, Path]) -> None:
    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(title="Stage 8 Event Timeline")
        table.add_column("Field")
        table.add_column("Value")
        for field, value in [
            ("Verdict", report["final_verdict"]),
            ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"),
            ("Trajectory points", report["trajectory_points_count"]),
            ("Source events", report["source_event_count"]),
            ("Timeline events", report["merged_timeline_event_count"]),
            ("Rally segments", report["rally_segments_count"]),
            ("Player-attributed events", report["player_attributed_events_count"]),
            ("Events by type", str(report["events_by_type"])),
            ("Lab notebook", str(lab_paths["stage_page"])),
            ("Recommended next step", report["recommended_next_step"]),
        ]:
            table.add_row(str(field), str(value))
        Console().print(table)
    except ImportError:
        print(f"Verdict: {report['final_verdict']}")
        print(f"Timeline events: {report['merged_timeline_event_count']}")


def main() -> int:
    args = parse_args()
    ensure_output_folders(PROJECT_ROOT)
    output_dir = PROJECT_ROOT / "outputs" / "timeline" / "stage_8_event_timeline"
    output_dir.mkdir(parents=True, exist_ok=True)

    trajectory_path = resolve_path(args.trajectory)
    events_path = resolve_path(args.events)
    interactions_path = resolve_path(args.interactions)
    identities_path = resolve_path(args.player_identities)
    refined_path = PROJECT_ROOT / "outputs" / "player_tracking" / "stage_7_1_player_filtering" / "refined_ball_player_distances.csv"
    side_states_path = PROJECT_ROOT / "outputs" / "player_tracking" / "stage_7_1_player_filtering" / "player_side_states.csv"

    warnings: list[str] = []
    errors: list[str] = []
    trajectory_rows, trajectory_errors = read_smoothed_trajectory(trajectory_path)
    errors.extend(trajectory_errors)
    stage_events, stage_event_warnings = read_stage_events(events_path)
    interactions, interaction_warnings = read_interactions(interactions_path)
    refined_events, refined_warnings = read_refined_associations(refined_path)
    warnings.extend(stage_event_warnings)
    warnings.extend(interaction_warnings)
    warnings.extend(refined_warnings)
    if not identities_path.exists():
        warnings.append(f"Stage 7.1 main player identity CSV not found: {identities_path}")

    fps = read_fps(PROJECT_ROOT / "outputs" / "reports" / "stage_1_video_probe_report.json")
    trajectory_events = make_trajectory_events(trajectory_rows)
    source_events = stage_events + interactions + refined_events
    timeline = merge_timeline_events(trajectory_events + source_events, args.merge_window, fps)
    timeline = attach_player_side_states(timeline, read_player_side_states(side_states_path))
    attribution_rows = build_player_event_attribution(timeline, refined_events, merge_window=args.merge_window)
    rally_segments = build_rally_segments(trajectory_rows, timeline, fps=fps)

    timeline_csv = output_dir / "event_timeline.csv"
    timeline_json = output_dir / "event_timeline.json"
    rally_csv = output_dir / "rally_segments.csv"
    attribution_csv = output_dir / "player_event_attribution.csv"
    write_timeline_csv(timeline_csv, timeline)
    write_timeline_json(timeline_json, timeline)
    write_rally_segments_csv(rally_csv, rally_segments)
    write_player_event_attribution_csv(attribution_csv, attribution_rows)

    timeline_preview = save_timeline_preview(timeline, rally_segments, output_dir / "timeline_preview.jpg")
    court_preview = save_court_timeline_preview(timeline, output_dir / "court_timeline_preview.jpg")
    timeline_summary = write_timeline_summary(output_dir / "timeline_summary.md", timeline, rally_segments)
    visual_failed = timeline_preview is None or court_preview is None
    if timeline_preview is None:
        warnings.append("Timeline preview image could not be generated.")
    if court_preview is None:
        warnings.append("Court timeline preview could not be generated; projected coordinates may be unavailable.")
    anchor_count = len([row for row in trajectory_rows if not row.get("is_interpolated")])
    attributed_count = sum(1 for row in attribution_rows if row.get("player_id") and row.get("player_id") != "unknown")

    flags = {
        "trajectory_missing": not trajectory_path.exists() or not trajectory_rows,
        "source_events_missing": not source_events,
        "player_identity_missing": not identities_path.exists(),
        "no_timeline_events": not timeline,
        "no_rally_segments": not rally_segments,
        "player_attribution_failed": attributed_count == 0,
        "visual_generation_failed": visual_failed,
        "too_few_points": anchor_count < 8,
    }
    if flags["too_few_points"] and anchor_count:
        warnings.append("Only a small number of high-confidence trajectory anchors are available; timeline segmentation is preliminary.")
    if flags["source_events_missing"]:
        warnings.append("No Stage 6/7/7.1 source events were available; timeline is trajectory-only.")
    if flags["player_attribution_failed"] and timeline:
        warnings.append("No timeline events could be attributed to stabilized player identities.")

    friction = calculate_stage_8_friction_score(**flags, errors_count=len(errors), warnings_count=len(warnings))
    counts = events_by_type(timeline)
    report: dict[str, Any] = {
        "timestamp": utc_timestamp(),
        "stage": "stage_8_event_timeline",
        "inputs_used": {
            "Stage 6 smoothed trajectory": str(trajectory_path),
            "Stage 6 trajectory events": str(events_path) if events_path.exists() else None,
            "Stage 7 interactions": str(interactions_path) if interactions_path.exists() else None,
            "Stage 7.1 main players": str(identities_path) if identities_path.exists() else None,
            "Stage 7.1 refined distances": str(refined_path) if refined_path.exists() else None,
            "Stage 7.1 side states": str(side_states_path) if side_states_path.exists() else None,
        },
        "trajectory_points_count": anchor_count,
        "source_event_count": len(source_events),
        "merged_timeline_event_count": len(timeline),
        "rally_segments_count": len(rally_segments),
        "player_attributed_events_count": attributed_count,
        "events_by_type": counts,
        "merge_window": args.merge_window,
        "rally_segments": rally_segments,
        "warnings": warnings,
        "errors": errors,
        "flags": flags,
        "friction": friction,
        "final_verdict": "blocked",
        "recommended_next_step": "",
        "output_paths": {
            "event_timeline_csv": str(timeline_csv),
            "event_timeline_json": str(timeline_json),
            "rally_segments_csv": str(rally_csv),
            "player_event_attribution_csv": str(attribution_csv),
            "timeline_preview": timeline_preview,
            "court_timeline_preview": court_preview,
            "timeline_summary": timeline_summary,
        },
        "json_report_path": str(PROJECT_ROOT / "outputs" / "reports" / "stage_8_event_timeline_report.json"),
        "markdown_report_path": str(PROJECT_ROOT / "outputs" / "reports" / "stage_8_event_timeline_report.md"),
        "log_path": "",
    }
    report["final_verdict"] = determine_verdict(report)
    report["recommended_next_step"] = recommended_next_step(report)

    log_path = write_timestamped_log(
        PROJECT_ROOT,
        "stage_8_event_timeline",
        [
            f"timestamp={report['timestamp']}",
            f"verdict={report['final_verdict']}",
            f"friction={friction['score']} ({friction['band']})",
            f"trajectory_points={anchor_count}",
            f"source_events={len(source_events)}",
            f"timeline_events={len(timeline)}",
            f"rally_segments={len(rally_segments)}",
        ],
    )
    report["log_path"] = str(log_path)

    json_path = Path(report["json_report_path"])
    markdown_path = Path(report["markdown_report_path"])
    write_json_report(json_path, report)
    write_markdown_report(markdown_path, "Stage 8 Shot/Event Timeline and Rally Segmentation Prototype Report", build_markdown_sections(report))

    lab_paths, notebook_warning = update_lab_notebook_safely()
    if notebook_warning:
        report["warnings"].append(notebook_warning)
        write_json_report(json_path, report)
        write_markdown_report(markdown_path, "Stage 8 Shot/Event Timeline and Rally Segmentation Prototype Report", build_markdown_sections(report))
        print(f"Warning: {notebook_warning}")

    print_summary(report, lab_paths)
    return 1 if report["final_verdict"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
