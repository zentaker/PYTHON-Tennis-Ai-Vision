"""Run Stage 8.2 manual bounce / hit event labeling helper."""

from __future__ import annotations

import argparse
import shutil
import sys
import time
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
    analyze_frame_duplicates,
    audit_event_labels,
    clean_event_labels_for_integrity,
    collect_event_labels_interactively,
    collect_event_labels_timeline_viewer,
    compare_manual_events_to_auto_events,
    dedupe_sorted_frame_indices,
    load_durable_event_labels,
    merge_event_labels,
    read_auto_events,
    read_ball_labels,
    write_event_comparison_csv,
    write_event_coverage_csv,
    write_event_label_integrity_reports,
    write_event_label_session_backup,
    write_event_labels_csv,
    write_event_labels_json,
    write_event_overlays,
    write_frame_duplicate_audit,
    write_manual_event_windows_csv,
    write_manual_event_windows_json,
)
from tennis_vision.event_timeline import read_fps  # noqa: E402
from tennis_vision.friction import calculate_stage_8_2_friction_score  # noqa: E402
from tennis_vision.friction_semantics import build_friction_breakdown  # noqa: E402
from tennis_vision.report import ensure_output_folders, utc_timestamp, write_json_report, write_markdown_report, write_timestamped_log  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 8.2 manual bounce / hit event labeling helper.")
    parser.add_argument("--interactive", dest="interactive", action="store_true", help="Open OpenCV UI to collect event labels.")
    parser.add_argument("--no-interactive", dest="interactive", action="store_false", help="Validate existing event labels only.")
    parser.set_defaults(interactive=False)
    parser.add_argument("--timeline-viewer", action="store_true", help="Use editable timeline viewer in interactive mode.")
    parser.add_argument("--review-only", action="store_true", help="Navigate frames without saving labels.")
    parser.add_argument("--preload", action="store_true", help="Preload resized frames instead of lazy loading them.")
    parser.add_argument("--preserve-no-event-points", action="store_true", help="Preserve existing x/y points on no_event labels.")
    parser.add_argument("--audit-labels", action="store_true", help="Audit durable manual labels without opening the UI.")
    parser.add_argument("--fix-labels", action="store_true", help="Fix duplicate labels and no_event points after creating a backup.")
    parser.add_argument("--audit-frames", action="store_true", help="Audit selected frames for near-duplicate visual content.")
    parser.add_argument("--audit-fast", dest="audit_fast", action="store_true", help="Use lightweight signature-only frame audit.")
    parser.add_argument("--no-audit-fast", dest="audit_fast", action="store_false", help="Disable lightweight signature-only frame audit.")
    parser.set_defaults(audit_fast=True)
    parser.add_argument("--signature-width", type=int, default=160, help="Width for downscaled grayscale frame signatures.")
    parser.add_argument("--duplicate-threshold", type=float, default=0.0006, help="Mean absolute visual diff threshold for near-duplicate frames.")
    parser.add_argument("--sequential-read", dest="sequential_read", action="store_true", help="Decode selected frame window sequentially.")
    parser.add_argument("--random-seek", dest="sequential_read", action="store_false", help="Seek each selected frame independently.")
    parser.set_defaults(sequential_read=None)
    parser.add_argument("--collapse-duplicates", dest="collapse_duplicates", action="store_true", help="Show one representative item per visual duplicate group.")
    parser.add_argument("--expand-duplicates", dest="collapse_duplicates", action="store_false", help="Show every selected frame individually.")
    parser.set_defaults(collapse_duplicates=True)
    parser.add_argument("--frames", type=str, default=None)
    parser.add_argument("--start-frame", type=int, default=90)
    parser.add_argument("--interval", type=int, default=15)
    parser.add_argument("--max-frames", type=int, default=12)
    parser.add_argument("--resize-width", type=int, default=1280)
    parser.add_argument("--merge-existing", dest="merge_existing", action="store_true", default=True)
    parser.add_argument("--no-merge-existing", dest="merge_existing", action="store_false")
    parser.add_argument("--candidate-window", type=int, default=5)
    parser.add_argument("--show-ball-overlay", dest="show_ball_overlay", action="store_true", help="Show nearest ball marker overlay in timeline viewer.")
    parser.add_argument("--hide-ball-overlay", dest="show_ball_overlay", action="store_false", help="Hide nearest ball marker overlay in timeline viewer.")
    parser.set_defaults(show_ball_overlay=False)
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
                    ("Viewer mode", report["viewer_mode"]),
                    ("Frames loaded", report["frames_loaded"]),
                    ("Duplicate frames removed", report["duplicate_frames_removed"]),
                    ("Near-duplicate pairs", report["near_duplicate_pairs"]),
                    ("Visual groups", report["visual_groups_count"]),
                    ("Sequential read used", report["sequential_read_used"]),
                    ("Audit runtime seconds", report["audit_runtime_seconds"]),
                    ("Signature width", report["signature_width"]),
                    ("Collapse duplicates", report["collapse_duplicates"]),
                ]
            ),
        ),
        (
            "LABEL SUMMARY",
            field_block(
                [
                    ("Existing labels", report["existing_labels_count"]),
                    ("New labels", report["new_labels_count"]),
                    ("Labels created", report["labels_created"]),
                    ("Labels updated", report["labels_updated"]),
                    ("Labels deleted", report["labels_deleted"]),
                    ("Event windows created", report["event_windows_created"]),
                    ("Event windows updated", report["event_windows_updated"]),
                    ("Merged labels", report["merged_labels_count"]),
                    ("Ball overlay enabled", report["ball_overlay_enabled"]),
                    ("Event point marker default off", report["event_point_marker_default_off"]),
                    ("Review only", report["review_only"]),
                    ("Preload", report["preload"]),
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
                    ("Session backup", report["session_backup_path"]),
                    ("Label integrity report", report["label_integrity_report_md"]),
                    ("Frame duplicate audit", report["frame_audit_path"]),
                ]
            ),
        ),
        (
            "FRAME DUPLICATE ANALYSIS",
            field_block(
                [
                    ("Enabled", report["frame_duplicate_analysis_enabled"]),
                    ("Near-duplicate pairs", report["near_duplicate_pairs"]),
                    ("Visual groups", report["visual_groups_count"]),
                    ("Largest duplicate group", report["frame_duplicate_audit"].get("largest_duplicate_group")),
                    ("Audit path", report["frame_audit_path"]),
                ]
            ),
        ),
        (
            "LABEL INTEGRITY AUDIT",
            field_block(
                [
                    ("no_event labels with points", report["label_integrity_audit"].get("suspicious_no_event_points_count")),
                    ("Repeated point sequences", report["label_integrity_audit"].get("repeated_point_sequences_count")),
                    ("Duplicate frame labels", report["label_integrity_audit"].get("duplicate_frame_labels_count")),
                    ("Bounce/hit labels without point", report["label_integrity_audit"].get("labels_without_point_count")),
                    ("Cleaned no_event points", report["label_integrity_audit"].get("cleaned_no_event_points_count")),
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
        ("Viewer mode", report["viewer_mode"]),
        ("Frames loaded", report["frames_loaded"]),
        ("Duplicate frames removed", report["duplicate_frames_removed"]),
        ("Near-duplicate pairs", report["near_duplicate_pairs"]),
        ("Visual groups", report["visual_groups_count"]),
        ("Audit runtime seconds", report["audit_runtime_seconds"]),
        ("Collapse duplicates", report["collapse_duplicates"]),
        ("Existing labels", report["existing_labels_count"]),
        ("New labels", report["new_labels_count"]),
        ("Labels created", report["labels_created"]),
        ("Labels updated", report["labels_updated"]),
        ("Labels deleted", report["labels_deleted"]),
        ("Event windows", report["event_windows_created"]),
        ("Merged labels", report["merged_labels_count"]),
        ("Bounce labels", report["bounce_count"]),
        ("Hit labels", report["hit_count"]),
        ("No-event labels", report["no_event_count"]),
        ("Uncertain labels", report["uncertain_count"]),
        ("Compatible matches", report["compatible_matches"]),
        ("Mismatches", report["mismatches"]),
        ("Ball overlay enabled", report["ball_overlay_enabled"]),
        ("Point marker enabled", report["point_marker_enabled"]),
        ("Integrity issues", report["label_integrity_audit"].get("suspicious_no_event_points_count", 0) + report["label_integrity_audit"].get("repeated_point_sequences_count", 0)),
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
    if args.fix_labels:
        args.audit_labels = True
    if args.audit_labels or args.audit_frames:
        args.interactive = False
    ensure_output_folders(PROJECT_ROOT)
    timestamp = utc_timestamp()
    output_dir = PROJECT_ROOT / "outputs" / "timeline" / "stage_8_2_event_labels"
    output_dir.mkdir(parents=True, exist_ok=True)
    session_dir = output_dir / "event_label_sessions"
    session_dir.mkdir(parents=True, exist_ok=True)
    overlay_dir = output_dir / "event_label_overlays"
    overlay_dir.mkdir(parents=True, exist_ok=True)

    video_path = resolve_path(args.video)
    raw_frame_indices = build_frame_indices(frames=args.frames, start_frame=args.start_frame, interval=args.interval, max_frames=args.max_frames)
    frame_indices, duplicate_frames_removed = dedupe_sorted_frame_indices(raw_frame_indices)
    sequential_read_used = bool(args.sequential_read) if args.sequential_read is not None else bool(args.interval == 1 and (args.timeline_viewer or args.audit_frames))
    fps = read_fps(PROJECT_ROOT / "outputs" / "reports" / "stage_1_video_probe_report.json")
    warnings: list[str] = []
    errors: list[str] = []

    video_missing = not video_path.exists()
    video_readable = video_path.exists() if args.audit_frames and not args.interactive else video_is_readable(video_path)
    if video_missing:
        errors.append(f"Video missing: {video_path}")
    elif not video_readable:
        errors.append(f"Video could not be opened: {video_path}")

    labels_csv = output_dir / "manual_event_labels.csv"
    labels_json = output_dir / "manual_event_labels.json"
    comparison_csv = output_dir / "event_label_comparison.csv"
    coverage_csv = output_dir / "event_label_coverage.csv"
    integrity_json = output_dir / "event_label_integrity_report.json"
    integrity_md = output_dir / "event_label_integrity_report.md"

    existing_labels, source_info, source_warnings = load_durable_event_labels(labels_csv)
    warnings.extend(source_warnings)
    integrity_audit = audit_event_labels(existing_labels, selected_frames=frame_indices if args.frames else None)
    fix_backup_path = ""
    if args.fix_labels and labels_csv.exists():
        backup_dir = output_dir / "label_backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        safe_timestamp = timestamp.replace(":", "").replace("+", "Z")
        backup_path = backup_dir / f"manual_event_labels_before_fix_{safe_timestamp}.csv"
        shutil.copy2(labels_csv, backup_path)
        fix_backup_path = str(backup_path)
        existing_labels, fix_summary = clean_event_labels_for_integrity(existing_labels, preserve_no_event_points=args.preserve_no_event_points)
        write_event_labels_csv(labels_csv, existing_labels)
        write_event_labels_json(labels_json, existing_labels)
        integrity_audit = audit_event_labels(existing_labels, selected_frames=frame_indices if args.frames else None)
        integrity_audit["cleaned_no_event_points_count"] = fix_summary["cleaned_no_event_points_count"]
        integrity_audit["duplicate_frame_labels_removed"] = fix_summary["duplicate_frame_labels_removed"]
        integrity_audit["fix_backup_path"] = fix_backup_path
    integrity_paths = write_event_label_integrity_reports(output_dir, integrity_audit)
    frame_audit_summary: dict[str, Any] = {
        "total_frames": 0,
        "unique_visual_groups": 0,
        "near_duplicate_pairs_count": 0,
        "visual_groups_with_more_than_one_frame": 0,
        "largest_duplicate_group": "",
        "csv_path": str(output_dir / "frame_duplicate_audit.csv"),
        "markdown_path": str(output_dir / "frame_duplicate_audit.md"),
        "audit_runtime_seconds": 0,
        "signature_width": args.signature_width,
        "collapse_duplicates_recommended": False,
    }
    if args.audit_frames and video_readable:
        audit_start = time.perf_counter()
        frame_rows, _group_meta, _payloads, frame_warnings = analyze_frame_duplicates(
            video_path=video_path,
            frame_indices=frame_indices,
            resize_width=args.resize_width,
            duplicate_threshold=args.duplicate_threshold,
            sequential_read=sequential_read_used,
            signature_width=args.signature_width,
            keep_display=not args.audit_fast,
        )
        warnings.extend(frame_warnings)
        audit_runtime = time.perf_counter() - audit_start
        frame_audit_summary = write_frame_duplicate_audit(
            output_dir,
            frame_rows,
            duplicate_threshold=args.duplicate_threshold,
            sequential_read=sequential_read_used,
            signature_width=args.signature_width,
            audit_runtime_seconds=audit_runtime,
        )
    elif args.audit_frames and not video_readable:
        errors.append("Frame duplicate audit requested but video is not readable.")

    if args.audit_frames and args.audit_fast and not args.interactive:
        coverage = analyze_event_label_coverage(existing_labels)
        integrity_issue_count = (
            int(integrity_audit.get("suspicious_no_event_points_count", 0))
            + int(integrity_audit.get("repeated_point_sequences_count", 0))
            + int(integrity_audit.get("duplicate_frame_labels_count", 0))
        )
        near_duplicate_pairs = int(frame_audit_summary.get("near_duplicate_pairs_count", 0))
        visual_groups_count = int(frame_audit_summary.get("unique_visual_groups", 0))
        friction = calculate_stage_8_2_friction_score(
            video_missing=video_missing or not video_readable,
            no_frames_loaded=False,
            no_event_labels=len(existing_labels) == 0,
            no_bounce_or_hit_labels=coverage["bounce_labels_count"] + coverage["hit_labels_count"] == 0,
            comparison_failed=False,
            label_persistence_failed=False,
            manual_action_required=False,
            errors_count=len(errors),
            warnings_count=len(warnings),
        )
        duplicate_frame_friction = 20 if near_duplicate_pairs else 0
        label_integrity_friction = 0 if integrity_issue_count == 0 else min(70, 20 + integrity_issue_count * 8)
        friction_breakdown = build_friction_breakdown(
            execution_score=friction["score"],
            execution_reason="Fast frame duplicate audit completed.",
            semantic_model_score=max(duplicate_frame_friction, label_integrity_friction),
            semantic_model_reason="Near-duplicate frames or label integrity issues require grouped/manual review." if (near_duplicate_pairs or integrity_issue_count) else "No duplicate-frame or label integrity issues found.",
            human_loop_score=30 if near_duplicate_pairs else 10,
            human_loop_reason="Near-duplicate frames should be reviewed as visual groups." if near_duplicate_pairs else "No duplicate-frame review required.",
            product_validation_status="pending_review" if near_duplicate_pairs else "passed_with_warnings",
            product_validation_reason="Product Owner should use collapsed visual groups for labeling." if near_duplicate_pairs else "No visual duplicate groups require review.",
            downstream_correction_score=10 if near_duplicate_pairs else 0,
            downstream_correction_reason="Use Stage 8.2 event windows before rerunning Stage 8.3." if near_duplicate_pairs else "No downstream duplicate-frame correction required.",
        )
        report: dict[str, Any] = {
            "timestamp": timestamp,
            "stage": "stage_8_2_event_labeling",
            "mode": "non_interactive",
            "viewer_mode": "linear",
            "review_only": False,
            "preload": False,
            "audit_fast": True,
            "signature_width": args.signature_width,
            "collapse_duplicates": bool(args.collapse_duplicates),
            "frames_requested": frame_indices,
            "frames_shown": 0,
            "frames_loaded": 0,
            "duplicate_frames_removed": duplicate_frames_removed,
            "frame_duplicate_analysis_enabled": True,
            "near_duplicate_pairs": near_duplicate_pairs,
            "visual_groups_count": visual_groups_count,
            "event_windows_created": 0,
            "event_windows_updated": 0,
            "sequential_read_used": sequential_read_used,
            "frame_audit_path": str(frame_audit_summary.get("markdown_path") or ""),
            "frame_duplicate_audit": frame_audit_summary,
            "audit_runtime_seconds": frame_audit_summary.get("audit_runtime_seconds", 0),
            "duplicate_frame_friction": {"score": duplicate_frame_friction, "band": "low friction" if duplicate_frame_friction else "none", "reason": "Near-duplicate visual frames found; collapsed mode is recommended." if near_duplicate_pairs else "No near-duplicate visual frames found."},
            "label_integrity_friction": {"score": label_integrity_friction, "band": "high friction" if label_integrity_friction >= 61 else ("medium friction" if label_integrity_friction >= 31 else ("low friction" if label_integrity_friction else "none")), "reason": "Label integrity audit found remaining issues." if integrity_issue_count else "Label integrity audit did not find stale point issues."},
            "human_loop_friction": friction_breakdown["human_loop"],
            "product_validation_status": friction_breakdown["product_validation"]["status"],
            "existing_labels_count": len(existing_labels),
            "new_labels_count": 0,
            "labels_created": 0,
            "labels_updated": 0,
            "labels_deleted": 0,
            "merged_labels_count": len(existing_labels),
            "overlays_default_off": True,
            "event_point_marker_default_off": True,
            "point_marker_enabled": False,
            "ball_overlay_enabled": False,
            "preserve_no_event_points": bool(args.preserve_no_event_points),
            "session_backup_path": "",
            "audit_labels": False,
            "fix_labels": False,
            "fix_backup_path": "",
            "label_integrity_audit": integrity_audit,
            "label_integrity_report_json": str(integrity_paths["json"]),
            "label_integrity_report_md": str(integrity_paths["markdown"]),
            "bounce_count": coverage["bounce_labels_count"],
            "hit_count": coverage["hit_labels_count"],
            "no_event_count": coverage["no_event_count"],
            "uncertain_count": coverage["uncertain_count"],
            "skipped_count": coverage["skipped_count"],
            "comparison_count": 0,
            "exact_matches": 0,
            "compatible_matches": 0,
            "mismatches": 0,
            "no_auto_event_nearby": 0,
            "manual_event_labels_path": str(labels_csv),
            "event_label_comparison_path": str(comparison_csv),
            "event_label_coverage_path": str(coverage_csv),
            "overlay_folder": str(overlay_dir),
            "overlay_count": 0,
            "label_source_used": source_info.get("label_source_used"),
            "warnings": warnings,
            "errors": errors,
            "flags": {
                "video_missing": video_missing or not video_readable,
                "no_frames_loaded": False,
                "no_event_labels": len(existing_labels) == 0,
                "no_bounce_or_hit_labels": coverage["bounce_labels_count"] + coverage["hit_labels_count"] == 0,
                "comparison_failed": False,
                "label_persistence_failed": False,
                "manual_action_required": False,
            },
            "friction": friction,
            "friction_breakdown": friction_breakdown,
            "final_verdict": "ready_for_stage_8_3" if not errors else "blocked",
            "recommended_next_step": "Use collapsed timeline viewer to label visual groups as event windows, then rerun Stage 8.3.",
            "output_paths": {
                "manual_event_labels_csv": str(labels_csv),
                "manual_event_labels_json": str(labels_json),
                "label_integrity_report_json": str(integrity_paths["json"]),
                "label_integrity_report_md": str(integrity_paths["markdown"]),
                "frame_duplicate_audit_csv": str(frame_audit_summary.get("csv_path") or ""),
                "frame_duplicate_audit_md": str(frame_audit_summary.get("markdown_path") or ""),
            },
        }
        report["json_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_8_2_event_labeling_report.json")
        report["markdown_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_8_2_event_labeling_report.md")
        write_json_report(Path(report["json_report_path"]), report)
        write_markdown_report(Path(report["markdown_report_path"]), "Stage 8.2 Manual Bounce / Hit Event Labeling Report", build_markdown_sections(report))
        print_summary(
            report,
            {
                "stage_page": PROJECT_ROOT / "docs" / "lab-notebook" / "stage_8_2_event_labeling.md",
                "experiment_index": PROJECT_ROOT / "docs" / "lab-notebook" / "experiment_index.md",
            },
        )
        return 1 if report["final_verdict"] == "blocked" else 0
    if args.audit_frames and not args.interactive:
        ball_labels: list[dict[str, Any]] = []
        auto_events: list[dict[str, Any]] = []
    else:
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
    deleted_frames: list[int] = []
    frames_shown = 0
    frames_loaded = 0
    labels_created = 0
    labels_updated = 0
    labels_deleted = 0
    event_windows_created = 0
    event_windows_updated = 0
    near_duplicate_pairs = int(frame_audit_summary.get("near_duplicate_pairs_count", 0))
    visual_groups_count = int(frame_audit_summary.get("unique_visual_groups", 0))
    session_backup_path = ""
    viewer_mode = "timeline_viewer" if args.timeline_viewer else "linear"
    ball_overlay_enabled_report = bool(args.show_ball_overlay)
    point_marker_enabled_report = False
    if args.interactive and video_readable:
        if args.timeline_viewer:
            result = collect_event_labels_timeline_viewer(
                video_path=video_path,
                frame_indices=frame_indices,
                output_dir=output_dir,
                resize_width=args.resize_width,
                fps=fps,
                ball_labels=ball_labels,
                auto_events=auto_events,
                candidate_window=args.candidate_window,
                label_session=f"stage_8_2_{timestamp}",
                existing_labels=existing_labels,
                show_ball_overlay=args.show_ball_overlay,
                preload=args.preload,
                review_only=args.review_only,
                preserve_no_event_points=args.preserve_no_event_points,
                duplicate_threshold=args.duplicate_threshold,
                sequential_read=sequential_read_used,
                signature_width=args.signature_width,
                collapse_duplicates=args.collapse_duplicates,
            )
        else:
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
        deleted_frames = [int(frame) for frame in result.get("deleted_frames", [])]
        frames_shown = int(result.get("frames_shown", 0))
        frames_loaded = int(result.get("frames_loaded", frames_shown))
        duplicate_frames_removed += int(result.get("duplicate_frames_removed", 0))
        labels_created = int(result.get("labels_created", len(new_labels)))
        labels_updated = int(result.get("labels_updated", 0))
        labels_deleted = int(result.get("labels_deleted", len(deleted_frames)))
        event_windows_created = int(result.get("event_windows_created", 0))
        event_windows_updated = int(result.get("event_windows_updated", 0))
        near_duplicate_pairs = int(result.get("near_duplicate_pairs", near_duplicate_pairs))
        visual_groups_count = int(result.get("visual_groups_count", visual_groups_count))
        session_backup_path = str(result.get("session_backup_path") or "")
        ball_overlay_enabled_report = bool(result.get("ball_overlay_enabled", ball_overlay_enabled_report))
        point_marker_enabled_report = bool(result.get("point_marker_enabled", point_marker_enabled_report))
        warnings.extend(result.get("warnings", []))
        errors.extend(result.get("errors", []))
        if args.review_only:
            new_labels = []
            deleted_frames = []
            labels_created = 0
            labels_updated = 0
            labels_deleted = 0
        if new_labels and not session_backup_path and not args.review_only:
            backup = write_event_label_session_backup(session_dir, timestamp, new_labels)
            session_backup_path = session_backup_path or str(backup.get("csv", ""))
    elif args.interactive and not video_readable:
        errors.append("Interactive labeling requested but video is not readable.")

    merged_labels = existing_labels if not args.merge_existing else existing_labels
    if new_labels or deleted_frames:
        merged_labels = merge_event_labels(existing_labels if args.merge_existing else [], new_labels, deleted_frames=deleted_frames)

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
    if merged_labels and video_readable and not (args.interactive and args.timeline_viewer) and not args.audit_labels:
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
        "comparison_failed": bool(merged_labels and not comparison_rows and not args.audit_frames),
        "label_persistence_failed": bool((merged_labels or not labels_csv.exists()) and not labels_csv.exists()),
        "manual_action_required": bool(not args.interactive and len(merged_labels) == 0),
    }
    if flags["manual_action_required"]:
        warnings.append("No manual event labels exist yet; run Stage 8.2 in interactive mode to collect event ground truth.")
    if flags["no_bounce_or_hit_labels"] and merged_labels:
        warnings.append("Manual labels exist, but no bounce or hit labels are available yet.")

    friction = calculate_stage_8_2_friction_score(**flags, errors_count=len(errors), warnings_count=len(warnings))
    integrity_issue_count = (
        int(integrity_audit.get("suspicious_no_event_points_count", 0))
        + int(integrity_audit.get("repeated_point_sequences_count", 0))
        + int(integrity_audit.get("duplicate_frame_labels_count", 0))
    )
    label_integrity_score = 0 if integrity_issue_count == 0 else min(70, 20 + integrity_issue_count * 8)
    duplicate_frame_friction = 0
    if near_duplicate_pairs > 0:
        duplicate_frame_friction = 20 if args.collapse_duplicates else 45
    label_integrity_friction = label_integrity_score
    human_loop_score = 40 if args.interactive else (20 if args.audit_labels else 10)
    product_status = "pending_review" if args.interactive or args.audit_labels else "passed_with_warnings"
    friction_breakdown = build_friction_breakdown(
        execution_score=friction["score"],
        execution_reason="Stage 8.2 script completed and wrote reports." if not errors else "Stage 8.2 reported execution errors.",
        semantic_model_score=max(label_integrity_score, duplicate_frame_friction),
        semantic_model_reason="Duplicate frame or label integrity issues need Product Owner-aware handling." if (integrity_issue_count or near_duplicate_pairs) else "No duplicate-frame or label integrity issues found.",
        human_loop_score=human_loop_score,
        human_loop_reason="Timeline/manual labeling requires Product Owner visual review." if args.interactive else "Non-interactive audit uses existing labels.",
        product_validation_status=product_status,
        product_validation_reason="Manual labeling output requires Product Owner validation of exact bounce/hit frames." if args.interactive else "Existing labels were validated non-interactively.",
        downstream_correction_score=15 if integrity_issue_count else 0,
        downstream_correction_reason="Integrity issues may require label cleanup before Stage 8.3/8.4." if integrity_issue_count else "No downstream label cleanup required from this run.",
    )
    report: dict[str, Any] = {
        "timestamp": timestamp,
        "stage": "stage_8_2_event_labeling",
        "mode": "interactive" if args.interactive else "non_interactive",
        "viewer_mode": viewer_mode,
        "review_only": bool(args.review_only),
        "preload": bool(args.preload),
        "audit_fast": bool(args.audit_fast),
        "signature_width": args.signature_width,
        "collapse_duplicates": bool(args.collapse_duplicates),
        "frames_requested": frame_indices,
        "frames_shown": frames_shown,
        "frames_loaded": frames_loaded,
        "duplicate_frames_removed": duplicate_frames_removed,
        "frame_duplicate_analysis_enabled": bool(args.audit_frames or args.timeline_viewer),
        "near_duplicate_pairs": near_duplicate_pairs,
        "visual_groups_count": visual_groups_count,
        "event_windows_created": event_windows_created,
        "event_windows_updated": event_windows_updated,
        "sequential_read_used": sequential_read_used,
        "frame_audit_path": str(frame_audit_summary.get("markdown_path") or ""),
        "frame_duplicate_audit": frame_audit_summary,
        "audit_runtime_seconds": frame_audit_summary.get("audit_runtime_seconds", 0),
        "duplicate_frame_friction": {
            "score": duplicate_frame_friction,
            "band": "medium friction" if duplicate_frame_friction >= 31 else ("low friction" if duplicate_frame_friction else "none"),
            "reason": "Near-duplicate visual frames found; collapsed mode reduces frame-perfect labeling friction." if near_duplicate_pairs else "No near-duplicate visual frames found.",
        },
        "label_integrity_friction": {
            "score": label_integrity_friction,
            "band": "high friction" if label_integrity_friction >= 61 else ("medium friction" if label_integrity_friction >= 31 else ("low friction" if label_integrity_friction else "none")),
            "reason": "Label integrity audit found remaining issues." if integrity_issue_count else "Label integrity audit did not find stale point issues.",
        },
        "human_loop_friction": friction_breakdown["human_loop"],
        "product_validation_status": friction_breakdown["product_validation"]["status"],
        "existing_labels_count": len(existing_labels),
        "new_labels_count": len(new_labels),
        "labels_created": labels_created,
        "labels_updated": labels_updated,
        "labels_deleted": labels_deleted,
        "merged_labels_count": len(merged_labels),
        "overlays_default_off": True,
        "event_point_marker_default_off": True,
        "point_marker_enabled": point_marker_enabled_report,
        "ball_overlay_enabled": ball_overlay_enabled_report,
        "preserve_no_event_points": bool(args.preserve_no_event_points),
        "session_backup_path": session_backup_path,
        "audit_labels": bool(args.audit_labels),
        "fix_labels": bool(args.fix_labels),
        "fix_backup_path": fix_backup_path,
        "label_integrity_audit": integrity_audit,
        "label_integrity_report_json": str(integrity_paths["json"]),
        "label_integrity_report_md": str(integrity_paths["markdown"]),
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
        "friction_breakdown": friction_breakdown,
        "final_verdict": "blocked",
        "recommended_next_step": "",
        "output_paths": {
            "manual_event_labels_csv": str(labels_csv),
            "manual_event_labels_json": str(labels_json),
            "event_label_comparison": str(comparison_csv),
            "event_label_coverage": str(coverage_csv),
            "event_label_overlays": str(overlay_dir),
            "session_backup": session_backup_path,
            "label_integrity_report_json": str(integrity_paths["json"]),
            "label_integrity_report_md": str(integrity_paths["markdown"]),
            "fix_backup": fix_backup_path,
            "frame_duplicate_audit_csv": str(frame_audit_summary.get("csv_path") or ""),
            "frame_duplicate_audit_md": str(frame_audit_summary.get("markdown_path") or ""),
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

    if args.audit_frames and not args.interactive and not args.audit_labels:
        lab_paths = {
            "stage_page": PROJECT_ROOT / "docs" / "lab-notebook" / "stage_8_2_event_labeling.md",
            "experiment_index": PROJECT_ROOT / "docs" / "lab-notebook" / "experiment_index.md",
        }
        notebook_warning = None
    else:
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
