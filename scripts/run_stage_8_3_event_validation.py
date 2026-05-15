"""Run Stage 8.3 event validation and reclassification."""

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

from tennis_vision.event_reclassification import (  # noqa: E402
    build_validated_event_timeline,
    reclassify_auto_event,
    summarize_reclassification,
    write_event_validation_results_csv,
    write_event_validation_summary_json,
    write_validated_event_timeline_csv,
)
from tennis_vision.event_validation import (  # noqa: E402
    classify_validation_status,
    group_manual_event_windows,
    manual_frame_range,
    nearest_manual_evidence,
    read_automatic_events,
    read_manual_event_labels,
    read_manual_event_windows,
    summarize_manual_event_labels,
    write_manual_event_windows_csv,
)
from tennis_vision.friction import calculate_stage_8_3_friction_score  # noqa: E402
from tennis_vision.report import ensure_output_folders, utc_timestamp, write_json_report, write_markdown_report, write_timestamped_log  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 8.3 event validation and reclassification.")
    parser.add_argument("--manual-labels", type=Path, default=PROJECT_ROOT / "outputs" / "timeline" / "stage_8_2_event_labels" / "manual_event_labels.csv")
    parser.add_argument("--manual-windows", type=Path, default=PROJECT_ROOT / "outputs" / "timeline" / "stage_8_2_event_labels" / "manual_event_windows.csv")
    parser.add_argument("--timeline", type=Path, default=PROJECT_ROOT / "outputs" / "timeline" / "stage_8_event_timeline" / "event_timeline.csv")
    parser.add_argument("--stage6-events", type=Path, default=PROJECT_ROOT / "outputs" / "ball_tracking" / "stage_6_trajectory_smoothing" / "trajectory_events.csv")
    parser.add_argument("--stage7-interactions", type=Path, default=PROJECT_ROOT / "outputs" / "player_tracking" / "stage_7_player_interaction" / "ball_player_interactions.csv")
    parser.add_argument("--validation-window", type=int, default=5)
    parser.add_argument("--bounce-window-gap", type=int, default=3)
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs" / "timeline" / "stage_8_3_event_validation")
    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def determine_verdict(report: dict[str, Any]) -> str:
    flags = report["flags"]
    if flags["manual_labels_missing"]:
        return "needs_more_event_labels"
    if flags["validation_output_failed"]:
        return "blocked"
    if flags["no_bounce_or_hit_labels"]:
        return "needs_more_event_labels"
    if report["manual_hit_labels_count"] == 0 and report["downgraded_hit_count"] > 0:
        return "ready_with_warnings"
    if report["warnings"]:
        return "ready_with_warnings"
    return "ready_for_stage_14_3"


def recommended_next_step(report: dict[str, Any]) -> str:
    verdict = report["final_verdict"]
    if verdict == "ready_for_stage_14_3":
        return "Proceed to Stage 14.3: Side-View Replay with Validated Events."
    if verdict == "ready_with_warnings":
        return "Proceed to Stage 14.3 using validated events, but collect manual hit labels before confirming hits."
    if verdict == "needs_more_event_labels":
        return "Return to Stage 8.2 and collect more manual event labels."
    return "Fix Stage 8.3 blockers, then rerun event validation."


def build_validation_results(
    *,
    auto_events: list[dict[str, Any]],
    manual_labels: list[dict[str, Any]],
    windows: list[dict[str, Any]],
    validation_window: int,
    manual_hit_count: int,
) -> list[dict[str, Any]]:
    """Compare and reclassify automatic events against manual evidence."""
    frame_range = manual_frame_range(manual_labels)
    results: list[dict[str, Any]] = []
    for event in auto_events:
        evidence = nearest_manual_evidence(event, manual_labels, windows, validation_window=validation_window)
        status, status_reason = classify_validation_status(
            event,
            evidence,
            manual_hit_count=manual_hit_count,
            manual_frame_range=frame_range,
            validation_window=validation_window,
        )
        reclassified = reclassify_auto_event(
            event,
            validation_status=status,
            nearest_manual_label=str(evidence.get("event_label") or ""),
            manual_hit_count=manual_hit_count,
        )
        reason = f"{status_reason} {reclassified['reason']}".strip()
        results.append(
            {
                **event,
                "nearest_manual_label": evidence.get("event_label") or "",
                "nearest_manual_frame_or_window": evidence.get("frame_or_window") or "",
                "frame_delta": evidence.get("frame_delta"),
                "validation_status": status,
                "reclassified_event_type": reclassified["reclassified_event_type"],
                "render_role": reclassified["render_role"],
                "confidence_after": reclassified["confidence_after"],
                "reason": reason,
                "should_render_as_physical_event": reclassified["should_render_as_physical_event"],
                "should_render_as_annotation": reclassified["should_render_as_annotation"],
            }
        )
    return results


