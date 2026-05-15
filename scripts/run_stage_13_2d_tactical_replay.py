"""Run Stage 13 deterministic 2D tactical replay renderer."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Any

import cv2


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from tennis_vision.friction import calculate_stage_13_friction_score  # noqa: E402
from tennis_vision.baseline_quarantine import annotate_report_with_failed_baseline_warning, failed_baseline_block_message, is_old_replay_schema, print_failed_baseline_warning  # noqa: E402
from tennis_vision.replay_renderer_2d import (  # noqa: E402
    create_contact_sheet,
    export_replay_video,
    extract_court_model,
    extract_events,
    extract_players,
    extract_replay_keyframes,
    load_replay_schema,
    render_replay_frames,
    write_renderer_manifest,
)
from tennis_vision.report import ensure_output_folders, utc_timestamp, write_json_report, write_markdown_report, write_timestamped_log  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 13 2D tactical replay renderer.")
    parser.add_argument("--schema", type=Path, default=PROJECT_ROOT / "outputs" / "replay" / "stage_12_replay_schema" / "replay_schema.json")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs" / "replay" / "stage_13_2d_tactical_replay")
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--interpolate", dest="interpolate", action="store_true", default=True)
    parser.add_argument("--no-interpolate", dest="interpolate", action="store_false")
    parser.add_argument("--interpolation-steps", type=int, default=5)
    parser.add_argument("--no-video", action="store_true")
    parser.add_argument("--allow-failed-baseline", action="store_true", help="Allow rendering from the failed baseline replay schema for explicit research only.")
    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def determine_verdict(report: dict[str, Any]) -> str:
    flags = report["flags"]
    if flags["replay_schema_missing"]:
        return "blocked"
    if flags["court_model_missing"] or flags["keyframes_missing"]:
        return "needs_more_replay_data"
    if flags["render_frames_failed"] or flags["manifest_write_failed"]:
        return "blocked"
    if flags["video_export_failed"] or flags["contact_sheet_failed"] or report["warnings"]:
        return "ready_with_warnings"
    return "ready_for_stage_14"


def recommended_next_step(report: dict[str, Any]) -> str:
    if report["final_verdict"] == "ready_for_stage_14":
        return "Proceed to Stage 14: Side-View Ball Flight Renderer."
    if report["final_verdict"] == "ready_with_warnings":
        return "Review renderer warnings, then proceed to Stage 14 or Stage 13.1 replay visual polish."
    if report["final_verdict"] == "needs_more_replay_data":
        return "Regenerate Stage 12 replay schema with court and replay keyframe data, then rerun Stage 13."
    return "Fix Stage 13 blockers, then rerun the 2D tactical replay renderer."


def field_block(rows: list[tuple[str, Any]]) -> str:
    lines: list[str] = []
    for key, value in rows:
        lines.append(f"{key}:")
        lines.append(f"  {value if value not in (None, '') else 'Not available'}")
        lines.append("")
    return "\n".join(lines).rstrip()


def bullet_list(items: list[str], empty: str) -> str:
    return empty if not items else "\n".join(f"- {item}" for item in items)


def build_replay_summary(report: dict[str, Any]) -> str:
    outputs = report["output_paths"]
    lines = [
        "# Stage 13 2D Tactical Replay Summary",
        "",
        "WHAT WAS RENDERED",
        "  - court",
        "  - ball trajectory",
        "  - players",
        "  - event markers",
        "  - timeline strip",
        "",
        "INPUT DATA",
        f"  Replay schema: {report['input_schema_path']}",
        f"  Schema version: {report['schema_version']}",
        f"  Keyframes: {report['keyframes_count']}",
        f"  Players: {report['players_count']}",
        f"  Events: {report['events_count']}",
        "",
        "OUTPUTS",
        f"  Frames: {outputs['frames_dir']}",
        f"  Video: {outputs['video_path'] if report['video_generated'] else 'Not generated'}",
        f"  Contact sheet: {outputs['contact_sheet_path']}",
        f"  Final frame: {outputs['final_frame_path']}",
        f"  Manifest: {outputs['renderer_manifest_path']}",
        "",
        "LIMITATIONS",
        "  - 2D tactical view only",
        "  - no photorealism",
        "  - no true ball height",
        "  - interpolated points are visual only",
        "  - possible_* events are hypotheses",
        "",
        "NEXT STEP",
        "  Stage 14: Side-View Ball Flight Renderer.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_report_sections(report: dict[str, Any]) -> list[tuple[str, str]]:
    return [
        ("VERDICT", field_block([("Final verdict", report["final_verdict"]), ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"), ("Renderer", "2d_tactical_replay")])),
        (
            "INPUTS",
            field_block(
                [
                    ("Replay schema", report["input_schema_path"]),
                    ("Schema version", report["schema_version"]),
                    ("Keyframes", report["keyframes_count"]),
                    ("Players", report["players_count"]),
                    ("Events", report["events_count"]),
                ]
            ),
        ),
        (
            "OUTPUTS",
            field_block(
                [
                    ("Frames generated", report["frames_generated"]),
                    ("Video generated", report["video_generated"]),
                    ("Video path", report["video_path"]),
                    ("Contact sheet", report["contact_sheet_path"]),
                    ("Final frame", report["final_frame_path"]),
                    ("Manifest", report["renderer_manifest_path"]),
                ]
            ),
        ),
        ("WARNINGS", bullet_list(report["warnings"], "No warnings.")),
        ("ERRORS", bullet_list(report["errors"], "No errors.")),
        ("PRODUCT OWNER INTERPRETATION", "This is the first visual replay generated from analysis data, not from the original video. It is a deterministic 2D tactical visualization and keeps event uncertainty visible."),
        ("NEXT STEP", report["recommended_next_step"]),
    ]


def update_lab_notebook_safely() -> tuple[dict[str, Path], str | None]:
    try:
        from tennis_vision.lab_notebook import lab_notebook_paths, update_lab_notebook

        update_lab_notebook(PROJECT_ROOT)
        return lab_notebook_paths(PROJECT_ROOT, "stage_13"), None
    except Exception as exc:
        try:
            from tennis_vision.lab_notebook import lab_notebook_paths

            return lab_notebook_paths(PROJECT_ROOT, "stage_13"), f"Lab notebook update failed: {exc}"
        except Exception:
            return {
                "stage_page": PROJECT_ROOT / "docs" / "lab-notebook" / "stage_13_2d_tactical_replay.md",
                "experiment_index": PROJECT_ROOT / "docs" / "lab-notebook" / "experiment_index.md",
            }, f"Lab notebook update failed: {exc}"


def print_summary(report: dict[str, Any], lab_paths: dict[str, Path]) -> None:
    rows = [
        ("Verdict", report["final_verdict"]),
        ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"),
        ("Schema version", report["schema_version"]),
        ("Keyframes", report["keyframes_count"]),
        ("Players", report["players_count"]),
        ("Events", report["events_count"]),
        ("Frames generated", report["frames_generated"]),
        ("Video generated", report["video_generated"]),
        ("Video path", report["video_path"]),
        ("Contact sheet", report["contact_sheet_path"]),
        ("Final frame", report["final_frame_path"]),
        ("Manifest", report["renderer_manifest_path"]),
        ("Lab notebook", lab_paths["stage_page"]),
        ("Recommended next step", report["recommended_next_step"]),
    ]
    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(title="Stage 13 2D Tactical Replay")
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")
        for field, value in rows:
            table.add_row(str(field), str(value))
        Console().print(table)
    except ImportError:
        print("Stage 13 2D Tactical Replay")
        for field, value in rows:
            print(f"{field}: {value}")


def main() -> int:
    args = parse_args()
    ensure_output_folders(PROJECT_ROOT)
    timestamp = utc_timestamp()
    schema_path = resolve_path(args.schema)
    if is_old_replay_schema(schema_path) and not args.allow_failed_baseline:
        print(failed_baseline_block_message())
        return 2
    if is_old_replay_schema(schema_path):
        print_failed_baseline_warning()
    output_dir = resolve_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    schema, warnings, errors = load_replay_schema(schema_path)
    court_model = extract_court_model(schema)
    keyframes = extract_replay_keyframes(schema)
    players = extract_players(schema)
    events = extract_events(schema)
    schema_version = schema.get("metadata", {}).get("schema_version") if schema else None

    frame_paths: list[Path] = []
    render_context: dict[str, Any] = {"display_points": [], "players": players, "events": events}
    if schema and keyframes:
        frame_paths, render_context, frame_warnings, frame_errors = render_replay_frames(
            schema=schema,
            output_dir=output_dir,
            interpolate=args.interpolate,
            interpolation_steps=args.interpolation_steps,
        )
        warnings.extend(frame_warnings)
        errors.extend(frame_errors)

    frames_dir = output_dir / "frames"
    video_path = output_dir / "tactical_replay.mp4"
    contact_sheet_path = output_dir / "tactical_replay_contact_sheet.jpg"
    final_frame_path = output_dir / "tactical_replay_final_frame.jpg"
    manifest_path = output_dir / "renderer_manifest.json"
    summary_path = output_dir / "replay_summary.md"

    video_generated = False
    if frame_paths and not args.no_video:
        video_generated, video_warnings, video_errors = export_replay_video(frame_paths, video_path, args.fps)
        warnings.extend(video_warnings)
        errors.extend(video_errors)
    elif args.no_video:
        warnings.append("Video export disabled by --no-video; frame outputs are available.")

    contact_sheet_generated = False
    if frame_paths:
        contact_sheet_generated, contact_warnings = create_contact_sheet(frame_paths, contact_sheet_path)
        warnings.extend(contact_warnings)
        if frame_paths[-1].exists():
            shutil.copyfile(frame_paths[-1], final_frame_path)

    output_paths = {
        "frames_dir": str(frames_dir),
        "video_path": str(video_path),
        "contact_sheet_path": str(contact_sheet_path),
        "final_frame_path": str(final_frame_path),
        "renderer_manifest_path": str(manifest_path),
        "replay_summary_path": str(summary_path),
    }
    flags = {
        "replay_schema_missing": not bool(schema),
        "court_model_missing": not bool(court_model.get("homography_status", {}).get("computed")),
        "keyframes_missing": len(keyframes) == 0,
        "render_frames_failed": len(frame_paths) == 0,
        "video_export_failed": bool(frame_paths and not args.no_video and not video_generated),
        "contact_sheet_failed": bool(frame_paths and not contact_sheet_generated),
        "manifest_write_failed": False,
    }
    friction = calculate_stage_13_friction_score(**flags, warnings_count=len(warnings), errors_count=len(errors))
    report: dict[str, Any] = {
        "timestamp": timestamp,
        "stage": "stage_13_2d_tactical_replay",
        "input_schema_path": str(schema_path),
        "schema_version": schema_version,
        "keyframes_count": len(keyframes),
        "players_count": len(players),
        "events_count": len(events),
        "frames_generated": len(frame_paths),
        "video_generated": video_generated,
        "video_path": str(video_path) if video_generated else "",
        "contact_sheet_path": str(contact_sheet_path) if contact_sheet_generated else "",
        "final_frame_path": str(final_frame_path) if final_frame_path.exists() else "",
        "renderer_manifest_path": str(manifest_path),
        "warnings": warnings,
        "errors": errors,
        "flags": flags,
        "friction": friction,
        "final_verdict": "blocked",
        "recommended_next_step": "",
        "output_paths": output_paths,
    }
    if is_old_replay_schema(schema_path):
        annotate_report_with_failed_baseline_warning(report)
    report["final_verdict"] = determine_verdict(report)
    report["recommended_next_step"] = recommended_next_step(report)
    try:
        write_renderer_manifest(
            manifest_path,
            {
                "generated_at": timestamp,
                "stage": "stage_13_2d_tactical_replay",
                "input_schema_path": str(schema_path),
                "schema_version": schema_version,
                "renderer_type": "2d_tactical_replay",
                "frames_generated": len(frame_paths),
                "video_generated": video_generated,
                "fps": args.fps,
                "interpolation_enabled": args.interpolate,
                "interpolation_steps": args.interpolation_steps,
                "players_rendered": len(players),
                "ball_keyframes_rendered": len(keyframes),
                "events_rendered": len(events),
                "output_paths": output_paths,
                "warnings": warnings,
                "errors": errors,
                "limitations": [
                    "2D tactical view only.",
                    "No photorealistic video.",
                    "No true ball height.",
                    "Interpolated points are visual only.",
                    "possible_* events are hypotheses.",
                ],
            },
        )
    except OSError as exc:
        flags["manifest_write_failed"] = True
        errors.append(f"Renderer manifest write failed: {exc}")
    friction = calculate_stage_13_friction_score(**flags, warnings_count=len(warnings), errors_count=len(errors))
    report["friction"] = friction
    report["final_verdict"] = determine_verdict(report)
    report["recommended_next_step"] = recommended_next_step(report)
    summary_path.write_text(build_replay_summary(report), encoding="utf-8")

    log_path = write_timestamped_log(
        PROJECT_ROOT,
        "stage_13_2d_tactical_replay",
        [
            f"timestamp={timestamp}",
            f"verdict={report['final_verdict']}",
            f"friction={friction['score']} ({friction['band']})",
            f"frames={len(frame_paths)}",
            f"video_generated={video_generated}",
        ],
    )
    report["log_path"] = str(log_path)
    report["json_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_13_2d_tactical_replay_report.json")
    report["markdown_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_13_2d_tactical_replay_report.md")
    write_json_report(Path(report["json_report_path"]), report)
    write_markdown_report(Path(report["markdown_report_path"]), "Stage 13 2D Tactical Replay Renderer Report", build_report_sections(report))

    lab_paths, notebook_warning = update_lab_notebook_safely()
    if notebook_warning:
        report["warnings"].append(notebook_warning)
        write_json_report(Path(report["json_report_path"]), report)
        write_markdown_report(Path(report["markdown_report_path"]), "Stage 13 2D Tactical Replay Renderer Report", build_report_sections(report))
        print(f"Warning: {notebook_warning}")
    print_summary(report, lab_paths)
    return 1 if report["final_verdict"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
