"""Run Stage 8.5 precise bounce contact localization."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from statistics import mean
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from tennis_vision.bounce_contact_localization import (  # noqa: E402
    CANDIDATE_FIELDS,
    CONTACT_POINT_FIELDS,
    localize_bounce_contact,
    read_ball_positions,
    read_bounce_windows,
    save_contact_overlay,
    save_timeline_preview,
    write_csv,
    write_json,
)
from tennis_vision.friction import calculate_stage_8_5_friction_score  # noqa: E402
from tennis_vision.report import ensure_output_folders, utc_timestamp, write_json_report, write_markdown_report, write_timestamped_log  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 8.5 precise bounce contact localization.")
    parser.add_argument("--manual-windows", type=Path, default=PROJECT_ROOT / "outputs" / "timeline" / "stage_8_2_event_labels" / "manual_event_windows.csv")
    parser.add_argument("--fallback-windows", type=Path, default=PROJECT_ROOT / "outputs" / "timeline" / "stage_8_3_event_validation" / "manual_event_windows.csv")
    parser.add_argument("--manual-labels", type=Path, default=PROJECT_ROOT / "outputs" / "timeline" / "stage_8_2_event_labels" / "manual_event_labels.csv")
    parser.add_argument("--validated-timeline", type=Path, default=PROJECT_ROOT / "outputs" / "timeline" / "stage_8_3_event_validation" / "validated_event_timeline.csv")
    parser.add_argument("--ball-labels", type=Path, default=PROJECT_ROOT / "outputs" / "timeline" / "stage_8_1_timeline_validation" / "expanded_ball_labels.csv")
    parser.add_argument("--projected-labels", type=Path, default=PROJECT_ROOT / "outputs" / "tactical" / "stage_9_1_projection_coverage" / "projected_expanded_labels.csv")
    parser.add_argument("--calibration-report", type=Path, default=PROJECT_ROOT / "outputs" / "reports" / "stage_3_court_calibration_probe_report.json")
    parser.add_argument("--video", type=Path, default=PROJECT_ROOT / "samples" / "video_01.mov")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs" / "timeline" / "stage_8_5_bounce_contact")
    parser.add_argument("--padding", type=int, default=3)
    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def field_block(rows: list[tuple[str, Any]]) -> str:
    lines: list[str] = []
    for key, value in rows:
        lines.append(f"{key}:")
        lines.append(f"  {value if value not in (None, '') else 'Not available'}")
        lines.append("")
    return "\n".join(lines).rstrip()


def bullet_list(items: list[str], empty: str = "No items.") -> str:
    return empty if not items else "\n".join(f"- {item}" for item in items)


def determine_verdict(report: dict[str, Any]) -> str:
    if report["errors"] and report["bounce_windows_processed"] == 0:
        return "blocked"
    if report["bounce_windows_processed"] == 0:
        return "needs_better_bounce_labels"
    if report["localized_contacts"] + report["estimated_contacts"] == 0:
        if report["ambiguous_contacts"] > 0:
            return "needs_better_ball_tracking"
        return "needs_better_bounce_labels"
    if report["warnings"] or report["line_call_ready_count"] < report["bounce_windows_processed"]:
        return "ready_with_warnings"
    return "ready_for_stage_14_4"


def recommended_next_step(report: dict[str, Any]) -> str:
    verdict = report["final_verdict"]
    if verdict == "ready_for_stage_14_4":
        return "Proceed to Stage 14.4: Side-View Replay with localized bounce contact points."
    if verdict == "ready_with_warnings":
        return "Use localized/estimated contact points for Stage 14.4, but reserve future line calling for line_call_ready contacts only."
    if verdict == "needs_better_ball_tracking":
        return "Improve ball labels/tracking around bounce windows before line-call-oriented localization."
    if verdict == "needs_better_bounce_labels":
        return "Add manual bounce event windows with Stage 8.2 direct event-window CLI, then rerun Stage 8.5."
    return "Fix Stage 8.5 input blockers, then rerun localization."


def build_markdown_sections(report: dict[str, Any]) -> list[tuple[str, str]]:
    return [
        ("VERDICT", field_block([("Final verdict", report["final_verdict"]), ("Friction", f"{report['friction']['score']} ({report['friction']['band']})")])),
        ("WHY THIS STAGE EXISTS", "Bounce windows are not enough for future in/out detection. Stage 8.5 estimates a contact frame and contact point, then records uncertainty and line-call readiness."),
        (
            "BOUNCE CONTACT SUMMARY",
            field_block(
                [
                    ("Bounce windows", report["bounce_windows_processed"]),
                    ("Localized contacts", report["localized_contacts"]),
                    ("Estimated contacts", report["estimated_contacts"]),
                    ("Ambiguous contacts", report["ambiguous_contacts"]),
                    ("Line-call-ready contacts", report["line_call_ready_count"]),
                    ("Average uncertainty frames", report["average_uncertainty_frames"]),
                    ("Average uncertainty px", report["average_uncertainty_px"]),
                ]
            ),
        ),
        ("IMPORTANT LIMITATION", "This is not official line calling. It estimates contact points and uncertainty. Future line calling should use only line_call_ready contact points."),
        (
            "OUTPUTS",
            field_block(
                [
                    ("Contact points", report["output_paths"]["contact_points"]),
                    ("Candidate frames", report["output_paths"]["candidate_frames"]),
                    ("Summary", report["output_paths"]["summary_json"]),
                    ("Debug overlays", report["output_paths"]["debug_dir"]),
                    ("Timeline preview", report["output_paths"]["timeline_preview"]),
                ]
            ),
        ),
        ("WARNINGS", bullet_list(report["warnings"], "No warnings.")),
        ("ERRORS", bullet_list(report["errors"], "No errors.")),
        ("NEXT STEP", report["recommended_next_step"]),
    ]


def update_lab_notebook(report: dict[str, Any]) -> dict[str, Path]:
    notebook_dir = PROJECT_ROOT / "docs" / "lab-notebook"
    notebook_dir.mkdir(parents=True, exist_ok=True)
    stage_path = notebook_dir / "stage_8_5_bounce_contact_localization.md"
    index_path = notebook_dir / "experiment_index.md"
    stage_body = "\n".join(
        [
            "# Stage 8.5 Precise Bounce Contact Localization",
            "",
            "VERDICT",
            f"  Final verdict: {report['final_verdict']}",
            f"  Friction: {report['friction']['score']} ({report['friction']['band']})",
            "",
            "RUN SUMMARY",
            f"  Bounce windows processed: {report['bounce_windows_processed']}",
            f"  Localized contacts: {report['localized_contacts']}",
            f"  Estimated contacts: {report['estimated_contacts']}",
            f"  Ambiguous contacts: {report['ambiguous_contacts']}",
            f"  Line-call-ready contacts: {report['line_call_ready_count']}",
            f"  Average uncertainty frames: {report['average_uncertainty_frames']}",
            f"  Average uncertainty px: {report['average_uncertainty_px']}",
            "",
            "OUTPUTS",
            f"  Contact points: {report['output_paths']['contact_points']}",
            f"  Candidate frames: {report['output_paths']['candidate_frames']}",
            f"  Timeline preview: {report['output_paths']['timeline_preview']}",
            "",
            "INTERPRETATION",
            "  Bounce windows are temporal evidence. Stage 8.5 converts them into",
            "  contact-point estimates with uncertainty, without claiming official line calling.",
            "",
            "NEXT STEP",
            f"  {report['recommended_next_step']}",
            "",
        ]
    )
    stage_path.write_text(stage_body, encoding="utf-8")
    index_text = index_path.read_text(encoding="utf-8") if index_path.exists() else "# Experiment Index\n\n"
    marker = "STAGE: Stage 8.5"
    block = "\n".join(
        [
            "---",
            "",
            "STAGE: Stage 8.5",
            "NAME: Bounce Contact Localization",
            f"VERDICT: {report['final_verdict']}",
            f"FRICTION: {report['friction']['score']} {report['friction']['band']}",
            "MAIN OUTPUT: outputs/timeline/stage_8_5_bounce_contact/bounce_contact_points.csv",
            f"NEXT STEP: {report['recommended_next_step']}",
            "",
        ]
    )
    if marker not in index_text:
        index_text = index_text.rstrip() + "\n\n" + block
    else:
        before = index_text.split(marker)[0].rstrip()
        after_parts = index_text.split(marker, 1)[1].split("---", 1)
        after = ("---" + after_parts[1]) if len(after_parts) > 1 else ""
        index_text = before + "\n\n" + block + after
    index_path.write_text(index_text, encoding="utf-8")
    return {"stage_page": stage_path, "experiment_index": index_path}


def print_summary(report: dict[str, Any], lab_paths: dict[str, Path]) -> None:
    rows = [
        ("Verdict", report["final_verdict"]),
        ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"),
        ("Bounce windows", report["bounce_windows_processed"]),
        ("Localized contacts", report["localized_contacts"]),
        ("Estimated contacts", report["estimated_contacts"]),
        ("Ambiguous contacts", report["ambiguous_contacts"]),
        ("Line-call ready", report["line_call_ready_count"]),
        ("Average uncertainty frames", report["average_uncertainty_frames"]),
        ("Average uncertainty px", report["average_uncertainty_px"]),
        ("Contact points path", report["output_paths"]["contact_points"]),
        ("Lab notebook", lab_paths["stage_page"]),
        ("Recommended next step", report["recommended_next_step"]),
    ]
    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(title="Stage 8.5 Bounce Contact Localization")
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")
        for field, value in rows:
            table.add_row(str(field), str(value))
        Console().print(table)
    except ImportError:
        print("Stage 8.5 Bounce Contact Localization")
        for field, value in rows:
            print(f"{field}: {value}")


def main() -> int:
    args = parse_args()
    ensure_output_folders(PROJECT_ROOT)
    timestamp = utc_timestamp()
    output_dir = resolve_path(args.output_dir)
    debug_dir = output_dir / "bounce_contact_debug"
    output_dir.mkdir(parents=True, exist_ok=True)
    debug_dir.mkdir(parents=True, exist_ok=True)
    warnings: list[str] = []
    errors: list[str] = []

    bounce_windows, window_source, window_warnings = read_bounce_windows(resolve_path(args.manual_windows), resolve_path(args.fallback_windows))
    warnings.extend(window_warnings)
    if not bounce_windows:
        errors.append("No manually supported bounce windows found in Stage 8.2 or Stage 8.3 inputs.")

    positions, position_warnings = read_ball_positions(resolve_path(args.ball_labels), resolve_path(args.projected_labels))
    warnings.extend(position_warnings)
    if not positions:
        errors.append("No ball positions were available for contact localization.")

    contacts: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    overlay_paths: list[str] = []
    video_path = resolve_path(args.video)
    for window in bounce_windows:
        contact, candidates = localize_bounce_contact(window, positions, padding=args.padding)
        contacts.append(contact)
        candidate_rows.extend(candidates)
        overlay_path = debug_dir / f"{contact['bounce_id']}_contact_overlay.jpg"
        if video_path.exists() and save_contact_overlay(video_path, contact, overlay_path):
            overlay_paths.append(str(overlay_path))
        else:
            warnings.append(f"Could not write debug overlay for {contact['bounce_id']}.")

    contact_points_csv = output_dir / "bounce_contact_points.csv"
    candidates_csv = output_dir / "bounce_contact_candidates.csv"
    summary_json = output_dir / "bounce_contact_summary.json"
    timeline_preview = output_dir / "bounce_contact_timeline_preview.jpg"
    write_csv(contact_points_csv, contacts, CONTACT_POINT_FIELDS)
    write_csv(candidates_csv, candidate_rows, CANDIDATE_FIELDS)
    preview_ok = save_timeline_preview(contacts, timeline_preview)
    if contacts and not preview_ok:
        warnings.append("Bounce contact timeline preview could not be generated.")

    localized = sum(1 for row in contacts if row.get("contact_status") == "localized")
    estimated = sum(1 for row in contacts if row.get("contact_status") == "estimated")
    ambiguous = sum(1 for row in contacts if row.get("contact_status") in {"ambiguous", "insufficient_data"})
    line_ready = sum(1 for row in contacts if row.get("line_call_ready") == "yes")
    uncertainty_frames = [float(row["uncertainty_frames"]) for row in contacts if row.get("uncertainty_frames") not in (None, "")]
    uncertainty_px = [float(row["uncertainty_px"]) for row in contacts if row.get("uncertainty_px") not in (None, "")]

    flags = {
        "no_bounce_windows": len(bounce_windows) == 0,
        "no_ball_labels_in_window": bool(bounce_windows and all(row.get("contact_x") is None and row.get("contact_y") is None for row in contacts)),
        "projection_missing": bool(contacts and any(row.get("contact_projected_x") is None or row.get("contact_projected_y") is None for row in contacts)),
        "contact_ambiguous": ambiguous > 0,
        "high_uncertainty": bool(contacts and any(float(row["uncertainty_px"]) > 60 or float(row["uncertainty_frames"]) > 3 for row in contacts)),
        "no_line_call_ready_contacts": bool(contacts and line_ready == 0),
    }
    friction = calculate_stage_8_5_friction_score(**flags, errors_count=len(errors), warnings_count=len(warnings))

    summary = {
        "timestamp": timestamp,
        "stage": "stage_8_5_bounce_contact_localization",
        "bounce_windows_processed": len(bounce_windows),
        "window_source_used": window_source,
        "contact_points_localized": localized,
        "contact_points_estimated": estimated,
        "ambiguous_contacts": ambiguous,
        "line_call_ready_count": line_ready,
        "average_uncertainty_frames": round(mean(uncertainty_frames), 2) if uncertainty_frames else 0,
        "average_uncertainty_px": round(mean(uncertainty_px), 2) if uncertainty_px else 0,
        "warnings": warnings,
        "errors": errors,
    }
    write_json(summary_json, {"summary": summary, "contacts": contacts})

    report: dict[str, Any] = {
        "timestamp": timestamp,
        "stage": "stage_8_5_bounce_contact_localization",
        "bounce_windows_processed": len(bounce_windows),
        "contact_points_localized": localized,
        "localized_contacts": localized,
        "contact_points_estimated": estimated,
        "estimated_contacts": estimated,
        "ambiguous_contacts": ambiguous,
        "line_call_ready_count": line_ready,
        "average_uncertainty_frames": summary["average_uncertainty_frames"],
        "average_uncertainty_px": summary["average_uncertainty_px"],
        "window_source_used": window_source,
        "padding": args.padding,
        "output_paths": {
            "contact_points": str(contact_points_csv),
            "candidate_frames": str(candidates_csv),
            "summary_json": str(summary_json),
            "debug_dir": str(debug_dir),
            "debug_overlays": overlay_paths,
            "timeline_preview": str(timeline_preview) if timeline_preview.exists() else "",
        },
        "warnings": warnings,
        "errors": errors,
        "flags": flags,
        "friction": friction,
        "final_verdict": "blocked",
        "recommended_next_step": "",
    }
    report["final_verdict"] = determine_verdict(report)
    report["recommended_next_step"] = recommended_next_step(report)
    log_path = write_timestamped_log(
        PROJECT_ROOT,
        "stage_8_5_bounce_contact_localization",
        [
            f"timestamp={timestamp}",
            f"verdict={report['final_verdict']}",
            f"friction={friction['score']} ({friction['band']})",
            f"bounce_windows={report['bounce_windows_processed']}",
            f"estimated_contacts={estimated}",
        ],
    )
    report["log_path"] = str(log_path)
    report["json_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_8_5_bounce_contact_localization_report.json")
    report["markdown_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_8_5_bounce_contact_localization_report.md")
    write_json_report(Path(report["json_report_path"]), report)
    write_markdown_report(Path(report["markdown_report_path"]), "Stage 8.5 Precise Bounce Contact Localization Report", build_markdown_sections(report))
    lab_paths = update_lab_notebook(report)
    print_summary(report, lab_paths)
    return 1 if report["final_verdict"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
