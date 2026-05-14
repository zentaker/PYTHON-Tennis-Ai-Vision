"""Run Stage 14 deterministic side-view ball flight replay renderer."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from tennis_vision.ball_flight_estimator import build_side_view_keyframes  # noqa: E402
from tennis_vision.friction import calculate_stage_14_1_friction_score, calculate_stage_14_friction_score  # noqa: E402
from tennis_vision.replay_renderer_side_view import (  # noqa: E402
    create_semantic_debug_image,
    create_side_contact_sheet,
    export_side_view_video,
    load_replay_schema,
    render_side_view_frames,
    write_side_view_manifest,
)
from tennis_vision.report import ensure_output_folders, utc_timestamp, write_json_report, write_markdown_report, write_timestamped_log  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 14 side-view ball flight replay renderer.")
    parser.add_argument("--schema", type=Path, default=PROJECT_ROOT / "outputs" / "replay" / "stage_12_replay_schema" / "replay_schema.json")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs" / "replay" / "stage_14_side_view_replay")
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--interpolate", dest="interpolate", action="store_true", default=True)
    parser.add_argument("--no-interpolate", dest="interpolate", action="store_false")
    parser.add_argument("--interpolation-steps", type=int, default=8)
    parser.add_argument("--no-video", action="store_true")
    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def determine_verdict(report: dict[str, Any]) -> str:
    flags = report["flags"]
    if flags["replay_schema_missing"]:
        return "blocked"
    if flags["keyframes_missing"] or flags["side_view_keyframes_missing"]:
        return "needs_more_replay_data"
    if flags["render_frames_failed"] or flags["manifest_write_failed"]:
        return "blocked"
    if flags["video_export_failed"] or flags["contact_sheet_failed"] or report["warnings"]:
        return "ready_with_warnings"
    return "ready_for_stage_15"


def recommended_next_step(report: dict[str, Any]) -> str:
    if report["final_verdict"] == "ready_for_stage_15":
        return "Proceed to Stage 15: Multi-Camera Analytical Replay."
    if report["final_verdict"] == "ready_with_warnings":
        return "Review renderer warnings, then proceed to Stage 15 or Stage 14.1 side-view visual polish."
    if report["final_verdict"] == "needs_more_replay_data":
        return "Regenerate Stage 12 replay data with usable keyframes, then rerun Stage 14."
    return "Fix Stage 14 blockers, then rerun the side-view renderer."


def determine_patch_verdict(report: dict[str, Any]) -> str:
    flags = report["flags"]
    if flags["replay_schema_missing"]:
        return "blocked"
    if flags["bounce_grounding_failed"] or flags["hit_contact_band_failed"] or flags["semantic_debug_generation_failed"]:
        return "needs_more_side_view_tuning"
    if flags["render_frames_failed"]:
        return "blocked"
    if flags["video_export_failed"] or report["warnings"]:
        return "ready_with_warnings"
    return "ready_for_stage_15"


def recommended_patch_next_step(report: dict[str, Any]) -> str:
    if report["final_verdict"] == "ready_for_stage_15":
        return "Proceed to Stage 15: Multi-Camera Analytical Replay."
    if report["final_verdict"] == "needs_more_side_view_tuning":
        return "Tune side-view semantics further before Stage 15."
    if report["final_verdict"] == "ready_with_warnings":
        return "Review side-view patch warnings, then proceed to Stage 15 or Stage 14.2 polish."
    return "Fix Stage 14.1 blockers, then rerun the side-view patch."


def field_block(rows: list[tuple[str, Any]]) -> str:
    lines: list[str] = []
    for key, value in rows:
        lines.append(f"{key}:")
        lines.append(f"  {value if value not in (None, '') else 'Not available'}")
        lines.append("")
    return "\n".join(lines).rstrip()


def bullet_list(items: list[str], empty: str) -> str:
    return empty if not items else "\n".join(f"- {item}" for item in items)


def build_side_view_summary(report: dict[str, Any]) -> str:
    outputs = report["output_paths"]
    lines = [
        "# Stage 14 Side-View Ball Flight Summary",
        "",
        "WHAT WAS RENDERED",
        "  - side-view court",
        "  - net",
        "  - estimated ball arc",
        "  - ball trajectory",
        "  - possible event markers",
        "  - timeline strip",
        "",
        "INPUT DATA",
        f"  Replay schema: {report['input_schema_path']}",
        f"  Schema version: {report['schema_version']}",
        f"  Keyframes: {report['keyframes_count']}",
        f"  Events: {report['events_count']}",
        "",
        "HEIGHT MODEL",
        "  True height available:",
        f"    {str(report['true_height_available']).lower()}",
        "",
        "  Height type:",
        "    synthetic / estimated",
        "",
        "  Explanation:",
        "    The project currently has 2D projected court data, not measured 3D ball height.",
        "    The side-view height is a visual approximation.",
        "",
        "SEMANTIC HEIGHT PATCH",
        "  Bounces are now visually grounded near the court surface.",
        "  Hits use a plausible estimated contact-height band.",
        "  Interpolated points remain synthetic visual points.",
        "  The renderer still does not use measured 3D height.",
        "",
        "OUTPUTS",
        f"  Frames: {outputs['frames_dir']}",
        f"  Video: {outputs['video_path'] if report['video_generated'] else 'Not generated'}",
        f"  Contact sheet: {outputs['contact_sheet_path']}",
        f"  Final frame: {outputs['final_frame_path']}",
        f"  Arc preview: {outputs['arc_preview_path']}",
        f"  Manifest: {outputs['manifest_path']}",
        "",
        "LIMITATIONS",
        "  - no true 3D reconstruction",
        "  - no measured ball height",
        "  - possible_* events are hypotheses",
        "  - side-view is analytical visualization only",
        "  - not a broadcast reconstruction",
        "",
        "NEXT STEP",
        "  Stage 15: Multi-Camera Analytical Replay or Stage 14.1 Side-View Visual Polish.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_report_sections(report: dict[str, Any]) -> list[tuple[str, str]]:
    return [
        ("VERDICT", field_block([("Final verdict", report["final_verdict"]), ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"), ("Renderer", "side_view_ball_flight")])),
        (
            "INPUTS",
            field_block(
                [
                    ("Replay schema", report["input_schema_path"]),
                    ("Schema version", report["schema_version"]),
                    ("Keyframes", report["keyframes_count"]),
                    ("Events", report["events_count"]),
                ]
            ),
        ),
        (
            "HEIGHT / ARC MODEL",
            field_block(
                [
                    ("True height available", report["true_height_available"]),
                    ("Synthetic height enabled", report["synthetic_height_enabled"]),
                    ("Height estimation method", report["height_estimation_method"]),
                ]
            ),
        ),
        (
            "OUTPUTS",
            field_block(
                [
                    ("Frames generated", report["frames_generated"]),
                    ("Video generated", report["video_generated"]),
                    ("Contact sheet", report["contact_sheet_path"]),
                    ("Final frame", report["final_frame_path"]),
                    ("Arc preview", report["arc_preview_path"]),
                    ("Manifest", report["manifest_path"]),
                ]
            ),
        ),
        ("WARNINGS", bullet_list(report["warnings"], "No warnings.")),
        ("ERRORS", bullet_list(report["errors"], "No errors.")),
        ("PRODUCT OWNER INTERPRETATION", "This is a side-view analytical visualization, not real 3D reconstruction. The ball height is synthetic and exists only to make the replay easier to understand."),
        ("NEXT STEP", report["recommended_next_step"]),
    ]


def build_patch_report_sections(report: dict[str, Any]) -> list[tuple[str, str]]:
    return [
        ("VERDICT", field_block([("Final verdict", report["final_verdict"]), ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"), ("Patch applied", report["semantic_height_patch_applied"])])),
        ("WHY THIS PATCH EXISTS", "The previous side-view replay could make bounce-like events appear to float above the court. That made the replay harder to interpret as tennis even though the renderer worked technically."),
        (
            "PATCH BEHAVIOR",
            field_block(
                [
                    ("Bounce grounding", report["bounce_grounding_enabled"]),
                    ("Hit contact band", report["hit_contact_band_enabled"]),
                    ("Interpolated point marking", report["interpolated_points_marked"]),
                    ("Net/ground reference improvement", True),
                ]
            ),
        ),
        (
            "OUTPUTS",
            field_block(
                [
                    ("Video", report["output_paths"].get("video_path")),
                    ("Contact sheet", report["output_paths"].get("contact_sheet_path")),
                    ("Final frame", report["output_paths"].get("final_frame_path")),
                    ("Arc preview", report["output_paths"].get("arc_preview_path")),
                    ("Semantic debug", report["semantic_debug_artifact"]),
                    ("Manifest", report["output_paths"].get("manifest_path")),
                ]
            ),
        ),
        ("PRODUCT OWNER INTERPRETATION", "The side-view should now read more like a tennis exchange: bounce-like anchors are grounded, hit-like anchors sit in a plausible contact band, and interpolated points are visibly synthetic."),
        ("WARNINGS", bullet_list(report["warnings"], "No warnings.")),
        ("ERRORS", bullet_list(report["errors"], "No errors.")),
        ("NEXT STEP", report["recommended_next_step"]),
    ]


def update_lab_notebook_safely() -> tuple[dict[str, Path], str | None]:
    try:
        from tennis_vision.lab_notebook import lab_notebook_paths, update_lab_notebook

        update_lab_notebook(PROJECT_ROOT)
        return lab_notebook_paths(PROJECT_ROOT, "stage_14_1"), None
    except Exception as exc:
        try:
            from tennis_vision.lab_notebook import lab_notebook_paths

            return lab_notebook_paths(PROJECT_ROOT, "stage_14_1"), f"Lab notebook update failed: {exc}"
        except Exception:
            return {
                "stage_page": PROJECT_ROOT / "docs" / "lab-notebook" / "stage_14_side_view_replay.md",
                "experiment_index": PROJECT_ROOT / "docs" / "lab-notebook" / "experiment_index.md",
            }, f"Lab notebook update failed: {exc}"


def print_summary(report: dict[str, Any], lab_paths: dict[str, Path]) -> None:
    rows = [
        ("Verdict", report["final_verdict"]),
        ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"),
        ("Semantic patch applied", report.get("semantic_height_patch_applied", True)),
        ("Bounce grounding", report.get("bounce_grounding_enabled", True)),
        ("Hit contact band", report.get("hit_contact_band_enabled", True)),
        ("Interpolated points marked", report.get("interpolated_points_marked", True)),
        ("Frames generated", report["frames_generated"]),
        ("Video generated", report["video_generated"]),
        ("Semantic debug", report.get("semantic_debug_artifact", "")),
        ("Manifest", report.get("manifest_path") or report.get("output_paths", {}).get("manifest_path", "")),
        ("Lab notebook", lab_paths["stage_page"]),
        ("Recommended next step", report["recommended_next_step"]),
    ]
    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(title="Stage 14.1 Side-View Patch")
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")
        for field, value in rows:
            table.add_row(str(field), str(value))
        Console().print(table)
    except ImportError:
        print("Stage 14.1 Side-View Patch")
        for field, value in rows:
            print(f"{field}: {value}")


def main() -> int:
    args = parse_args()
    ensure_output_folders(PROJECT_ROOT)
    timestamp = utc_timestamp()
    schema_path = resolve_path(args.schema)
    output_dir = resolve_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    schema, warnings, errors = load_replay_schema(schema_path)
    schema_version = schema.get("metadata", {}).get("schema_version") if schema else None
    keyframes = list(schema.get("ball_trajectory", {}).get("replay_keyframes", [])) if schema else []
    events = list(schema.get("event_timeline", [])) if schema else []
    side_view_keyframes = build_side_view_keyframes(schema) if schema else []

    frame_paths: list[Path] = []
    render_context: dict[str, Any] = {"side_view_keyframes": side_view_keyframes, "display_points": [], "players": [], "events": events}
    if schema and side_view_keyframes:
        frame_paths, render_context, frame_warnings, frame_errors = render_side_view_frames(
            schema=schema,
            output_dir=output_dir,
            interpolate=args.interpolate,
            interpolation_steps=args.interpolation_steps,
        )
        warnings.extend(frame_warnings)
        errors.extend(frame_errors)

    frames_dir = output_dir / "frames"
    video_path = output_dir / "side_view_replay.mp4"
    contact_sheet_path = output_dir / "side_view_contact_sheet.jpg"
    final_frame_path = output_dir / "side_view_final_frame.jpg"
    arc_preview_path = output_dir / "side_view_arc_preview.jpg"
    semantic_debug_path = output_dir / "side_view_semantic_debug.jpg"
    manifest_path = output_dir / "side_view_manifest.json"
    summary_path = output_dir / "side_view_summary.md"

    video_generated = False
    if frame_paths and not args.no_video:
        video_generated, video_warnings, video_errors = export_side_view_video(frame_paths, video_path, args.fps)
        warnings.extend(video_warnings)
        errors.extend(video_errors)
    elif args.no_video:
        warnings.append("Video export disabled by --no-video; frame outputs are available.")

    contact_sheet_generated = False
    semantic_debug_generated = False
    if frame_paths:
        contact_sheet_generated, contact_warnings = create_side_contact_sheet(frame_paths, contact_sheet_path)
        warnings.extend(contact_warnings)
        if frame_paths[-1].exists():
            shutil.copyfile(frame_paths[-1], final_frame_path)
            shutil.copyfile(frame_paths[-1], arc_preview_path)
        semantic_debug_generated, debug_warnings = create_semantic_debug_image(
            schema=schema,
            side_view_keyframes=render_context.get("side_view_keyframes", []),
            display_points=render_context.get("display_points", []),
            events=render_context.get("events", []),
            players=render_context.get("players", []),
            output_path=semantic_debug_path,
        )
        warnings.extend(debug_warnings)

    output_paths = {
        "frames_dir": str(frames_dir),
        "video_path": str(video_path),
        "contact_sheet_path": str(contact_sheet_path),
        "final_frame_path": str(final_frame_path),
        "arc_preview_path": str(arc_preview_path),
        "semantic_debug_path": str(semantic_debug_path),
        "manifest_path": str(manifest_path),
        "summary_path": str(summary_path),
    }
    flags = {
        "replay_schema_missing": not bool(schema),
        "keyframes_missing": len(keyframes) == 0,
        "side_view_keyframes_missing": len(side_view_keyframes) == 0,
        "render_frames_failed": len(frame_paths) == 0,
        "video_export_failed": bool(frame_paths and not args.no_video and not video_generated),
        "contact_sheet_failed": bool(frame_paths and not contact_sheet_generated),
        "manifest_write_failed": False,
    }
    patch_flags = {
        "replay_schema_missing": not bool(schema),
        "side_view_source_missing": len(side_view_keyframes) == 0,
        "bounce_grounding_failed": not validate_bounce_grounding(side_view_keyframes),
        "hit_contact_band_failed": not validate_hit_contact_band(side_view_keyframes),
        "semantic_debug_generation_failed": bool(frame_paths and not semantic_debug_generated),
        "render_frames_failed": len(frame_paths) == 0,
        "video_export_failed": bool(frame_paths and not args.no_video and not video_generated),
    }
    friction = calculate_stage_14_friction_score(**flags, warnings_count=len(warnings), errors_count=len(errors))
    report: dict[str, Any] = {
        "timestamp": timestamp,
        "stage": "stage_14_side_view_replay",
        "input_schema_path": str(schema_path),
        "schema_version": schema_version,
        "keyframes_count": len(keyframes),
        "side_view_keyframes_count": len(side_view_keyframes),
        "events_count": len(events),
        "frames_generated": len(frame_paths),
        "video_generated": video_generated,
        "video_path": str(video_path) if video_generated else "",
        "contact_sheet_path": str(contact_sheet_path) if contact_sheet_generated else "",
        "final_frame_path": str(final_frame_path) if final_frame_path.exists() else "",
        "arc_preview_path": str(arc_preview_path) if arc_preview_path.exists() else "",
        "semantic_debug_path": str(semantic_debug_path) if semantic_debug_path.exists() else "",
        "manifest_path": str(manifest_path),
        "synthetic_height_enabled": True,
        "true_height_available": False,
        "height_estimation_method": "event-aware synthetic arc from 2D projected keyframes",
        "warnings": warnings,
        "errors": errors,
        "flags": flags,
        "friction": friction,
        "final_verdict": "blocked",
        "recommended_next_step": "",
        "output_paths": output_paths,
    }
    report["final_verdict"] = determine_verdict(report)
    report["recommended_next_step"] = recommended_next_step(report)
    try:
        write_side_view_manifest(
            manifest_path,
            {
                "generated_at": timestamp,
                "stage": "stage_14_side_view_replay",
                "input_schema_path": str(schema_path),
                "schema_version": schema_version,
                "renderer_type": "side_view_ball_flight",
                "frames_generated": len(frame_paths),
                "video_generated": video_generated,
                "fps": args.fps,
                "interpolation_enabled": args.interpolate,
                "interpolation_steps": args.interpolation_steps,
                "keyframes_used": len(side_view_keyframes),
                "events_used": len(events),
                "synthetic_height_enabled": True,
                "true_height_available": False,
                "height_estimation_method": report["height_estimation_method"],
                "semantic_height_patch_applied": True,
                "bounce_grounding_enabled": True,
                "hit_contact_band_enabled": True,
                "interpolated_points_marked": True,
                "height_anchor_summary": summarize_height_anchors(side_view_keyframes),
                "semantic_warnings": semantic_warnings(side_view_keyframes),
                "output_paths": output_paths,
                "warnings": warnings,
                "errors": errors,
                "limitations": [
                    "No true 3D reconstruction.",
                    "No measured ball height.",
                    "possible_* events are hypotheses.",
                    "Side-view is analytical visualization only.",
                    "Not a broadcast reconstruction.",
                ],
            },
        )
    except OSError as exc:
        flags["manifest_write_failed"] = True
        errors.append(f"Side-view manifest write failed: {exc}")
    friction = calculate_stage_14_friction_score(**flags, warnings_count=len(warnings), errors_count=len(errors))
    report["friction"] = friction
    report["final_verdict"] = determine_verdict(report)
    report["recommended_next_step"] = recommended_next_step(report)
    summary_path.write_text(build_side_view_summary(report), encoding="utf-8")

    patch_friction = calculate_stage_14_1_friction_score(**patch_flags, warnings_count=len(warnings), errors_count=len(errors))
    patch_report: dict[str, Any] = {
        "timestamp": timestamp,
        "stage": "stage_14_1_side_view_patch",
        "source_stage": 14,
        "semantic_height_patch_applied": True,
        "bounce_grounding_enabled": True,
        "hit_contact_band_enabled": True,
        "interpolated_points_marked": True,
        "frames_generated": len(frame_paths),
        "video_generated": video_generated,
        "semantic_debug_artifact": str(semantic_debug_path) if semantic_debug_path.exists() else "",
        "warnings": warnings,
        "errors": errors,
        "flags": patch_flags,
        "friction": patch_friction,
        "final_verdict": "blocked",
        "recommended_next_step": "",
        "output_paths": output_paths,
        "height_anchor_summary": summarize_height_anchors(side_view_keyframes),
        "semantic_warnings": semantic_warnings(side_view_keyframes),
    }
    patch_report["final_verdict"] = determine_patch_verdict(patch_report)
    patch_report["recommended_next_step"] = recommended_patch_next_step(patch_report)

    log_path = write_timestamped_log(
        PROJECT_ROOT,
        "stage_14_side_view_replay",
        [
            f"timestamp={timestamp}",
            f"verdict={report['final_verdict']}",
            f"friction={friction['score']} ({friction['band']})",
            f"frames={len(frame_paths)}",
            f"video_generated={video_generated}",
            "synthetic_height_enabled=True",
            "true_height_available=False",
        ],
    )
    report["log_path"] = str(log_path)
    report["json_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_14_side_view_replay_report.json")
    report["markdown_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_14_side_view_replay_report.md")
    write_json_report(Path(report["json_report_path"]), report)
    write_markdown_report(Path(report["markdown_report_path"]), "Stage 14 Side-View Ball Flight Renderer Report", build_report_sections(report))
    patch_report["json_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_14_1_side_view_patch_report.json")
    patch_report["markdown_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_14_1_side_view_patch_report.md")
    write_json_report(Path(patch_report["json_report_path"]), patch_report)
    write_markdown_report(Path(patch_report["markdown_report_path"]), "Stage 14.1 Side-View Height Semantics Patch Report", build_patch_report_sections(patch_report))

    lab_paths, notebook_warning = update_lab_notebook_safely()
    if notebook_warning:
        report["warnings"].append(notebook_warning)
        patch_report["warnings"].append(notebook_warning)
        write_json_report(Path(report["json_report_path"]), report)
        write_markdown_report(Path(report["markdown_report_path"]), "Stage 14 Side-View Ball Flight Renderer Report", build_report_sections(report))
        write_json_report(Path(patch_report["json_report_path"]), patch_report)
        write_markdown_report(Path(patch_report["markdown_report_path"]), "Stage 14.1 Side-View Height Semantics Patch Report", build_patch_report_sections(patch_report))
        print(f"Warning: {notebook_warning}")
    print_summary(patch_report, lab_paths)
    return 1 if patch_report["final_verdict"] == "blocked" else 0


def summarize_height_anchors(side_view_keyframes: list[dict[str, Any]]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for point in side_view_keyframes:
        key = str(point.get("height_anchor_type") or "unknown")
        summary[key] = summary.get(key, 0) + 1
    return summary


def semantic_warnings(side_view_keyframes: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    if not any(point.get("height_anchor_type") == "bounce_grounded" for point in side_view_keyframes):
        warnings.append("No possible_bounce anchors were present in the current replay schema; bounce grounding is enabled for future bounce events.")
    return warnings


def validate_bounce_grounding(side_view_keyframes: list[dict[str, Any]]) -> bool:
    bounce_points = [point for point in side_view_keyframes if point.get("height_anchor_type") == "bounce_grounded"]
    if not bounce_points:
        return True
    return all(float(point.get("synthetic_height") or 99) <= 2.5 for point in bounce_points)


def validate_hit_contact_band(side_view_keyframes: list[dict[str, Any]]) -> bool:
    hit_points = [point for point in side_view_keyframes if point.get("height_anchor_type") == "hit_contact"]
    if not hit_points:
        return True
    return all(62.0 <= float(point.get("synthetic_height") or 0) <= 118.0 for point in hit_points)


if __name__ == "__main__":
    raise SystemExit(main())
