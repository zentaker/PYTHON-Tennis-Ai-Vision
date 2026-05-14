"""Run Stage 10 analytical report and coaching summary prototype."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from tennis_vision.analytical_report import (  # noqa: E402
    build_analysis_summary,
    build_plain_language_report,
    read_stage_inputs,
    write_report_json,
    write_report_markdown,
)
from tennis_vision.coaching_summary import build_coaching_observations, build_key_findings, write_coaching_summary, write_key_findings  # noqa: E402
from tennis_vision.friction import calculate_stage_10_friction_score  # noqa: E402
from tennis_vision.report import ensure_output_folders, utc_timestamp, write_json_report, write_markdown_report, write_timestamped_log  # noqa: E402
from tennis_vision.report_confidence import evaluate_report_confidence  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 10 analytical report and coaching summary prototype.")
    parser.add_argument("--tactical-zones", type=Path, default=PROJECT_ROOT / "outputs" / "tactical" / "stage_9_1_projection_coverage" / "tuned_ball_zone_assignments.csv")
    parser.add_argument("--directions", type=Path, default=PROJECT_ROOT / "outputs" / "tactical" / "stage_9_1_projection_coverage" / "tuned_shot_direction_estimates.csv")
    parser.add_argument("--rally-summary", type=Path, default=PROJECT_ROOT / "outputs" / "tactical" / "stage_9_1_projection_coverage" / "tuned_rally_tactical_summary.csv")
    parser.add_argument("--timeline", type=Path, default=PROJECT_ROOT / "outputs" / "timeline" / "stage_8_1_timeline_validation" / "validated_event_timeline.csv")
    parser.add_argument("--players", type=Path, default=PROJECT_ROOT / "outputs" / "player_tracking" / "stage_7_1_player_filtering" / "main_players.csv")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs" / "reports_final" / "stage_10_analytical_report")
    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def default_input_paths(args: argparse.Namespace) -> dict[str, Path]:
    """Build Stage 10 input path map."""
    return {
        "tactical_zones": resolve_path(args.tactical_zones),
        "directions": resolve_path(args.directions),
        "rally_summary": resolve_path(args.rally_summary),
        "validated_timeline": resolve_path(args.timeline),
        "main_players": resolve_path(args.players),
        "expanded_labels": PROJECT_ROOT / "outputs" / "timeline" / "stage_8_1_timeline_validation" / "expanded_ball_labels.csv",
        "expanded_candidate_validation": PROJECT_ROOT / "outputs" / "timeline" / "stage_8_1_timeline_validation" / "expanded_candidate_validation.csv",
        "event_timeline": PROJECT_ROOT / "outputs" / "timeline" / "stage_8_event_timeline" / "event_timeline.csv",
        "rally_segments": PROJECT_ROOT / "outputs" / "timeline" / "stage_8_event_timeline" / "rally_segments.csv",
        "player_event_attribution": PROJECT_ROOT / "outputs" / "timeline" / "stage_8_event_timeline" / "player_event_attribution.csv",
        "player_side_states": PROJECT_ROOT / "outputs" / "player_tracking" / "stage_7_1_player_filtering" / "player_side_states.csv",
        "refined_player_distances": PROJECT_ROOT / "outputs" / "player_tracking" / "stage_7_1_player_filtering" / "refined_ball_player_distances.csv",
        "smoothed_trajectory": PROJECT_ROOT / "outputs" / "ball_tracking" / "stage_6_trajectory_smoothing" / "smoothed_trajectory.csv",
        "trajectory_events": PROJECT_ROOT / "outputs" / "ball_tracking" / "stage_6_trajectory_smoothing" / "trajectory_events.csv",
        "stage_9_tactical_summary": PROJECT_ROOT / "outputs" / "tactical" / "stage_9_tactical_metrics" / "tactical_summary.md",
        "tuned_ball_placement_map": PROJECT_ROOT / "outputs" / "tactical" / "stage_9_1_projection_coverage" / "tuned_ball_placement_map.jpg",
        "projection_coverage_map": PROJECT_ROOT / "outputs" / "tactical" / "stage_9_1_projection_coverage" / "projection_coverage_map.jpg",
        "timeline_preview": PROJECT_ROOT / "outputs" / "timeline" / "stage_8_event_timeline" / "timeline_preview.jpg",
        "court_timeline_preview": PROJECT_ROOT / "outputs" / "timeline" / "stage_8_event_timeline" / "court_timeline_preview.jpg",
        "player_interaction_preview": PROJECT_ROOT / "outputs" / "player_tracking" / "stage_7_player_interaction" / "player_interaction_preview.jpg",
    }


def determine_verdict(report: dict[str, Any]) -> str:
    if report["flags"]["tactical_data_missing"] or report["flags"]["report_generation_failed"]:
        return "blocked"
    if report["flags"]["sparse_data"] or report["flags"]["low_confidence"]:
        return "needs_more_validation"
    if report["confidence_level"] == "medium-high" and report["unknown_zone_count"] == 0:
        return "ready_for_stage_11"
    return "ready_with_warnings"


def recommended_next_step(report: dict[str, Any]) -> str:
    if report["final_verdict"] == "ready_for_stage_11":
        return "Proceed to Stage 11: Annotated Highlight/Report Package Generator."
    if report["final_verdict"] == "needs_more_validation":
        return "Tune report wording in Stage 10.1 or validate more events before packaging."
    if report["final_verdict"] == "blocked":
        return "Fix missing Stage 9.1 tactical outputs, then rerun Stage 10."
    return "Proceed cautiously to Stage 11 or Stage 10.1 wording/confidence tuning."


def field_block(rows: list[tuple[str, Any]]) -> str:
    lines: list[str] = []
    for key, value in rows:
        lines.append(f"{key}:")
        lines.append(f"  {value if value not in (None, '') else 'Not available'}")
        lines.append("")
    return "\n".join(lines).rstrip()


def bullet_list(items: list[str], empty: str) -> str:
    return empty if not items else "\n".join(f"- {item}" for item in items)


def write_visual_references(path: Path, input_paths: dict[str, str]) -> Path:
    lines = [
        "# Stage 10 Visual References",
        "",
        "These files are referenced rather than copied.",
        "",
    ]
    for key in ("tuned_ball_placement_map", "projection_coverage_map", "timeline_preview", "court_timeline_preview", "player_interaction_preview"):
        value = input_paths.get(key)
        lines.append(f"{key}:")
        lines.append(f"  {value if value else 'Not available'}")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def build_pipeline_markdown_sections(report: dict[str, Any]) -> list[tuple[str, str]]:
    return [
        ("VERDICT", field_block([("Final verdict", report["final_verdict"]), ("Friction score", report["friction"]["score"]), ("Friction level", report["friction"]["band"]), ("Confidence level", report["confidence_level"])])),
        ("INPUTS USED", "\n".join(f"- {name}: {path}" for name, path in report["inputs_used"].items())),
        (
            "OUTPUTS",
            field_block(
                [
                    ("Analytical report", report["output_paths"]["analytical_report_md"]),
                    ("Coaching summary", report["output_paths"]["coaching_summary_md"]),
                    ("JSON summary", report["output_paths"]["analytical_report_json"]),
                    ("Confidence summary", report["output_paths"]["confidence_summary_json"]),
                    ("Visual references", report["output_paths"]["visual_references_md"]),
                ]
            ),
        ),
        (
            "SUMMARY",
            field_block(
                [
                    ("Labels analyzed", report["label_count"]),
                    ("Projected points", report["projected_points_count"]),
                    ("Unknown zones", report["unknown_zone_count"]),
                    ("Key findings", report["key_findings_count"]),
                    ("Coaching observations", report["observations_count"]),
                ]
            ),
        ),
        ("PRODUCT OWNER INTERPRETATION", "Stage 10 converts validated tactical outputs into a readable local report. It preserves possible_* uncertainty and does not provide official coaching, scoring, line calling, or confirmed shot classification."),
        ("WARNINGS", bullet_list(report["warnings"], "No warnings.")),
        ("ERRORS", bullet_list(report["errors"], "No errors.")),
        ("NEXT STEP", report["recommended_next_step"]),
    ]


def update_lab_notebook_safely() -> tuple[dict[str, Path], str | None]:
    try:
        from tennis_vision.lab_notebook import lab_notebook_paths, update_lab_notebook

        update_lab_notebook(PROJECT_ROOT)
        return lab_notebook_paths(PROJECT_ROOT, "stage_10"), None
    except Exception as exc:
        try:
            from tennis_vision.lab_notebook import lab_notebook_paths

            return lab_notebook_paths(PROJECT_ROOT, "stage_10"), f"Lab notebook update failed: {exc}"
        except Exception:
            return {
                "stage_page": PROJECT_ROOT / "docs" / "lab-notebook" / "stage_10_analytical_report.md",
                "experiment_index": PROJECT_ROOT / "docs" / "lab-notebook" / "experiment_index.md",
            }, f"Lab notebook update failed: {exc}"


def print_summary(report: dict[str, Any], lab_paths: dict[str, Path]) -> None:
    rows = [
        ("Verdict", report["final_verdict"]),
        ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"),
        ("Confidence level", report["confidence_level"]),
        ("Labels analyzed", report["label_count"]),
        ("Projected points", report["projected_points_count"]),
        ("Unknown zones", report["unknown_zone_count"]),
        ("Key findings", report["key_findings_count"]),
        ("Coaching observations", report["observations_count"]),
        ("Analytical report", report["output_paths"]["analytical_report_md"]),
        ("Coaching summary", report["output_paths"]["coaching_summary_md"]),
        ("Lab notebook", lab_paths["stage_page"]),
        ("Recommended next step", report["recommended_next_step"]),
    ]
    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(title="Stage 10 Analytical Report")
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")
        for field, value in rows:
            table.add_row(str(field), str(value))
        Console().print(table)
    except ImportError:
        print("Stage 10 Analytical Report")
        for field, value in rows:
            print(f"{field}: {value}")


def main() -> int:
    args = parse_args()
    ensure_output_folders(PROJECT_ROOT)
    timestamp = utc_timestamp()
    output_dir = resolve_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = default_input_paths(args)
    data = read_stage_inputs(paths)
    summary = build_analysis_summary(data)
    confidence = evaluate_report_confidence(
        label_count=summary["label_count"],
        projected_points_count=summary["projected_points_count"],
        unknown_zone_count=summary["unknown_zone_count"],
        candidate_validation_rows=data["expanded_candidate_validation"],
        validated_events_count=summary["event_summary"]["timeline_events_count"],
        supported_events_count=summary["event_summary"]["supported_events_count"],
        player_identity_count=summary["player_context"]["player_identities_count"],
    )
    observations = build_coaching_observations(summary, confidence)
    findings = build_key_findings(summary, confidence)
    input_paths = {key: str(value) for key, value in paths.items()}

    analytical_md = output_dir / "analytical_report.md"
    analytical_json = output_dir / "analytical_report.json"
    coaching_md = output_dir / "coaching_summary.md"
    confidence_json = output_dir / "confidence_summary.json"
    key_findings_md = output_dir / "key_findings.md"
    visual_refs_md = output_dir / "visual_references.md"

    warnings = list(data["warnings"])
    errors = list(data["errors"])
    flags = {
        "tactical_data_missing": not data["tactical_zones"],
        "report_generation_failed": False,
        "coaching_summary_failed": False,
        "low_confidence": confidence["confidence_level"] == "low",
        "sparse_data": summary["label_count"] < 10,
        "missing_player_context": summary["player_context"]["player_identities_count"] < 2,
        "missing_event_context": summary["event_summary"]["timeline_events_count"] == 0,
    }
    if flags["missing_player_context"]:
        warnings.append("Player identity context is incomplete.")
    if flags["missing_event_context"]:
        warnings.append("Validated event context is missing.")
    friction = calculate_stage_10_friction_score(**flags, errors_count=len(errors), warnings_count=len(warnings))

    output_paths = {
        "analytical_report_md": str(analytical_md),
        "analytical_report_json": str(analytical_json),
        "coaching_summary_md": str(coaching_md),
        "confidence_summary_json": str(confidence_json),
        "key_findings_md": str(key_findings_md),
        "visual_references_md": str(visual_refs_md),
    }
    report_stub = {
        "flags": flags,
        "confidence_level": confidence["confidence_level"],
        "unknown_zone_count": summary["unknown_zone_count"],
    }
    report_stub["final_verdict"] = determine_verdict(report_stub)
    report_stub["recommended_next_step"] = recommended_next_step(report_stub)

    try:
        analytical_content = build_plain_language_report(
            summary=summary,
            key_findings=findings,
            coaching_observations=observations,
            confidence=confidence,
            input_paths=input_paths,
            output_paths={**output_paths, **input_paths},
            verdict=report_stub["final_verdict"],
            friction=friction,
            timestamp=timestamp,
            recommended_next_step=report_stub["recommended_next_step"],
        )
        write_report_markdown(analytical_md, analytical_content)
        write_report_json(
            analytical_json,
            {
                "timestamp": timestamp,
                "stage": "stage_10_analytical_report",
                "verdict": report_stub["final_verdict"],
                "confidence_level": confidence["confidence_level"],
                "input_paths": input_paths,
                "label_count": summary["label_count"],
                "projected_points_count": summary["projected_points_count"],
                "unknown_zone_count": summary["unknown_zone_count"],
                "depth_distribution": summary["depth_distribution"],
                "lateral_distribution": summary["lateral_distribution"],
                "direction_distribution": summary["direction_distribution"],
                "player_context": summary["player_context"],
                "event_summary": summary["event_summary"],
                "key_findings": findings,
                "coaching_observations": observations,
                "limitations": confidence["limiting_factors"],
                "recommended_next_step": report_stub["recommended_next_step"],
                "output_paths": output_paths,
            },
        )
        write_coaching_summary(coaching_md, observations, confidence)
        write_report_json(confidence_json, confidence)
        write_key_findings(key_findings_md, findings)
        write_visual_references(visual_refs_md, input_paths)
    except OSError as exc:
        flags["report_generation_failed"] = True
        errors.append(f"Stage 10 report generation failed: {exc}")

    friction = calculate_stage_10_friction_score(**flags, errors_count=len(errors), warnings_count=len(warnings))
    stage_report: dict[str, Any] = {
        "timestamp": timestamp,
        "stage": "stage_10_analytical_report",
        "inputs_used": input_paths,
        "analytical_report_path": str(analytical_md),
        "coaching_summary_path": str(coaching_md),
        "confidence_level": confidence["confidence_level"],
        "label_count": summary["label_count"],
        "projected_points_count": summary["projected_points_count"],
        "unknown_zone_count": summary["unknown_zone_count"],
        "key_findings_count": len(findings),
        "observations_count": len(observations),
        "warnings": warnings,
        "errors": errors,
        "flags": flags,
        "friction": friction,
        "final_verdict": "blocked",
        "recommended_next_step": "",
        "output_paths": output_paths,
    }
    stage_report["final_verdict"] = determine_verdict(stage_report)
    stage_report["recommended_next_step"] = recommended_next_step(stage_report)
    log_path = write_timestamped_log(
        PROJECT_ROOT,
        "stage_10_analytical_report",
        [
            f"timestamp={timestamp}",
            f"verdict={stage_report['final_verdict']}",
            f"friction={friction['score']} ({friction['band']})",
            f"confidence={confidence['confidence_level']}",
            f"labels={summary['label_count']}",
            f"projected={summary['projected_points_count']}",
            f"unknown_zones={summary['unknown_zone_count']}",
        ],
    )
    stage_report["log_path"] = str(log_path)
    stage_report["json_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_10_analytical_report_report.json")
    stage_report["markdown_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_10_analytical_report_report.md")
    write_json_report(Path(stage_report["json_report_path"]), stage_report)
    write_markdown_report(Path(stage_report["markdown_report_path"]), "Stage 10 Analytical Report Generator and Coaching Summary Prototype Report", build_pipeline_markdown_sections(stage_report))

    lab_paths, notebook_warning = update_lab_notebook_safely()
    if notebook_warning:
        stage_report["warnings"].append(notebook_warning)
        write_json_report(Path(stage_report["json_report_path"]), stage_report)
        write_markdown_report(Path(stage_report["markdown_report_path"]), "Stage 10 Analytical Report Generator and Coaching Summary Prototype Report", build_pipeline_markdown_sections(stage_report))
        print(f"Warning: {notebook_warning}")
    print_summary(stage_report, lab_paths)
    return 1 if stage_report["final_verdict"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
