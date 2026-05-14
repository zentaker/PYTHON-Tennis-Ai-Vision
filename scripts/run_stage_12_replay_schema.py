"""Run Stage 12 synthetic rally replay data schema generation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from tennis_vision.friction import calculate_stage_12_friction_score  # noqa: E402
from tennis_vision.replay_camera_presets import build_camera_profiles  # noqa: E402
from tennis_vision.replay_data_builder import (  # noqa: E402
    build_pretty_markdown,
    build_replay_schema,
    load_replay_inputs,
    replay_event_rows,
    replay_keyframe_rows,
)
from tennis_vision.replay_schema import DEFAULT_SCHEMA_VERSION, build_visual_layers, write_csv, write_json  # noqa: E402
from tennis_vision.report import ensure_output_folders, utc_timestamp, write_json_report, write_markdown_report, write_timestamped_log  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 12 synthetic rally replay data schema.")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs" / "replay" / "stage_12_replay_schema")
    parser.add_argument("--schema-version", default=DEFAULT_SCHEMA_VERSION)
    parser.add_argument("--reference-only", action="store_true")
    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def input_paths() -> dict[str, Path]:
    return {
        "stage11_manifest": PROJECT_ROOT / "outputs" / "report_packages" / "stage_11_report_package" / "package_manifest.json",
        "analytical_report_json": PROJECT_ROOT / "outputs" / "reports_final" / "stage_10_analytical_report" / "analytical_report.json",
        "confidence_summary": PROJECT_ROOT / "outputs" / "reports_final" / "stage_10_analytical_report" / "confidence_summary.json",
        "key_findings": PROJECT_ROOT / "outputs" / "reports_final" / "stage_10_analytical_report" / "key_findings.md",
        "tuned_zones": PROJECT_ROOT / "outputs" / "tactical" / "stage_9_1_projection_coverage" / "tuned_ball_zone_assignments.csv",
        "directions": PROJECT_ROOT / "outputs" / "tactical" / "stage_9_1_projection_coverage" / "tuned_shot_direction_estimates.csv",
        "rally_tactical_summary": PROJECT_ROOT / "outputs" / "tactical" / "stage_9_1_projection_coverage" / "tuned_rally_tactical_summary.csv",
        "projected_labels": PROJECT_ROOT / "outputs" / "tactical" / "stage_9_1_projection_coverage" / "projected_expanded_labels.csv",
        "validated_timeline": PROJECT_ROOT / "outputs" / "timeline" / "stage_8_1_timeline_validation" / "validated_event_timeline.csv",
        "expanded_labels": PROJECT_ROOT / "outputs" / "timeline" / "stage_8_1_timeline_validation" / "expanded_ball_labels.csv",
        "event_timeline": PROJECT_ROOT / "outputs" / "timeline" / "stage_8_event_timeline" / "event_timeline.csv",
        "rally_segments": PROJECT_ROOT / "outputs" / "timeline" / "stage_8_event_timeline" / "rally_segments.csv",
        "player_event_attribution": PROJECT_ROOT / "outputs" / "timeline" / "stage_8_event_timeline" / "player_event_attribution.csv",
        "main_players": PROJECT_ROOT / "outputs" / "player_tracking" / "stage_7_1_player_filtering" / "main_players.csv",
        "player_side_states": PROJECT_ROOT / "outputs" / "player_tracking" / "stage_7_1_player_filtering" / "player_side_states.csv",
        "refined_ball_player_distances": PROJECT_ROOT / "outputs" / "player_tracking" / "stage_7_1_player_filtering" / "refined_ball_player_distances.csv",
        "player_identity_profiles": PROJECT_ROOT / "outputs" / "player_tracking" / "stage_7_1_player_filtering" / "player_identity_profiles.json",
        "smoothed_trajectory": PROJECT_ROOT / "outputs" / "ball_tracking" / "stage_6_trajectory_smoothing" / "smoothed_trajectory.csv",
        "raw_trajectory": PROJECT_ROOT / "outputs" / "ball_tracking" / "stage_6_trajectory_smoothing" / "raw_trajectory.csv",
        "trajectory_events": PROJECT_ROOT / "outputs" / "ball_tracking" / "stage_6_trajectory_smoothing" / "trajectory_events.csv",
        "stage3_report": PROJECT_ROOT / "outputs" / "reports" / "stage_3_court_calibration_probe_report.json",
        "calibration_config": PROJECT_ROOT / "configs" / "court_calibration_sample.json",
        "stage1_report": PROJECT_ROOT / "outputs" / "reports" / "stage_1_video_probe_report.json",
    }


def determine_verdict(report: dict[str, Any]) -> str:
    flags = report["flags"]
    core_errors = [
        error
        for error in report.get("errors", [])
        if "analytical_report.json" in error
        or "tuned_ball_zone_assignments.csv" in error
        or "stage_3_court_calibration_probe_report.json" in error
    ]
    if flags["stage11_manifest_missing"] or flags["schema_write_failed"] or core_errors:
        return "blocked"
    if flags["court_model_missing"] or flags["ball_trajectory_missing"]:
        return "needs_more_replay_data"
    if flags["player_data_missing"] or flags["event_timeline_missing"]:
        return "ready_with_warnings"
    return "ready_for_stage_13"


def recommended_next_step(report: dict[str, Any]) -> str:
    if report["final_verdict"] == "ready_for_stage_13":
        return "Proceed to Stage 13: 2D Tactical Replay Renderer."
    if report["final_verdict"] == "needs_more_replay_data":
        return "Regenerate court/trajectory data, then rerun Stage 12."
    if report["final_verdict"] == "blocked":
        return "Fix missing Stage 11 package or schema write blockers, then rerun Stage 12."
    return "Proceed cautiously to Stage 13 or fill missing optional replay context."


def field_block(rows: list[tuple[str, Any]]) -> str:
    lines: list[str] = []
    for key, value in rows:
        lines.append(f"{key}:")
        lines.append(f"  {value if value not in (None, '') else 'Not available'}")
        lines.append("")
    return "\n".join(lines).rstrip()


def bullet_list(items: list[str], empty: str) -> str:
    return empty if not items else "\n".join(f"- {item}" for item in items)


def build_report_sections(report: dict[str, Any]) -> list[tuple[str, str]]:
    return [
        ("VERDICT", field_block([("Final verdict", report["final_verdict"]), ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"), ("Schema version", report["schema_version"])])),
        (
            "SCHEMA SUMMARY",
            field_block(
                [
                    ("Replay keyframes", report["replay_keyframes_count"]),
                    ("Players", report["players_count"]),
                    ("Events", report["event_count"]),
                    ("Rally segments", report["rally_segments_count"]),
                    ("Camera presets", report["camera_presets_count"]),
                    ("Visual layers", report["visual_layers_count"]),
                    ("Confidence level", report["confidence_level"]),
                ]
            ),
        ),
        ("OUTPUTS", "\n".join(f"- {path}" for path in report["output_paths"].values())),
        ("WARNINGS", bullet_list(report["warnings"], "No warnings.")),
        ("ERRORS", bullet_list(report["errors"], "No errors.")),
        ("PRODUCT OWNER INTERPRETATION", "Stage 12 creates the data contract between the analysis pipeline and future replay renderers. It does not render video, generate synthetic images, or hide uncertainty."),
        ("NEXT STEP", report["recommended_next_step"]),
    ]


def update_lab_notebook_safely() -> tuple[dict[str, Path], str | None]:
    try:
        from tennis_vision.lab_notebook import lab_notebook_paths, update_lab_notebook

        update_lab_notebook(PROJECT_ROOT)
        return lab_notebook_paths(PROJECT_ROOT, "stage_12"), None
    except Exception as exc:
        try:
            from tennis_vision.lab_notebook import lab_notebook_paths

            return lab_notebook_paths(PROJECT_ROOT, "stage_12"), f"Lab notebook update failed: {exc}"
        except Exception:
            return {
                "stage_page": PROJECT_ROOT / "docs" / "lab-notebook" / "stage_12_replay_schema.md",
                "experiment_index": PROJECT_ROOT / "docs" / "lab-notebook" / "experiment_index.md",
            }, f"Lab notebook update failed: {exc}"


def print_summary(report: dict[str, Any], lab_paths: dict[str, Path]) -> None:
    rows = [
        ("Verdict", report["final_verdict"]),
        ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"),
        ("Schema version", report["schema_version"]),
        ("Replay keyframes", report["replay_keyframes_count"]),
        ("Players", report["players_count"]),
        ("Events", report["event_count"]),
        ("Rally segments", report["rally_segments_count"]),
        ("Camera presets", report["camera_presets_count"]),
        ("Visual layers", report["visual_layers_count"]),
        ("Replay schema", report["output_paths"]["replay_schema_json"]),
        ("Lab notebook", lab_paths["stage_page"]),
        ("Recommended next step", report["recommended_next_step"]),
    ]
    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(title="Stage 12 Replay Schema")
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")
        for field, value in rows:
            table.add_row(str(field), str(value))
        Console().print(table)
    except ImportError:
        print("Stage 12 Replay Schema")
        for field, value in rows:
            print(f"{field}: {value}")


def main() -> int:
    args = parse_args()
    ensure_output_folders(PROJECT_ROOT)
    timestamp = utc_timestamp()
    output_dir = resolve_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = input_paths()
    data = load_replay_inputs(paths)
    warnings = list(data["warnings"])
    errors = list(data["errors"])
    schema = build_replay_schema(data=data, paths=paths, generated_at=timestamp, schema_version=args.schema_version)

    replay_schema_json = output_dir / "replay_schema.json"
    pretty_md = output_dir / "replay_schema_pretty.md"
    keyframes_csv = output_dir / "replay_keyframes.csv"
    events_csv = output_dir / "replay_events.csv"
    players_json = output_dir / "replay_players.json"
    cameras_json = output_dir / "replay_camera_presets.json"
    manifest_json = output_dir / "replay_manifest.json"
    output_paths = {
        "replay_schema_json": str(replay_schema_json),
        "replay_schema_pretty_md": str(pretty_md),
        "replay_keyframes_csv": str(keyframes_csv),
        "replay_events_csv": str(events_csv),
        "replay_players_json": str(players_json),
        "replay_camera_presets_json": str(cameras_json),
        "replay_manifest_json": str(manifest_json),
    }
    flags = {
        "stage11_manifest_missing": not paths["stage11_manifest"].exists(),
        "court_model_missing": not schema["court_model"]["homography_status"]["computed"],
        "ball_trajectory_missing": len(schema["ball_trajectory"]["replay_keyframes"]) == 0,
        "player_data_missing": len(schema["players"]) == 0,
        "event_timeline_missing": len(schema["event_timeline"]) == 0,
        "camera_presets_missing": len(schema["camera_profiles"]) == 0,
        "schema_write_failed": False,
    }
    friction = calculate_stage_12_friction_score(**flags, warnings_count=len(warnings), errors_count=len(errors))
    stub = {
        "flags": flags,
        "errors": errors,
        "final_verdict": "blocked",
    }
    stub["final_verdict"] = determine_verdict(stub)
    stub["recommended_next_step"] = recommended_next_step(stub)

    try:
        write_json(replay_schema_json, schema)
        pretty_md.write_text(build_pretty_markdown(schema=schema, verdict=stub["final_verdict"], friction=friction, next_step=stub["recommended_next_step"]), encoding="utf-8")
        write_csv(
            keyframes_csv,
            replay_keyframe_rows(schema),
            ["frame_index", "timestamp_seconds", "image_x", "image_y", "projected_x", "projected_y", "zone", "depth", "lateral_lane", "source", "confidence_like_score", "is_interpolated", "notes"],
        )
        write_csv(
            events_csv,
            replay_event_rows(schema),
            ["event_id", "frame_index", "timestamp_seconds", "event_type", "possible_event", "player_id", "side_state", "ball_x", "ball_y", "projected_x", "projected_y", "validation_status", "confidence_like_score", "reason"],
        )
        write_json(players_json, schema["players"])
        write_json(cameras_json, build_camera_profiles())
        write_json(
            manifest_json,
            {
                "generated_at": timestamp,
                "stage": "stage_12_replay_schema",
                "schema_version": args.schema_version,
                "schema_name": schema["metadata"]["schema_name"],
                "replay_keyframes_count": len(schema["ball_trajectory"]["replay_keyframes"]),
                "players_count": len(schema["players"]),
                "event_count": len(schema["event_timeline"]),
                "rally_segments_count": len(schema["rally_segments"]),
                "camera_presets_count": len(schema["camera_profiles"]),
                "visual_layers_count": len(schema["visual_layers"]),
                "confidence_level": schema["confidence"]["confidence_level"],
                "output_paths": output_paths,
                "source_artifacts": schema["source_artifacts"],
                "warnings": warnings,
                "errors": errors,
                "reference_only": args.reference_only,
            },
        )
    except OSError as exc:
        flags["schema_write_failed"] = True
        errors.append(f"Replay schema write failed: {exc}")

    friction = calculate_stage_12_friction_score(**flags, warnings_count=len(warnings), errors_count=len(errors))
    report: dict[str, Any] = {
        "timestamp": timestamp,
        "stage": "stage_12_replay_schema",
        "schema_version": args.schema_version,
        "replay_schema_path": str(replay_schema_json),
        "replay_keyframes_count": len(schema["ball_trajectory"]["replay_keyframes"]),
        "players_count": len(schema["players"]),
        "event_count": len(schema["event_timeline"]),
        "rally_segments_count": len(schema["rally_segments"]),
        "camera_presets_count": len(schema["camera_profiles"]),
        "visual_layers_count": len(schema["visual_layers"]),
        "confidence_level": schema["confidence"]["confidence_level"],
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
    log_path = write_timestamped_log(
        PROJECT_ROOT,
        "stage_12_replay_schema",
        [
            f"timestamp={timestamp}",
            f"verdict={report['final_verdict']}",
            f"friction={friction['score']} ({friction['band']})",
            f"schema_version={args.schema_version}",
            f"keyframes={report['replay_keyframes_count']}",
            f"players={report['players_count']}",
            f"events={report['event_count']}",
        ],
    )
    report["log_path"] = str(log_path)
    report["json_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_12_replay_schema_report.json")
    report["markdown_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_12_replay_schema_report.md")
    write_json_report(Path(report["json_report_path"]), report)
    write_markdown_report(Path(report["markdown_report_path"]), "Stage 12 Replay Schema Report", build_report_sections(report))

    lab_paths, notebook_warning = update_lab_notebook_safely()
    if notebook_warning:
        report["warnings"].append(notebook_warning)
        write_json_report(Path(report["json_report_path"]), report)
        write_markdown_report(Path(report["markdown_report_path"]), "Stage 12 Replay Schema Report", build_report_sections(report))
        print(f"Warning: {notebook_warning}")
    print_summary(report, lab_paths)
    return 1 if report["final_verdict"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
