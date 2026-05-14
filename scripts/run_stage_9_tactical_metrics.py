"""Run Stage 9 tactical metrics and shot zone prototype."""

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

from tennis_vision.court_zones import COURT_HEIGHT, COURT_WIDTH, describe_zone  # noqa: E402
from tennis_vision.friction import calculate_stage_9_friction_score  # noqa: E402
from tennis_vision.report import ensure_output_folders, utc_timestamp, write_json_report, write_markdown_report, write_timestamped_log  # noqa: E402
from tennis_vision.tactical_metrics import (  # noqa: E402
    build_ball_zone_assignments,
    build_rally_tactical_summary,
    distribution,
    estimate_shot_directions,
    most_common,
    read_csv_rows,
    summarize_player_context,
    write_csv,
    write_tactical_summary,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 9 tactical metrics and shot zone prototype.")
    parser.add_argument("--timeline", type=Path, default=PROJECT_ROOT / "outputs" / "timeline" / "stage_8_1_timeline_validation" / "validated_event_timeline.csv")
    parser.add_argument("--labels", type=Path, default=PROJECT_ROOT / "outputs" / "timeline" / "stage_8_1_timeline_validation" / "expanded_ball_labels.csv")
    parser.add_argument("--trajectory", type=Path, default=PROJECT_ROOT / "outputs" / "ball_tracking" / "stage_6_trajectory_smoothing" / "smoothed_trajectory.csv")
    parser.add_argument("--player-associations", type=Path, default=PROJECT_ROOT / "outputs" / "player_tracking" / "stage_7_1_player_filtering" / "refined_ball_player_distances.csv")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs" / "tactical" / "stage_9_tactical_metrics")
    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def determine_verdict(report: dict[str, Any]) -> str:
    flags = report["flags"]
    if flags["validated_timeline_missing"] or flags["zone_assignment_failed"]:
        return "blocked"
    if flags["too_few_ball_points"]:
        return "needs_more_labels"
    if flags["projected_points_missing"]:
        return "needs_better_projection"
    if flags["too_many_unknown_zones"] or flags["direction_estimation_unreliable"]:
        return "ready_with_warnings"
    return "ready_for_stage_10"


def recommended_next_step(report: dict[str, Any]) -> str:
    verdict = report["final_verdict"]
    if verdict == "ready_for_stage_10":
        return "Proceed to Stage 10: Analytical Report Generator and Coaching Summary Prototype."
    if verdict == "needs_more_labels":
        return "Collect more validated ball labels, then rerun Stage 8.1 and Stage 9."
    if verdict == "needs_better_projection":
        return "Review court projection and candidate projection coverage before tactical metrics."
    if verdict == "blocked":
        return "Fix missing Stage 8.1 timeline or Stage 9 input blockers, then rerun Stage 9."
    return "Proceed cautiously to Stage 9.1 court zone tuning or validate more events before Stage 10."


def draw_court_base(width: int = 720, height: int = 1560) -> np.ndarray:
    """Create a mini-court canvas scaled from normalized court dimensions."""
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    canvas[:] = (42, 117, 65)
    margin = 40
    cv2.rectangle(canvas, (margin, margin), (width - margin, height - margin), (255, 255, 255), 3)
    for x_frac in (1 / 3, 2 / 3):
        x = margin + int((width - 2 * margin) * x_frac)
        cv2.line(canvas, (x, margin), (x, height - margin), (215, 245, 220), 1)
    for y_frac in (1 / 6, 2 / 6, 3 / 6, 4 / 6, 5 / 6):
        y = margin + int((height - 2 * margin) * y_frac)
        cv2.line(canvas, (margin, y), (width - margin, y), (215, 245, 220), 1)
    return canvas


def map_court_point(projected_x: float, projected_y: float, canvas: np.ndarray) -> tuple[int, int]:
    """Map normalized court coordinates to image pixels."""
    height, width = canvas.shape[:2]
    margin = 40
    x = margin + int((projected_x / COURT_WIDTH) * (width - 2 * margin))
    y = margin + int((projected_y / COURT_HEIGHT) * (height - 2 * margin))
    return x, y


def save_court_zone_map(path: Path) -> str | None:
    """Save a mini-court zone grid."""
    canvas = draw_court_base()
    labels = [
        ("FDL", 0.16, 0.08), ("FDC", 0.50, 0.08), ("FDR", 0.84, 0.08),
        ("FML", 0.16, 0.25), ("FMC", 0.50, 0.25), ("FMR", 0.84, 0.25),
        ("FSL", 0.16, 0.42), ("FSC", 0.50, 0.42), ("FSR", 0.84, 0.42),
        ("NSL", 0.16, 0.58), ("NSC", 0.50, 0.58), ("NSR", 0.84, 0.58),
        ("NML", 0.16, 0.75), ("NMC", 0.50, 0.75), ("NMR", 0.84, 0.75),
        ("NDL", 0.16, 0.92), ("NDC", 0.50, 0.92), ("NDR", 0.84, 0.92),
    ]
    for text, x_frac, y_frac in labels:
        x = int(x_frac * canvas.shape[1]) - 22
        y = int(y_frac * canvas.shape[0])
        cv2.putText(canvas, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path) if cv2.imwrite(str(path), canvas) else None


def save_ball_placement_map(path: Path, zone_rows: list[dict[str, Any]]) -> str | None:
    """Save projected ball points on the zone map."""
    canvas = draw_court_base()
    points: list[tuple[int, int]] = []
    for row in zone_rows:
        if row.get("projected_x") is None or row.get("projected_y") is None or row.get("court_zone") == "unknown":
            continue
        point = map_court_point(float(row["projected_x"]), float(row["projected_y"]), canvas)
        points.append(point)
        color = (0, 240, 255) if row.get("depth") == "deep" else (0, 190, 255) if row.get("depth") == "mid" else (0, 130, 255)
        cv2.circle(canvas, point, 10, color, -1)
        cv2.putText(canvas, str(row["frame_index"]), (point[0] + 12, point[1] - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
    for start, end in zip(points, points[1:]):
        cv2.line(canvas, start, end, (0, 255, 255), 2)
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path) if cv2.imwrite(str(path), canvas) else None


def save_direction_preview(path: Path, zone_rows: list[dict[str, Any]], directions: list[dict[str, Any]]) -> str | None:
    """Save arrows between consecutive projected points."""
    canvas = draw_court_base()
    by_frame = {int(row["frame_index"]): row for row in zone_rows}
    for direction in directions:
        start = by_frame.get(int(direction["from_frame"]))
        end = by_frame.get(int(direction["to_frame"]))
        if not start or not end or start.get("court_zone") == "unknown" or end.get("court_zone") == "unknown":
            continue
        p1 = map_court_point(float(start["projected_x"]), float(start["projected_y"]), canvas)
        p2 = map_court_point(float(end["projected_x"]), float(end["projected_y"]), canvas)
        cv2.arrowedLine(canvas, p1, p2, (0, 255, 255), 3, tipLength=0.08)
        midpoint = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)
        cv2.putText(canvas, str(direction["direction_type"]), midpoint, cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path) if cv2.imwrite(str(path), canvas) else None


def save_summary_preview(path: Path, report: dict[str, Any]) -> str | None:
    """Save a lightweight image summary."""
    canvas = np.full((640, 960, 3), 246, dtype=np.uint8)
    lines = [
        "Stage 9 Tactical Metrics Prototype",
        f"Verdict: {report['final_verdict']}",
        f"Ball points: {report['ball_points_analyzed']}",
        f"Projected points: {report['projected_points_count']}",
        f"Unknown zones: {report['unknown_zone_count']}",
        f"Directions: {report['direction_estimates_count']}",
        "All outputs are approximate hypotheses.",
    ]
    for index, line in enumerate(lines):
        cv2.putText(canvas, line, (40, 70 + index * 60), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (30, 30, 30), 2)
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path) if cv2.imwrite(str(path), canvas) else None


