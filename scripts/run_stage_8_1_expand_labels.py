"""Run Stage 8.1 expanded ball labels and timeline validation."""

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

from tennis_vision.ball_labeling import build_frame_indices, load_frame_at_index  # noqa: E402
from tennis_vision.ball_tracking_probe import resize_frame  # noqa: E402
from tennis_vision.event_timeline import read_fps  # noqa: E402
from tennis_vision.friction import calculate_stage_8_1_friction_score  # noqa: E402
from tennis_vision.label_expansion import (  # noqa: E402
    analyze_label_coverage,
    collect_interactive_labels,
    merge_labels,
    read_manual_labels,
    write_coverage_csv,
    write_expanded_labels_csv,
    write_expanded_labels_json,
)
from tennis_vision.report import ensure_output_folders, utc_timestamp, write_json_report, write_markdown_report, write_timestamped_log  # noqa: E402
from tennis_vision.timeline_validation import (  # noqa: E402
    read_candidates,
    read_timeline,
    validate_candidates_against_labels,
    validate_timeline_events,
    write_candidate_validation_csv,
    write_timeline_validation_csv,
    write_validated_timeline_csv,
    write_validated_timeline_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 8.1 expanded ball labels and timeline validation.")
    parser.add_argument("--interactive", dest="interactive", action="store_true", help="Open OpenCV UI to collect new ball labels.")
    parser.add_argument("--no-interactive", dest="interactive", action="store_false", help="Validate using existing labels only.")
    parser.set_defaults(interactive=False)
    parser.add_argument("--frames", type=str, default=None)
    parser.add_argument("--start-frame", type=int, default=90)
    parser.add_argument("--interval", type=int, default=15)
    parser.add_argument("--max-frames", type=int, default=12)
    parser.add_argument("--resize-width", type=int, default=1280)
    parser.add_argument("--merge-existing", dest="merge_existing", action="store_true", default=True)
    parser.add_argument("--no-merge-existing", dest="merge_existing", action="store_false")
    parser.add_argument("--candidate-frame-tolerance", type=int, default=5)
    parser.add_argument("--video", type=Path, default=PROJECT_ROOT / "samples" / "video_01.mov")
    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def determine_verdict(report: dict[str, Any]) -> str:
    flags = report["flags"]
    if flags["labels_missing"] or flags["timeline_missing"]:
        return "blocked"
    if flags["candidate_validation_failed"]:
        return "needs_better_candidate_generation"
    if flags["event_validation_unsupported"]:
        return "needs_event_labeling"
    if flags["sparse_label_coverage"]:
        return "needs_more_labels"
    return "ready_for_stage_9"


def recommended_next_step(report: dict[str, Any]) -> str:
    verdict = report["final_verdict"]
    if verdict == "ready_for_stage_9":
        return "Proceed to Stage 9: Tactical Metrics and Shot Zone Prototype."
    if verdict == "needs_more_labels":
        return "Run Stage 8.1 interactively across more frames, then rerun timeline validation."
    if verdict == "needs_event_labeling":
        return "Proceed to Stage 8.2: Manual Event Labeling Helper."
    if verdict == "needs_better_candidate_generation":
        return "Return to candidate generation improvements before validating timeline events."
    return "Fix missing labels or Stage 8 timeline outputs, then rerun Stage 8.1."


def save_expanded_labels_preview(labels: list[dict[str, Any]], video_path: Path, output_path: Path, resize_width: int) -> str | None:
    """Save a contact sheet of visible expanded labels."""
    visible = [label for label in labels if label.get("visible") and label.get("x") is not None and label.get("y") is not None]
    if not visible or not video_path.exists():
        return None
    tiles: list[np.ndarray] = []
    for label in visible[:12]:
        frame, error = load_frame_at_index(video_path, int(label["frame_index"]))
        if error or frame is None:
            continue
        display, scale = resize_frame(frame, resize_width // 2)
        point = (int(round(float(label["x"]) * scale)), int(round(float(label["y"]) * scale)))
        cv2.circle(display, point, 14, (0, 0, 0), 3)
        cv2.circle(display, point, 12, (0, 255, 255), 3)
        cv2.putText(display, f"frame {label['frame_index']}", (16, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 3)
        cv2.putText(display, f"frame {label['frame_index']}", (16, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 1)
        tiles.append(display)
    if not tiles:
        return None
    width = max(tile.shape[1] for tile in tiles)
    height = max(tile.shape[0] for tile in tiles)
    normalized = [cv2.copyMakeBorder(tile, 0, height - tile.shape[0], 0, width - tile.shape[1], cv2.BORDER_CONSTANT, value=(30, 30, 30)) for tile in tiles]
    rows: list[np.ndarray] = []
    for index in range(0, len(normalized), 3):
        chunk = normalized[index : index + 3]
        while len(chunk) < 3:
            chunk.append(np.full((height, width, 3), 30, dtype=np.uint8))
        rows.append(np.hstack(chunk))
    contact_sheet = np.vstack(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return str(output_path) if cv2.imwrite(str(output_path), contact_sheet) else None


def save_timeline_validation_preview(
    *,
    validation_rows: list[dict[str, Any]],
    coverage: dict[str, Any],
    output_path: Path,
) -> str | None:
    """Save a frame-axis preview of event validation status."""
    if not validation_rows:
        return None
    width, height = 1280, 420
    canvas = np.full((height, width, 3), 248, dtype=np.uint8)
    frames = [int(row["frame_index"]) for row in validation_rows]
    label_frames = [int(row["nearest_label_frame"]) for row in validation_rows if row.get("nearest_label_frame") not in (None, "")]
    all_frames = frames + label_frames
    min_frame, max_frame = min(all_frames), max(all_frames)
    span = max(max_frame - min_frame, 1)
    left, right, axis_y = 80, width - 80, 220
    cv2.line(canvas, (left, axis_y), (right, axis_y), (40, 40, 40), 2)

    def x_for_frame(frame: int) -> int:
        return left + int((frame - min_frame) / span * (right - left))

    for frame in sorted(set(label_frames)):
        x = x_for_frame(frame)
        cv2.line(canvas, (x, axis_y - 90), (x, axis_y + 90), (190, 220, 190), 1)
        cv2.circle(canvas, (x, axis_y + 80), 5, (0, 150, 0), -1)
    colors = {
        "supported_by_label": (0, 150, 0),
        "near_labeled_frame": (0, 180, 220),
        "outside_label_coverage": (0, 0, 220),
        "insufficient_data": (120, 120, 120),
    }
    for row in validation_rows:
        x = x_for_frame(int(row["frame_index"]))
        color = colors.get(str(row["validation_status"]), (0, 0, 0))
        cv2.drawMarker(canvas, (x, axis_y), color, cv2.MARKER_TRIANGLE_UP, 22, 2)
        cv2.putText(canvas, f"{row['frame_index']} {row['validation_status']}", (max(8, x - 84), axis_y - 72), cv2.FONT_HERSHEY_SIMPLEX, 0.42, color, 1)
    cv2.putText(canvas, "Stage 8.1 timeline validation: green lines are labeled frames", (32, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (20, 20, 20), 2)
    cv2.putText(canvas, f"coverage: {coverage.get('label_frame_range')}", (32, height - 32), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (20, 20, 20), 1)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return str(output_path) if cv2.imwrite(str(output_path), canvas) else None


def save_court_validation_preview(validated_rows: list[dict[str, Any]], output_path: Path) -> str | None:
    """Save a projected court validation preview when coordinates exist."""
    projected = [row for row in validated_rows if row.get("ball_projected_x") not in (None, "") and row.get("ball_projected_y") not in (None, "")]
    if not projected:
        return None
    width, height = 420, 760
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    canvas[:] = (38, 112, 62)
    cv2.rectangle(canvas, (30, 30), (width - 30, height - 30), (255, 255, 255), 2)
    xs = [float(row["ball_projected_x"]) for row in projected]
    ys = [float(row["ball_projected_y"]) for row in projected]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max(max_x - min_x, 1.0)
    span_y = max(max_y - min_y, 1.0)

    def point(row: dict[str, Any]) -> tuple[int, int]:
        x = 50 + int((float(row["ball_projected_x"]) - min_x) / span_x * (width - 100))
        y = 60 + int((float(row["ball_projected_y"]) - min_y) / span_y * (height - 120))
        return x, y

    points = [point(row) for row in projected]
    for start, end in zip(points, points[1:]):
        cv2.line(canvas, start, end, (0, 255, 255), 2)
    for row, marker in zip(projected, points):
        supported = row.get("validation_status") == "supported_by_label"
        color = (0, 255, 255) if supported else (0, 0, 255)
        cv2.circle(canvas, marker, 6, color, -1)
        cv2.putText(canvas, str(row["frame_index"]), (marker[0] + 8, marker[1] - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return str(output_path) if cv2.imwrite(str(output_path), canvas) else None


def _metric_table(rows: list[tuple[str, Any]]) -> str:
    lines = ["| Metric | Value |", "|---|---:|"]
    for key, value in rows:
        lines.append(f"| {key} | {value if value is not None else 'Not available'} |")
    return "\n".join(lines)


def _bullet_list(items: list[str], empty_text: str) -> str:
    return empty_text if not items else "\n".join(f"- {item}" for item in items)


def build_markdown_sections(report: dict[str, Any]) -> list[tuple[str, str]]:
    candidate = report["candidate_validation_summary"]
    timeline = report["timeline_validation_summary"]
    interpretation = (
        "Stage 8.1 validates the Stage 8 timeline against expanded ball labels. "
        f"The current run used {report['merged_labels_count']} merged labels with {report['visible_labels_count']} visible ball labels. "
    )
    if report["final_verdict"] == "ready_for_stage_9":
        interpretation += "Label coverage and event support are sufficient for a cautious tactical metrics prototype."
    elif report["final_verdict"] == "needs_more_labels":
        interpretation += "Candidate quality remains strong where labels exist, but coverage is still too sparse for tactical metrics."
    elif report["final_verdict"] == "needs_event_labeling":
        interpretation += "Ball labels exist, but event hypotheses need direct manual event validation."
    else:
        interpretation += "Review warnings before advancing."
    return [
        ("Verdict", f"- Final verdict: {report['final_verdict']}\n- Friction score: {report['friction']['score']}\n- Friction level: {report['friction']['band']}"),
        (
            "Label expansion summary",
            _metric_table(
                [
                    ("existing labels", report["existing_labels_count"]),
                    ("new labels", report["new_labels_count"]),
                    ("merged labels", report["merged_labels_count"]),
                    ("visible labels", report["visible_labels_count"]),
                    ("frame range", report["label_frame_range"]),
                    ("average label gap", report["average_label_gap"]),
                    ("maximum label gap", report["maximum_label_gap"]),
                ]
            ),
        ),
        (
            "Candidate validation summary",
            _metric_table(
                [
                    ("candidate comparisons", candidate.get("candidate_validation_count")),
                    ("average distance", candidate.get("average_candidate_distance")),
                    ("median distance", candidate.get("median_candidate_distance")),
                    ("frames within 10 px", candidate.get("within_10_px")),
                    ("frames within 25 px", candidate.get("within_25_px")),
                    ("frames within 50 px", candidate.get("within_50_px")),
                    ("frames within 100 px", candidate.get("within_100_px")),
                    ("frames within 200 px", candidate.get("within_200_px")),
                ]
            ),
        ),
        (
            "Timeline validation summary",
            _metric_table(
                [
                    ("timeline events", timeline.get("timeline_events_validated")),
                    ("supported events", timeline.get("supported_events_count")),
                    ("unsupported events", timeline.get("unsupported_events_count")),
                    ("outside coverage events", timeline.get("outside_coverage_events_count")),
                    ("adjusted confidence notes", "See validated timeline CSV."),
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
        return lab_notebook_paths(PROJECT_ROOT, "stage_8_1"), None
    except Exception as exc:
        try:
            from tennis_vision.lab_notebook import lab_notebook_paths

            return lab_notebook_paths(PROJECT_ROOT, "stage_8_1"), f"Lab notebook update failed: {exc}"
        except Exception:
            return {
                "stage_page": PROJECT_ROOT / "docs" / "lab-notebook" / "stage_8_1_timeline_validation.md",
                "experiment_index": PROJECT_ROOT / "docs" / "lab-notebook" / "experiment_index.md",
            }, f"Lab notebook update failed: {exc}"


def print_summary(report: dict[str, Any], lab_paths: dict[str, Path]) -> None:
    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(title="Stage 8.1 Timeline Validation")
        table.add_column("Field")
        table.add_column("Value")
        rows = [
            ("Verdict", report["final_verdict"]),
            ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"),
            ("Existing labels", report["existing_labels_count"]),
            ("New labels", report["new_labels_count"]),
            ("Visible labels", report["visible_labels_count"]),
            ("Average label gap", report["average_label_gap"]),
            ("Maximum label gap", report["maximum_label_gap"]),
            ("Candidate avg distance", report["candidate_validation_summary"].get("average_candidate_distance")),
            ("Timeline events validated", report["timeline_validation_summary"].get("timeline_events_validated")),
            ("Supported events", report["timeline_validation_summary"].get("supported_events_count")),
            ("Lab notebook", str(lab_paths["stage_page"])),
            ("Recommended next step", report["recommended_next_step"]),
        ]
        for field, value in rows:
            table.add_row(str(field), str(value))
        Console().print(table)
    except ImportError:
        print(f"Verdict: {report['final_verdict']}")


def main() -> int:
    args = parse_args()
    ensure_output_folders(PROJECT_ROOT)
    output_dir = PROJECT_ROOT / "outputs" / "timeline" / "stage_8_1_timeline_validation"
    output_dir.mkdir(parents=True, exist_ok=True)
    video_path = resolve_path(args.video)
    timestamp = utc_timestamp()
    frame_indices = build_frame_indices(frames=args.frames, start_frame=args.start_frame, interval=args.interval, max_frames=args.max_frames)

    warnings: list[str] = []
    errors: list[str] = []
    existing_labels, existing_warnings = read_manual_labels(PROJECT_ROOT / "outputs" / "ball_tracking" / "stage_4_1_manual_labels" / "manual_ball_labels.csv")
    warnings.extend(existing_warnings)
    new_labels: list[dict[str, Any]] = []
    if args.interactive:
        collected, label_warnings, label_errors = collect_interactive_labels(
            video_path=video_path,
            frame_indices=frame_indices,
            output_dir=output_dir,
            resize_width=args.resize_width,
            label_session=f"stage_8_1_{timestamp}",
        )
        new_labels = collected
        warnings.extend(label_warnings)
        errors.extend(label_errors)
    else:
        warnings.append("Non-interactive mode used existing labels only; no new labels were collected.")

    labels = merge_labels(existing_labels if args.merge_existing else [], new_labels)
    fps = read_fps(PROJECT_ROOT / "outputs" / "reports" / "stage_1_video_probe_report.json")
    coverage = analyze_label_coverage(labels, fps=fps)

    expanded_csv = output_dir / "expanded_ball_labels.csv"
    expanded_json = output_dir / "expanded_ball_labels.json"
    coverage_csv = output_dir / "label_coverage_report.csv"
    write_expanded_labels_csv(expanded_csv, labels)
    write_expanded_labels_json(expanded_json, labels)
    write_coverage_csv(coverage_csv, coverage)

    candidates, candidate_errors = read_candidates(PROJECT_ROOT / "outputs" / "ball_tracking" / "stage_5_1_candidate_improvement" / "improved_ball_candidates.csv")
    errors.extend(candidate_errors)
    candidate_rows, candidate_summary = validate_candidates_against_labels(labels=labels, candidates=candidates, frame_tolerance=args.candidate_frame_tolerance)
    candidate_csv = output_dir / "expanded_candidate_validation.csv"
    write_candidate_validation_csv(candidate_csv, candidate_rows)

    timeline_rows, timeline_errors = read_timeline(PROJECT_ROOT / "outputs" / "timeline" / "stage_8_event_timeline" / "event_timeline.csv")
    errors.extend(timeline_errors)
    validation_rows, validated_timeline, timeline_summary = validate_timeline_events(timeline_rows=timeline_rows, labels=labels)
    timeline_validation_csv = output_dir / "timeline_event_validation.csv"
    validated_csv = output_dir / "validated_event_timeline.csv"
    validated_json = output_dir / "validated_event_timeline.json"
    write_timeline_validation_csv(timeline_validation_csv, validation_rows)
    write_validated_timeline_csv(validated_csv, validated_timeline)
    write_validated_timeline_json(validated_json, validated_timeline)

    labels_preview = save_expanded_labels_preview(labels, video_path, output_dir / "expanded_labels_preview.jpg", args.resize_width)
    timeline_preview = save_timeline_validation_preview(validation_rows=validation_rows, coverage=coverage, output_path=output_dir / "timeline_validation_preview.jpg")
    court_preview = save_court_validation_preview(validated_timeline, output_dir / "court_validation_preview.jpg")
    if labels and labels_preview is None:
        warnings.append("Expanded label preview could not be generated.")
    if validation_rows and timeline_preview is None:
        warnings.append("Timeline validation preview could not be generated.")
    if validated_timeline and court_preview is None:
        warnings.append("Court validation preview could not be generated.")

    avg_distance = candidate_summary.get("average_candidate_distance")
    supported = timeline_summary.get("supported_events_count", 0)
    timeline_count = timeline_summary.get("timeline_events_validated", 0)
    flags = {
        "labels_missing": not labels or coverage["visible_labels"] == 0,
        "timeline_missing": not timeline_rows,
        "candidate_validation_failed": bool(not candidate_rows or avg_distance is None or avg_distance > 50),
        "sparse_label_coverage": not coverage["coverage_enough_for_timeline_validation"],
        "event_validation_unsupported": bool(timeline_count and supported / max(timeline_count, 1) < 0.6),
        "manual_action_required": not args.interactive,
    }
    if flags["sparse_label_coverage"]:
        warnings.append("Label coverage is still sparse for tactical metrics; collect more labels across the rally.")
    if flags["event_validation_unsupported"]:
        warnings.append("Not enough timeline events are directly supported by labels.")
    friction = calculate_stage_8_1_friction_score(**flags, errors_count=len(errors), warnings_count=len(warnings))

    report: dict[str, Any] = {
        "timestamp": timestamp,
        "stage": "stage_8_1_timeline_validation",
        "mode": "interactive" if args.interactive else "non_interactive",
        "video_path": str(video_path),
        "selected_frame_indices": frame_indices,
        "existing_labels_count": len(existing_labels),
        "new_labels_count": len(new_labels),
        "merged_labels_count": len(labels),
        "visible_labels_count": coverage["visible_labels"],
        "skipped_frames": coverage["skipped_frames"],
        "label_frame_range": coverage["label_frame_range"],
        "average_label_gap": coverage["average_label_gap"],
        "maximum_label_gap": coverage["maximum_label_gap"],
        "labels_per_second": coverage["labels_per_second"],
        "coverage_enough_for_timeline_validation": coverage["coverage_enough_for_timeline_validation"],
        "candidate_validation_count": candidate_summary.get("candidate_validation_count"),
        "average_candidate_distance": candidate_summary.get("average_candidate_distance"),
        "median_candidate_distance": candidate_summary.get("median_candidate_distance"),
        "candidate_validation_summary": candidate_summary,
        "timeline_events_validated": timeline_summary.get("timeline_events_validated"),
        "supported_events_count": timeline_summary.get("supported_events_count"),
        "unsupported_events_count": timeline_summary.get("unsupported_events_count"),
        "outside_coverage_events_count": timeline_summary.get("outside_coverage_events_count"),
        "timeline_validation_summary": timeline_summary,
        "validated_timeline_path": str(validated_csv),
        "warnings": warnings,
        "errors": errors,
        "flags": flags,
        "friction": friction,
        "final_verdict": "blocked",
        "recommended_next_step": "",
        "output_paths": {
            "expanded_labels_csv": str(expanded_csv),
            "expanded_labels_json": str(expanded_json),
            "label_coverage_report": str(coverage_csv),
            "expanded_candidate_validation": str(candidate_csv),
            "timeline_event_validation": str(timeline_validation_csv),
            "validated_event_timeline_csv": str(validated_csv),
            "validated_event_timeline_json": str(validated_json),
            "expanded_labels_preview": labels_preview,
            "timeline_validation_preview": timeline_preview,
            "court_validation_preview": court_preview,
        },
        "json_report_path": str(PROJECT_ROOT / "outputs" / "reports" / "stage_8_1_timeline_validation_report.json"),
        "markdown_report_path": str(PROJECT_ROOT / "outputs" / "reports" / "stage_8_1_timeline_validation_report.md"),
        "log_path": "",
    }
    report["final_verdict"] = determine_verdict(report)
    report["recommended_next_step"] = recommended_next_step(report)

    log_path = write_timestamped_log(
        PROJECT_ROOT,
        "stage_8_1_timeline_validation",
        [
            f"timestamp={timestamp}",
            f"mode={report['mode']}",
            f"verdict={report['final_verdict']}",
            f"friction={friction['score']} ({friction['band']})",
            f"visible_labels={coverage['visible_labels']}",
            f"timeline_events={timeline_summary.get('timeline_events_validated')}",
            f"supported_events={timeline_summary.get('supported_events_count')}",
        ],
    )
    report["log_path"] = str(log_path)
    json_path = Path(report["json_report_path"])
    markdown_path = Path(report["markdown_report_path"])
    write_json_report(json_path, report)
    write_markdown_report(markdown_path, "Stage 8.1 Expanded Ball Labels and Timeline Validation Report", build_markdown_sections(report))

    lab_paths, notebook_warning = update_lab_notebook_safely()
    if notebook_warning:
        report["warnings"].append(notebook_warning)
        write_json_report(json_path, report)
        write_markdown_report(markdown_path, "Stage 8.1 Expanded Ball Labels and Timeline Validation Report", build_markdown_sections(report))
        print(f"Warning: {notebook_warning}")

    print_summary(report, lab_paths)
    return 1 if report["final_verdict"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
