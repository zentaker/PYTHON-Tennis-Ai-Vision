"""Run Stage 9.1 projection coverage and court zone tuning."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import cv2
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from tennis_vision.court_zone_tuning import (  # noqa: E402
    compare_stage_9_to_9_1,
    summarize_zone_coverage,
    tune_zone_assignments,
)
from tennis_vision.court_zones import COURT_HEIGHT, COURT_WIDTH  # noqa: E402
from tennis_vision.friction import calculate_stage_9_1_friction_score  # noqa: E402
from tennis_vision.projection_coverage import (  # noqa: E402
    calculate_projection_coverage,
    load_expanded_ball_labels,
    load_stage_3_homography,
    merge_projected_labels_with_stage_9_assignments,
    project_labels_to_court,
    read_csv_rows,
    write_csv,
)
from tennis_vision.report import ensure_output_folders, utc_timestamp, write_json_report, write_markdown_report, write_timestamped_log  # noqa: E402
from tennis_vision.tactical_metrics import build_rally_tactical_summary, estimate_shot_directions, write_tactical_summary  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 9.1 court zone tuning and projection coverage.")
    parser.add_argument("--labels", type=Path, default=PROJECT_ROOT / "outputs" / "timeline" / "stage_8_1_timeline_validation" / "expanded_ball_labels.csv")
    parser.add_argument("--stage9-zones", type=Path, default=PROJECT_ROOT / "outputs" / "tactical" / "stage_9_tactical_metrics" / "ball_zone_assignments.csv")
    parser.add_argument("--calibration", type=Path, default=PROJECT_ROOT / "outputs" / "reports" / "stage_3_court_calibration_probe_report.json")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs" / "tactical" / "stage_9_1_projection_coverage")
    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def court_canvas() -> np.ndarray:
    canvas = np.zeros((1560, 720, 3), dtype=np.uint8)
    canvas[:] = (42, 117, 65)
    margin = 40
    cv2.rectangle(canvas, (margin, margin), (680, 1520), (255, 255, 255), 3)
    for x_frac in (1 / 3, 2 / 3):
        x = margin + int((720 - 2 * margin) * x_frac)
        cv2.line(canvas, (x, margin), (x, 1520), (215, 245, 220), 1)
    for y_frac in (1 / 6, 2 / 6, 3 / 6, 4 / 6, 5 / 6):
        y = margin + int((1560 - 2 * margin) * y_frac)
        cv2.line(canvas, (margin, y), (680, y), (215, 245, 220), 1)
    return canvas


def map_point(x_value: float, y_value: float, canvas: np.ndarray) -> tuple[int, int]:
    h, w = canvas.shape[:2]
    margin = 40
    x_clamped = min(max(x_value, 0.0), COURT_WIDTH)
    y_clamped = min(max(y_value, 0.0), COURT_HEIGHT)
    x = margin + int((x_clamped / COURT_WIDTH) * (w - 2 * margin))
    y = margin + int((y_clamped / COURT_HEIGHT) * (h - 2 * margin))
    return x, y


def save_projection_coverage_map(path: Path, projected_rows: list[dict[str, Any]]) -> str | None:
    canvas = court_canvas()
    for row in projected_rows:
        if row.get("projected_x") in (None, "") or row.get("projected_y") in (None, ""):
            continue
        point = map_point(float(row["projected_x"]), float(row["projected_y"]), canvas)
        color = (0, 255, 255) if row.get("projection_status") == "projected" else (0, 120, 255)
        cv2.circle(canvas, point, 10, color, -1)
        cv2.putText(canvas, str(row["frame_index"]), (point[0] + 12, point[1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
    cv2.putText(canvas, "Projection coverage: yellow=inside/near, orange=outside range", (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path) if cv2.imwrite(str(path), canvas) else None


def save_tuned_ball_placement_map(path: Path, tuned_rows: list[dict[str, Any]]) -> str | None:
    canvas = court_canvas()
    points: list[tuple[int, int]] = []
    for row in tuned_rows:
        if row.get("projected_x") in (None, "") or row.get("projected_y") in (None, ""):
            continue
        point = map_point(float(row["projected_x"]), float(row["projected_y"]), canvas)
        points.append(point)
        zone = str(row.get("tuned_zone"))
        color = (0, 255, 255) if zone != "out_of_bounds" else (0, 0, 255)
        cv2.circle(canvas, point, 10, color, -1)
        cv2.putText(canvas, f"{row['frame_index']} {zone}", (point[0] + 10, point[1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1)
    for start, end in zip(points, points[1:]):
        cv2.line(canvas, start, end, (0, 255, 255), 2)
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path) if cv2.imwrite(str(path), canvas) else None


def save_zone_comparison_preview(path: Path, report: dict[str, Any]) -> str | None:
    canvas = np.full((620, 1000, 3), 246, dtype=np.uint8)
    lines = [
        "Stage 9 vs Stage 9.1 Projection Coverage",
        f"Stage 9 projected points: {report['stage_9_projected_points']}",
        f"Stage 9 unknown zones: {report['stage_9_unknown_zones']}",
        f"Stage 9.1 projected points: {report['stage_9_1_projected_points']}",
        f"Stage 9.1 unknown zones: {report['stage_9_1_unknown_zones']}",
        f"Unknown zone reduction: {report['unknown_zone_reduction']}",
        f"Projection coverage improvement: {report['projection_coverage_improvement']}",
        f"Verdict: {report['final_verdict']}",
    ]
    for index, line in enumerate(lines):
        cv2.putText(canvas, line, (36, 58 + index * 62), cv2.FONT_HERSHEY_SIMPLEX, 0.82, (30, 30, 30), 2)
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path) if cv2.imwrite(str(path), canvas) else None


def field_block(rows: list[tuple[str, Any]]) -> str:
    lines: list[str] = []
    for key, value in rows:
        lines.append(f"{key}:")
        lines.append(f"  {value if value not in (None, '') else 'Not available'}")
        lines.append("")
    return "\n".join(lines).rstrip()


def bullet_distribution(data: dict[str, Any]) -> str:
    if not data:
        return "- none: 0"
    return "\n".join(f"- {key}: {value}" for key, value in sorted(data.items()))


def bullet_list(items: list[str], empty: str) -> str:
    return empty if not items else "\n".join(f"- {item}" for item in items)


def determine_verdict(report: dict[str, Any]) -> str:
    if report["flags"]["expanded_labels_missing"] or report["flags"]["homography_missing"]:
        return "blocked"
    if report["expanded_labels_count"] < 10:
        return "needs_more_labels"
    if report["flags"]["unknown_zones_not_reduced"]:
        return "needs_projection_review"
    if report["flags"]["many_out_of_bounds_points"]:
        return "needs_projection_review"
    if report["stage_9_1_unknown_zones"] == 0 and report["unknown_zone_reduction"] > 0:
        return "ready_for_stage_10"
    return "ready_with_warnings"


def recommended_next_step(report: dict[str, Any]) -> str:
    if report["final_verdict"] == "ready_for_stage_10":
        return "Proceed to Stage 10: Analytical Report Generator and Coaching Summary Prototype."
    if report["final_verdict"] == "needs_projection_review":
        return "Review projection bounds and court zone tuning before analytical reporting."
    if report["final_verdict"] == "needs_more_labels":
        return "Collect more expanded labels, then rerun Stage 9.1."
    if report["final_verdict"] == "blocked":
        return "Fix missing expanded labels or Stage 3 homography, then rerun Stage 9.1."
    return "Proceed cautiously or tune Stage 9.1 zone bounds before Stage 10."


def build_markdown_sections(report: dict[str, Any]) -> list[tuple[str, str]]:
    return [
        ("VERDICT", field_block([("Final verdict", report["final_verdict"]), ("Friction score", report["friction"]["score"]), ("Friction level", report["friction"]["band"])])),
        ("WHY THIS STAGE EXISTS", "Stage 9 analyzed 12 ball points, but only 5 had projected coordinates. That caused 7 unknown zones. Stage 9.1 projects expanded labels directly with the Stage 3 homography and reruns tuned zone assignment."),
        ("INPUTS USED", "\n".join(f"- {name}: {path}" for name, path in report["inputs_used"].items())),
        (
            "BEFORE / AFTER SUMMARY",
            field_block(
                [
                    ("Stage 9 projected points", report["stage_9_projected_points"]),
                    ("Stage 9 unknown zones", report["stage_9_unknown_zones"]),
                    ("Stage 9.1 projected points", report["stage_9_1_projected_points"]),
                    ("Stage 9.1 unknown zones", report["stage_9_1_unknown_zones"]),
                    ("Unknown zone reduction", report["unknown_zone_reduction"]),
                    ("Projection coverage improvement", report["projection_coverage_improvement"]),
                ]
            ),
        ),
        ("ZONE DISTRIBUTION", bullet_distribution(report["tuned_zone_distribution"])),
        ("DEPTH DISTRIBUTION", bullet_distribution(report["tuned_depth_distribution"])),
        ("LATERAL DISTRIBUTION", bullet_distribution(report["tuned_lateral_distribution"])),
        ("OUTPUT ARTIFACTS", "\n".join(f"- {value}" for value in report["output_paths"].values() if value)),
        ("PRODUCT OWNER INTERPRETATION", "Stage 9.1 reduces the unknown-zone problem by projecting all expanded labels through the court homography. The metrics are more usable, but still approximate and not official line calling or coaching advice."),
        ("WARNINGS", bullet_list(report["warnings"], "No warnings.")),
        ("ERRORS", bullet_list(report["errors"], "No errors.")),
        ("NEXT STEP", report["recommended_next_step"]),
    ]


def update_lab_notebook_safely() -> tuple[dict[str, Path], str | None]:
    try:
        from tennis_vision.lab_notebook import lab_notebook_paths, update_lab_notebook

        update_lab_notebook(PROJECT_ROOT)
        return lab_notebook_paths(PROJECT_ROOT, "stage_9_1"), None
    except Exception as exc:
        try:
            from tennis_vision.lab_notebook import lab_notebook_paths

            return lab_notebook_paths(PROJECT_ROOT, "stage_9_1"), f"Lab notebook update failed: {exc}"
        except Exception:
            return {
                "stage_page": PROJECT_ROOT / "docs" / "lab-notebook" / "stage_9_1_projection_coverage.md",
                "experiment_index": PROJECT_ROOT / "docs" / "lab-notebook" / "experiment_index.md",
            }, f"Lab notebook update failed: {exc}"


def print_summary(report: dict[str, Any], lab_paths: dict[str, Path]) -> None:
    print("Stage 9.1 Projection Coverage")
    print(f"Verdict: {report['final_verdict']}")
    print(f"Friction: {report['friction']['score']} ({report['friction']['band']})")
    print(f"Stage 9 projected points: {report['stage_9_projected_points']}")
    print(f"Stage 9 unknown zones: {report['stage_9_unknown_zones']}")
    print(f"Stage 9.1 projected points: {report['stage_9_1_projected_points']}")
    print(f"Stage 9.1 unknown zones: {report['stage_9_1_unknown_zones']}")
    print(f"Unknown zone reduction: {report['unknown_zone_reduction']}")
    print(f"Lab notebook: {lab_paths['stage_page']}")


def main() -> int:
    args = parse_args()
    ensure_output_folders(PROJECT_ROOT)
    labels_path = resolve_path(args.labels)
    stage9_path = resolve_path(args.stage9_zones)
    calibration_path = resolve_path(args.calibration)
    output_dir = resolve_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    warnings: list[str] = []
    errors: list[str] = []
    labels, label_errors = load_expanded_ball_labels(labels_path)
    errors.extend(label_errors)
    stage9_rows, stage9_errors = read_csv_rows(stage9_path)
    errors.extend(stage9_errors)
    matrix, homography_info, homography_errors = load_stage_3_homography(calibration_path)
    errors.extend(homography_errors)

    projected = project_labels_to_court(labels, matrix)
    merged = merge_projected_labels_with_stage_9_assignments(projected, stage9_rows)
    tuned = tune_zone_assignments(merged)
    comparison = compare_stage_9_to_9_1(stage9_rows, tuned)
    coverage = calculate_projection_coverage(projected, stage9_rows)
    zone_summary = summarize_zone_coverage(tuned)
    unknown_reduction = coverage["stage_9_unknown_zones"] - zone_summary["stage_9_1_unknown_zones"]

    tuned_for_metrics = [
        {
            **row,
            "court_zone": row.get("tuned_zone"),
            "depth": row.get("tuned_depth"),
            "lateral_lane": row.get("tuned_lateral_lane"),
            "side": str(row.get("tuned_zone", "unknown")).split("_", 1)[0] if str(row.get("tuned_zone", "")).startswith(("near_", "far_")) else "unknown",
        }
        for row in tuned
    ]
    directions = estimate_shot_directions(tuned_for_metrics)
    rally_rows, rally_warnings = read_csv_rows(PROJECT_ROOT / "outputs" / "timeline" / "stage_8_event_timeline" / "rally_segments.csv")
    warnings.extend(rally_warnings)
    rally_summary = build_rally_tactical_summary(rally_rows, tuned_for_metrics)

    projected_csv = output_dir / "projected_expanded_labels.csv"
    tuned_csv = output_dir / "tuned_ball_zone_assignments.csv"
    comparison_csv = output_dir / "stage_9_vs_9_1_zone_comparison.csv"
    direction_csv = output_dir / "tuned_shot_direction_estimates.csv"
    rally_csv = output_dir / "tuned_rally_tactical_summary.csv"
    write_csv(projected_csv, projected, ["frame_index", "x", "y", "projected_x", "projected_y", "projection_status", "source", "notes"])
    write_csv(tuned_csv, tuned, ["frame_index", "x", "y", "projected_x", "projected_y", "original_zone", "tuned_zone", "original_depth", "tuned_depth", "original_lateral_lane", "tuned_lateral_lane", "projection_status", "zone_confidence", "notes"])
    write_csv(comparison_csv, comparison, ["frame_index", "stage_9_zone", "stage_9_1_zone", "stage_9_depth", "stage_9_1_depth", "stage_9_projection_available", "stage_9_1_projection_available", "improvement_status"])
    write_csv(direction_csv, directions, ["from_frame", "to_frame", "from_zone", "to_zone", "direction_type", "confidence_like_score", "reason"])
    write_csv(rally_csv, rally_summary, ["rally_id", "start_frame", "end_frame", "duration_seconds", "event_count", "possible_hit_count", "possible_bounce_count", "dominant_depth", "dominant_lateral_lane", "dominant_zone", "confidence_like_score", "notes"])

    projection_map = save_projection_coverage_map(output_dir / "projection_coverage_map.jpg", projected)
    tuned_map = save_tuned_ball_placement_map(output_dir / "tuned_ball_placement_map.jpg", tuned)
    comparison_preview = None

    out_of_bounds = sum(1 for row in projected if row.get("projection_status") == "outside_expected_range")
    flags = {
        "expanded_labels_missing": not labels,
        "homography_missing": matrix is None,
        "projection_failed": bool(projected and coverage["projection_failed_count"] > 0),
        "many_out_of_bounds_points": bool(projected and out_of_bounds / max(len(projected), 1) > 0.4),
        "unknown_zones_not_reduced": unknown_reduction <= 0,
        "visual_generation_failed": projection_map is None or tuned_map is None,
    }
    if flags["many_out_of_bounds_points"]:
        warnings.append("Many projected labels are outside the expected court range; review calibration or zone bounds.")
    if flags["unknown_zones_not_reduced"]:
        warnings.append("Unknown zones did not decrease after projection coverage tuning.")

    friction = calculate_stage_9_1_friction_score(**flags, warnings_count=len(warnings), errors_count=len(errors))
    report: dict[str, Any] = {
        "timestamp": utc_timestamp(),
        "stage": "stage_9_1_projection_coverage",
        "inputs_used": {
            "expanded_labels": str(labels_path),
            "stage_9_assignments": str(stage9_path),
            "court_calibration": str(calibration_path),
            "homography_source": str(calibration_path),
        },
        "expanded_labels_count": len(labels),
        "stage_9_projected_points": coverage["stage_9_projected_points"],
        "stage_9_unknown_zones": coverage["stage_9_unknown_zones"],
        "stage_9_1_projected_points": coverage["stage_9_1_projected_points"],
        "stage_9_1_unknown_zones": zone_summary["stage_9_1_unknown_zones"],
        "projection_success_count": coverage["projection_success_count"],
        "projection_failed_count": coverage["projection_failed_count"],
        "unknown_zone_reduction": unknown_reduction,
        "projection_coverage_improvement": coverage["projection_coverage_improvement"],
        "tuned_zone_distribution": zone_summary["tuned_zone_distribution"],
        "tuned_depth_distribution": zone_summary["tuned_depth_distribution"],
        "tuned_lateral_distribution": zone_summary["tuned_lateral_distribution"],
        "homography_info": homography_info,
        "warnings": warnings,
        "errors": errors,
        "flags": flags,
        "friction": friction,
        "final_verdict": "blocked",
        "recommended_next_step": "",
        "output_paths": {
            "projected_expanded_labels_csv": str(projected_csv),
            "tuned_ball_zone_assignments_csv": str(tuned_csv),
            "stage_9_vs_9_1_zone_comparison_csv": str(comparison_csv),
            "tuned_shot_direction_estimates_csv": str(direction_csv),
            "tuned_rally_tactical_summary_csv": str(rally_csv),
            "projection_coverage_map": projection_map,
            "tuned_ball_placement_map": tuned_map,
            "zone_comparison_preview": None,
        },
    }
    report["final_verdict"] = determine_verdict(report)
    report["recommended_next_step"] = recommended_next_step(report)
    comparison_preview = save_zone_comparison_preview(output_dir / "zone_comparison_preview.jpg", report)
    report["output_paths"]["zone_comparison_preview"] = comparison_preview
    if comparison_preview is None:
        report["warnings"].append("Zone comparison preview could not be generated.")

    log_path = write_timestamped_log(
        PROJECT_ROOT,
        "stage_9_1_projection_coverage",
        [
            f"timestamp={report['timestamp']}",
            f"verdict={report['final_verdict']}",
            f"friction={friction['score']} ({friction['band']})",
            f"stage_9_projected={report['stage_9_projected_points']}",
            f"stage_9_unknown={report['stage_9_unknown_zones']}",
            f"stage_9_1_projected={report['stage_9_1_projected_points']}",
            f"stage_9_1_unknown={report['stage_9_1_unknown_zones']}",
        ],
    )
    report["log_path"] = str(log_path)
    report["json_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_9_1_projection_coverage_report.json")
    report["markdown_report_path"] = str(PROJECT_ROOT / "outputs" / "reports" / "stage_9_1_projection_coverage_report.md")
    json_path = Path(report["json_report_path"])
    markdown_path = Path(report["markdown_report_path"])
    write_json_report(json_path, report)
    write_markdown_report(markdown_path, "Stage 9.1 Projection Coverage and Court Zone Tuning Report", build_markdown_sections(report))

    lab_paths, notebook_warning = update_lab_notebook_safely()
    if notebook_warning:
        report["warnings"].append(notebook_warning)
        write_json_report(json_path, report)
        write_markdown_report(markdown_path, "Stage 9.1 Projection Coverage and Court Zone Tuning Report", build_markdown_sections(report))
        print(f"Warning: {notebook_warning}")
    print_summary(report, lab_paths)
    return 1 if report["final_verdict"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