def field_block(rows: list[tuple[str, Any]]) -> str:
    """Render report rows as plain-text blocks."""
    lines: list[str] = []
    for key, value in rows:
        lines.append(f"{key}:")
        lines.append(f"  {value if value not in (None, '') else 'Not available'}")
        lines.append("")
    return "\n".join(lines).rstrip()


def bullet_list(items: list[str], empty: str) -> str:
    return empty if not items else "\n".join(f"- {item}" for item in items)


def build_markdown_sections(report: dict[str, Any]) -> list[tuple[str, str]]:
    return [
        ("VERDICT", field_block([("Final verdict", report["final_verdict"]), ("Friction score", report["friction"]["score"]), ("Friction level", report["friction"]["band"])])),
        ("INPUTS USED", "\n".join(f"- {path}" for path in report["inputs_used"].values() if path)),
        (
            "TACTICAL METRICS SUMMARY",
            field_block(
                [
                    ("Ball points analyzed", report["ball_points_analyzed"]),
                    ("Projected points", report["projected_points_count"]),
                    ("Zone assignments", report["zone_assignments_count"]),
                    ("Unknown zones", report["unknown_zone_count"]),
                    ("Direction estimates", report["direction_estimates_count"]),
                    ("Rally summaries", report["rally_summaries_count"]),
                ]
            ),
        ),
        ("DEPTH DISTRIBUTION", field_block(list(report["depth_distribution"].items()))),
        ("LATERAL DISTRIBUTION", field_block(list(report["lateral_distribution"].items()))),
        (
            "EVENT / PLAYER CONTEXT",
            field_block(
                [
                    ("player_a associated events", report["player_context"]["player_a_associated_events"]),
                    ("player_b associated events", report["player_context"]["player_b_associated_events"]),
                    ("unknown player events", report["player_context"]["unknown_player_events"]),
                ]
            ),
        ),
        ("OUTPUT ARTIFACTS", "\n".join(f"- {path}" for path in report["output_paths"].values() if path)),
        (
            "PRODUCT OWNER INTERPRETATION",
            "Stage 9 converts validated trajectory and timeline evidence into first tactical placement signals. "
            "The court zones, shot directions, and rally summaries are approximate and hypothesis-based. "
            "They are useful for deciding whether a SwingVision-style tactical layer is becoming feasible, "
            "but they are not official scoring, line calling, confirmed shot classification, or coaching advice.",
        ),
        ("WARNINGS", bullet_list(report["warnings"], "No warnings.")),
        ("ERRORS", bullet_list(report["errors"], "No errors.")),
        ("NEXT STEP", report["recommended_next_step"]),
    ]


