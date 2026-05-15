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

from tennis_vision.ball_flight_estimator import build_side_view_keyframes, downgrade_implausible_hits  # noqa: E402
from tennis_vision.baseline_quarantine import annotate_report_with_failed_baseline_warning, failed_baseline_block_message, is_old_replay_schema, print_failed_baseline_warning  # noqa: E402
from tennis_vision.friction import calculate_stage_14_1_friction_score, calculate_stage_14_2_friction_score, calculate_stage_14_3_friction_score, calculate_stage_14_friction_score  # noqa: E402
from tennis_vision.replay_renderer_side_view import (  # noqa: E402
    create_semantic_debug_image,
    create_side_contact_sheet,
    create_validated_events_debug_image,
    export_side_view_video,
    load_replay_schema,
    render_side_view_frames,
    write_side_view_manifest,
)
from tennis_vision.report import ensure_output_folders, utc_timestamp, write_json_report, write_markdown_report, write_timestamped_log  # noqa: E402
from tennis_vision.validated_event_source import load_validated_event_source, summarize_validated_render_events  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 14 side-view ball flight replay renderer.")
    parser.add_argument("--schema", type=Path, default=PROJECT_ROOT / "outputs" / "replay" / "stage_12_replay_schema" / "replay_schema.json")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs" / "replay" / "stage_14_side_view_replay")
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--interpolate", dest="interpolate", action="store_true", default=True)
    parser.add_argument("--no-interpolate", dest="interpolate", action="store_false")
    parser.add_argument("--interpolation-steps", type=int, default=8)
    parser.add_argument("--no-video", action="store_true")
    parser.add_argument("--validated-events", type=Path, default=PROJECT_ROOT / "outputs" / "timeline" / "stage_8_3_event_validation" / "validated_event_timeline.csv")
    parser.add_argument("--allow-failed-baseline", action="store_true", help="Allow rendering from the failed baseline replay schema for explicit research only.")
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


def determine_event_patch_verdict(report: dict[str, Any]) -> str:
    flags = report["flags"]
    if flags["replay_schema_missing"]:
        return "blocked"
    if (
        flags["player_aware_hit_validation_failed"]
        or flags["implausible_hit_downgrade_failed"]
        or flags["render_role_assignment_failed"]
        or flags["semantic_debug_generation_failed"]
    ):
        return "needs_more_event_disambiguation"
    if flags["render_frames_failed"]:
        return "blocked"
    if flags["video_export_failed"] or report["warnings"]:
        return "ready_with_warnings"
    return "ready_for_stage_15"


def recommended_event_patch_next_step(report: dict[str, Any]) -> str:
    if report["final_verdict"] == "ready_for_stage_15":
        return "Proceed to Stage 15: Multi-Camera Analytical Replay."
    if report["final_verdict"] == "needs_more_event_disambiguation":
        return "Tune side-view event disambiguation before Stage 15."
    if report["final_verdict"] == "ready_with_warnings":
        return "Review side-view semantic warnings, then proceed to Stage 15 or Stage 14.3 tuning."
    return "Fix Stage 14.2 blockers, then rerun the side-view patch."


def determine_validated_events_verdict(report: dict[str, Any]) -> str:
    """Return Stage 14.3 verdict from validated-event rendering flags."""
    flags = report["flags"]
    if flags["replay_schema_missing"] or flags["render_frames_failed"]:
        return "blocked"
    if flags["downgraded_hits_rendered_as_physical"]:
        return "needs_more_side_view_tuning"
    if not report["validated_event_source_available"]:
        return "ready_with_warnings" if report["event_source_used"] != "missing" else "blocked"
    if report["validated_hits_rendered_count"] == 0:
        return "ready_with_warnings"
    if flags["video_export_failed"] or report["warnings"]:
        return "ready_with_warnings"
    return "ready_for_stage_15"