def save_timeline_preview(
    *,
    manual_labels: list[dict[str, Any]],
    windows: list[dict[str, Any]],
    validation_results: list[dict[str, Any]],
    output_path: Path,
) -> bool:
    """Save simple frame-axis validation preview."""
    frames = [int(row["frame_index"]) for row in manual_labels] + [int(row["auto_frame_index"]) for row in validation_results]
    if not frames:
        return False
    width, height = 1400, 520
    canvas = np.full((height, width, 3), 246, dtype=np.uint8)
    left, right, axis_y = 80, width - 80, 260
    min_frame, max_frame = min(frames), max(frames)
    span = max(max_frame - min_frame, 1)

    def x_for(frame: int) -> int:
        return left + int(round(((frame - min_frame) / span) * (right - left)))

    cv2.line(canvas, (left, axis_y), (right, axis_y), (30, 30, 30), 2)
    cv2.putText(canvas, "Stage 8.3 event validation preview", (35, 44), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (20, 20, 20), 2)
    cv2.putText(canvas, "manual windows/labels above axis; automatic reclassified events below axis", (35, 76), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (80, 80, 80), 1)

    for window in windows:
        x0 = x_for(int(window["start_frame"]))
        x1 = x_for(int(window["end_frame"]))
        cv2.rectangle(canvas, (x0, axis_y - 118), (x1, axis_y - 72), (110, 220, 120), thickness=-1)
        cv2.rectangle(canvas, (x0, axis_y - 118), (x1, axis_y - 72), (20, 130, 40), thickness=2)
        cv2.putText(canvas, window["window_id"], (x0, axis_y - 126), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (20, 100, 30), 1)

    for label in manual_labels:
        event_label = str(label.get("event_label") or "")
        if event_label == "skipped":
            continue
        x = x_for(int(label["frame_index"]))
        color = manual_color(event_label)
        cv2.circle(canvas, (x, axis_y - 36), 6, color, -1)
        if event_label in {"bounce", "hit", "no_event", "uncertain"}:
            cv2.putText(canvas, event_label[:9], (x - 22, axis_y - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1)

    for result in validation_results:
        x = x_for(int(result["auto_frame_index"]))
        color = role_color(str(result.get("render_role") or ""))
        cv2.drawMarker(canvas, (x, axis_y + 55), color, cv2.MARKER_TRIANGLE_UP, 17, 2)
        cv2.putText(canvas, str(result.get("render_role") or "")[:16], (x - 36, axis_y + 92), cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1)

    legend_y = height - 42
    cv2.putText(canvas, "green=bounce window  gray=no_event  yellow=uncertain  orange=hit/downstream role", (35, legend_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (50, 50, 50), 1)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return bool(cv2.imwrite(str(output_path), canvas))


def write_notes(path: Path, report: dict[str, Any]) -> Path:
    """Write plain-text event validation notes."""
    lines = [
        "# Stage 8.3 Event Validation Notes",
        "",
        "WHAT WAS VALIDATED",
        f"  Validated bounces: {report['validated_bounce_count']}",
        f"  Validated hits: {report['validated_hit_count']}",
        "",
        "WHAT WAS DOWNGRADED",
        f"  Downgraded hits: {report['downgraded_hit_count']}",
        f"  Rejected events: {report['rejected_events_count']}",
        "",
        "IMPORTANT LIMITATION",
        "  No hit events are confirmed because no manual hit labels were provided." if report["manual_hit_labels_count"] == 0 else "  Manual hit labels are available.",
        "",
        "WHY THIS MATTERS",
        "  Side-view replay should consume validated_event_timeline.csv instead of raw possible_hit hypotheses.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


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
    what_changed = (
        f"Stage 8.3 grouped {report['manual_bounce_labels_count']} manual bounce labels into "
        f"{report['bounce_windows_count']} bounce window(s). Automatic events were then validated, downgraded, "
        "or left uncertain using those manual labels."
    )
    limitation = "No hit events are confirmed because no manual hit labels were provided." if report["manual_hit_labels_count"] == 0 else "Manual hit labels are available for hit validation."
    return [
        ("VERDICT", field_block([("Final verdict", report["final_verdict"]), ("Friction", f"{report['friction']['score']} ({report['friction']['band']})")])),
        (
            "MANUAL LABEL SUMMARY",
            field_block(
                [
                    ("Manual labels", report["manual_labels_count"]),
                    ("Bounce labels", report["manual_bounce_labels_count"]),
                    ("Hit labels", report["manual_hit_labels_count"]),
                    ("No-event labels", report["manual_no_event_count"]),
                    ("Uncertain labels", report["manual_uncertain_count"]),
                    ("Bounce windows", report["bounce_windows_count"]),
                ]
            ),
        ),
        (
            "AUTOMATIC EVENT SUMMARY",
            field_block(
                [
                    ("Automatic events", report["automatic_events_count"]),
                    ("Validated bounces", report["validated_bounce_count"]),
                    ("Validated hits", report["validated_hit_count"]),
                    ("Downgraded hits", report["downgraded_hit_count"]),
                    ("Rejected events", report["rejected_events_count"]),
                    ("Unvalidated events", report["unvalidated_events_count"]),
                    ("Outside manual coverage", report["outside_coverage_count"]),
                ]
            ),
        ),
        ("WHAT CHANGED", what_changed),
        ("IMPORTANT LIMITATION", limitation),
        (
            "OUTPUTS",
            field_block(
                [
                    ("Manual event windows", report["output_paths"]["manual_event_windows"]),
                    ("Event validation results", report["output_paths"]["event_validation_results"]),
                    ("Validated event timeline", report["output_paths"]["validated_event_timeline"]),
                    ("Validation preview", report["output_paths"]["event_validation_timeline_preview"]),
                ]
            ),
        ),
        ("PRODUCT OWNER INTERPRETATION", "This stage gives side-view replay a better event truth layer. It prevents raw possible_hit hypotheses from being rendered as contact events when manual labels indicate bounce or no_event evidence."),
        ("WARNINGS", bullet_list(report["warnings"], "No warnings.")),
        ("ERRORS", bullet_list(report["errors"], "No errors.")),
        ("NEXT STEP", report["recommended_next_step"]),
    ]


def update_lab_notebook_safely() -> tuple[dict[str, Path], str | None]:
    try:
        from tennis_vision.lab_notebook import lab_notebook_paths, update_lab_notebook

        update_lab_notebook(PROJECT_ROOT)
        return lab_notebook_paths(PROJECT_ROOT, "stage_8_3"), None
    except Exception as exc:
        try:
            from tennis_vision.lab_notebook import lab_notebook_paths

            return lab_notebook_paths(PROJECT_ROOT, "stage_8_3"), f"Lab notebook update failed: {exc}"
        except Exception:
            return {
                "stage_page": PROJECT_ROOT / "docs" / "lab-notebook" / "stage_8_3_event_validation.md",
                "experiment_index": PROJECT_ROOT / "docs" / "lab-notebook" / "experiment_index.md",
            }, f"Lab notebook update failed: {exc}"


def print_summary(report: dict[str, Any], lab_paths: dict[str, Path]) -> None:
    rows = [
        ("Verdict", report["final_verdict"]),
        ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"),
        ("Manual labels", report["manual_labels_count"]),
        ("Bounce labels", report["manual_bounce_labels_count"]),
        ("Hit labels", report["manual_hit_labels_count"]),
        ("No-event labels", report["manual_no_event_count"]),
        ("Uncertain labels", report["manual_uncertain_count"]),
        ("Bounce windows", report["bounce_windows_count"]),
        ("Auto events", report["automatic_events_count"]),
        ("Validated bounces", report["validated_bounce_count"]),
        ("Validated hits", report["validated_hit_count"]),
        ("Downgraded hits", report["downgraded_hit_count"]),
        ("Rejected events", report["rejected_events_count"]),
        ("Unvalidated events", report["unvalidated_events_count"]),
        ("Lab notebook", lab_paths["stage_page"]),
        ("Recommended next step", report["recommended_next_step"]),
    ]
    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(title="Stage 8.3 Event Validation")
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")
        for field, value in rows:
            table.add_row(str(field), str(value))
        Console().print(table)
    except ImportError:
        print("Stage 8.3 Event Validation")
        for field, value in rows:
            print(f"{field}: {value}")


def manual_color(label: str) -> tuple[int, int, int]:
    return {"bounce": (70, 180, 80), "hit": (40, 110, 230), "no_event": (145, 145, 145), "uncertain": (40, 200, 220)}.get(label, (80, 80, 80))


def role_color(role: str) -> tuple[int, int, int]:
    return {
        "bounce_validated": (50, 180, 70),
        "hit_validated": (40, 110, 230),
        "hit_unvalidated": (40, 170, 230),
        "rejected_event": (120, 120, 120),
        "uncertain_event": (60, 190, 210),
        "interaction_cue": (220, 90, 200),
        "trajectory_annotation": (180, 160, 90),
    }.get(role, (100, 100, 100))


def main() -> int:
    args = parse_args()
    ensure_output_folders(PROJECT_ROOT)
    timestamp = utc_timestamp()
    output_dir = resolve_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manual_path = resolve_path(args.manual_labels)
    warnings: list[str] = []
    errors: list[str] = []

    manual_labels, manual_errors = read_manual_event_labels(manual_path)
    errors.extend(manual_errors)
    user_windows, window_warnings = read_manual_event_windows(resolve_path(args.manual_windows))
    warnings.extend(window_warnings)
    windows = user_windows if user_windows else group_manual_event_windows(manual_labels, bounce_window_gap=args.bounce_window_gap)
    manual_summary = summarize_manual_event_labels(manual_labels, windows)
    if user_windows:
        warnings.append("Stage 8.3 used user-created Stage 8.2 manual event windows directly.")

    auto_events, auto_warnings = read_automatic_events(
        [
            (resolve_path(args.timeline), "stage_8_timeline"),
            (resolve_path(args.stage6_events), "stage_6_trajectory"),
            (resolve_path(args.stage7_interactions), "stage_7_interaction"),
        ]
    )
    warnings.extend(auto_warnings)
    validation_results = build_validation_results(
        auto_events=auto_events,
        manual_labels=manual_labels,
        windows=windows,
        validation_window=args.validation_window,
        manual_hit_count=manual_summary["manual_hit_count"],
    )
    validated_timeline = build_validated_event_timeline(validation_results)
    reclassification_summary = summarize_reclassification(validation_results, manual_summary)
    if manual_summary["manual_hit_count"] == 0 and any(row.get("auto_event_type") == "auto_possible_hit" for row in validation_results):
        warnings.append("No hit events are confirmed because no manual hit labels were provided.")
    if manual_summary["manual_bounce_count"] > 1 and len(windows) < manual_summary["manual_bounce_count"]:
        warnings.append("Adjacent manual bounce labels were grouped into bounce windows.")

    windows_csv = output_dir / "manual_event_windows.csv"
    results_csv = output_dir / "event_validation_results.csv"
    timeline_csv = output_dir / "validated_event_timeline.csv"
    summary_json = output_dir / "event_validation_summary.json"
    preview_path = output_dir / "event_validation_timeline_preview.jpg"
    notes_path = output_dir / "event_validation_notes.md"
    write_manual_event_windows_csv(windows_csv, windows)
    write_event_validation_results_csv(results_csv, validation_results)
    write_validated_event_timeline_csv(timeline_csv, validated_timeline)
    write_event_validation_summary_json(summary_json, reclassification_summary)
    preview_generated = save_timeline_preview(manual_labels=manual_labels, windows=windows, validation_results=validation_results, output_path=preview_path)

    output_paths = {
        "manual_event_windows": str(windows_csv),
        "event_validation_results": str(results_csv),
        "validated_event_timeline": str(timeline_csv),
        "event_validation_summary": str(summary_json),
        "event_validation_timeline_preview": str(preview_path) if preview_path.exists() else "",
        "event_validation_notes": str(notes_path),
    }
    flags = {
        "manual_labels_missing": len(manual_labels) == 0,
        "no_bounce_or_hit_labels": manual_summary["manual_bounce_count"] + manual_summary["manual_hit_count"] == 0,
        "no_hit_labels": manual_summary["manual_hit_count"] == 0,
        "many_auto_events_unvalidated": bool(validation_results and reclassification_summary["unvalidated_event_count"] / max(len(validation_results), 1) > 0.5),
        "validation_output_failed": not timeline_csv.exists(),
        "preview_generation_failed": not preview_generated,
    }
    if flags["preview_generation_failed"]:
        warnings.append("Event validation timeline preview could not be generated.")
    friction = calculate_stage_8_3_friction_score(**flags, errors_count=len(errors), warnings_count=len(warnings))

    report: dict[str, Any] = {
        "timestamp": timestamp,
        "stage": "stage_8_3_event_validation",
        "manual_labels_count": manual_summary["manual_labels_count"],
        "manual_bounce_labels_count": manual_summary["manual_bounce_count"],
        "manual_hit_labels_count": manual_summary["manual_hit_count"],
        "manual_no_event_count": manual_summary["manual_no_event_count"],
        "manual_uncertain_count": manual_summary["manual_uncertain_count"],
        "bounce_windows_count": len(windows),
        "automatic_events_count": len(auto_events),
        "validated_bounce_count": reclassification_summary["validated_bounce_count"],
        "validated_hit_count": reclassification_summary["validated_hit_count"],
        "downgraded_hit_count": reclassification_summary["downgraded_hit_count"],
        "rejected_events_count": reclassification_summary["rejected_event_count"],
        "unvalidated_events_count": reclassification_summary["unvalidated_event_count"],
        "outside_coverage_count": reclassification_summary["outside_coverage_count"],
        "output_paths": output_paths,
        "warnings": warnings,
        "errors": errors,
        "flags": flags,
        "friction": friction,
        "final_verdict": "blocked",
        "recommended_next_step": "",
    }
    write_notes(notes_path, report)
    report["final_verdict"] = determine_verdict(report)
    report["recommended_next_step"] = recommended_next_step(report)
    log_path = write_timestamped_log(
        PROJECT_ROOT,
        "stage_8_3_event_validation",
        [
            f"timestamp={timestamp}",
            f"verdict={report['final_verdict']}",
            f"friction={friction['score']} ({friction['band']})",
            f"manual_labels={report['manual_labels_count']}",
            f"bounce_windows={report['bounce_windows_count']}",
            f"downgraded_hits={report['downgraded_hit_count']}",
        ],
    )
    report["log_path"] = str(log_path)
    report["json_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_8_3_event_validation_report.json")
    report["markdown_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_8_3_event_validation_report.md")
    write_json_report(Path(report["json_report_path"]), report)
    write_markdown_report(Path(report["markdown_report_path"]), "Stage 8.3 Event Validation and Reclassification Report", build_markdown_sections(report))
    lab_paths, notebook_warning = update_lab_notebook_safely()
    if notebook_warning:
        report["warnings"].append(notebook_warning)
        write_json_report(Path(report["json_report_path"]), report)
        write_markdown_report(Path(report["markdown_report_path"]), "Stage 8.3 Event Validation and Reclassification Report", build_markdown_sections(report))
        print(f"Warning: {notebook_warning}")
    print_summary(report, lab_paths)
    return 1 if report["final_verdict"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