def update_lab_notebook_safely() -> tuple[dict[str, Path], str | None]:
    try:
        from tennis_vision.lab_notebook import lab_notebook_paths, update_lab_notebook

        update_lab_notebook(PROJECT_ROOT)
        return lab_notebook_paths(PROJECT_ROOT, "stage_9"), None
    except Exception as exc:
        try:
            from tennis_vision.lab_notebook import lab_notebook_paths

            return lab_notebook_paths(PROJECT_ROOT, "stage_9"), f"Lab notebook update failed: {exc}"
        except Exception:
            return {
                "stage_page": PROJECT_ROOT / "docs" / "lab-notebook" / "stage_9_tactical_metrics.md",
                "experiment_index": PROJECT_ROOT / "docs" / "lab-notebook" / "experiment_index.md",
            }, f"Lab notebook update failed: {exc}"


def print_summary(report: dict[str, Any], lab_paths: dict[str, Path]) -> None:
    try:
        from rich.console import Console

        Console().print(
            "\n".join(
                [
                    "Stage 9 Tactical Metrics",
                    f"Verdict: {report['final_verdict']}",
                    f"Friction: {report['friction']['score']} ({report['friction']['band']})",
                    f"Ball points analyzed: {report['ball_points_analyzed']}",
                    f"Projected points: {report['projected_points_count']}",
                    f"Zone assignments: {report['zone_assignments_count']}",
                    f"Unknown zones: {report['unknown_zone_count']}",
                    f"Direction estimates: {report['direction_estimates_count']}",
                    f"Rally summaries: {report['rally_summaries_count']}",
                    f"Lab notebook: {lab_paths['stage_page']}",
                    f"Recommended next step: {report['recommended_next_step']}",
                ]
            )
        )
    except ImportError:
        print(f"Verdict: {report['final_verdict']}")


