"""Run Stage 8.2 manual bounce / hit event labeling helper."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import cv2


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from tennis_vision.ball_labeling import build_frame_indices  # noqa: E402
from tennis_vision.event_labeling import (  # noqa: E402
    analyze_event_label_coverage,
    collect_event_labels_interactively,
    compare_manual_events_to_auto_events,
    load_durable_event_labels,
    read_auto_events,
    read_ball_labels,
    write_event_comparison_csv,
    write_event_coverage_csv,
    write_event_label_session_backup,
    write_event_labels_csv,
    write_event_labels_json,
    write_event_overlays,
)
from tennis_vision.event_timeline import read_fps  # noqa: E402
from tennis_vision.friction import calculate_stage_8_2_friction_score  # noqa: E402
from tennis_vision.report import ensure_output_folders, utc_timestamp, write_json_report, write_markdown_report, write_timestamped_log  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 8.2 manual bounce / hit event labeling helper.")
    parser.add_argument("--interactive", dest="interactive", action="store_true", help="Open OpenCV UI to collect event labels.")
    parser.add_argument("--no-interactive", dest="interactive", action="store_false", help="Validate existing event labels only.")
    parser.set_defaults(interactive=False)
    parser.add_argument("--frames", type=str, default=None)
    parser.add_argument("--start-frame", type=int, default=90)
    parser.add_argument("--interval", type=int, default=15)
    parser.add_argument("--max-frames", type=int, default=12)
    parser.add_argument("--resize-width", type=int, default=1280)
    parser.add_argument("--merge-existing", dest="merge_existing", action="store_true", default=True)
    parser.add_argument("--no-merge-existing", dest="merge_existing", action="store_false")
    parser.add_argument("--candidate-window", type=int, default=5)
    parser.add_argument("--video", type=Path, default=PROJECT_ROOT / "samples" / "video_01.mov")
    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def determine_verdict(report: dict[str, Any]) -> str:
    flags = report["flags"]
    if flags["video_missing"] or flags["no_frames_loaded"]:
        return "blocked"
    if flags["no_event_labels"] or flags["no_bounce_or_hit_labels"]:
        return "needs_more_event_labels"
    if report["warnings"]:
        return "ready_with_warnings"
    return "ready_for_stage_8_3"


def recommended_next_step(report: dict[str, Any]) -> str:
    verdict = report["final_verdict"]
    if verdict == "ready_for_stage_8_3":
        return "Proceed to Stage 8.3: Event Validation and Reclassification."
    if verdict == "ready_with_warnings":
        return "Review manual label warnings, then proceed to Stage 8.3."
    if verdict == "needs_more_event_labels":
        return "Run Stage 8.2 interactively to label bounce, hit, no_event, and uncertain frames."
    return "Fix video/input blockers, then rerun Stage 8.2."


def field_block(rows: list[tuple[str, Any]]) -> str:
    lines: list[str] = []
    for key, value in rows:
        lines.append(f"{key}:")
        lines.append(f"  {value if value not in (None, '') else 'Not available'}")
        lines.append("")
    return "\n".join(lines).rstrip()


def bullet_list(items: list[str], empty: str) -> str:
    return empty if not items else "\n".join(f"- {item}" for item in items)


def build_markdown_sections(report: dict[str, Any]) -> list[tuple[str, str]]:
    interpretation = (
        "Stage 8.2 creates human event ground truth for the ambiguous hit/bounce layer. "
        "These labels are intended to validate and reclassify automatic event hypotheses before side-view replay relies on them."
    )
    if report["final_verdict"] == "needs_more_event_labels":
        interpretation += " No manual bounce/hit labels are available yet, so the next action is an interactive labeling pass."
    elif report["final_verdict"] in {"ready_for_stage_8_3", "ready_with_warnings"}:
        interpretation += " Manual event labels are available and can feed the next event validation stage."
    return [
        (
            "VERDICT",
            field_block(
                [
                    ("Final verdict", report["final_verdict"]),
                    ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"),
                    ("Mode", report["mode"]),
                ]
            ),
        ),
        (
            "LABEL SUMMARY",
            field_block(
                [
                    ("Existing labels", report["existing_labels_count"]),
                    ("New labels", report["new_labels_count"]),
                    ("Merged labels", report["merged_labels_count"]),
                    ("Bounce", report["bounce_count"]),
                    ("Hit", report["hit_count"]),
                    ("No event", report["no_event_count"]),
                    ("Uncertain", report["uncertain_count"]),
                    ("Skipped", report["skipped_count"]),
                ]
            ),
        ),
        (
            "AUTOMATIC EVENT COMPARISON",
            field_block(
                [
                    ("Exact matches", report["exact_matches"]),
                    ("Compatible matches", report["compatible_matches"]),
                    ("Mismatches", report["mismatches"]),
                    ("No auto event nearby", report["no_auto_event_nearby"]),
                ]
            ),
        ),
        (
            "OUTPUTS",
            field_block(
                [
                    ("Manual event labels", report["manual_event_labels_path"]),
                    ("Event comparison", report["event_label_comparison_path"]),
                    ("Event coverage", report["event_label_coverage_path"]),
                    ("Overlay folder", report["overlay_folder"]),
                ]
            ),
        ),
        ("PRODUCT OWNER INTERPRETATION", interpretation),
        ("WARNINGS", bullet_list(report["warnings"], "No warnings.")),
        ("ERRORS", bullet_list(report["errors"], "No errors.")),
        ("NEXT STEP", report["recommended_next_step"]),
    ]


def update_lab_notebook_safely() -> tuple[dict[str, Path], str | None]:
    try:
        from tennis_vision.lab_notebook import lab_notebook_paths, update_lab_notebook

        update_lab_notebook(PROJECT_ROOT)
        return lab_notebook_paths(PROJECT_ROOT, "stage_8_2"), None
    except Exception as exc:
        try:
            from tennis_vision.lab_notebook import lab_notebook_paths

            return lab_notebook_paths(PROJECT_ROOT, "stage_8_2"), f"Lab notebook update failed: {exc}"
        except Exception:
            return {
                "stage_page": PROJECT_ROOT / "docs" / "lab-notebook" / "stage_8_2_event_labeling.md",
                "experiment_index": PROJECT_ROOT / "docs" / "lab-notebook" / "experiment_index.md",
            }, f"Lab notebook update failed: {exc}"


def print_summary(report: dict[str, Any], lab_paths: dict[str, Path]) -> None:
    rows = [
        ("Verdict", report["final_verdict"]),
        ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"),
        ("Mode", report["mode"]),
        ("Existing labels", report["existing_labels_count"]),
        ("New labels", report["new_labels_count"]),
        ("Merged labels", report["merged_labels_count"]),
        ("Bounce labels", report["bounce_count"]),
        ("Hit labels", report["hit_count"]),
        ("No-event labels", report["no_event_count"]),
        ("Uncertain labels", report["uncertain_count"]),
        ("Compatible matches", report["compatible_matches"]),
        ("Mismatches", report["mismatches"]),
        ("Labels path", report["manual_event_labels_path"]),
        ("Lab notebook", lab_paths["stage_page"]),
        ("Recommended next step", report["recommended_next_step"]),
    ]
    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(title="Stage 8.2 Event Labeling")
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")
        for field, value in rows:
            table.add_row(str(field), str(value))
        Console().print(table)
    except ImportError:
        print("Stage 8.2 Event Labeling")
        for field, value in rows:
            print(f"{field}: {value}")


def video_is_readable(path: Path) -> bool:
    if not path.exists():
        return False
    capture = cv2.VideoCapture(str(path))
    try:
        return bool(capture.isOpened())
    finally:
        capture.release()


def main() -> int:
    args = parse_args()
    ensure_output_folders(PROJECT_ROOT)
    timestamp = utc_timestamp()
    output_dir = PROJECT_ROOT / "outputs" / "timeline" / "stage_8_2_event_labels"
    output_dir.mkdir(parents=True, exist_ok=True)
    session_dir = output_dir / "event_label_sessions"
    session_dir.mkdir(parents=True, exist_ok=True)
    overlay_dir = output_dir / "event_label_overlays"
    overlay_dir.mkdir(parents=True, exist_ok=True)

    video_path = resolve_path(args.video)
    frame_indices = build_frame_indices(frames=args.frames, start_frame=args.start_frame, interval=args.interval, max_frames=args.max_frames)
    fps = read_fps(PROJECT_ROOT / "outputs" / "reports" / "stage_1_video_probe_report.json")
    warnings: list[str] = []
    errors: list[str] = []

    video_missing = not video_path.exists()
    video_readable = video_is_readable(video_path)
    if video_missing:
        errors.append(f"Video missing: {video_path}")
    elif not video_readable:
        errors.append(f"Video could not be opened: {video_path}")

    labels_csv = output_dir / "manual_event_labels.csv"
    labels_json = output_dir / "manual_event_labels.json"
    comparison_csv = output_dir / "event_label_comparison.csv"
    coverage_csv = output_dir / "event_label_coverage.csv"

    existing_labels, source_info, source_warnings = load_durable_event_labels(labels_csv)
    warnings.extend(source_warnings)
    ball_labels, ball_warnings = read_ball_labels(PROJECT_ROOT / "outputs" / "timeline" / "stage_8_1_timeline_validation" / "expanded_ball_labels.csv")
    warnings.extend(ball_warnings)
    auto_events, auto_warnings = read_auto_events(
        [
            (PROJECT_ROOT / "outputs" / "timeline" / "stage_8_event_timeline" / "event_timeline.csv", "stage_8_event_timeline"),
            (PROJECT_ROOT / "outputs" / "ball_tracking" / "stage_6_trajectory_smoothing" / "trajectory_events.csv", "stage_6_trajectory_events"),
            (PROJECT_ROOT / "outputs" / "player_tracking" / "stage_7_player_interaction" / "ball_player_interactions.csv", "stage_7_interactions"),
        ]
    )
    warnings.extend(auto_warnings)

    new_labels: list[dict[str, Any]] = []
    frames_shown = 0
    if args.interactive and video_readable:
        result = collect_event_labels_interactively(
            video_path=video_path,
            frame_indices=frame_indices,
            output_dir=output_dir,
            resize_width=args.resize_width,
            fps=fps,
            ball_labels=ball_labels,
            auto_events=auto_events,
            candidate_window=args.candidate_window,
            label_session=f"stage_8_2_{timestamp}",
        )
        new_labels = list(result.get("labels", []))
        frames_shown = int(result.get("frames_shown", 0))
        warnings.extend(result.get("warnings", []))
        errors.extend(result.get("errors", []))
        if new_labels:
            write_event_label_session_backup(session_dir, timestamp, new_labels)
    elif args.interactive and not video_readable:
        errors.append("Interactive labeling requested but video is not readable.")

    merged_labels = existing_labels if not args.merge_existing else existing_labels
    if new_labels:
        from tennis_vision.event_labeling import merge_event_labels

        merged_labels = merge_event_labels(existing_labels if args.merge_existing else [], new_labels)

    if merged_labels or not labels_csv.exists():
        write_event_labels_csv(labels_csv, merged_labels)
        write_event_labels_json(labels_json, merged_labels)
    elif not merged_labels and labels_csv.exists():
        warnings.append("No labels were available; existing durable event label file was left unchanged.")

    coverage = analyze_event_label_coverage(merged_labels)
    comparison_rows, comparison_summary = compare_manual_events_to_auto_events(merged_labels, auto_events, candidate_window=args.candidate_window)
    write_event_coverage_csv(coverage_csv, coverage)
    write_event_comparison_csv(comparison_csv, comparison_rows)
    overlay_count = 0
    if merged_labels and video_readable:
        overlay_count, overlay_warnings = write_event_overlays(
            video_path=video_path,
            labels=merged_labels,
            ball_labels=ball_labels,
            auto_events=auto_events,
            overlay_dir=overlay_dir,
            resize_width=args.resize_width,
            candidate_window=args.candidate_window,
        )
        warnings.extend(overlay_warnings)

    flags = {
        "video_missing": video_missing or not video_readable,
        "no_frames_loaded": bool(args.interactive and frames_shown == 0),
        "no_event_labels": len(merged_labels) == 0,
        "no_bounce_or_hit_labels": coverage["bounce_labels_count"] + coverage["hit_labels_count"] == 0,
        "comparison_failed": bool(merged_labels and not comparison_rows),
        "label_persistence_failed": bool((merged_labels or not labels_csv.exists()) and not labels_csv.exists()),
        "manual_action_required": bool(not args.interactive and len(merged_labels) == 0),
    }
    if flags["manual_action_required"]:
        warnings.append("No manual event labels exist yet; run Stage 8.2 in interactive mode to collect event ground truth.")
    if flags["no_bounce_or_hit_labels"] and merged_labels:
        warnings.append("Manual labels exist, but no bounce or hit labels are available yet.")

    friction = calculate_stage_8_2_friction_score(**flags, errors_count=len(errors), warnings_count=len(warnings))
    report: dict[str, Any] = {
        "timestamp": timestamp,
        "stage": "stage_8_2_event_labeling",
        "mode": "interactive" if args.interactive else "non_interactive",
        "frames_requested": frame_indices,
        "frames_shown": frames_shown,
        "existing_labels_count": len(existing_labels),
        "new_labels_count": len(new_labels),
        "merged_labels_count": len(merged_labels),
        "bounce_count": coverage["bounce_labels_count"],
        "hit_count": coverage["hit_labels_count"],
        "no_event_count": coverage["no_event_count"],
        "uncertain_count": coverage["uncertain_count"],
        "skipped_count": coverage["skipped_count"],
        "comparison_count": comparison_summary["comparison_count"],
        "exact_matches": comparison_summary["exact_matches"],
        "compatible_matches": comparison_summary["compatible_matches"],
        "mismatches": comparison_summary["mismatches"],
        "no_auto_event_nearby": comparison_summary["no_auto_event_nearby"],
        "manual_event_labels_path": str(labels_csv),
        "event_label_comparison_path": str(comparison_csv),
        "event_label_coverage_path": str(coverage_csv),
        "overlay_folder": str(overlay_dir),
        "overlay_count": overlay_count,
        "label_source_used": source_info.get("label_source_used"),
        "warnings": warnings,
        "errors": errors,
        "flags": flags,
        "friction": friction,
        "final_verdict": "blocked",
        "recommended_next_step": "",
        "output_paths": {
            "manual_event_labels_csv": str(labels_csv),
            "manual_event_labels_json": str(labels_json),
            "event_label_comparison": str(comparison_csv),
            "event_label_coverage": str(coverage_csv),
            "event_label_overlays": str(overlay_dir),
        },
    }
    report["final_verdict"] = determine_verdict(report)
    report["recommended_next_step"] = recommended_next_step(report)

    log_path = write_timestamped_log(
        PROJECT_ROOT,
        "stage_8_2_event_labeling",
        [
            f"timestamp={timestamp}",
            f"mode={report['mode']}",
            f"verdict={report['final_verdict']}",
            f"friction={friction['score']} ({friction['band']})",
            f"merged_labels={len(merged_labels)}",
            f"bounce={report['bounce_count']}",
            f"hit={report['hit_count']}",
        ],
    )
    report["log_path"] = str(log_path)
    report["json_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_8_2_event_labeling_report.json")
    report["markdown_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_8_2_event_labeling_report.md")
    write_json_report(Path(report["json_report_path"]), report)
    write_markdown_report(Path(report["markdown_report_path"]), "Stage 8.2 Manual Bounce / Hit Event Labeling Report", build_markdown_sections(report))

    lab_paths, notebook_warning = update_lab_notebook_safely()
    if notebook_warning:
        report["warnings"].append(notebook_warning)
        write_json_report(Path(report["json_report_path"]), report)
        write_markdown_report(Path(report["markdown_report_path"]), "Stage 8.2 Manual Bounce / Hit Event Labeling Report", build_markdown_sections(report))
        print(f"Warning: {notebook_warning}")
    print_summary(report, lab_paths)
    return 1 if report["final_verdict"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
