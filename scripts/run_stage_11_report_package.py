"""Run Stage 11 annotated report package generator."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from tennis_vision.friction import calculate_stage_11_friction_score  # noqa: E402
from tennis_vision.package_manifest import artifact, build_manifest, write_manifest  # noqa: E402
from tennis_vision.report import ensure_output_folders, utc_timestamp, write_json_report, write_markdown_report, write_timestamped_log  # noqa: E402
from tennis_vision.report_package import (  # noqa: E402
    build_report_package,
    write_limitations,
    write_package_index,
    write_package_readme,
    write_source_artifacts,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 11 annotated report package generator.")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs" / "report_packages" / "stage_11_report_package")
    parser.add_argument("--include-optional-visuals", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--copy-mode", choices=["copy", "reference_only"], default="copy")
    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def artifact_plan(package_root: Path, include_optional_visuals: bool) -> list[dict[str, Any]]:
    """Build curated artifact list for Stage 11."""
    final = PROJECT_ROOT / "outputs" / "reports_final" / "stage_10_analytical_report"
    tactical = PROJECT_ROOT / "outputs" / "tactical" / "stage_9_1_projection_coverage"
    timeline = PROJECT_ROOT / "outputs" / "timeline" / "stage_8_event_timeline"
    players = PROJECT_ROOT / "outputs" / "player_tracking" / "stage_7_1_player_filtering"
    trajectory = PROJECT_ROOT / "outputs" / "ball_tracking" / "stage_6_trajectory_smoothing"
    candidates = PROJECT_ROOT / "outputs" / "ball_tracking" / "stage_5_1_candidate_improvement"

    items = [
        artifact(name="analytical_report.md", artifact_type="Markdown report", source_path=final / "analytical_report.md", package_path=package_root / "analysis" / "analytical_report.md", purpose="Human-readable rally analysis.", required=True),
        artifact(name="coaching_summary.md", artifact_type="Markdown report", source_path=final / "coaching_summary.md", package_path=package_root / "analysis" / "coaching_summary.md", purpose="Cautious coaching-style observations.", required=True),
        artifact(name="key_findings.md", artifact_type="Markdown report", source_path=final / "key_findings.md", package_path=package_root / "analysis" / "key_findings.md", purpose="Compact key findings.", required=True),
        artifact(name="confidence_summary.json", artifact_type="JSON", source_path=final / "confidence_summary.json", package_path=package_root / "analysis" / "confidence_summary.json", purpose="Confidence level, reasons, and limitations.", required=True),
        artifact(name="visual_references.md", artifact_type="Markdown notes", source_path=final / "visual_references.md", package_path=package_root / "notes" / "visual_references.md", purpose="References to existing visual assets."),
        artifact(name="tuned_ball_zone_assignments.csv", artifact_type="CSV data", source_path=tactical / "tuned_ball_zone_assignments.csv", package_path=package_root / "data" / "tuned_ball_zone_assignments.csv", purpose="Tuned tactical zone assignment data."),
        artifact(name="tuned_shot_direction_estimates.csv", artifact_type="CSV data", source_path=tactical / "tuned_shot_direction_estimates.csv", package_path=package_root / "data" / "tuned_shot_direction_estimates.csv", purpose="Approximate shot direction estimates."),
        artifact(name="tuned_rally_tactical_summary.csv", artifact_type="CSV data", source_path=tactical / "tuned_rally_tactical_summary.csv", package_path=package_root / "data" / "tuned_rally_tactical_summary.csv", purpose="Rally-level tactical summary."),
        artifact(name="event_timeline.csv", artifact_type="CSV data", source_path=timeline / "event_timeline.csv", package_path=package_root / "data" / "event_timeline.csv", purpose="Stage 8 event timeline."),
        artifact(name="rally_segments.csv", artifact_type="CSV data", source_path=timeline / "rally_segments.csv", package_path=package_root / "data" / "rally_segments.csv", purpose="Stage 8 rally segments."),
        artifact(name="main_players.csv", artifact_type="CSV data", source_path=players / "main_players.csv", package_path=package_root / "data" / "main_players.csv", purpose="Stage 7.1 main player identities."),
        artifact(name="smoothed_trajectory.csv", artifact_type="CSV data", source_path=trajectory / "smoothed_trajectory.csv", package_path=package_root / "data" / "smoothed_trajectory.csv", purpose="Stage 6 smoothed trajectory."),
    ]
    if include_optional_visuals:
        items.extend(
            [
                artifact(name="projection_coverage_map.jpg", artifact_type="Image", source_path=tactical / "projection_coverage_map.jpg", package_path=package_root / "visuals" / "projection_coverage_map.jpg", purpose="Projection coverage mini-court map."),
                artifact(name="tuned_ball_placement_map.jpg", artifact_type="Image", source_path=tactical / "tuned_ball_placement_map.jpg", package_path=package_root / "visuals" / "tuned_ball_placement_map.jpg", purpose="Tuned ball placement map."),
                artifact(name="zone_comparison_preview.jpg", artifact_type="Image", source_path=tactical / "zone_comparison_preview.jpg", package_path=package_root / "visuals" / "zone_comparison_preview.jpg", purpose="Stage 9 vs Stage 9.1 comparison preview."),
                artifact(name="timeline_preview.jpg", artifact_type="Image", source_path=timeline / "timeline_preview.jpg", package_path=package_root / "visuals" / "timeline_preview.jpg", purpose="Timeline preview."),
                artifact(name="court_timeline_preview.jpg", artifact_type="Image", source_path=timeline / "court_timeline_preview.jpg", package_path=package_root / "visuals" / "court_timeline_preview.jpg", purpose="Court-space timeline preview."),
                artifact(name="image_trajectory_preview.jpg", artifact_type="Image", source_path=trajectory / "image_trajectory_preview.jpg", package_path=package_root / "visuals" / "image_trajectory_preview.jpg", purpose="Image-space trajectory preview."),
                artifact(name="court_trajectory_preview.jpg", artifact_type="Image", source_path=trajectory / "court_trajectory_preview.jpg", package_path=package_root / "visuals" / "court_trajectory_preview.jpg", purpose="Court-space trajectory preview."),
                artifact(name="player_identity_preview.jpg", artifact_type="Image", source_path=players / "player_identity_preview.jpg", package_path=package_root / "visuals" / "player_identity_preview.jpg", purpose="Main player identity preview."),
                artifact(name="strategy_preview.jpg", artifact_type="Image", source_path=candidates / "strategy_preview.jpg", package_path=package_root / "visuals" / "strategy_preview.jpg", purpose="Candidate generation strategy preview."),
            ]
        )
    return items


def load_stage_10_confidence() -> str | None:
    path = PROJECT_ROOT / "outputs" / "reports_final" / "stage_10_analytical_report" / "confidence_summary.json"
    if not path.exists():
        return None
    try:
        return str(json.loads(path.read_text(encoding="utf-8")).get("confidence_level") or "")
    except (OSError, json.JSONDecodeError):
        return None


def determine_verdict(report: dict[str, Any]) -> str:
    if report["flags"]["analytical_report_missing"] or report["flags"]["coaching_summary_missing"] or report["flags"]["package_manifest_failed"]:
        return "blocked"
    if report["flags"]["missing_core_artifacts"]:
        return "package_incomplete"
    if report["missing_artifact_count"] > 0:
        return "ready_with_warnings"
    return "ready_for_stage_12"


def recommended_next_step(report: dict[str, Any]) -> str:
    if report["final_verdict"] == "ready_for_stage_12":
        return "Proceed to Stage 12: Synthetic Rally Replay Data Schema."
    if report["final_verdict"] == "ready_with_warnings":
        return "Review missing optional artifacts, then proceed to Stage 12 or Stage 11.1 package polish."
    if report["final_verdict"] == "package_incomplete":
        return "Regenerate Stage 10 reports or rerun Stage 11 after fixing missing core package artifacts."
    return "Fix missing Stage 10 analytical report/coaching summary, then rerun Stage 11."


def count_by_type(artifacts: list[dict[str, Any]], kind: str) -> int:
    return sum(1 for item in artifacts if item.get("exists") and str(item.get("type", "")).lower().startswith(kind))


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
    outputs = report["output_paths"]
    return [
        ("VERDICT", field_block([("Final verdict", report["final_verdict"]), ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"), ("Package root", report["package_root"])])),
        (
            "PACKAGE SUMMARY",
            field_block(
                [
                    ("Included artifacts", report["included_artifact_count"]),
                    ("Missing artifacts", report["missing_artifact_count"]),
                    ("Visual artifacts", report["visual_artifacts_included_count"]),
                    ("Data artifacts", report["data_artifacts_included_count"]),
                    ("Core report included", report["core_report_included"]),
                    ("Coaching summary included", report["coaching_summary_included"]),
                ]
            ),
        ),
        (
            "KEY OUTPUTS",
            "\n".join(
                [
                    f"- package README: {outputs['package_readme']}",
                    f"- package manifest: {outputs['package_manifest']}",
                    f"- analytical report: {outputs['analytical_report']}",
                    f"- coaching summary: {outputs['coaching_summary']}",
                    f"- tactical visuals: {outputs['visuals_dir']}",
                ]
            ),
        ),
        ("WARNINGS", bullet_list(report["warnings"], "No warnings.")),
        ("ERRORS", bullet_list(report["errors"], "No errors.")),
        ("PRODUCT OWNER INTERPRETATION", "The package is the first local deliverable bundle. It organizes selected reports, visuals, data files, provenance, and limitations without creating new analysis or overclaiming certainty."),
        ("NEXT STEP", report["recommended_next_step"]),
    ]


def update_lab_notebook_safely() -> tuple[dict[str, Path], str | None]:
    try:
        from tennis_vision.lab_notebook import lab_notebook_paths, update_lab_notebook

        update_lab_notebook(PROJECT_ROOT)
        return lab_notebook_paths(PROJECT_ROOT, "stage_11"), None
    except Exception as exc:
        try:
            from tennis_vision.lab_notebook import lab_notebook_paths

            return lab_notebook_paths(PROJECT_ROOT, "stage_11"), f"Lab notebook update failed: {exc}"
        except Exception:
            return {
                "stage_page": PROJECT_ROOT / "docs" / "lab-notebook" / "stage_11_report_package.md",
                "experiment_index": PROJECT_ROOT / "docs" / "lab-notebook" / "experiment_index.md",
            }, f"Lab notebook update failed: {exc}"


def print_summary(report: dict[str, Any], lab_paths: dict[str, Path]) -> None:
    rows = [
        ("Verdict", report["final_verdict"]),
        ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"),
        ("Package root", report["package_root"]),
        ("Included artifacts", report["included_artifact_count"]),
        ("Missing artifacts", report["missing_artifact_count"]),
        ("Visual artifacts", report["visual_artifacts_included_count"]),
        ("Data artifacts", report["data_artifacts_included_count"]),
        ("Analytical report", report["output_paths"]["analytical_report"]),
        ("Coaching summary", report["output_paths"]["coaching_summary"]),
        ("Manifest", report["output_paths"]["package_manifest"]),
        ("Lab notebook", lab_paths["stage_page"]),
        ("Recommended next step", report["recommended_next_step"]),
    ]
    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(title="Stage 11 Report Package")
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")
        for field, value in rows:
            table.add_row(str(field), str(value))
        Console().print(table)
    except ImportError:
        print("Stage 11 Report Package")
        for field, value in rows:
            print(f"{field}: {value}")


def main() -> int:
    args = parse_args()
    ensure_output_folders(PROJECT_ROOT)
    timestamp = utc_timestamp()
    package_root = resolve_path(args.output_dir)
    artifacts = artifact_plan(package_root, args.include_optional_visuals)
    artifacts, package_warnings = build_report_package(package_root=package_root, artifacts=artifacts, copy_mode=args.copy_mode)

    warnings = list(package_warnings)
    errors: list[str] = []
    confidence_level = load_stage_10_confidence()
    core_missing = [item for item in artifacts if item.get("required") and not item.get("exists")]
    included = [item for item in artifacts if item.get("exists")]
    missing = [item for item in artifacts if not item.get("exists")]
    copy_failures = [item for item in artifacts if item.get("exists") and args.copy_mode == "copy" and not item.get("copied")]

    flags = {
        "analytical_report_missing": any(item["name"] == "analytical_report.md" for item in core_missing),
        "coaching_summary_missing": any(item["name"] == "coaching_summary.md" for item in core_missing),
        "key_findings_missing": any(item["name"] == "key_findings.md" for item in core_missing),
        "package_manifest_failed": False,
        "missing_core_artifacts": bool(core_missing),
        "many_optional_artifacts_missing": len([item for item in missing if not item.get("required")]) >= 3,
        "copy_failures": bool(copy_failures),
    }
    if copy_failures:
        errors.append(f"{len(copy_failures)} artifact copy operations failed.")

    readme_path = package_root / "README.md"
    index_path = package_root / "package_index.md"
    manifest_path = package_root / "package_manifest.json"
    limitations_path = package_root / "notes" / "limitations.md"
    source_artifacts_path = package_root / "notes" / "source_artifacts.md"
    output_paths = {
        "package_readme": str(readme_path),
        "package_manifest": str(manifest_path),
        "package_index": str(index_path),
        "analytical_report": str(package_root / "analysis" / "analytical_report.md"),
        "coaching_summary": str(package_root / "analysis" / "coaching_summary.md"),
        "visuals_dir": str(package_root / "visuals"),
        "limitations": str(limitations_path),
        "source_artifacts": str(source_artifacts_path),
    }
    stub = {
        "flags": flags,
        "missing_artifact_count": len(missing),
        "final_verdict": "blocked",
    }
    stub["final_verdict"] = determine_verdict(stub)
    stub["recommended_next_step"] = recommended_next_step(stub)

    try:
        write_package_readme(readme_path, verdict=stub["final_verdict"], confidence_level=confidence_level, generated_at=timestamp, next_step=stub["recommended_next_step"])
        write_package_index(index_path, artifacts)
        write_limitations(limitations_path)
        write_source_artifacts(source_artifacts_path, artifacts)
        manifest = build_manifest(
            generated_at=timestamp,
            package_root=package_root,
            verdict=stub["final_verdict"],
            confidence_level=confidence_level,
            artifacts=artifacts,
            warnings=warnings,
            errors=errors,
            output_paths=output_paths,
            recommended_next_step=stub["recommended_next_step"],
        )
        write_manifest(manifest_path, manifest)
    except OSError as exc:
        flags["package_manifest_failed"] = True
        errors.append(f"Package metadata generation failed: {exc}")

    friction = calculate_stage_11_friction_score(**flags, warnings_count=len(warnings), errors_count=len(errors))
    report: dict[str, Any] = {
        "timestamp": timestamp,
        "stage": "stage_11_report_package",
        "package_root": str(package_root),
        "included_artifact_count": len(included),
        "missing_artifact_count": len(missing),
        "core_report_included": not flags["analytical_report_missing"],
        "coaching_summary_included": not flags["coaching_summary_missing"],
        "key_findings_included": not flags["key_findings_missing"],
        "visual_artifacts_included_count": count_by_type(included, "image"),
        "data_artifacts_included_count": count_by_type(included, "csv"),
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
        "stage_11_report_package",
        [
            f"timestamp={timestamp}",
            f"verdict={report['final_verdict']}",
            f"friction={friction['score']} ({friction['band']})",
            f"included={report['included_artifact_count']}",
            f"missing={report['missing_artifact_count']}",
        ],
    )
    report["log_path"] = str(log_path)
    report["json_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_11_report_package_report.json")
    report["markdown_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_11_report_package_report.md")
    write_json_report(Path(report["json_report_path"]), report)
    write_markdown_report(Path(report["markdown_report_path"]), "Stage 11 Annotated Report Package Report", build_markdown_sections(report))

    lab_paths, notebook_warning = update_lab_notebook_safely()
    if notebook_warning:
        report["warnings"].append(notebook_warning)
        write_json_report(Path(report["json_report_path"]), report)
        write_markdown_report(Path(report["markdown_report_path"]), "Stage 11 Annotated Report Package Report", build_markdown_sections(report))
        print(f"Warning: {notebook_warning}")
    print_summary(report, lab_paths)
    return 1 if report["final_verdict"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
