"""Run Stage 3.1 court point selection helper."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from tennis_vision.court_point_selector import (  # noqa: E402
    generate_coordinate_grid,
    select_court_points_interactively,
    update_calibration_config,
    validate_selected_points,
)
from tennis_vision.friction import calculate_stage_3_1_friction_score  # noqa: E402
from tennis_vision.report import (  # noqa: E402
    ensure_output_folders,
    utc_timestamp,
    write_json_report,
    write_markdown_report,
    write_timestamped_log,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 3.1 court point selection helper.")
    parser.add_argument(
        "--image",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "calibration" / "stage_3_court_probe" / "calibration_reference_frame.jpg",
        help="Path to the Stage 3 calibration reference frame.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "configs" / "court_calibration_sample.json",
        help="Path to the court calibration JSON config to update.",
    )
    parser.add_argument("--grid-step", type=int, default=200, help="Grid spacing in pixels.")
    parser.add_argument("--interactive", dest="interactive", action="store_true", help="Attempt OpenCV click selection.")
    parser.add_argument("--no-interactive", dest="interactive", action="store_false", help="Generate grid only.")
    parser.set_defaults(interactive=True)
    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def determine_verdict(report: dict[str, Any]) -> str:
    flags = report["flags"]
    if flags["image_missing"] or flags["grid_generation_failed"]:
        return "blocked"
    if report["points_valid"] and report["config_update"]["updated"]:
        return "ready_to_rerun_stage_3"
    return "ready_with_grid_only"


def recommended_next_step(report: dict[str, Any]) -> str:
    verdict = report["final_verdict"]
    if verdict == "ready_to_rerun_stage_3":
        return "Rerun Stage 3 to compute the court homography from the saved point coordinates."
    if verdict == "blocked":
        return "Rerun Stage 3 first so calibration_reference_frame.jpg exists, then rerun Stage 3.1."
    return "Use the grid image or rerun this helper with --interactive to select court point coordinates."


def recommended_fixes(report: dict[str, Any]) -> list[str]:
    fixes: list[str] = []
    flags = report["flags"]
    if flags["image_missing"]:
        fixes.append("Run python scripts/run_stage_3_court_calibration_probe.py to generate the reference frame.")
    if flags["grid_generation_failed"]:
        fixes.append("Confirm the reference frame is readable by OpenCV and rerun Stage 3.1.")
    if flags["interactive_unavailable"]:
        fixes.append("Use the generated grid image to estimate coordinates manually, or run the selector in a local desktop session with OpenCV GUI support.")
    if flags["no_points_selected"]:
        fixes.append("Run with --interactive and click the four court corners, or edit configs/court_calibration_sample.json manually using the grid.")
    if flags["invalid_points"]:
        fixes.append("Select four non-placeholder, non-negative court corner coordinates.")
    if flags.get("point_order_suspicious") or flags.get("polygon_self_intersects"):
        fixes.append(
            "Rerun the selector and click points in this exact order: "
            "near_left_corner, near_right_corner, far_left_corner, far_right_corner."
        )
    if flags["config_update_failed"]:
        fixes.append("Check write permissions for configs/court_calibration_sample.json.")
    return fixes


def _bullet_list(items: list[str], empty_text: str) -> str:
    if not items:
        return empty_text
    return "\n".join(f"- {item}" for item in items)


def _points_table(points: dict[str, Any]) -> str:
    lines = ["| Point | X | Y | Status |", "|---|---:|---:|---|"]
    for name, details in points.items():
        x_value = details.get("x")
        y_value = details.get("y")
        lines.append(
            f"| {name} | {x_value if x_value is not None else 'Not available'} | "
            f"{y_value if y_value is not None else 'Not available'} | {details.get('status', 'missing')} |"
        )
    return "\n".join(lines)


def build_markdown_sections(report: dict[str, Any]) -> list[tuple[str, str]]:
    interpretation = (
        "The coordinate grid was generated successfully. No points were saved during this run, so this helper is ready for manual coordinate reading or an interactive selection pass."
        if report["final_verdict"] == "ready_with_grid_only"
        else "Four valid court points were saved to the calibration config. Stage 3 can now be rerun to compute homography."
        if report["final_verdict"] == "ready_to_rerun_stage_3"
        else "The helper could not generate the required grid image. Stage 3 should be rerun to recreate the reference frame."
    )
    geometry = report["selected_points_status"].get("geometry", {})
    order_checks = geometry.get("order_checks", {})
    return [
        (
            "Verdict",
            "\n".join(
                [
                    f"- Final verdict: {report['final_verdict']}",
                    f"- Friction score: {report['friction']['score']}",
                    f"- Friction level: {report['friction']['band']}",
                ]
            ),
        ),
        (
            "Input",
            "\n".join(
                [
                    f"- Image path: `{report['image_path']}`",
                    f"- Config path: `{report['config_path']}`",
                    f"- Calibration basis: {report['calibration_basis']}",
                    f"- Grid step: {report['grid_step']}",
                    f"- Interactive attempted: {'yes' if report['interactive_attempted'] else 'no'}",
                ]
            ),
        ),
        (
            "Output",
            "\n".join(
                [
                    f"- Grid image: `{report['grid_image_path'] or 'Not created'}`",
                    f"- JSON report: `{report['json_report_path']}`",
                    f"- Markdown report: `{report['markdown_report_path']}`",
                    f"- Log path: `{report['log_path']}`",
                    f"- Config updated: {'yes' if report['config_update']['updated'] else 'no'}",
                ]
            ),
        ),
        ("Selected points", _points_table(report["selected_points_status"]["points"])),
        (
            "Point order validation",
            "\n".join(
                [
                    f"- near_left_corner.x < near_right_corner.x: {order_checks.get('near_left_before_near_right')}",
                    f"- far_left_corner.x < far_right_corner.x: {order_checks.get('far_left_before_far_right')}",
                    f"- Point order valid: {geometry.get('point_order_valid')}",
                    f"- Polygon self-intersects: {geometry.get('polygon_self_intersects')}",
                    f"- Geometry valid: {geometry.get('valid')}",
                ]
            ),
        ),
        ("Warnings", _bullet_list(report["warnings"], "No warnings.")),
        ("Errors", _bullet_list(report["errors"], "No errors.")),
        ("Recommended fixes", _bullet_list(report["recommended_fixes"], "No fixes required.")),
        ("Interpretation", interpretation),
        ("Next step", report["recommended_next_step"]),
    ]


def print_summary(report: dict[str, Any], lab_paths: dict[str, Path]) -> None:
    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(title="Stage 3.1 Court Point Selection Helper")
        table.add_column("Field")
        table.add_column("Value")
        rows = [
            ("Stage name", "Stage 3.1 court point selection helper"),
            ("Reference image", report["image_path"]),
            ("Calibration basis", report["calibration_basis"]),
            ("Grid image", str(report["grid_image_path"])),
            ("Grid step", str(report["grid_step"])),
            ("Interactive attempted", "yes" if report["interactive_attempted"] else "no"),
            ("Interactive completed", "yes" if report["interactive_completed"] else "no"),
            ("Points valid", "yes" if report["points_valid"] else "no"),
            ("Config updated", "yes" if report["config_update"]["updated"] else "no"),
            ("Verdict", report["final_verdict"]),
            ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"),
            ("JSON report", report["json_report_path"]),
            ("Markdown report", report["markdown_report_path"]),
            ("Lab notebook", str(lab_paths["stage_page"])),
            ("Experiment index", str(lab_paths["experiment_index"])),
            ("Recommended next step", report["recommended_next_step"]),
        ]
        for field, value in rows:
            table.add_row(field, value)
        Console().print(table)
    except ImportError:
        print("Stage name: Stage 3.1 court point selection helper")
        print(f"Reference image: {report['image_path']}")
        print(f"Grid image: {report['grid_image_path']}")
        print(f"Grid step: {report['grid_step']}")
        print(f"Interactive attempted: {'yes' if report['interactive_attempted'] else 'no'}")
        print(f"Interactive completed: {'yes' if report['interactive_completed'] else 'no'}")
        print(f"Points valid: {'yes' if report['points_valid'] else 'no'}")
        print(f"Config updated: {'yes' if report['config_update']['updated'] else 'no'}")
        print(f"Verdict: {report['final_verdict']}")
        print(f"Friction: {report['friction']['score']} ({report['friction']['band']})")
        print(f"JSON report: {report['json_report_path']}")
        print(f"Markdown report: {report['markdown_report_path']}")
        print(f"Lab notebook: {lab_paths['stage_page']}")
        print(f"Experiment index: {lab_paths['experiment_index']}")
        print(f"Recommended next step: {report['recommended_next_step']}")


def update_lab_notebook_safely() -> tuple[dict[str, Path], str | None]:
    try:
        from tennis_vision.lab_notebook import lab_notebook_paths, update_lab_notebook

        update_lab_notebook(PROJECT_ROOT)
        return lab_notebook_paths(PROJECT_ROOT, "stage_3_1"), None
    except Exception as exc:
        try:
            from tennis_vision.lab_notebook import lab_notebook_paths

            return lab_notebook_paths(PROJECT_ROOT, "stage_3_1"), f"Lab notebook update failed: {exc}"
        except Exception:
            return {
                "stage_page": PROJECT_ROOT / "docs" / "lab-notebook" / "stage_3_1_court_point_selector.md",
                "experiment_index": PROJECT_ROOT / "docs" / "lab-notebook" / "experiment_index.md",
            }, f"Lab notebook update failed: {exc}"


def main() -> int:
    args = parse_args()
    ensure_output_folders(PROJECT_ROOT)
    output_folder = PROJECT_ROOT / "outputs" / "calibration" / "stage_3_court_probe"
    output_folder.mkdir(parents=True, exist_ok=True)

    image_path = resolve_path(args.image)
    config_path = resolve_path(args.config)
    grid_path = output_folder / "calibration_reference_grid.jpg"

    grid_result = generate_coordinate_grid(image_path=image_path, output_path=grid_path, grid_step=args.grid_step)
    selected_points: dict[str, list[int]] = {}
    selector_result: dict[str, Any] = {
        "interactive_attempted": False,
        "interactive_completed": False,
        "selected_points": {},
        "errors": [],
        "warnings": [],
    }

    if args.interactive and grid_result["generated"]:
        selector_result = select_court_points_interactively(image_path=image_path)
        selected_points = selector_result.get("selected_points", {})
    elif not args.interactive:
        selector_result["warnings"].append("Interactive point selection was skipped by --no-interactive.")

    selected_status = validate_selected_points(selected_points)
    config_update = {
        "updated": False,
        "config_path": str(config_path),
        "errors": [],
        "warnings": [],
    }
    if selected_status["points_valid"]:
        config_update = update_calibration_config(config_path=config_path, selected_points=selected_points)

    errors = list(grid_result["errors"]) + list(selector_result["errors"]) + list(config_update["errors"])
    warnings = list(grid_result["warnings"]) + list(selector_result["warnings"]) + list(config_update["warnings"])
    geometry = selected_status.get("geometry", {})
    if selected_points and geometry.get("required_points_available") and not geometry.get("valid"):
        warnings.append(
            "Court points appear crossed, inverted, or geometrically invalid. "
            "Rerun Stage 3.1 and select points in this exact order: "
            "near_left_corner, near_right_corner, far_left_corner, far_right_corner."
        )
    flags = {
        "image_missing": not image_path.exists(),
        "grid_generation_failed": not bool(grid_result["generated"]),
        "interactive_unavailable": args.interactive and bool(selector_result["errors"]),
        "no_points_selected": not bool(selected_points),
        "invalid_points": bool(selected_points) and not bool(selected_status["points_valid"]),
        "point_order_suspicious": bool(geometry.get("required_points_available") and not geometry.get("point_order_valid")),
        "polygon_self_intersects": bool(geometry.get("polygon_self_intersects")),
        "config_update_failed": bool(selected_status["points_valid"]) and not bool(config_update["updated"]),
    }
    friction = calculate_stage_3_1_friction_score(
        **flags,
        errors_count=len(errors),
        warnings_count=len(warnings),
    )

    report: dict[str, Any] = {
        "timestamp": utc_timestamp(),
        "stage": "stage_3_1_court_point_selector",
        "image_path": str(image_path),
        "config_path": str(config_path),
        "calibration_basis": "doubles court outer boundary",
        "grid_image_path": grid_result["grid_image_path"],
        "grid_step": grid_result["grid_step"],
        "interactive_attempted": bool(selector_result["interactive_attempted"]),
        "interactive_completed": bool(selector_result["interactive_completed"]),
        "selected_points": selected_points,
        "selected_points_status": selected_status,
        "points_valid": bool(selected_status["points_valid"]),
        "point_order_validation_status": geometry,
        "polygon_self_intersection_status": geometry.get("polygon_self_intersects"),
        "config_update": config_update,
        "flags": flags,
        "warnings": warnings,
        "errors": errors,
        "recommended_fixes": [],
        "friction": friction,
        "final_verdict": "blocked",
        "recommended_next_step": "",
        "json_report_path": str(PROJECT_ROOT / "outputs" / "reports" / "stage_3_1_court_point_selector_report.json"),
        "markdown_report_path": str(PROJECT_ROOT / "outputs" / "reports" / "stage_3_1_court_point_selector_report.md"),
        "log_path": "",
    }
    report["final_verdict"] = determine_verdict(report)
    report["recommended_next_step"] = recommended_next_step(report)
    report["recommended_fixes"] = recommended_fixes(report)

    log_path = write_timestamped_log(
        PROJECT_ROOT,
        "stage_3_1_court_point_selector",
        [
            f"timestamp={report['timestamp']}",
            f"image={image_path}",
            f"grid={grid_result['grid_image_path']}",
            f"grid_step={grid_result['grid_step']}",
            f"interactive_attempted={report['interactive_attempted']}",
            f"interactive_completed={report['interactive_completed']}",
            f"points_valid={report['points_valid']}",
            f"verdict={report['final_verdict']}",
            f"friction={friction['score']} ({friction['band']})",
        ],
    )
    report["log_path"] = str(log_path)

    json_path = Path(report["json_report_path"])
    markdown_path = Path(report["markdown_report_path"])
    write_json_report(json_path, report)
    write_markdown_report(
        markdown_path,
        "Stage 3.1 Court Point Selection Helper Report",
        build_markdown_sections(report),
    )

    lab_paths, notebook_warning = update_lab_notebook_safely()
    if notebook_warning:
        report["warnings"].append(notebook_warning)
        write_json_report(json_path, report)
        write_markdown_report(
            markdown_path,
            "Stage 3.1 Court Point Selection Helper Report",
            build_markdown_sections(report),
        )
        print(f"Warning: {notebook_warning}")

    print_summary(report, lab_paths)
    return 1 if report["final_verdict"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
