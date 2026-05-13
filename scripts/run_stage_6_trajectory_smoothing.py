"""Run Stage 6 trajectory smoothing and event segmentation probe."""

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

from tennis_vision.event_segmentation import detect_events, events_by_type, write_events_csv  # noqa: E402
from tennis_vision.friction import calculate_stage_6_friction_score  # noqa: E402
from tennis_vision.report import ensure_output_folders, utc_timestamp, write_json_report, write_markdown_report, write_timestamped_log  # noqa: E402
from tennis_vision.trajectory_smoothing import (  # noqa: E402
    build_raw_trajectory,
    enrich_with_projected_candidates,
    interpolate_trajectory,
    moving_average_smooth,
    read_fps,
    read_improved_candidates,
    read_manual_labels,
    read_projected_candidates,
    write_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 6 trajectory smoothing and event segmentation probe.")
    parser.add_argument(
        "--improved-candidates",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "ball_tracking" / "stage_5_1_candidate_improvement" / "improved_ball_candidates.csv",
    )
    parser.add_argument(
        "--projected-candidates",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "ball_tracking" / "stage_5_1_candidate_improvement" / "projected_improved_candidates.csv",
    )
    parser.add_argument(
        "--manual-labels",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "ball_tracking" / "stage_4_1_manual_labels" / "manual_ball_labels.csv",
    )
    parser.add_argument("--window-size", type=int, default=3)
    parser.add_argument("--allow-interpolation", dest="allow_interpolation", action="store_true", default=True)
    parser.add_argument("--no-interpolation", dest="allow_interpolation", action="store_false")
    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def determine_verdict(report: dict[str, Any]) -> str:
    flags = report["flags"]
    if flags["improved_candidates_missing"] or flags["smoothing_failed"]:
        return "blocked"
    if report["trajectory_points_count"] < 4:
        return "needs_more_labels"
    if report["projected_candidates_available"] and report["events_count"] > 0 and report["trajectory_points_count"] >= 5:
        return "ready_for_stage_7"
    return "ready_with_warnings"


def recommended_next_step(report: dict[str, Any]) -> str:
    verdict = report["final_verdict"]
    if verdict == "ready_for_stage_7":
        return "Proceed to Stage 7: player tracking and ball-player interaction probe."
    if verdict == "needs_more_labels":
        return "Proceed to Stage 6.1: expand manual labels and rerun trajectory smoothing."
    if verdict == "blocked":
        return "Fix missing Stage 5.1 improved candidates, then rerun Stage 6."
    return "Review event hypotheses, then decide whether to expand labels or proceed cautiously to Stage 7."


def save_image_trajectory_preview(
    *,
    raw_rows: list[dict[str, Any]],
    smoothed_rows: list[dict[str, Any]],
    manual_labels: list[dict[str, Any]],
    events: list[dict[str, Any]],
    output_path: Path,
    size: tuple[int, int] = (1280, 720),
) -> str | None:
    """Save image-space trajectory preview."""
    if not raw_rows:
        return None
    canvas = np.full((size[1], size[0], 3), 245, dtype=np.uint8)
    scale_x = size[0] / 3840
    scale_y = size[1] / 2160
    manual_points = [(int(round(label["x"] * scale_x)), int(round(label["y"] * scale_y))) for label in manual_labels]
    raw_points = [(int(round(row["x"] * scale_x)), int(round(row["y"] * scale_y))) for row in raw_rows]
    smooth_points = [(int(round(row["smooth_x"] * scale_x)), int(round(row["smooth_y"] * scale_y))) for row in smoothed_rows if not row.get("is_interpolated")]
    for point in manual_points:
        cv2.circle(canvas, point, 7, (0, 0, 255), -1)
    for point in raw_points:
        cv2.circle(canvas, point, 6, (255, 0, 0), 2)
    for start, end in zip(smooth_points, smooth_points[1:]):
        cv2.line(canvas, start, end, (0, 180, 0), 2)
    for event in events:
        point = (int(round(event["x"] * scale_x)), int(round(event["y"] * scale_y)))
        cv2.drawMarker(canvas, point, (0, 165, 255), cv2.MARKER_STAR, 18, 2)
        cv2.putText(canvas, event["event_type"], (point[0] + 8, point[1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)
    cv2.putText(canvas, "red=manual blue=raw green=smoothed orange=event hypothesis", (24, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if cv2.imwrite(str(output_path), canvas):
        return str(output_path)
    return None


def save_court_trajectory_preview(
    *,
    smoothed_rows: list[dict[str, Any]],
    events: list[dict[str, Any]],
    output_path: Path,
    size: tuple[int, int] = (360, 780),
) -> str | None:
    """Save court-space trajectory preview."""
    projected_rows = [row for row in smoothed_rows if row.get("smooth_projected_x") is not None and not row.get("is_interpolated")]
    if not projected_rows:
        return None
    width, height = size
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    canvas[:] = (34, 105, 55)
    cv2.rectangle(canvas, (0, 0), (width - 1, height - 1), (255, 255, 255), 2)
    points = [(int(round(row["smooth_projected_x"])), int(round(row["smooth_projected_y"]))) for row in projected_rows]
    for point in points:
        cv2.circle(canvas, point, 5, (0, 255, 255), -1)
    for start, end in zip(points, points[1:]):
        cv2.line(canvas, start, end, (0, 255, 255), 2)
    for event in events:
        if event.get("projected_x") is None:
            continue
        point = (int(round(float(event["projected_x"]))), int(round(float(event["projected_y"]))))
        cv2.drawMarker(canvas, point, (0, 165, 255), cv2.MARKER_STAR, 15, 2)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if cv2.imwrite(str(output_path), canvas):
        return str(output_path)
    return None


def save_overlay_frames(smoothed_rows: list[dict[str, Any]], output_dir: Path) -> str | None:
    """Save a tiny set of local review overlay canvases."""
    selected = [row for row in smoothed_rows if not row.get("is_interpolated")][:5]
    if not selected:
        return None
    output_dir.mkdir(parents=True, exist_ok=True)
    scale_x = 1280 / 3840
    scale_y = 720 / 2160
    for row in selected:
        canvas = np.full((720, 1280, 3), 245, dtype=np.uint8)
        point = (int(round(row["smooth_x"] * scale_x)), int(round(row["smooth_y"] * scale_y)))
        cv2.circle(canvas, point, 10, (0, 180, 0), -1)
        cv2.putText(canvas, f"frame {row['frame_index']} smoothed ball hypothesis", (24, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        cv2.imwrite(str(output_dir / f"stage_6_overlay_frame_{int(row['frame_index']):06d}.jpg"), canvas)
    return str(output_dir)


def _metric_table(rows: list[tuple[str, Any]]) -> str:
    lines = ["| Metric | Value |", "|---|---|"]
    for key, value in rows:
        lines.append(f"| {key} | {value if value is not None else 'Not available'} |")
    return "\n".join(lines)


def _event_table(counts: dict[str, int]) -> str:
    lines = ["| Event type | Count |", "|---|---:|"]
    if not counts:
        lines.append("| None | 0 |")
    for event_type, count in counts.items():
        lines.append(f"| {event_type} | {count} |")
    return "\n".join(lines)


def _bullet_list(items: list[str], empty_text: str) -> str:
    return empty_text if not items else "\n".join(f"- {item}" for item in items)


def build_markdown_sections(report: dict[str, Any]) -> list[tuple[str, str]]:
    interpretation = (
        "Stage 6 builds a first trajectory from improved candidates and smooths it with a moving average. "
        "Event segmentation is hypothesis-only. "
    )
    if report["trajectory_points_count"] < 6:
        interpretation += "The current sequence is short, so more manual labels would make event segmentation more meaningful. "
    if report["final_verdict"] == "ready_for_stage_7":
        interpretation += "Projection and smoothing are working well enough for a cautious player-interaction probe."
    else:
        interpretation += "Do not treat these event hypotheses as confirmed tennis events."
    return [
        (
            "Verdict",
            "\n".join(
                [
                    f"- Final verdict: {report['final_verdict']}",
                    f"- Friction score: {report['friction']['score']}",
                    f"- Friction level: {report['friction']['band']}",
                ]
            ),
        ),
        (
            "Inputs",
            "\n".join(
                [
                    f"- Improved candidates CSV: `{report['input_improved_candidates_path']}`",
                    f"- Projected candidates CSV: `{report['input_projected_candidates_path']}`",
                    f"- Manual labels CSV: `{report['input_manual_labels_path']}`",
                    f"- Calibration/homography availability: {report['projected_candidates_available']}",
                ]
            ),
        ),
        (
            "Trajectory summary",
            _metric_table(
                [
                    ("trajectory points", report["trajectory_points_count"]),
                    ("interpolated points", report["interpolated_points_count"]),
                    ("frame range", report["frame_range"]),
                    ("smoothing method", report["smoothing_method"]),
                    ("image preview path", report["image_trajectory_preview_path"]),
                    ("court preview path", report["court_trajectory_preview_path"]),
                ]
            ),
        ),
        ("Event segmentation summary", _event_table(report["events_by_type"])),
        (
            "Output artifacts",
            "\n".join(
                [
                    f"- Raw trajectory CSV: `{report['raw_trajectory_csv_path']}`",
                    f"- Smoothed trajectory CSV: `{report['smoothed_trajectory_csv_path']}`",
                    f"- Events CSV: `{report['events_csv_path']}`",
                    f"- Image trajectory preview: `{report['image_trajectory_preview_path']}`",
                    f"- Court trajectory preview: `{report['court_trajectory_preview_path']}`",
                    f"- Overlay folder: `{report['overlay_folder']}`",
                ]
            ),
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
        return lab_notebook_paths(PROJECT_ROOT, "stage_6"), None
    except Exception as exc:
        try:
            from tennis_vision.lab_notebook import lab_notebook_paths

            return lab_notebook_paths(PROJECT_ROOT, "stage_6"), f"Lab notebook update failed: {exc}"
        except Exception:
            return {
                "stage_page": PROJECT_ROOT / "docs" / "lab-notebook" / "stage_6_trajectory_smoothing.md",
                "experiment_index": PROJECT_ROOT / "docs" / "lab-notebook" / "experiment_index.md",
            }, f"Lab notebook update failed: {exc}"


def print_summary(report: dict[str, Any], lab_paths: dict[str, Path]) -> None:
    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(title="Stage 6 Trajectory Smoothing")
        table.add_column("Field")
        table.add_column("Value")
        for field, value in [
            ("Verdict", report["final_verdict"]),
            ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"),
            ("Trajectory points", report["trajectory_points_count"]),
            ("Interpolated points", report["interpolated_points_count"]),
            ("Events", report["events_count"]),
            ("Events by type", str(report["events_by_type"])),
            ("Image preview", str(report["image_trajectory_preview_path"])),
            ("Court preview", str(report["court_trajectory_preview_path"])),
            ("Lab notebook", str(lab_paths["stage_page"])),
            ("Recommended next step", report["recommended_next_step"]),
        ]:
            table.add_row(str(field), str(value))
        Console().print(table)
    except ImportError:
        print(f"Verdict: {report['final_verdict']}")
        print(f"Trajectory points: {report['trajectory_points_count']}")
        print(f"Events: {report['events_count']}")


def main() -> int:
    args = parse_args()
    ensure_output_folders(PROJECT_ROOT)
    improved_path = resolve_path(args.improved_candidates)
    projected_path = resolve_path(args.projected_candidates)
    manual_path = resolve_path(args.manual_labels)
    output_dir = PROJECT_ROOT / "outputs" / "ball_tracking" / "stage_6_trajectory_smoothing"
    output_dir.mkdir(parents=True, exist_ok=True)

    warnings: list[str] = []
    errors: list[str] = []
    candidates, candidate_errors = read_improved_candidates(improved_path)
    errors.extend(candidate_errors)
    projected_by_frame, projected_warnings = read_projected_candidates(projected_path)
    if projected_warnings:
        warnings.extend(projected_warnings)
    candidates = enrich_with_projected_candidates(candidates, projected_by_frame)
    manual_labels, manual_warnings = read_manual_labels(manual_path)
    if manual_warnings:
        warnings.extend(manual_warnings)
    fps = read_fps(PROJECT_ROOT / "outputs" / "reports" / "stage_1_video_probe_report.json")

    raw_rows = build_raw_trajectory(candidates, fps=fps)
    expanded_rows = interpolate_trajectory(raw_rows, enabled=args.allow_interpolation)
    smoothed_rows = moving_average_smooth(expanded_rows, window_size=args.window_size)
    events, event_warnings = detect_events(raw_rows)
    warnings.extend(event_warnings)
    counts = events_by_type(events)

    raw_csv = output_dir / "raw_trajectory.csv"
    smoothed_csv = output_dir / "smoothed_trajectory.csv"
    events_csv = output_dir / "trajectory_events.csv"
    write_csv(
        raw_csv,
        raw_rows,
        [
            "frame_index",
            "x",
            "y",
            "projected_x",
            "projected_y",
            "source_strategy",
            "score",
            "distance_to_manual_label",
            "delta_frame",
            "delta_x",
            "delta_y",
            "image_velocity_px_per_frame",
            "image_speed_px_per_second",
            "projected_delta_x",
            "projected_delta_y",
            "projected_speed",
        ],
    )
    write_csv(
        smoothed_csv,
        smoothed_rows,
        [
            "frame_index",
            "raw_x",
            "raw_y",
            "smooth_x",
            "smooth_y",
            "raw_projected_x",
            "raw_projected_y",
            "smooth_projected_x",
            "smooth_projected_y",
            "is_interpolated",
            "smoothing_method",
        ],
    )
    write_events_csv(events_csv, events)

    image_preview = save_image_trajectory_preview(
        raw_rows=raw_rows,
        smoothed_rows=smoothed_rows,
        manual_labels=manual_labels,
        events=events,
        output_path=output_dir / "image_trajectory_preview.jpg",
    )
    court_preview = save_court_trajectory_preview(
        smoothed_rows=smoothed_rows,
        events=events,
        output_path=output_dir / "court_trajectory_preview.jpg",
    )
    overlay_folder = save_overlay_frames(smoothed_rows, output_dir / "overlays")

    flags = {
        "improved_candidates_missing": not improved_path.exists() or not candidates,
        "projected_candidates_missing": not projected_path.exists(),
        "too_few_points": len(raw_rows) < 4,
        "smoothing_failed": bool(candidates and not smoothed_rows),
        "event_detection_unreliable": len(raw_rows) < 5,
        "projection_preview_failed": bool(projected_by_frame and court_preview is None),
    }
    if len(raw_rows) < 6 and raw_rows:
        warnings.append("Only a small number of trajectory points are available; event hypotheses are preliminary.")
    if flags["projected_candidates_missing"]:
        warnings.append("Projected candidates CSV is missing; court-space preview may be unavailable.")
    if flags["projection_preview_failed"]:
        warnings.append("Court trajectory preview could not be created.")

    friction = calculate_stage_6_friction_score(**flags, errors_count=len(errors), warnings_count=len(warnings))
    frame_range = f"{raw_rows[0]['frame_index']} to {raw_rows[-1]['frame_index']}" if raw_rows else "Not available"
    report: dict[str, Any] = {
        "timestamp": utc_timestamp(),
        "stage": "stage_6_trajectory_smoothing",
        "input_improved_candidates_path": str(improved_path),
        "input_projected_candidates_path": str(projected_path) if projected_path.exists() else None,
        "input_manual_labels_path": str(manual_path) if manual_path.exists() else None,
        "projected_candidates_available": bool(projected_by_frame),
        "trajectory_points_count": len(raw_rows),
        "interpolated_points_count": sum(1 for row in smoothed_rows if row.get("is_interpolated")),
        "smoothing_method": f"moving_average_{args.window_size}",
        "frame_range": frame_range,
        "events_count": len(events),
        "events_by_type": counts,
        "image_trajectory_preview_path": image_preview,
        "court_trajectory_preview_path": court_preview,
        "raw_trajectory_csv_path": str(raw_csv),
        "smoothed_trajectory_csv_path": str(smoothed_csv),
        "events_csv_path": str(events_csv),
        "overlay_folder": overlay_folder,
        "warnings": warnings,
        "errors": errors,
        "flags": flags,
        "friction": friction,
        "final_verdict": "blocked",
        "recommended_next_step": "",
        "json_report_path": str(PROJECT_ROOT / "outputs" / "reports" / "stage_6_trajectory_smoothing_report.json"),
        "markdown_report_path": str(PROJECT_ROOT / "outputs" / "reports" / "stage_6_trajectory_smoothing_report.md"),
        "log_path": "",
    }
    report["final_verdict"] = determine_verdict(report)
    report["recommended_next_step"] = recommended_next_step(report)

    log_path = write_timestamped_log(
        PROJECT_ROOT,
        "stage_6_trajectory_smoothing",
        [
            f"timestamp={report['timestamp']}",
            f"verdict={report['final_verdict']}",
            f"friction={friction['score']} ({friction['band']})",
            f"trajectory_points={len(raw_rows)}",
            f"interpolated_points={report['interpolated_points_count']}",
            f"events={len(events)}",
        ],
    )
    report["log_path"] = str(log_path)

    json_path = Path(report["json_report_path"])
    markdown_path = Path(report["markdown_report_path"])
    write_json_report(json_path, report)
    write_markdown_report(markdown_path, "Stage 6 Trajectory Smoothing and Event Segmentation Probe Report", build_markdown_sections(report))

    lab_paths, notebook_warning = update_lab_notebook_safely()
    if notebook_warning:
        report["warnings"].append(notebook_warning)
        write_json_report(json_path, report)
        write_markdown_report(markdown_path, "Stage 6 Trajectory Smoothing and Event Segmentation Probe Report", build_markdown_sections(report))
        print(f"Warning: {notebook_warning}")

    print_summary(report, lab_paths)
    return 1 if report["final_verdict"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
