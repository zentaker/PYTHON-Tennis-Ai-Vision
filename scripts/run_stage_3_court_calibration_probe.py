"""Run Stage 3 manual court calibration probe."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from tennis_vision.court_calibration import run_court_calibration_probe  # noqa: E402
from tennis_vision.friction import calculate_stage_3_friction_score  # noqa: E402
from tennis_vision.report import (  # noqa: E402
    ensure_output_folders,
    utc_timestamp,
    write_json_report,
    write_markdown_report,
    write_timestamped_log,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 3 manual court calibration probe.")
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "configs" / "court_calibration_sample.json",
        help="Path to a court calibration JSON config.",
    )
    parser.add_argument("--frame-index", type=int, default=None)
    parser.add_argument("--video", type=Path, default=None)
    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def determine_verdict(report: dict[str, Any]) -> str:
    result = report["calibration_result"]
    points = result["points_status"]
    homography = result["homography"]

    if not result["reference_frame_path"] or report["flags"]["frame_load_failed"]:
        return "blocked"
    if report["errors"]:
        return "blocked"
    if homography["computed"]:
        return "ready_for_stage_4"
    if points.get("has_placeholders") or report["flags"].get("geometrically_invalid"):
        return "ready_for_manual_point_selection"
    return "ready_with_warnings"


def recommended_next_step(report: dict[str, Any]) -> str:
    verdict = report["final_verdict"]
    if verdict == "ready_for_stage_4":
        return "Proceed to Stage 4: Ball Tracking Probe."
    if verdict == "ready_for_manual_point_selection":
        if report["flags"].get("geometrically_invalid"):
            return "Rerun Stage 3.1 and select points in this exact order: near_left_corner, near_right_corner, far_left_corner, far_right_corner."
        return "Fill pixel coordinates in configs/court_calibration_sample.json using the reference frame, then rerun Stage 3."
    if verdict == "blocked":
        return "Fix the blocking video/config/frame issue, then rerun Stage 3."
    return "Review court point warnings, update the calibration config, then rerun Stage 3."


def recommended_fixes(report: dict[str, Any]) -> list[str]:
    fixes: list[str] = []
    flags = report["flags"]
    if flags["config_missing"]:
        fixes.append("Create configs/court_calibration_sample.json or pass --config PATH.")
    if flags["video_missing"]:
        fixes.append("Place the local sample video at samples/video_01.mov or pass --video PATH.")
    if flags["frame_load_failed"]:
        fixes.append("Try a different --frame-index that exists in the video.")
    if flags["placeholder_points_detected"] or flags["calibration_points_missing"]:
        fixes.append("Fill the four court corner pixel coordinates in the calibration config.")
    if flags["invalid_points"]:
        fixes.append("Use non-negative point coordinates inside the calibration reference frame.")
    if flags.get("point_order_suspicious") or flags.get("polygon_self_intersects"):
        fixes.append(
            "Rerun Stage 3.1 and select points in this exact order: "
            "near_left_corner, near_right_corner, far_left_corner, far_right_corner."
        )
    if flags["homography_failed"]:
        fixes.append("Check point order and spacing; four usable corner points are required for homography.")
    return fixes


def _point_table(points: dict[str, Any]) -> str:
    lines = ["| Point | X | Y | Status |", "|---|---:|---:|---|"]
    for name, details in points.items():
        x_value = details.get("x")
        y_value = details.get("y")
        lines.append(
            f"| {name} | {x_value if x_value is not None else 'Not available'} | "
            f"{y_value if y_value is not None else 'Not available'} | {details.get('status', 'missing')} |"
        )
    return "\n".join(lines)


def _bullet_list(items: list[str], empty_text: str) -> str:
    if not items:
        return empty_text
    return "\n".join(f"- {item}" for item in items)


def build_markdown_sections(report: dict[str, Any]) -> list[tuple[str, str]]:
    result = report["calibration_result"]
    points = result["points_status"]
    homography = result["homography"]
    homography_text = (
        "Homography was computed from four usable manual court corner points."
        if homography["computed"]
        else f"Homography was not computed. Reason: {homography.get('error') or 'Not available'}"
    )
    geometry = points.get("geometry", {})
    order_checks = geometry.get("order_checks", {})
    interpretation = (
        "The reference frame and overlay are ready. Placeholder, inverted, or crossed points mean the project is ready for manual point selection, not Stage 4 yet."
        if report["final_verdict"] == "ready_for_manual_point_selection"
        else "Valid court points and homography are available, so the project can move to Stage 4."
        if report["final_verdict"] == "ready_for_stage_4"
        else "The court calibration probe needs attention before the next stage."
    )

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
                    f"- Config path: `{report['config_path']}`",
                    f"- Video path: `{report['video_path']}`",
                    f"- Frame index: {report['frame_index']}",
                    f"- Calibration basis: {report['calibration_basis']}",
                    f"- Calibration points status: {report['points_status_summary']}",
                ]
            ),
        ),
        (
            "Output",
            "\n".join(
                [
                    f"- Reference frame: `{result['reference_frame_path']}`",
                    f"- Points overlay: `{result['overlay_path']}`",
                    f"- Mini-court preview: `{result['mini_court_preview_path'] or 'Not created'}`",
                    f"- JSON report: `{report['json_report_path']}`",
                    f"- Markdown report: `{report['markdown_report_path']}`",
                    f"- Log path: `{report['log_path']}`",
                ]
            ),
        ),
        ("Court points", _point_table(points.get("points", {}))),
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
        ("Homography", homography_text),
        ("Warnings", _bullet_list(report["warnings"], "No warnings.")),
        ("Errors", _bullet_list(report["errors"], "No errors.")),
        ("Interpretation", interpretation),
        ("Next step", report["recommended_next_step"]),
    ]


def print_summary(report: dict[str, Any], lab_paths: dict[str, Path]) -> None:
    result = report["calibration_result"]
    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(title="Stage 3 Court Calibration Probe")
        table.add_column("Field")
        table.add_column("Value")
        rows = [
            ("Stage name", "Stage 3 court calibration probe"),
            ("Config", report["config_path"]),
            ("Input video", report["video_path"]),
            ("Frame index", str(report["frame_index"])),
            ("Verdict", report["final_verdict"]),
            ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"),
            ("Reference frame", str(result["reference_frame_path"])),
            ("Overlay", str(result["overlay_path"])),
            ("Homography", "computed" if result["homography"]["computed"] else "not computed"),
            ("Point order valid", str(result["points_status"].get("geometry", {}).get("point_order_valid"))),
            ("Polygon self-intersects", str(result["points_status"].get("geometry", {}).get("polygon_self_intersects"))),
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
        print(f"Stage name: Stage 3 court calibration probe")
        print(f"Config: {report['config_path']}")
        print(f"Input video: {report['video_path']}")
        print(f"Frame index: {report['frame_index']}")
        print(f"Verdict: {report['final_verdict']}")
        print(f"Friction: {report['friction']['score']} ({report['friction']['band']})")
        print(f"Reference frame: {result['reference_frame_path']}")
        print(f"Overlay: {result['overlay_path']}")
        print(f"Homography: {'computed' if result['homography']['computed'] else 'not computed'}")
        print(f"Point order valid: {result['points_status'].get('geometry', {}).get('point_order_valid')}")
        print(f"Polygon self-intersects: {result['points_status'].get('geometry', {}).get('polygon_self_intersects')}")
        print(f"JSON report: {report['json_report_path']}")
        print(f"Markdown report: {report['markdown_report_path']}")
        print(f"Lab notebook: {lab_paths['stage_page']}")
        print(f"Experiment index: {lab_paths['experiment_index']}")
        print(f"Recommended next step: {report['recommended_next_step']}")


def update_lab_notebook_safely() -> tuple[dict[str, Path], str | None]:
    try:
        from tennis_vision.lab_notebook import lab_notebook_paths, update_lab_notebook

        update_lab_notebook(PROJECT_ROOT)
        return lab_notebook_paths(PROJECT_ROOT, "stage_3"), None
    except Exception as exc:
        from tennis_vision.lab_notebook import lab_notebook_paths

        return lab_notebook_paths(PROJECT_ROOT, "stage_3"), f"Lab notebook update failed: {exc}"


def main() -> int:
    args = parse_args()
    ensure_output_folders(PROJECT_ROOT)
    output_folder = PROJECT_ROOT / "outputs" / "calibration" / "stage_3_court_probe"
    output_folder.mkdir(parents=True, exist_ok=True)

    config_path = resolve_path(args.config)
    video_override = resolve_path(args.video) if args.video is not None else None
    result = run_court_calibration_probe(
        config_path=config_path,
        output_folder=output_folder,
        project_root=PROJECT_ROOT,
        video_override=video_override,
        frame_index_override=args.frame_index,
    )

    points = result["points_status"]
    errors = list(result["errors"])
    warnings = list(result["warnings"])
    flags = {
        "config_missing": not config_path.exists(),
        "video_missing": not Path(result["video_path"]).exists(),
        "frame_load_failed": result["reference_frame_path"] is None,
        "calibration_points_missing": bool(points.get("has_missing")),
        "placeholder_points_detected": bool(points.get("has_placeholders")),
        "invalid_points": bool(points.get("has_invalid")) or bool(points.get("geometry", {}).get("required_points_available") and not points.get("geometry", {}).get("valid")),
        "point_order_suspicious": bool(points.get("geometry", {}).get("required_points_available") and not points.get("geometry", {}).get("point_order_valid")),
        "polygon_self_intersects": bool(points.get("geometry", {}).get("polygon_self_intersects")),
        "geometrically_invalid": bool(points.get("geometry", {}).get("required_points_available") and not points.get("geometry", {}).get("valid")),
        "homography_failed": bool(points.get("homography_ready")) and not result["homography"]["computed"],
    }
    friction = calculate_stage_3_friction_score(
        **flags,
        errors_count=len(errors),
        warnings_count=len(warnings),
    )

    report: dict[str, Any] = {
        "timestamp": utc_timestamp(),
        "stage": "stage_3_court_calibration_probe",
        "config_path": str(config_path),
        "video_path": result["video_path"],
        "frame_index": result["frame_index"],
        "reference_frame_path": result["reference_frame_path"],
        "overlay_path": result["overlay_path"],
        "mini_court_preview_path": result["mini_court_preview_path"],
        "calibration_basis": "doubles court outer boundary",
        "points_status": points,
        "point_order_validation_status": points.get("geometry", {}),
        "polygon_self_intersection_status": points.get("geometry", {}).get("polygon_self_intersects"),
        "points_status_summary": "placeholder_points_detected"
        if flags["placeholder_points_detected"]
        else "geometrically_invalid"
        if flags["geometrically_invalid"]
        else "homography_ready"
        if points.get("homography_ready")
        else "needs_attention",
        "homography_status": result["homography"],
        "calibration_result": result,
        "flags": flags,
        "warnings": warnings,
        "errors": errors,
        "recommended_fixes": [],
        "friction": friction,
        "final_verdict": "blocked",
        "recommended_next_step": "",
        "json_report_path": str(PROJECT_ROOT / "outputs" / "reports" / "stage_3_court_calibration_probe_report.json"),
        "markdown_report_path": str(PROJECT_ROOT / "outputs" / "reports" / "stage_3_court_calibration_probe_report.md"),
        "log_path": "",
    }
    report["final_verdict"] = determine_verdict(report)
    report["recommended_next_step"] = recommended_next_step(report)
    report["recommended_fixes"] = recommended_fixes(report)

    log_path = write_timestamped_log(
        PROJECT_ROOT,
        "stage_3_court_calibration_probe",
        [
            f"timestamp={report['timestamp']}",
            f"config={config_path}",
            f"video={result['video_path']}",
            f"frame_index={result['frame_index']}",
            f"verdict={report['final_verdict']}",
            f"friction={friction['score']} ({friction['band']})",
            f"reference_frame={result['reference_frame_path']}",
            f"overlay={result['overlay_path']}",
        ],
    )
    report["log_path"] = str(log_path)

    json_path = Path(report["json_report_path"])
    markdown_path = Path(report["markdown_report_path"])
    write_json_report(json_path, report)
    write_markdown_report(
        markdown_path,
        "Stage 3 Court Calibration Probe Report",
        build_markdown_sections(report),
    )

    lab_paths, notebook_warning = update_lab_notebook_safely()
    if notebook_warning:
        report["warnings"].append(notebook_warning)
        write_json_report(json_path, report)
        write_markdown_report(
            markdown_path,
            "Stage 3 Court Calibration Probe Report",
            build_markdown_sections(report),
        )
        print(f"Warning: {notebook_warning}")

    print_summary(report, lab_paths)
    return 1 if report["final_verdict"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
