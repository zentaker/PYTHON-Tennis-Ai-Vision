"""Run Stage 8.4 bounce candidate propagation."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import cv2
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from tennis_vision.bounce_candidate_propagation import (  # noqa: E402
    build_manual_hit_windows,
    build_manual_bounce_windows,
    build_no_event_exclusion_zones,
    learn_bounce_window_signature,
    propose_bounce_candidates,
    write_csv,
)
from tennis_vision.bounce_pattern_features import (  # noqa: E402
    compute_local_motion_features,
    load_ball_sequence,
    summarize_manual_bounce_pattern,
)
from tennis_vision.event_validation import read_manual_event_labels, summarize_manual_event_labels  # noqa: E402
from tennis_vision.friction import calculate_stage_8_4_friction_score  # noqa: E402
from tennis_vision.friction_semantics import build_friction_breakdown, classify_human_loop_level, summarize_friction_breakdown  # noqa: E402
from tennis_vision.report import ensure_output_folders, utc_timestamp, write_json_report, write_markdown_report, write_timestamped_log  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 8.4 bounce candidate propagation.")
    parser.add_argument("--manual-labels", type=Path, default=PROJECT_ROOT / "outputs" / "timeline" / "stage_8_2_event_labels" / "manual_event_labels.csv")
    parser.add_argument("--manual-windows", type=Path, default=PROJECT_ROOT / "outputs" / "timeline" / "stage_8_3_event_validation" / "manual_event_windows.csv")
    parser.add_argument("--ball-sequence", type=Path, default=PROJECT_ROOT / "outputs" / "tactical" / "stage_9_1_projection_coverage" / "projected_expanded_labels.csv")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs" / "timeline" / "stage_8_4_bounce_candidates")
    parser.add_argument("--min-score", type=float, default=0.45)
    parser.add_argument("--candidate-window-gap", type=int, default=3)
    parser.add_argument("--max-candidates", type=int, default=5)
    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def determine_verdict(report: dict[str, Any]) -> str:
    flags = report["flags"]
    if flags["trajectory_missing"]:
        return "blocked"
    if flags["manual_bounce_missing"]:
        return "needs_more_manual_bounce_labels"
    if report.get("insufficient_post_hit_trajectory"):
        return "needs_more_post_hit_ball_labels"
    if report["candidate_windows_proposed"] > 0:
        return "ready_for_manual_bounce_review"
    if flags["no_candidates_found"]:
        return "ready_with_warnings"
    return "ready_with_warnings" if report["warnings"] else "ready_for_manual_bounce_review"


def recommended_next_step(report: dict[str, Any]) -> str:
    if report["final_verdict"] == "ready_for_manual_bounce_review":
        return "Review proposed bounce candidates with Stage 8.2 interactive labeling, then rerun Stage 8.3 event validation."
    if report["final_verdict"] == "needs_more_manual_bounce_labels":
        return "Return to Stage 8.2 and label at least one bounce window."
    if report["final_verdict"] == "needs_more_post_hit_ball_labels":
        return "Collect more post-hit ball/event labels after the manual hit, then rerun Stage 8.4."
    if report["final_verdict"] == "blocked":
        return "Regenerate projected labels or trajectory data, then rerun Stage 8.4."
    return "Review warnings, then add more manual bounce labels or lower the candidate threshold."


def write_review_queue(path: Path, windows: list[dict[str, Any]]) -> Path:
    rows: list[dict[str, Any]] = []
    for index, window in enumerate(windows, start=1):
        center = int(window["center_frame"])
        frames = [center - 1, center, center + 1]
        rows.append(
            {
                "review_id": f"bounce_review_{index:03d}",
                "frame_index": center,
                "candidate_id": window["candidate_id"],
                "score": window["score"],
                "reason": window["reason"],
                "suggested_command": f"python scripts/run_stage_8_2_event_labeling_helper.py --interactive --frames {','.join(str(frame) for frame in frames)}",
                "recommended_label": "bounce_or_no_event_review",
            }
        )
    return write_csv(path, rows, ["review_id", "frame_index", "candidate_id", "score", "reason", "suggested_command", "recommended_label"])


def build_proposed_bounce_events(windows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, window in enumerate(windows, start=1):
        rows.append(
            {
                "event_id": f"inferred_bounce_{index:03d}",
                "frame_index": window["center_frame"],
                "event_type": "inferred_possible_bounce",
                "validation_status": "inferred_unvalidated",
                "confidence_like_score": window["confidence_like_score"],
                "should_render_as_physical_event": "no",
                "should_render_as_annotation": "yes",
                "reason": window["reason"],
            }
        )
    return rows


def save_timeline_preview(
    *,
    features: list[dict[str, Any]],
    manual_windows: list[dict[str, Any]],
    candidate_windows: list[dict[str, Any]],
    manual_labels: list[dict[str, Any]],
    output_path: Path,
) -> bool:
    frames = [int(row["frame_index"]) for row in features]
    if not frames:
        return False
    width, height = 1400, 460
    canvas = np.full((height, width, 3), 246, dtype=np.uint8)
    left, right, axis_y = 80, width - 80, 235
    min_frame, max_frame = min(frames), max(frames)
    span = max(max_frame - min_frame, 1)

    def x_for(frame: int) -> int:
        return left + int(round(((frame - min_frame) / span) * (right - left)))

    cv2.putText(canvas, "Stage 8.4 bounce candidate propagation", (35, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.82, (25, 25, 25), 2)
    cv2.putText(canvas, "green=manual bounce window  orange=proposed candidate  gray=no_event labels", (35, 72), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (80, 80, 80), 1)
    cv2.line(canvas, (left, axis_y), (right, axis_y), (35, 35, 35), 2)
    for feature in features:
        x = x_for(int(feature["frame_index"]))
        cv2.circle(canvas, (x, axis_y), 4, (60, 120, 180), -1)
    for label in manual_labels:
        if label.get("event_label") != "no_event":
            continue
        x = x_for(int(label["frame_index"]))
        cv2.circle(canvas, (x, axis_y - 34), 3, (140, 140, 140), -1)
    for window in manual_windows:
        x0 = x_for(int(window["start_frame"]))
        x1 = x_for(int(window["end_frame"]))
        cv2.rectangle(canvas, (x0, axis_y - 118), (x1, axis_y - 72), (95, 210, 110), -1)
        cv2.putText(canvas, window["window_id"], (x0, axis_y - 124), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (40, 120, 55), 1)
    for window in candidate_windows:
        x = x_for(int(window["center_frame"]))
        cv2.drawMarker(canvas, (x, axis_y + 70), (40, 135, 245), cv2.MARKER_TRIANGLE_UP, 22, 2)
        cv2.putText(canvas, f"{window['candidate_id']} score={window['score']}", (x - 70, axis_y + 102), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (40, 100, 210), 1)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return bool(cv2.imwrite(str(output_path), canvas))


def build_markdown_sections(report: dict[str, Any]) -> list[tuple[str, str]]:
    return [
        ("VERDICT", field_block([("Final verdict", report["final_verdict"]), ("Friction", f"{report['friction']['score']} ({report['friction']['band']})")])),
        ("WHY THIS STAGE EXISTS", "The system should not require the user to label every bounce manually. This stage uses the existing manual bounce window, manual hit labels, no_event labels, and tennis sequence constraints to propose other likely bounce candidates."),
        (
            "INPUTS",
            field_block(
                [
                    ("Manual bounce windows", report["manual_bounce_windows_count"]),
                    ("Manual hit labels", report["manual_hit_labels_count"]),
                    ("No-event labels", report["manual_no_event_count"]),
                    ("Ball sequence points", report["ball_sequence_points_count"]),
                    ("Validated event timeline", report["inputs_used"].get("validated_event_timeline")),
                    ("Projected labels", report["inputs_used"].get("ball_sequence")),
                ]
            ),
        ),
        (
            "BOUNCE PATTERN SUMMARY",
            field_block(
                [
                    ("Manual bounce labels", report["manual_bounce_labels_count"]),
                    ("Bounce windows", report["manual_bounce_windows_count"]),
                    ("Pattern confidence", report["pattern_summary"].get("pattern_confidence")),
                    ("Notes", report["pattern_summary"].get("notes")),
                ]
            ),
        ),
        (
            "CANDIDATE SUMMARY",
            field_block(
                [
                    ("Candidate windows proposed", report["candidate_windows_proposed"]),
                    ("Candidate frames proposed", report["candidate_frames_proposed"]),
                    ("Top candidate frame", report["top_candidate_frame"]),
                    ("Top candidate score", report["top_candidate_score"]),
                    ("Review queue", report["review_queue_count"]),
                    ("Candidates excluded by hit labels", report["candidates_excluded_by_hit_labels"]),
                    ("Candidates excluded by no_event labels", report["candidates_excluded_by_no_event_labels"]),
                    ("Post-hit search enabled", report["post_hit_search_enabled"]),
                    ("Insufficient post-hit trajectory", report["insufficient_post_hit_trajectory"]),
                ]
            ),
        ),
        (
            "FRICTION BREAKDOWN",
            field_block(
                [
                    ("Execution friction", f"{report['friction_breakdown']['execution']['score']} ({report['friction_breakdown']['execution']['band']}) - {report['friction_breakdown']['execution']['reason']}"),
                    ("Semantic/model friction", f"{report['friction_breakdown']['semantic_model']['score']} ({report['friction_breakdown']['semantic_model']['band']}) - {report['friction_breakdown']['semantic_model']['reason']}"),
                    ("Human-loop friction", f"{report['friction_breakdown']['human_loop']['score']} ({report['friction_breakdown']['human_loop']['band']}) - {report['friction_breakdown']['human_loop']['reason']}"),
                    ("Product validation", f"{report['friction_breakdown']['product_validation']['status']} - {report['friction_breakdown']['product_validation']['reason']}"),
                    ("Downstream correction friction", f"{report['friction_breakdown']['downstream_correction']['score']} ({report['friction_breakdown']['downstream_correction']['band']}) - {report['friction_breakdown']['downstream_correction']['reason']}"),
                ]
            ),
        ),
        ("IMPORTANT LIMITATION", "Inferred bounce candidates are not validated bounces. They require manual review before being rendered as physical bounce events."),
        ("WARNINGS", bullet_list(report["warnings"], "No warnings.")),
        ("ERRORS", bullet_list(report["errors"], "No errors.")),
        ("NEXT STEP", report["recommended_next_step"]),
    ]


def field_block(rows: list[tuple[str, Any]]) -> str:
    lines: list[str] = []
    for key, value in rows:
        lines.append(f"{key}:")
        lines.append(f"  {value if value not in (None, '') else 'Not available'}")
        lines.append("")
    return "\n".join(lines).rstrip()


def bullet_list(items: list[str], empty: str) -> str:
    return empty if not items else "\n".join(f"- {item}" for item in items)


def update_lab_notebook_safely() -> tuple[dict[str, Path], str | None]:
    try:
        from tennis_vision.lab_notebook import lab_notebook_paths, update_lab_notebook

        update_lab_notebook(PROJECT_ROOT)
        return lab_notebook_paths(PROJECT_ROOT, "stage_8_4"), None
    except Exception as exc:
        try:
            from tennis_vision.lab_notebook import lab_notebook_paths

            return lab_notebook_paths(PROJECT_ROOT, "stage_8_4"), f"Lab notebook update failed: {exc}"
        except Exception:
            return {
                "stage_page": PROJECT_ROOT / "docs" / "lab-notebook" / "stage_8_4_bounce_candidate_propagation.md",
                "experiment_index": PROJECT_ROOT / "docs" / "lab-notebook" / "experiment_index.md",
            }, f"Lab notebook update failed: {exc}"


def print_summary(report: dict[str, Any], lab_paths: dict[str, Path]) -> None:
    rows = [
        ("Verdict", report["final_verdict"]),
        ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"),
        ("Execution friction", report["friction_breakdown"]["execution"]["band"]),
        ("Semantic friction", report["friction_breakdown"]["semantic_model"]["band"]),
        ("Human-loop friction", report["friction_breakdown"]["human_loop"]["band"]),
        ("Product validation", report["friction_breakdown"]["product_validation"]["status"]),
        ("Manual bounce windows", report["manual_bounce_windows_count"]),
        ("Manual bounce labels", report["manual_bounce_labels_count"]),
        ("Manual hit labels", report["manual_hit_labels_count"]),
        ("No-event labels", report["manual_no_event_count"]),
        ("Ball sequence points", report["ball_sequence_points_count"]),
        ("Candidate windows", report["candidate_windows_proposed"]),
        ("Candidate frames", report["candidate_frames_proposed"]),
        ("Excluded by hit", report["candidates_excluded_by_hit_labels"]),
        ("Excluded by no_event", report["candidates_excluded_by_no_event_labels"]),
        ("Post-hit search", report["post_hit_search_enabled"]),
        ("Top candidate frame", report["top_candidate_frame"]),
        ("Top candidate score", report["top_candidate_score"]),
        ("Review queue", report["review_queue_count"]),
        ("Lab notebook", lab_paths["stage_page"]),
        ("Recommended next step", report["recommended_next_step"]),
    ]
    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(title="Stage 8.4 Bounce Candidate Propagation")
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")
        for field, value in rows:
            table.add_row(str(field), str(value))
        Console().print(table)
    except ImportError:
        print("Stage 8.4 Bounce Candidate Propagation")
        for field, value in rows:
            print(f"{field}: {value}")


def count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", newline="", encoding="utf-8") as handle:
        return max(sum(1 for _row in csv.DictReader(handle)), 0)


def main() -> int:
    args = parse_args()
    ensure_output_folders(PROJECT_ROOT)
    timestamp = utc_timestamp()
    output_dir = resolve_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    manual_labels_path = resolve_path(args.manual_labels)
    manual_windows_path = resolve_path(args.manual_windows)
    ball_sequence_path = resolve_path(args.ball_sequence)
    validated_timeline_path = PROJECT_ROOT / "outputs" / "timeline" / "stage_8_3_event_validation" / "validated_event_timeline.csv"

    warnings: list[str] = []
    errors: list[str] = []
    manual_labels, label_errors = read_manual_event_labels(manual_labels_path)
    errors.extend(label_errors)
    manual_windows, window_warnings = build_manual_bounce_windows(manual_windows_path)
    warnings.extend(window_warnings)
    manual_hit_windows = build_manual_hit_windows(manual_labels)
    no_event_zones = build_no_event_exclusion_zones(manual_labels)
    uncertain_labels = [row for row in manual_labels if row.get("event_label") == "uncertain"]
    ball_rows, ball_warnings = load_ball_sequence(ball_sequence_path)
    warnings.extend(ball_warnings)
    features = compute_local_motion_features(ball_rows)
    manual_summary = summarize_manual_event_labels(manual_labels, manual_windows)
    pattern_summary = summarize_manual_bounce_pattern(features, manual_windows)
    signature = learn_bounce_window_signature(features, manual_windows)
    if len(manual_windows) == 1:
        warnings.append("Only one manual bounce window is available; candidate propagation confidence is limited.")
    candidate_windows, candidate_frames, constraint_summary = propose_bounce_candidates(
        features,
        manual_windows,
        hit_windows=manual_hit_windows,
        no_event_zones=no_event_zones,
        uncertain_labels=uncertain_labels,
        min_score=args.min_score,
        candidate_window_gap=args.candidate_window_gap,
        max_candidates=args.max_candidates,
    )
    if constraint_summary.get("post_hit_search_enabled"):
        warnings.append("Post-hit next-bounce search is enabled from manual hit labels.")
    if constraint_summary.get("post_hit_search_enabled") and not candidate_windows and int(constraint_summary.get("post_hit_points_count") or 0) < 5:
        constraint_summary["insufficient_post_hit_trajectory"] = True
    if constraint_summary.get("insufficient_post_hit_trajectory"):
        warnings.append("insufficient_post_hit_trajectory: not enough post-hit ball points are available to propose a reliable next bounce.")
    windows_path = output_dir / "bounce_candidate_windows.csv"
    frames_path = output_dir / "bounce_candidate_frames.csv"
    review_path = output_dir / "bounce_review_queue.csv"
    proposed_events_path = output_dir / "proposed_bounce_events.csv"
    preview_path = output_dir / "bounce_candidate_timeline_preview.jpg"
    write_csv(
        windows_path,
        candidate_windows,
        [
            "candidate_id",
            "start_frame",
            "end_frame",
            "center_frame",
            "score",
            "confidence_like_score",
            "reason",
            "supporting_features",
            "already_validated",
            "sequence_context",
            "nearest_manual_hit_frame",
            "distance_from_hit",
            "excluded_by_hit_window",
            "excluded_by_no_event",
            "event_sequence_status",
            "rejection_reason",
            "recommendation",
        ],
    )
    write_csv(
        frames_path,
        candidate_frames,
        ["frame_index", "candidate_id", "score", "projected_x", "projected_y", "x", "y", "feature_summary", "recommendation"],
    )
    write_review_queue(review_path, candidate_windows)
    write_csv(
        proposed_events_path,
        build_proposed_bounce_events(candidate_windows),
        ["event_id", "frame_index", "event_type", "validation_status", "confidence_like_score", "should_render_as_physical_event", "should_render_as_annotation", "reason"],
    )
    preview_generated = save_timeline_preview(features=features, manual_windows=manual_windows, candidate_windows=candidate_windows, manual_labels=manual_labels, output_path=preview_path)
    if not preview_generated:
        warnings.append("Bounce candidate timeline preview could not be generated.")

    top_candidate = candidate_windows[0] if candidate_windows else {}
    output_paths = {
        "bounce_candidate_windows": str(windows_path),
        "bounce_candidate_frames": str(frames_path),
        "bounce_review_queue": str(review_path),
        "proposed_bounce_events": str(proposed_events_path),
        "bounce_candidate_timeline_preview": str(preview_path) if preview_path.exists() else "",
    }
    flags = {
        "manual_bounce_missing": len(manual_windows) == 0,
        "only_one_bounce_window": len(manual_windows) == 1,
        "trajectory_missing": len(features) == 0,
        "no_candidates_found": len(candidate_windows) == 0,
        "review_queue_failed": not review_path.exists(),
        "preview_generation_failed": not preview_generated,
    }
    friction = calculate_stage_8_4_friction_score(**flags, errors_count=len(errors), warnings_count=len(warnings))
    human_loop = classify_human_loop_level(
        manual_labels_required=True,
        manual_review_required=len(candidate_windows) > 0,
        new_manual_stage_required=True,
    )
    semantic_score = 70 if constraint_summary.get("excluded_candidate_frames") else 45 if candidate_windows else 60
    downstream_score = 50
    friction_breakdown = build_friction_breakdown(
        execution_score=friction["score"],
        execution_reason="Stage 8.4 script ran and generated its expected output files." if not errors else "Stage 8.4 reported execution errors.",
        semantic_model_score=semantic_score,
        semantic_model_reason="Bounce candidates are event-sequence constrained; prior motion-only candidate frames near manual hits are excluded.",
        human_loop_score=human_loop["score"],
        human_loop_reason=f"{human_loop['reason']}; user already inspected and labeled the mistaken hit-region candidate.",
        product_validation_status="failed_previous_candidate" if constraint_summary.get("excluded_candidate_frames") and not candidate_windows else "pending_review",
        product_validation_reason="The previous top candidate was near a manual hit and is now excluded." if constraint_summary.get("excluded_candidate_frames") else "The top candidate must be inspected by the Product Owner before it can become a validated bounce.",
        downstream_correction_score=downstream_score,
        downstream_correction_reason="Stage 8.4 exists because earlier side-view/event semantics needed extra repair and active validation.",
    )
    report: dict[str, Any] = {
        "timestamp": timestamp,
        "stage": "stage_8_4_bounce_candidate_propagation",
        "manual_bounce_windows_count": len(manual_windows),
        "manual_bounce_labels_count": manual_summary["manual_bounce_count"],
        "manual_hit_labels_count": manual_summary["manual_hit_count"],
        "manual_no_event_count": manual_summary["manual_no_event_count"],
        "ball_sequence_points_count": len(features),
        "candidate_windows_proposed": len(candidate_windows),
        "candidate_frames_proposed": len(candidate_frames),
        "top_candidate_frame": top_candidate.get("center_frame", ""),
        "top_candidate_score": top_candidate.get("score", ""),
        "review_queue_count": count_csv_rows(review_path),
        "candidates_excluded_by_hit_labels": constraint_summary.get("candidates_excluded_by_hit_labels", 0),
        "candidates_excluded_by_no_event_labels": constraint_summary.get("candidates_excluded_by_no_event_labels", 0),
        "post_hit_search_enabled": bool(constraint_summary.get("post_hit_search_enabled")),
        "insufficient_post_hit_trajectory": bool(constraint_summary.get("insufficient_post_hit_trajectory")),
        "frame_195_excluded_as_bounce_candidate": 195 in set(constraint_summary.get("excluded_candidate_frames", [])),
        "event_sequence_constraints": constraint_summary,
        "pattern_summary": {**pattern_summary, "signature": signature},
        "inputs_used": {
            "manual_labels": str(manual_labels_path),
            "manual_windows": str(manual_windows_path),
            "ball_sequence": str(ball_sequence_path),
            "validated_event_timeline": str(validated_timeline_path),
        },
        "output_paths": output_paths,
        "warnings": warnings,
        "errors": errors,
        "flags": flags,
        "friction": friction,
        "friction_breakdown": friction_breakdown,
        "friction_breakdown_summary": summarize_friction_breakdown(friction_breakdown),
        "final_verdict": "blocked",
        "recommended_next_step": "",
    }
    report["final_verdict"] = determine_verdict(report)
    report["recommended_next_step"] = recommended_next_step(report)
    log_path = write_timestamped_log(
        PROJECT_ROOT,
        "stage_8_4_bounce_candidate_propagation",
        [
            f"timestamp={timestamp}",
            f"verdict={report['final_verdict']}",
            f"friction={friction['score']} ({friction['band']})",
            f"candidate_windows={len(candidate_windows)}",
            f"review_queue={report['review_queue_count']}",
        ],
    )
    report["log_path"] = str(log_path)
    report["json_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_8_4_bounce_candidate_propagation_report.json")
    report["markdown_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_8_4_bounce_candidate_propagation_report.md")
    write_json_report(Path(report["json_report_path"]), report)
    write_markdown_report(Path(report["markdown_report_path"]), "Stage 8.4 Bounce Candidate Propagation Report", build_markdown_sections(report))
    lab_paths, notebook_warning = update_lab_notebook_safely()
    if notebook_warning:
        report["warnings"].append(notebook_warning)
        write_json_report(Path(report["json_report_path"]), report)
        write_markdown_report(Path(report["markdown_report_path"]), "Stage 8.4 Bounce Candidate Propagation Report", build_markdown_sections(report))
        print(f"Warning: {notebook_warning}")
    print_summary(report, lab_paths)
    return 1 if report["final_verdict"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