def recommended_validated_events_next_step(report: dict[str, Any]) -> str:
    """Return Stage 14.3 next step text."""
    if report["final_verdict"] == "ready_for_stage_15":
        return "Proceed to Stage 15: Multi-Camera Analytical Replay."
    if report["final_verdict"] == "ready_with_warnings" and report["validated_hits_rendered_count"] == 0:
        return "Proceed to Stage 15 for multi-camera prototype, or collect manual hit labels before showing confident side-view hit markers."
    if report["final_verdict"] == "needs_more_side_view_tuning":
        return "Tune the side-view renderer so downgraded hits remain annotations only."
    if report["event_source_used"] == "missing":
        return "Regenerate Stage 8.3 event validation or a fallback event timeline, then rerun Stage 14.3."
    return "Fix Stage 14.3 blockers, then rerun the side-view renderer."


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
        "EVENT DISAMBIGUATION PATCH",
        "  Hit labels are now filtered by player-aware plausibility.",
        f"  Implausible hit labels downgraded: {report.get('implausible_hits_downgraded_count', 0)}",
        "  Bounce events remain grounded.",
        "  Player interaction cues are visually separated from hit and bounce labels.",
        "  Synthetic height is still estimated, not measured.",
        "",
        "VALIDATED EVENT SOURCE PATCH",
        f"  Event source used: {report.get('event_source_used', 'Not available')}",
        f"  Validated bounces rendered: {report.get('validated_bounces_rendered_count', 0)}",
        f"  Validated hits rendered: {report.get('validated_hits_rendered_count', 0)}",
        f"  Downgraded hits shown as annotation: {report.get('downgraded_hits_annotation_count', 0)}",
        "  Rejected, unvalidated, and downgraded events are not physical ball-contact markers.",
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