def main() -> int:
    args = parse_args()
    ensure_output_folders(PROJECT_ROOT)
    output_dir = resolve_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timeline_path = resolve_path(args.timeline)
    labels_path = resolve_path(args.labels)
    trajectory_path = resolve_path(args.trajectory)
    associations_path = resolve_path(args.player_associations)
    projected_path = PROJECT_ROOT / "outputs" / "ball_tracking" / "stage_5_1_candidate_improvement" / "projected_improved_candidates.csv"
    rally_path = PROJECT_ROOT / "outputs" / "timeline" / "stage_8_event_timeline" / "rally_segments.csv"
    player_attribution_path = PROJECT_ROOT / "outputs" / "timeline" / "stage_8_event_timeline" / "player_event_attribution.csv"

    errors: list[str] = []
    warnings: list[str] = []
    timeline_rows, timeline_warnings = read_csv_rows(timeline_path)
    labels, label_warnings = read_csv_rows(labels_path)
    trajectory_rows, trajectory_warnings = read_csv_rows(trajectory_path)
    projected_rows, projected_warnings = read_csv_rows(projected_path)
    association_rows, association_warnings = read_csv_rows(associations_path)
    rally_rows, rally_warnings = read_csv_rows(rally_path)
    attribution_rows, attribution_warnings = read_csv_rows(player_attribution_path)
    errors.extend(timeline_warnings if not timeline_rows else [])
    errors.extend(label_warnings if not labels else [])
    warnings.extend(trajectory_warnings + projected_warnings + association_warnings + rally_warnings + attribution_warnings)

    zone_rows = build_ball_zone_assignments(labels=labels, trajectory_rows=trajectory_rows, projected_rows=projected_rows)
    directions = estimate_shot_directions(zone_rows)
    rally_summaries = build_rally_tactical_summary(rally_rows, zone_rows)
    player_context = summarize_player_context(association_rows)
    depth_distribution = {"short": 0, "mid": 0, "deep": 0, "unknown": 0, **distribution(zone_rows, "depth")}
    lateral_distribution = {"left": 0, "center": 0, "right": 0, "unknown": 0, **distribution(zone_rows, "lateral_lane")}
    zone_distribution = distribution(zone_rows, "court_zone")
    projected_points = [row for row in zone_rows if row.get("projected_x") is not None and row.get("projected_y") is not None]
    unknown_zone_count = sum(1 for row in zone_rows if row.get("court_zone") == "unknown")

    zone_csv = output_dir / "ball_zone_assignments.csv"
    direction_csv = output_dir / "shot_direction_estimates.csv"
    rally_csv = output_dir / "rally_tactical_summary.csv"
    summary_md = output_dir / "tactical_summary.md"
    write_csv(
        zone_csv,
        zone_rows,
        ["frame_index", "timestamp_seconds", "x", "y", "projected_x", "projected_y", "court_zone", "depth", "lateral_lane", "side", "source", "confidence_like_score", "notes"],
    )
    write_csv(direction_csv, directions, ["from_frame", "to_frame", "from_zone", "to_zone", "direction_type", "confidence_like_score", "reason"])
    write_csv(
        rally_csv,
        rally_summaries,
        ["rally_id", "start_frame", "end_frame", "duration_seconds", "event_count", "possible_hit_count", "possible_bounce_count", "dominant_depth", "dominant_lateral_lane", "dominant_zone", "confidence_like_score", "notes"],
    )

    court_zone_map = save_court_zone_map(output_dir / "court_zone_map.jpg")
    ball_map = save_ball_placement_map(output_dir / "ball_placement_map.jpg", zone_rows)
    direction_preview = save_direction_preview(output_dir / "shot_direction_preview.jpg", zone_rows, directions)
    summary_preview = None

    if not timeline_rows:
        errors.append(f"Validated timeline missing or unreadable: {timeline_path}")
    if len(zone_rows) < 10:
        warnings.append("Fewer than 10 visible ball labels are available for tactical metrics.")
    if projected_rows and unknown_zone_count:
        warnings.append("Some visible labels do not have projected court coordinates; zone coverage is incomplete.")
    if not directions:
        warnings.append("Direction estimates could not be generated from the available projected points.")
    if not rally_summaries:
        warnings.append("Rally tactical summary could not be generated.")

    flags = {
        "validated_timeline_missing": not timeline_rows,
        "projected_points_missing": len(projected_points) == 0,
        "too_few_ball_points": len(zone_rows) < 10,
        "zone_assignment_failed": not zone_rows,
        "too_many_unknown_zones": bool(zone_rows and unknown_zone_count / max(len(zone_rows), 1) > 0.4),
        "direction_estimation_unreliable": len(directions) < 2,
        "rally_summary_failed": not rally_summaries,
        "visual_generation_failed": court_zone_map is None or ball_map is None or direction_preview is None,
    }
    friction = calculate_stage_9_friction_score(**flags, errors_count=len(errors), warnings_count=len(warnings))
    report: dict[str, Any] = {
        "timestamp": utc_timestamp(),
        "stage": "stage_9_tactical_metrics",
        "inputs_used": {
            "validated_timeline": str(timeline_path),
            "expanded_labels": str(labels_path),
            "expanded_candidate_validation": str(PROJECT_ROOT / "outputs" / "timeline" / "stage_8_1_timeline_validation" / "expanded_candidate_validation.csv"),
            "stage_8_event_timeline": str(PROJECT_ROOT / "outputs" / "timeline" / "stage_8_event_timeline" / "event_timeline.csv"),
            "rally_segments": str(rally_path),
            "player_event_attribution": str(player_attribution_path),
            "smoothed_trajectory": str(trajectory_path),
            "projected_improved_candidates": str(projected_path),
            "refined_player_associations": str(associations_path),
        },
        "ball_points_analyzed": len(zone_rows),
        "projected_points_count": len(projected_points),
        "zone_assignments_count": len(zone_rows),
        "unknown_zone_count": unknown_zone_count,
        "zone_distribution": zone_distribution,
        "depth_distribution": depth_distribution,
        "lateral_distribution": lateral_distribution,
        "direction_estimates_count": len(directions),
        "rally_summaries_count": len(rally_summaries),
        "player_associated_events_count": len(attribution_rows),
        "player_context": player_context,
        "warnings": warnings,
        "errors": errors,
        "flags": flags,
        "friction": friction,
        "final_verdict": "blocked",
        "recommended_next_step": "",
        "output_paths": {
            "ball_zone_assignments_csv": str(zone_csv),
            "shot_direction_estimates_csv": str(direction_csv),
            "rally_tactical_summary_csv": str(rally_csv),
            "tactical_summary_md": str(summary_md),
            "court_zone_map": court_zone_map,
            "ball_placement_map": ball_map,
            "shot_direction_preview": direction_preview,
            "tactical_summary_preview": None,
        },
    }
    report["final_verdict"] = determine_verdict(report)
    report["recommended_next_step"] = recommended_next_step(report)
    write_tactical_summary(
        summary_md,
        {
            "ball_points_analyzed": report["ball_points_analyzed"],
            "projected_points_count": report["projected_points_count"],
            "most_frequent_zone": most_common(row.get("court_zone") for row in zone_rows),
            "dominant_depth": most_common(row.get("depth") for row in zone_rows),
            "dominant_lateral_lane": most_common(row.get("lateral_lane") for row in zone_rows),
            "recommended_next_step": report["recommended_next_step"],
        },
    )
    summary_preview = save_summary_preview(output_dir / "tactical_summary_preview.jpg", report)
    report["output_paths"]["tactical_summary_preview"] = summary_preview
    if summary_preview is None:
        report["warnings"].append("Tactical summary preview could not be generated.")

    log_path = write_timestamped_log(
        PROJECT_ROOT,
        "stage_9_tactical_metrics",
        [
            f"timestamp={report['timestamp']}",
            f"verdict={report['final_verdict']}",
            f"friction={report['friction']['score']} ({report['friction']['band']})",
            f"ball_points={report['ball_points_analyzed']}",
            f"projected_points={report['projected_points_count']}",
            f"unknown_zones={report['unknown_zone_count']}",
        ],
    )
    report["log_path"] = str(log_path)
    report["json_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_9_tactical_metrics_report.json")
    report["markdown_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_9_tactical_metrics_report.md")
    json_path = Path(report["json_report_path"])
    markdown_path = Path(report["markdown_report_path"])
    write_json_report(json_path, report)
    write_markdown_report(markdown_path, "Stage 9 Tactical Metrics and Shot Zone Prototype Report", build_markdown_sections(report))

    lab_paths, notebook_warning = update_lab_notebook_safely()
    if notebook_warning:
        report["warnings"].append(notebook_warning)
        write_json_report(json_path, report)
        write_markdown_report(markdown_path, "Stage 9 Tactical Metrics and Shot Zone Prototype Report", build_markdown_sections(report))
        print(f"Warning: {notebook_warning}")
    print_summary(report, lab_paths)
    return 1 if report["final_verdict"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
