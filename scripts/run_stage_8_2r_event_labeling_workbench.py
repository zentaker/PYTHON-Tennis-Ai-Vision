"""Run Stage 8.2R Event Labeling Workbench."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from tennis_vision.event_contact_labels import load_contact_candidates, load_event_windows  # noqa: E402
from tennis_vision.event_labeling_workbench import (  # noqa: E402
    build_frame_cache,
    cache_dir_for,
    cache_is_valid,
    clear_cache,
    export_legacy_compatibility,
    run_label_integrity_audit,
    run_review_or_label_viewer,
)
from tennis_vision.frame_decode_audit import run_frame_decode_audit, write_decode_audit_outputs  # noqa: E402
from tennis_vision.friction import friction_band  # noqa: E402
from tennis_vision.friction_semantics import build_friction_breakdown  # noqa: E402
from tennis_vision.report import ensure_output_folders, utc_timestamp, write_json_report, write_markdown_report, write_timestamped_log  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 8.2R event labeling workbench.")
    parser.add_argument("--audit-decode", action="store_true", help="Audit sequential/random frame decoding and visual groups.")
    parser.add_argument("--build-cache", action="store_true", help="Build clean resized frame cache for the selected range.")
    parser.add_argument("--use-cache", action="store_true", default=True, help="Use frame cache if available.")
    parser.add_argument("--clear-cache", action="store_true", help="Clear Stage 8.2R frame cache before running.")
    parser.add_argument("--label", action="store_true", help="Open local OpenCV labeling workbench.")
    parser.add_argument("--review", action="store_true", help="Open local OpenCV review-only workbench.")
    parser.add_argument("--export-compat", action="store_true", help="Export Stage 8.2R labels to legacy Stage 8.2 paths.")
    parser.add_argument("--audit-labels", action="store_true", help="Audit Stage 8.2R event windows and contact candidates.")
    parser.add_argument("--start-frame", type=int, default=198)
    parser.add_argument("--end-frame", type=int, default=288)
    parser.add_argument("--resize-width", type=int, default=1280)
    parser.add_argument("--duplicate-threshold", type=float, default=0.0006)
    parser.add_argument("--signature-width", type=int, default=128)
    parser.add_argument("--random-seek-compare", action="store_true", default=False, help="Also compare sequential decode against random seek. Slower; use only for decode diagnostics.")
    parser.add_argument("--video", type=Path, default=PROJECT_ROOT / "samples" / "video_01.mov")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs" / "timeline" / "stage_8_2r_event_labeling_workbench")
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


def score_friction(*, errors: list[str], warnings: list[str], timings: dict[str, float], audit_summary: dict[str, Any], integrity: dict[str, Any], cache_status: str) -> tuple[dict[str, Any], dict[str, Any]]:
    duplicate_pairs = int(audit_summary.get("near_duplicate_pairs") or 0)
    integrity_issues = int(integrity.get("integrity_issues_count") or 0)
    bounce_windows = int(integrity.get("event_windows_count") or 0)
    contact_candidates = int(integrity.get("contact_candidates_count") or 0)
    line_candidates = int(integrity.get("line_call_candidates") or 0)
    performance_score = 0
    if timings.get("save_seconds", 0) > 10 or timings.get("viewer_start_seconds", 0) > 10:
        performance_score = 45
    elif timings.get("cache_build_seconds", 0) > 10 or timings.get("audit_seconds", 0) > 10:
        performance_score = 30
    duplicate_score = 35 if duplicate_pairs else 0
    human_loop_score = 35 if duplicate_pairs else 15
    integrity_score = min(80, integrity_issues * 15)
    line_score = 30 if bounce_windows and contact_candidates == 0 else (20 if contact_candidates and line_candidates == 0 else 0)
    execution_score = min(len(errors) * 35 + len(warnings) * 2, 100)
    total = min(100, max(execution_score, duplicate_score, human_loop_score, integrity_score, line_score, performance_score))
    friction = {"score": total, "band": friction_band(total)}
    breakdown = {
        "execution": {"score": execution_score, "band": friction_band(execution_score), "reason": "errors or warnings occurred" if errors or warnings else "stage commands ran"},
        "human_loop": {"score": human_loop_score, "band": friction_band(human_loop_score), "reason": "visual duplicates require group/window labeling" if duplicate_pairs else "group workflow available"},
        "label_integrity": {"score": integrity_score, "band": friction_band(integrity_score), "reason": "integrity issues found" if integrity_issues else "no integrity issues found"},
        "duplicate_frame": {"score": duplicate_score, "band": friction_band(duplicate_score), "reason": f"{duplicate_pairs} near-duplicate pairs found" if duplicate_pairs else "no near-duplicate pairs found"},
        "line_call_readiness": {"score": line_score, "band": friction_band(line_score), "reason": "contact candidates are missing or not line-call-ready" if line_score else "line-call candidate status acceptable for current labels"},
        "performance": {"score": performance_score, "band": friction_band(performance_score), "reason": "performance timing exceeded threshold" if performance_score else "performance timing acceptable"},
        "product_validation": {"status": "pending_review", "reason": "Product Owner must validate labels/contact candidates visually."},
    }
    return friction, breakdown


def determine_verdict(report: dict[str, Any]) -> str:
    if report["errors"]:
        return "blocked"
    if report["integrity_issues_count"] > 0:
        return "needs_label_cleanup"
    if report["bounce_windows_count"] > 0 and report["contact_candidates_count"] == 0:
        return "needs_contact_candidates"
    if report["event_windows_count"] > 0:
        return "ready_for_stage_8_3" if report["compatibility_export_status"] == "exported" else "ready_for_contact_review"
    return "ready_for_contact_review"


def recommended_next_step(report: dict[str, Any]) -> str:
    verdict = report["final_verdict"]
    if verdict == "ready_for_stage_8_3":
        return "Rerun Stage 8.3 using Stage 8.2R compatibility exports."
    if verdict == "needs_contact_candidates":
        return "Add precise contact candidates for bounce windows before line-call-oriented work."
    if verdict == "needs_label_cleanup":
        return "Resolve label integrity issues, then export compatibility and rerun Stage 8.3."
    if verdict == "blocked":
        return "Fix workbench input or execution blockers, then rerun Stage 8.2R."
    return "Use the workbench to add event windows/contact candidates, then export compatibility."


def build_markdown_sections(report: dict[str, Any]) -> list[tuple[str, str]]:
    return [
        ("VERDICT", field_block([("Final verdict", report["final_verdict"]), ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"), ("Mode", report["mode"])])),
        (
            "WORKBENCH SUMMARY",
            field_block(
                [
                    ("Frames audited", report["audited_frames"]),
                    ("Visual groups", report["visual_groups"]),
                    ("Near duplicate pairs", report["near_duplicate_pairs"]),
                    ("Event windows", report["event_windows_count"]),
                    ("Contact candidates", report["contact_candidates_count"]),
                    ("Bounce windows", report["bounce_windows_count"]),
                    ("Hit windows", report["hit_windows_count"]),
                    ("Line-call candidates", report["line_call_candidates_count"]),
                    ("Ambiguous contacts", report["ambiguous_contacts_count"]),
                    ("Integrity issues", report["integrity_issues_count"]),
                    ("Cache status", report["cache_status"]),
                ]
            ),
        ),
        (
            "PERFORMANCE",
            field_block([(key, value) for key, value in report["performance_timings"].items()]),
        ),
        (
            "FRICTION BREAKDOWN",
            field_block(
                [
                    ("Execution", f"{report['friction_breakdown']['execution']['score']} ({report['friction_breakdown']['execution']['band']}) - {report['friction_breakdown']['execution']['reason']}"),
                    ("Human-loop", f"{report['friction_breakdown']['human_loop']['score']} ({report['friction_breakdown']['human_loop']['band']}) - {report['friction_breakdown']['human_loop']['reason']}"),
                    ("Label integrity", f"{report['friction_breakdown']['label_integrity']['score']} ({report['friction_breakdown']['label_integrity']['band']}) - {report['friction_breakdown']['label_integrity']['reason']}"),
                    ("Duplicate-frame", f"{report['friction_breakdown']['duplicate_frame']['score']} ({report['friction_breakdown']['duplicate_frame']['band']}) - {report['friction_breakdown']['duplicate_frame']['reason']}"),
                    ("Line-call readiness", f"{report['friction_breakdown']['line_call_readiness']['score']} ({report['friction_breakdown']['line_call_readiness']['band']}) - {report['friction_breakdown']['line_call_readiness']['reason']}"),
                    ("Performance", f"{report['friction_breakdown']['performance']['score']} ({report['friction_breakdown']['performance']['band']}) - {report['friction_breakdown']['performance']['reason']}"),
                    ("Product validation", f"{report['friction_breakdown']['product_validation']['status']} - {report['friction_breakdown']['product_validation']['reason']}"),
                ]
            ),
        ),
        ("WARNINGS", bullet_list(report["warnings"], "No warnings.")),
        ("ERRORS", bullet_list(report["errors"], "No errors.")),
        ("NEXT STEP", report["recommended_next_step"]),
    ]


def write_lab_notebook(report: dict[str, Any]) -> dict[str, Path]:
    notebook_dir = PROJECT_ROOT / "docs" / "lab-notebook"
    notebook_dir.mkdir(parents=True, exist_ok=True)
    stage_path = notebook_dir / "stage_8_2r_event_labeling_workbench.md"
    index_path = notebook_dir / "experiment_index.md"
    stage_path.write_text(
        "\n".join(
            [
                "# Stage 8.2R Event Labeling Workbench",
                "",
                f"Verdict: {report['final_verdict']}",
                f"Friction: {report['friction']['score']} ({report['friction']['band']})",
                f"Mode: {report['mode']}",
                "",
                "SUMMARY",
                f"  Frames audited: {report['audited_frames']}",
                f"  Visual groups: {report['visual_groups']}",
                f"  Near duplicate pairs: {report['near_duplicate_pairs']}",
                f"  Event windows: {report['event_windows_count']}",
                f"  Contact candidates: {report['contact_candidates_count']}",
                f"  Integrity issues: {report['integrity_issues_count']}",
                "",
                "NEXT STEP",
                f"  {report['recommended_next_step']}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    index_text = index_path.read_text(encoding="utf-8") if index_path.exists() else "# Experiment Index\n\n"
    if "STAGE: Stage 8.2R" not in index_text:
        index_text = index_text.rstrip() + "\n\n---\n\nSTAGE: Stage 8.2R\nNAME: Event Labeling Workbench\nVERDICT: {verdict}\nFRICTION: {score} {band}\nMAIN OUTPUT: outputs/timeline/stage_8_2r_event_labeling_workbench/frame_decode_audit.md\nNEXT STEP: {next_step}\n".format(
            verdict=report["final_verdict"],
            score=report["friction"]["score"],
            band=report["friction"]["band"],
            next_step=report["recommended_next_step"],
        )
        index_path.write_text(index_text, encoding="utf-8")
    return {"stage_page": stage_path, "experiment_index": index_path}


def print_summary(report: dict[str, Any]) -> None:
    rows = [
        ("Verdict", report["final_verdict"]),
        ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"),
        ("Mode", report["mode"]),
        ("Frames audited", report["audited_frames"]),
        ("Visual groups", report["visual_groups"]),
        ("Near duplicates", report["near_duplicate_pairs"]),
        ("Event windows", report["event_windows_count"]),
        ("Contact candidates", report["contact_candidates_count"]),
        ("Bounce windows", report["bounce_windows_count"]),
        ("Hit windows", report["hit_windows_count"]),
        ("Line-call candidates", report["line_call_candidates_count"]),
        ("Ambiguous contacts", report["ambiguous_contacts_count"]),
        ("Integrity issues", report["integrity_issues_count"]),
        ("Cache status", report["cache_status"]),
        ("Save seconds", report["performance_timings"].get("save_seconds", 0)),
        ("Recommended next step", report["recommended_next_step"]),
    ]
    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(title="Stage 8.2R Event Labeling Workbench")
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")
        for field, value in rows:
            table.add_row(str(field), str(value))
        Console().print(table)
    except ImportError:
        print("Stage 8.2R Event Labeling Workbench")
        for field, value in rows:
            print(f"{field}: {value}")


def main() -> int:
    args = parse_args()
    ensure_output_folders(PROJECT_ROOT)
    timestamp = utc_timestamp()
    output_dir = resolve_path(args.output_dir)
    video_path = resolve_path(args.video)
    output_dir.mkdir(parents=True, exist_ok=True)
    if args.clear_cache:
        clear_cache(output_dir)

    mode_parts = [name for name, enabled in [("audit_decode", args.audit_decode), ("build_cache", args.build_cache), ("label", args.label), ("review", args.review), ("export_compat", args.export_compat), ("audit_labels", args.audit_labels)] if enabled]
    mode = "+".join(mode_parts) if mode_parts else "status"
    warnings: list[str] = []
    errors: list[str] = []
    timings = {
        "cache_build_seconds": 0.0,
        "audit_seconds": 0.0,
        "frame_loading_seconds": 0.0,
        "signature_compute_seconds": 0.0,
        "grouping_seconds": 0.0,
        "random_seek_seconds": 0.0,
        "viewer_start_seconds": 0.0,
        "save_seconds": 0.0,
        "report_seconds": 0.0,
    }
    audit_summary: dict[str, Any] = {}
    audit_paths: dict[str, str] = {}
    cache_metadata: dict[str, Any] = {}
    compatibility_status: dict[str, Any] = {"status": "not_run", "windows_exported": 0, "frame_labels_exported": 0, "backups": {}}

    if args.audit_decode or args.label or args.review:
        rows, audit_summary, audit_warnings = run_frame_decode_audit(
            video_path,
            start_frame=args.start_frame,
            end_frame=args.end_frame,
            duplicate_threshold=args.duplicate_threshold,
            signature_width=args.signature_width,
            random_seek_compare=args.random_seek_compare,
        )
        warnings.extend(audit_warnings)
        audit_paths = write_decode_audit_outputs(output_dir, rows, audit_summary)
        timings["audit_seconds"] = float(audit_summary.get("audit_seconds") or 0)
        timings["frame_loading_seconds"] = float(audit_summary.get("frame_loading_seconds") or 0)
        timings["signature_compute_seconds"] = float(audit_summary.get("signature_compute_seconds") or 0)
        timings["grouping_seconds"] = float(audit_summary.get("grouping_seconds") or 0)
        timings["random_seek_seconds"] = float(audit_summary.get("random_seek_seconds") or 0)
    else:
        audit_json = output_dir / "frame_decode_audit.json"
        if audit_json.exists():
            try:
                payload = json.loads(audit_json.read_text(encoding="utf-8"))
                audit_summary = dict(payload.get("summary") or {})
                audit_paths = {"json": str(audit_json), "csv": str(output_dir / "frame_decode_audit.csv"), "markdown": str(output_dir / "frame_decode_audit.md")}
                timings["audit_seconds"] = float(audit_summary.get("audit_seconds") or 0)
                timings["frame_loading_seconds"] = float(audit_summary.get("frame_loading_seconds") or 0)
                timings["signature_compute_seconds"] = float(audit_summary.get("signature_compute_seconds") or 0)
                timings["grouping_seconds"] = float(audit_summary.get("grouping_seconds") or 0)
                timings["random_seek_seconds"] = float(audit_summary.get("random_seek_seconds") or 0)
            except json.JSONDecodeError:
                warnings.append("Existing frame_decode_audit.json could not be read.")

    if args.build_cache or args.label or args.review:
        cache_metadata, cache_warnings = build_frame_cache(video_path, output_dir, start_frame=args.start_frame, end_frame=args.end_frame, resize_width=args.resize_width)
        warnings.extend(cache_warnings)
        timings["cache_build_seconds"] = float(cache_metadata.get("cache_build_seconds") or 0)
    else:
        cache_dir = cache_dir_for(output_dir, args.start_frame, args.end_frame, args.resize_width)
        if cache_is_valid(cache_dir, start_frame=args.start_frame, end_frame=args.end_frame, resize_width=args.resize_width, video_path=video_path):
            cache_metadata = json.loads((cache_dir / "cache_metadata.json").read_text(encoding="utf-8"))
            cache_metadata["cache_status"] = "available"

    if args.label or args.review:
        if not cache_metadata:
            cache_metadata, cache_warnings = build_frame_cache(video_path, output_dir, start_frame=args.start_frame, end_frame=args.end_frame, resize_width=args.resize_width)
            warnings.extend(cache_warnings)
        viewer_result = run_review_or_label_viewer(output_dir=output_dir, cache_metadata=cache_metadata, audit_json=output_dir / "frame_decode_audit.json", review_only=args.review)
        warnings.extend(viewer_result.get("warnings", []))
        errors.extend(viewer_result.get("errors", []))
        timings["viewer_start_seconds"] = float(viewer_result.get("viewer_start_seconds") or 0)
        timings["save_seconds"] = float(viewer_result.get("save_seconds") or 0)

    if args.export_compat:
        compatibility_status = export_legacy_compatibility(output_dir, PROJECT_ROOT / "outputs" / "timeline" / "stage_8_2_event_labels")

    integrity, integrity_paths = run_label_integrity_audit(output_dir)
    if args.audit_labels and not integrity.get("event_windows_count"):
        warnings.append("No Stage 8.2R event windows exist yet. Use --label or direct CSV editing to add labels.")

    if timings["save_seconds"] > 10:
        warnings.append("Save performance high.")

    windows = load_event_windows(output_dir)
    contacts = load_contact_candidates(output_dir)
    bounce_windows = sum(1 for row in windows if str(row.get("event_label")) == "bounce_window")
    hit_windows = sum(1 for row in windows if str(row.get("event_label")) == "hit_window")
    line_candidates = sum(1 for row in contacts if str(row.get("line_call_candidate")).lower() == "true")
    ambiguous_contacts = sum(1 for row in contacts if str(row.get("contact_precision")) == "ambiguous")
    friction, breakdown = score_friction(errors=errors, warnings=warnings, timings=timings, audit_summary=audit_summary, integrity=integrity, cache_status=str(cache_metadata.get("cache_status") or "missing"))

    report: dict[str, Any] = {
        "timestamp": timestamp,
        "stage": "stage_8_2r_event_labeling_workbench",
        "mode": mode,
        "audited_frames": int(audit_summary.get("total_frames_audited") or 0),
        "visual_groups": int(audit_summary.get("visual_groups") or 0),
        "near_duplicate_pairs": int(audit_summary.get("near_duplicate_pairs") or 0),
        "event_windows_count": len(windows),
        "contact_candidates_count": len(contacts),
        "bounce_windows_count": bounce_windows,
        "hit_windows_count": hit_windows,
        "line_call_candidates_count": line_candidates,
        "ambiguous_contacts_count": ambiguous_contacts,
        "integrity_issues_count": int(integrity.get("integrity_issues_count") or 0),
        "cache_status": str(cache_metadata.get("cache_status") or "missing"),
        "performance_timings": timings,
        "compatibility_export_status": compatibility_status.get("status"),
        "compatibility_export": compatibility_status,
        "audit_paths": audit_paths,
        "integrity_paths": integrity_paths,
        "warnings": warnings,
        "errors": errors,
        "friction": friction,
        "friction_breakdown": breakdown,
        "final_verdict": "blocked",
        "recommended_next_step": "",
    }
    report["final_verdict"] = determine_verdict(report)
    report["recommended_next_step"] = recommended_next_step(report)
    report_start = time.perf_counter()
    report["json_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_8_2r_event_labeling_workbench_report.json")
    report["markdown_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_8_2r_event_labeling_workbench_report.md")
    log_path = write_timestamped_log(PROJECT_ROOT, "stage_8_2r_event_labeling_workbench", [f"timestamp={timestamp}", f"mode={mode}", f"verdict={report['final_verdict']}", f"friction={friction['score']} ({friction['band']})"])
    report["log_path"] = str(log_path)
    write_json_report(Path(report["json_report_path"]), report)
    write_markdown_report(Path(report["markdown_report_path"]), "Stage 8.2R Event Labeling Workbench Report", build_markdown_sections(report))
    write_lab_notebook(report)
    timings["report_seconds"] = round(time.perf_counter() - report_start, 3)
    report["performance_timings"] = timings
    write_json_report(Path(report["json_report_path"]), report)
    write_markdown_report(Path(report["markdown_report_path"]), "Stage 8.2R Event Labeling Workbench Report", build_markdown_sections(report))
    print_summary(report)
    return 1 if report["final_verdict"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