def build_event_patch_report_sections(report: dict[str, Any]) -> list[tuple[str, str]]:
    return [
        ("VERDICT", field_block([("Final verdict", report["final_verdict"]), ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"), ("Patch applied", report["event_disambiguation_patch_applied"])])),
        ("WHY THIS PATCH EXISTS", "The previous side-view replay could label some implausible in-court events as hits even when player position did not support that contact location."),
        (
            "PATCH BEHAVIOR",
            field_block(
                [
                    ("Player-aware hit validation", report["player_aware_hit_validation_enabled"]),
                    ("Event render roles", report["event_render_roles_enabled"]),
                    ("Implausible hit downgrade", report["implausible_hits_downgraded_count"]),
                    ("Bounce preservation", report["plausible_bounces_count"]),
                    ("Interaction cue separation", report["player_interactions_count"]),
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
        ("PRODUCT OWNER INTERPRETATION", "The side-view should now be more readable as a tennis exchange because raw possible_hit labels are no longer rendered as hits when the attributed player is too far away in court depth. Ambiguous cues remain visible as uncertain or interaction markers."),
        ("WARNINGS", bullet_list(report["warnings"], "No warnings.")),
        ("ERRORS", bullet_list(report["errors"], "No errors.")),
        ("NEXT STEP", report["recommended_next_step"]),
    ]


def build_validated_events_report_sections(report: dict[str, Any]) -> list[tuple[str, str]]:
    """Build plain-text-friendly Stage 14.3 report sections."""
    return [
        ("VERDICT", field_block([("Final verdict", report["final_verdict"]), ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"), ("Event source used", report["event_source_used"])])),
        (
            "VALIDATED EVENT SOURCE",
            field_block(
                [
                    ("Stage 8.3 available", report["validated_event_source_available"]),
                    ("Source path", report["event_source_path"]),
                    ("Fallback used", report["fallback_used"]),
                ]
            ),
        ),
        (
            "RENDERING BEHAVIOR",
            field_block(
                [
                    ("Validated bounces rendered", report["validated_bounces_rendered_count"]),
                    ("Validated hits rendered", report["validated_hits_rendered_count"]),
                    ("Downgraded hits shown as annotation", report["downgraded_hits_annotation_count"]),
                    ("Rejected events ignored", report["rejected_events_ignored_count"]),
                    ("Unvalidated events shown as annotation", report["unvalidated_events_annotation_count"]),
                    ("Main path physical-only", report["main_path_physical_events_only"]),
                    ("Annotation band enabled", report["annotation_band_enabled"]),
                ]
            ),
        ),
        ("WHY THIS PATCH EXISTS", "Previous side-view versions rendered raw possible_hit hypotheses too strongly. Stage 8.3 now provides validated and reclassified event semantics, so the side-view uses that layer before drawing physical contact markers."),
        ("LIMITATIONS", "- no validated hit labels yet\n- no true 3D height\n- side-view is still synthetic\n- bounces are validated from manual labels\n- hits remain unconfirmed until manually labeled"),
        ("WARNINGS", bullet_list(report["warnings"], "No warnings.")),
        ("ERRORS", bullet_list(report["errors"], "No errors.")),
        ("NEXT STEP", report["recommended_next_step"]),
    ]


def update_lab_notebook_safely() -> tuple[dict[str, Path], str | None]:
    try:
        from tennis_vision.lab_notebook import lab_notebook_paths, update_lab_notebook

        update_lab_notebook(PROJECT_ROOT)
        return lab_notebook_paths(PROJECT_ROOT, "stage_14_3"), None
    except Exception as exc:
        try:
            from tennis_vision.lab_notebook import lab_notebook_paths

            return lab_notebook_paths(PROJECT_ROOT, "stage_14_3"), f"Lab notebook update failed: {exc}"
        except Exception:
            return {
                "stage_page": PROJECT_ROOT / "docs" / "lab-notebook" / "stage_14_3_validated_events_side_view.md",
                "experiment_index": PROJECT_ROOT / "docs" / "lab-notebook" / "experiment_index.md",
            }, f"Lab notebook update failed: {exc}"


def print_summary(report: dict[str, Any], lab_paths: dict[str, Path]) -> None:
    rows = [
        ("Verdict", report["final_verdict"]),
        ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"),
        ("Event source used", report.get("event_source_used", "")),
        ("Stage 8.3 available", report.get("validated_event_source_available", False)),
        ("Validated bounces rendered", report.get("validated_bounces_rendered_count", 0)),
        ("Validated hits rendered", report.get("validated_hits_rendered_count", 0)),
        ("Downgraded hit annotations", report.get("downgraded_hits_annotation_count", 0)),
        ("Rejected events ignored", report.get("rejected_events_ignored_count", 0)),
        ("Unvalidated annotations", report.get("unvalidated_events_annotation_count", 0)),
        ("Frames generated", report["frames_generated"]),
        ("Video generated", report["video_generated"]),
        ("Validated debug", report.get("validated_events_debug_path", "")),
        ("Manifest", report.get("manifest_path") or report.get("output_paths", {}).get("manifest_path", "")),
        ("Lab notebook", lab_paths["stage_page"]),
        ("Recommended next step", report["recommended_next_step"]),
    ]
    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(title="Stage 14.3 Side-View Validated Events")
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")
        for field, value in rows:
            table.add_row(str(field), str(value))
        Console().print(table)
    except ImportError:
        print("Stage 14.3 Side-View Validated Events")
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
    validated_events_path = resolve_path(args.validated_events)
    output_dir.mkdir(parents=True, exist_ok=True)

    schema, warnings, errors = load_replay_schema(schema_path)
    schema_version = schema.get("metadata", {}).get("schema_version") if schema else None
    keyframes = list(schema.get("ball_trajectory", {}).get("replay_keyframes", [])) if schema else []
    events = list(schema.get("event_timeline", [])) if schema else []
    players = list(schema.get("players", [])) if schema else []
    event_source = load_validated_event_source(PROJECT_ROOT, schema, preferred_path=validated_events_path) if schema else {
        "events": [],
        "event_source_used": "missing",
        "event_source_path": "",
        "event_source_priority": [],
        "validated_event_source_available": False,
        "fallback_used": False,
        "warnings": [],
        "errors": [],
        "summary": summarize_validated_render_events([]),
    }
    warnings.extend(event_source.get("warnings", []))
    errors.extend(event_source.get("errors", []))
    enriched_events = event_source.get("events", [])
    event_role_summary = event_source.get("summary", summarize_validated_render_events(enriched_events))
    if not enriched_events:
        enriched_events, event_role_summary = downgrade_implausible_hits(events, players)
    side_view_keyframes = build_side_view_keyframes(schema, event_rows=enriched_events) if schema else []

    frame_paths: list[Path] = []
    render_context: dict[str, Any] = {"side_view_keyframes": side_view_keyframes, "display_points": [], "players": players, "events": enriched_events, "event_render_role_summary": event_role_summary}
    if schema and side_view_keyframes:
        frame_paths, render_context, frame_warnings, frame_errors = render_side_view_frames(
            schema=schema,
            output_dir=output_dir,
            interpolate=args.interpolate,
            interpolation_steps=args.interpolation_steps,
            event_rows=enriched_events,
        )
        warnings.extend(frame_warnings)
        errors.extend(frame_errors)
        event_role_summary = render_context.get("event_render_role_summary", event_role_summary) or summarize_validated_render_events(render_context.get("events", []))
        enriched_events = render_context.get("events", enriched_events)

    frames_dir = output_dir / "frames"
    video_path = output_dir / "side_view_replay.mp4"
    contact_sheet_path = output_dir / "side_view_contact_sheet.jpg"
    final_frame_path = output_dir / "side_view_final_frame.jpg"
    arc_preview_path = output_dir / "side_view_arc_preview.jpg"
    semantic_debug_path = output_dir / "side_view_semantic_debug.jpg"
    validated_events_debug_path = output_dir / "side_view_validated_events_debug.jpg"
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
    validated_events_debug_generated = False
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
        validated_events_debug_generated, validated_debug_warnings = create_validated_events_debug_image(
            schema=schema,
            display_points=render_context.get("display_points", []),
            events=render_context.get("events", []),
            players=render_context.get("players", []),
            output_path=validated_events_debug_path,
            event_source_used=event_source.get("event_source_used", "missing"),
        )
        warnings.extend(validated_debug_warnings)

    output_paths = {
        "frames_dir": str(frames_dir),
        "video_path": str(video_path),
        "contact_sheet_path": str(contact_sheet_path),
        "final_frame_path": str(final_frame_path),
        "arc_preview_path": str(arc_preview_path),
        "semantic_debug_path": str(semantic_debug_path),
        "validated_events_debug_path": str(validated_events_debug_path),
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
    event_patch_flags = {
        "replay_schema_missing": not bool(schema),
        "player_data_missing": len(players) == 0,
        "player_aware_hit_validation_failed": not validate_player_aware_hit_validation(enriched_events, players),
        "implausible_hit_downgrade_failed": not validate_implausible_hit_downgrade(enriched_events),
        "render_role_assignment_failed": not validate_render_role_assignment(enriched_events),
        "semantic_debug_generation_failed": bool(frame_paths and not semantic_debug_generated),
        "render_frames_failed": len(frame_paths) == 0,
        "video_export_failed": bool(frame_paths and not args.no_video and not video_generated),
    }
    validated_event_flags = {
        "replay_schema_missing": not bool(schema),
        "event_source_missing": event_source.get("event_source_used") == "missing",
        "validated_event_source_missing": not bool(event_source.get("validated_event_source_available")),
        "render_frames_failed": len(frame_paths) == 0,
        "video_export_failed": bool(frame_paths and not args.no_video and not video_generated),
        "validated_debug_generation_failed": bool(frame_paths and not validated_events_debug_generated),
        "downgraded_hits_rendered_as_physical": downgraded_hits_rendered_as_physical(enriched_events),
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
        "player_aware_hit_validation_enabled": True,
        "event_render_roles_enabled": True,
        "implausible_hits_downgraded_count": event_role_summary.get("implausible_hits_downgraded_count", 0),
        "plausible_hits_count": event_role_summary.get("plausible_hits_count", 0),
        "plausible_bounces_count": event_role_summary.get("plausible_bounces_count", 0),
        "uncertain_events_count": event_role_summary.get("uncertain_events_count", 0),
        "player_interactions_count": event_role_summary.get("player_interactions_count", 0),
        "event_source_used": event_source.get("event_source_used", "missing"),
        "validated_event_source_available": event_source.get("validated_event_source_available", False),
        "fallback_used": event_source.get("fallback_used", False),
        "validated_bounces_rendered_count": event_role_summary.get("validated_bounces_rendered_count", event_role_summary.get("plausible_bounces_count", 0)),
        "validated_hits_rendered_count": event_role_summary.get("validated_hits_rendered_count", event_role_summary.get("plausible_hits_count", 0)),
        "downgraded_hits_annotation_count": event_role_summary.get("downgraded_hits_annotation_count", event_role_summary.get("implausible_hits_downgraded_count", 0)),
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
                "player_aware_hit_validation_enabled": True,
                "event_render_roles_enabled": True,
                "implausible_hits_downgraded_count": event_role_summary.get("implausible_hits_downgraded_count", 0),
                "plausible_hits_count": event_role_summary.get("plausible_hits_count", 0),
                "plausible_bounces_count": event_role_summary.get("plausible_bounces_count", 0),
                "uncertain_events_count": event_role_summary.get("uncertain_events_count", 0),
                "validated_event_source_used": bool(event_source.get("validated_event_source_available")),
                "event_source_path": event_source.get("event_source_path", ""),
                "event_source_priority": event_source.get("event_source_priority", []),
                "validated_bounces_rendered_count": event_role_summary.get("validated_bounces_rendered_count", 0),
                "validated_hits_rendered_count": event_role_summary.get("validated_hits_rendered_count", 0),
                "downgraded_hits_annotation_count": event_role_summary.get("downgraded_hits_annotation_count", 0),
                "rejected_events_ignored_count": event_role_summary.get("rejected_events_ignored_count", 0),
                "unvalidated_events_annotation_count": event_role_summary.get("unvalidated_events_annotation_count", 0),
                "main_path_physical_events_only": True,
                "annotation_band_enabled": True,
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
    if is_old_replay_schema(schema_path):
        annotate_report_with_failed_baseline_warning(report)
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
    if is_old_replay_schema(schema_path):
        annotate_report_with_failed_baseline_warning(patch_report)

    event_patch_friction = calculate_stage_14_2_friction_score(**event_patch_flags, warnings_count=len(warnings), errors_count=len(errors))
    event_patch_report: dict[str, Any] = {
        "timestamp": timestamp,
        "stage": "stage_14_2_side_view_event_disambiguation",
        "source_stage": 14.1,
        "event_disambiguation_patch_applied": True,
        "player_aware_hit_validation_enabled": True,
        "event_render_roles_enabled": True,
        "implausible_hits_downgraded_count": event_role_summary.get("implausible_hits_downgraded_count", 0),
        "plausible_hits_count": event_role_summary.get("plausible_hits_count", 0),
        "plausible_bounces_count": event_role_summary.get("plausible_bounces_count", 0),
        "uncertain_events_count": event_role_summary.get("uncertain_events_count", 0),
        "player_interactions_count": event_role_summary.get("player_interactions_count", 0),
        "frames_generated": len(frame_paths),
        "video_generated": video_generated,
        "semantic_debug_artifact": str(semantic_debug_path) if semantic_debug_path.exists() else "",
        "warnings": warnings,
        "errors": errors,
        "flags": event_patch_flags,
        "friction": event_patch_friction,
        "final_verdict": "blocked",
        "recommended_next_step": "",
        "output_paths": output_paths,
        "event_render_role_summary": event_role_summary,
        "semantic_warnings": semantic_warnings(side_view_keyframes),
    }
    event_patch_report["final_verdict"] = determine_event_patch_verdict(event_patch_report)
    event_patch_report["recommended_next_step"] = recommended_event_patch_next_step(event_patch_report)
    if is_old_replay_schema(schema_path):
        annotate_report_with_failed_baseline_warning(event_patch_report)

    validated_event_friction = calculate_stage_14_3_friction_score(**validated_event_flags, warnings_count=len(warnings), errors_count=len(errors))
    validated_event_report: dict[str, Any] = {
        "timestamp": timestamp,
        "stage": "stage_14_3_validated_events_side_view",
        "source_stage": "8.3",
        "event_source_used": event_source.get("event_source_used", "missing"),
        "event_source_path": event_source.get("event_source_path", ""),
        "event_source_priority": event_source.get("event_source_priority", []),
        "validated_event_source_available": bool(event_source.get("validated_event_source_available")),
        "fallback_used": bool(event_source.get("fallback_used")),
        "validated_bounces_rendered_count": event_role_summary.get("validated_bounces_rendered_count", 0),
        "validated_hits_rendered_count": event_role_summary.get("validated_hits_rendered_count", 0),
        "downgraded_hits_annotation_count": event_role_summary.get("downgraded_hits_annotation_count", 0),
        "rejected_events_ignored_count": event_role_summary.get("rejected_events_ignored_count", 0),
        "unvalidated_events_annotation_count": event_role_summary.get("unvalidated_events_annotation_count", 0),
        "main_path_physical_events_only": True,
        "annotation_band_enabled": True,
        "frames_generated": len(frame_paths),
        "video_generated": video_generated,
        "validated_events_debug_path": str(validated_events_debug_path) if validated_events_debug_path.exists() else "",
        "warnings": warnings,
        "errors": errors,
        "flags": validated_event_flags,
        "friction": validated_event_friction,
        "final_verdict": "blocked",
        "recommended_next_step": "",
        "output_paths": output_paths,
    }
    if validated_event_report["validated_hits_rendered_count"] == 0:
        validated_event_report["warnings"] = list(dict.fromkeys(validated_event_report["warnings"] + ["No validated hit labels are available yet; confident hit markers are not rendered."]))
        validated_event_report["friction"] = calculate_stage_14_3_friction_score(**validated_event_flags, warnings_count=len(validated_event_report["warnings"]), errors_count=len(errors))
    validated_event_report["final_verdict"] = determine_validated_events_verdict(validated_event_report)
    validated_event_report["recommended_next_step"] = recommended_validated_events_next_step(validated_event_report)
    if is_old_replay_schema(schema_path):
        annotate_report_with_failed_baseline_warning(validated_event_report)

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
    event_patch_report["json_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_14_2_side_view_event_disambiguation_report.json")
    event_patch_report["markdown_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_14_2_side_view_event_disambiguation_report.md")
    write_json_report(Path(event_patch_report["json_report_path"]), event_patch_report)
    write_markdown_report(Path(event_patch_report["markdown_report_path"]), "Stage 14.2 Side-View Event Disambiguation Report", build_event_patch_report_sections(event_patch_report))
    validated_event_report["json_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_14_3_validated_events_side_view_report.json")
    validated_event_report["markdown_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_14_3_validated_events_side_view_report.md")
    write_json_report(Path(validated_event_report["json_report_path"]), validated_event_report)
    write_markdown_report(Path(validated_event_report["markdown_report_path"]), "Stage 14.3 Side-View Replay with Validated Events Report", build_validated_events_report_sections(validated_event_report))

    lab_paths, notebook_warning = update_lab_notebook_safely()
    if notebook_warning:
        report["warnings"].append(notebook_warning)
        patch_report["warnings"].append(notebook_warning)
        event_patch_report["warnings"].append(notebook_warning)
        validated_event_report["warnings"].append(notebook_warning)
        write_json_report(Path(report["json_report_path"]), report)
        write_markdown_report(Path(report["markdown_report_path"]), "Stage 14 Side-View Ball Flight Renderer Report", build_report_sections(report))
        write_json_report(Path(patch_report["json_report_path"]), patch_report)
        write_markdown_report(Path(patch_report["markdown_report_path"]), "Stage 14.1 Side-View Height Semantics Patch Report", build_patch_report_sections(patch_report))
        write_json_report(Path(event_patch_report["json_report_path"]), event_patch_report)
        write_markdown_report(Path(event_patch_report["markdown_report_path"]), "Stage 14.2 Side-View Event Disambiguation Report", build_event_patch_report_sections(event_patch_report))
        write_json_report(Path(validated_event_report["json_report_path"]), validated_event_report)
        write_markdown_report(Path(validated_event_report["markdown_report_path"]), "Stage 14.3 Side-View Replay with Validated Events Report", build_validated_events_report_sections(validated_event_report))
        print(f"Warning: {notebook_warning}")
    print_summary(validated_event_report, lab_paths)
    return 1 if validated_event_report["final_verdict"] == "blocked" else 0


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


def validate_player_aware_hit_validation(events: list[dict[str, Any]], players: list[dict[str, Any]]) -> bool:
    raw_hits = [event for event in events if "hit" in str(event.get("event_type") or "").lower()]
    if not raw_hits:
        return True
    if not players:
        return False
    return all(event.get("player_aware_plausibility_status") in {"plausible", "implausible", "validated", "not_physical"} for event in raw_hits)


def validate_implausible_hit_downgrade(events: list[dict[str, Any]]) -> bool:
    for event in events:
        raw_type = str(event.get("event_type") or "").lower()
        if "hit" not in raw_type:
            continue
        if event.get("player_aware_plausibility_status") == "implausible" and event.get("render_role") == "hit_plausible":
            return False
    return True


def validate_render_role_assignment(events: list[dict[str, Any]]) -> bool:
    valid_roles = {"hit_plausible", "bounce_plausible", "player_interaction", "uncertain_event", "interpolation_only", "rejected_event", "trajectory_annotation"}
    return all(str(event.get("render_role") or "") in valid_roles for event in events)


def downgraded_hits_rendered_as_physical(events: list[dict[str, Any]]) -> bool:
    """Return true if a downgraded/unvalidated hit would be rendered as a physical hit."""
    for event in events:
        raw_type = str(event.get("raw_event_type") or event.get("event_type") or "").lower()
        role = str(event.get("render_role") or "").lower()
        validated_type = str(event.get("validated_event_type") or event.get("event_type") or "").lower()
        if "hit" in raw_type and role == "hit_plausible" and "validated" not in validated_type and event.get("side_view_physical_event"):
            return True
    return False


if __name__ == "__main__":
    raise SystemExit(main())
