"""Run Stage 5 ball candidate filtering and court projection."""

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

from tennis_vision.ball_candidate_filtering import (  # noqa: E402
    add_projection_to_rows,
    compare_candidates_to_labels,
    filter_candidates,
    read_ball_candidates,
    read_manual_labels,
    save_filtered_trajectory_preview,
    write_csv,
)
from tennis_vision.court_projection import (  # noqa: E402
    load_stage_3_calibration,
    project_image_points,
    save_court_projection_preview,
)
from tennis_vision.friction import calculate_stage_5_friction_score  # noqa: E402
from tennis_vision.report import (  # noqa: E402
    ensure_output_folders,
    utc_timestamp,
    write_json_report,
    write_markdown_report,
    write_timestamped_log,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 5 ball candidate filtering and court projection.")
    parser.add_argument(
        "--candidates",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "ball_tracking" / "stage_4_ball_probe" / "ball_candidates.csv",
        help="Stage 4 automatic candidate CSV.",
    )
    parser.add_argument(
        "--labels",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "ball_tracking" / "stage_4_1_manual_labels" / "manual_ball_labels.csv",
        help="Stage 4.1 manual labels CSV.",
    )
    parser.add_argument(
        "--calibration-report",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "reports" / "stage_3_court_calibration_probe_report.json",
        help="Stage 3 report containing homography.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "ball_tracking" / "stage_5_filtered_candidates",
        help="Stage 5 output directory.",
    )
    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def determine_verdict(report: dict[str, Any]) -> str:
    flags = report["flags"]
    if flags["candidate_csv_missing"] or flags["manual_labels_missing"] or flags["comparison_failed"] or flags["filtering_failed"]:
        return "blocked"
    if flags["nearest_candidates_too_far"]:
        return "needs_better_ball_model"
    if report["projected_candidates_count"] > 0 and report["frames_within_100_px"] > 0:
        return "ready_for_stage_6"
    return "ready_with_warnings"


def recommended_next_step(report: dict[str, Any]) -> str:
    if report["final_verdict"] == "ready_for_stage_6":
        return "Proceed to Stage 6: trajectory smoothing and event/rally segmentation probe."
    if report["final_verdict"] == "needs_better_ball_model":
        return "Proceed to Stage 5.1: specialized ball detector research or improved candidate generation."
    if report["final_verdict"] == "blocked":
        return "Fix missing or unreadable Stage 4/Stage 4.1 inputs, then rerun Stage 5."
    return "Review Stage 5 warnings, then decide between Stage 6 smoothing or Stage 5.1 detector improvement."


def recommended_fixes(report: dict[str, Any]) -> list[str]:
    flags = report["flags"]
    fixes: list[str] = []
    if flags["candidate_csv_missing"]:
        fixes.append("Run Stage 4 to regenerate automatic ball candidates.")
    if flags["manual_labels_missing"]:
        fixes.append("Run Stage 4.1 interactively and save manual ball labels.")
    if flags["homography_missing"]:
        fixes.append("Rerun Stage 3 and confirm homography is computed.")
    if flags["nearest_candidates_too_far"]:
        fixes.append("Improve candidate generation or research a specialized tennis ball detector.")
    if flags["too_many_false_candidates"]:
        fixes.append("Use Stage 5 filtering outputs to constrain candidates by court and temporal consistency.")
    if flags["projection_failed"]:
        fixes.append("Check Stage 3 homography and calibration report.")
    return fixes


def _metric_table(rows: list[tuple[str, Any]]) -> str:
    lines = ["| Metric | Value |", "|---|---|"]
    for key, value in rows:
        lines.append(f"| {key} | {value if value is not None else 'Not available'} |")
    return "\n".join(lines)


def _bullet_list(items: list[str], empty_text: str) -> str:
    if not items:
        return empty_text
    return "\n".join(f"- {item}" for item in items)


def build_markdown_sections(report: dict[str, Any]) -> list[tuple[str, str]]:
    comparison_rows = [
        ("manual labels count", report["manual_labels_count"]),
        ("automatic candidates count", report["automatic_candidates_count"]),
        ("labeled frames compared", report["labeled_frames_compared"]),
        ("average nearest distance", report["nearest_candidate_average_distance"]),
        ("median nearest distance", report["nearest_candidate_median_distance"]),
        ("frames within 10 px", report["frames_within_10_px"]),
        ("frames within 25 px", report["frames_within_25_px"]),
        ("frames within 50 px", report["frames_within_50_px"]),
        ("frames within 100 px", report["frames_within_100_px"]),
        ("frames within 200 px", report["frames_within_200_px"]),
    ]
    filter_rows = [
        ("selected candidates", report["filtered_candidates_count"]),
        ("rejected candidates", report["rejected_candidates_count"]),
        ("main rejection reasons", report["main_rejection_reasons"]),
    ]
    projection = (
        f"Homography available: {report['homography_status']['homography_available']}. "
        f"Projection succeeded for {report['projected_candidates_count']} candidates. "
        f"Preview: `{report['output_paths']['court_projection_preview'] or 'Not available'}`."
    )
    interpretation = (
        "Stage 5 compares noisy Stage 4 candidates against manual labels and selects a cleaner baseline trajectory. "
        "This is still not production tracking. "
    )
    if report["frames_within_100_px"] > 0:
        interpretation += "At least some automatic candidates are close enough to manual labels to support Stage 6 smoothing. "
    else:
        interpretation += "Automatic candidates are not close enough to the manual labels, so a specialized ball model is likely needed. "
    if report["projected_candidates_count"] > 0:
        interpretation += "Court projection is working for selected candidates."
    else:
        interpretation += "Court projection is not yet producing usable projected candidates."
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
            "Inputs",
            "\n".join(
                [
                    f"- Automatic candidates CSV: `{report['input_candidate_csv']}`",
                    f"- Manual labels CSV: `{report['input_manual_labels_csv']}`",
                    f"- Calibration source: `{report['calibration_source']}`",
                    f"- Homography status: {report['homography_status']['homography_available']}",
                ]
            ),
        ),
        ("Candidate-to-label comparison", _metric_table(comparison_rows)),
        ("Filtered candidates", _metric_table(filter_rows)),
        ("Court projection", projection),
        ("Interpretation", interpretation),
        ("Warnings", _bullet_list(report["warnings"], "No warnings.")),
        ("Errors", _bullet_list(report["errors"], "No errors.")),
        ("Recommended fixes", _bullet_list(report["recommended_fixes"], "No fixes required.")),
        ("Next step", report["recommended_next_step"]),
    ]


def save_overlays(
    *,
    labels: list[dict[str, Any]],
    distance_rows: list[dict[str, Any]],
    filtered_rows: list[dict[str, Any]],
    overlay_dir: Path,
) -> list[str]:
    """Save lightweight review overlays for labeled and selected candidates."""
    overlay_dir.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []
    nearest_by_frame = {}
    for row in distance_rows:
        if int(row["candidate_rank"]) == 1:
            nearest_by_frame[int(row["frame_index"])] = row
    selected_by_frame = {int(row["frame_index"]): row for row in filtered_rows if row["selected"]}
    for label in labels:
        frame_index = int(label["frame_index"])
        canvas = np.full((720, 1280, 3), 255, dtype=np.uint8)
        scale_x = 1280 / 3840
        scale_y = 720 / 2160
        lx = int(round(label["x"] * scale_x))
        ly = int(round(label["y"] * scale_y))
        cv2.circle(canvas, (lx, ly), 10, (0, 0, 255), -1)
        cv2.putText(canvas, f"manual {frame_index}", (lx + 12, ly - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1)
        nearest = nearest_by_frame.get(frame_index)
        if nearest:
            nx = int(round(float(nearest["candidate_x"]) * scale_x))
            ny = int(round(float(nearest["candidate_y"]) * scale_y))
            cv2.circle(canvas, (nx, ny), 10, (0, 255, 255), 2)
            cv2.line(canvas, (lx, ly), (nx, ny), (0, 180, 255), 1)
        selected = selected_by_frame.get(frame_index)
        if selected:
            sx = int(round(float(selected["x"]) * scale_x))
            sy = int(round(float(selected["y"]) * scale_y))
            cv2.circle(canvas, (sx, sy), 14, (0, 180, 0), 2)
        path = overlay_dir / f"stage_5_label_candidate_frame_{frame_index:06d}.jpg"
        if cv2.imwrite(str(path), canvas):
            saved.append(str(path))
    return saved


def print_summary(report: dict[str, Any], lab_paths: dict[str, Path]) -> None:
    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(title="Stage 5 Ball Candidate Filtering")
        table.add_column("Field")
        table.add_column("Value")
        rows = [
            ("Verdict", report["final_verdict"]),
            ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"),
            ("Manual labels", str(report["manual_labels_count"])),
            ("Auto candidates", str(report["automatic_candidates_count"])),
            ("Avg nearest distance", str(report["nearest_candidate_average_distance"])),
            ("Median nearest distance", str(report["nearest_candidate_median_distance"])),
            ("Filtered candidates", str(report["filtered_candidates_count"])),
            ("Projected candidates", str(report["projected_candidates_count"])),
            ("Report", report["json_report_path"]),
            ("Lab notebook", str(lab_paths["stage_page"])),
            ("Recommended next step", report["recommended_next_step"]),
        ]
        for field, value in rows:
            table.add_row(field, value)
        Console().print(table)
    except ImportError:
        print(f"Verdict: {report['final_verdict']}")
        print(f"Friction: {report['friction']['score']} ({report['friction']['band']})")
        print(f"Manual labels: {report['manual_labels_count']}")
        print(f"Auto candidates: {report['automatic_candidates_count']}")
        print(f"Filtered candidates: {report['filtered_candidates_count']}")
        print(f"Projected candidates: {report['projected_candidates_count']}")
        print(f"Lab notebook: {lab_paths['stage_page']}")


def update_lab_notebook_safely() -> tuple[dict[str, Path], str | None]:
    try:
        from tennis_vision.lab_notebook import lab_notebook_paths, update_lab_notebook

        update_lab_notebook(PROJECT_ROOT)
        return lab_notebook_paths(PROJECT_ROOT, "stage_5"), None
    except Exception as exc:
        try:
            from tennis_vision.lab_notebook import lab_notebook_paths

            return lab_notebook_paths(PROJECT_ROOT, "stage_5"), f"Lab notebook update failed: {exc}"
        except Exception:
            return {
                "stage_page": PROJECT_ROOT / "docs" / "lab-notebook" / "stage_5_ball_candidate_filtering.md",
                "experiment_index": PROJECT_ROOT / "docs" / "lab-notebook" / "experiment_index.md",
            }, f"Lab notebook update failed: {exc}"


def main() -> int:
    args = parse_args()
    ensure_output_folders(PROJECT_ROOT)
    candidate_csv = resolve_path(args.candidates)
    labels_csv = resolve_path(args.labels)
    calibration_report = resolve_path(args.calibration_report)
    output_dir = resolve_path(args.output_dir)
    overlay_dir = output_dir / "overlays"
    output_dir.mkdir(parents=True, exist_ok=True)

    candidates, candidate_errors = read_ball_candidates(candidate_csv)
    labels, label_errors = read_manual_labels(labels_csv)
    calibration = load_stage_3_calibration(calibration_report)
    warnings: list[str] = [*calibration.get("warnings", [])]
    errors: list[str] = [*candidate_errors, *label_errors]
    if calibration.get("error") and not calibration.get("homography_available"):
        warnings.append(str(calibration["error"]))

    distance_rows, comparison = compare_candidates_to_labels(candidates, labels) if candidates and labels else ([], {})
    filtered_rows, filter_summary = filter_candidates(candidates, labels, calibration.get("court_polygon", [])) if candidates and labels else ([], {"selected_candidates": 0, "rejected_candidates": 0, "main_rejection_reasons": {}})
    projected_count = 0
    if calibration.get("homography_available") and filtered_rows:
        filtered_rows, projected_count = add_projection_to_rows(filtered_rows, calibration.get("matrix"))
    projected_rows = [row for row in filtered_rows if row["selected"] and row.get("projected_x") is not None]

    distance_path = output_dir / "candidate_label_distances.csv"
    filtered_path = output_dir / "filtered_ball_candidates.csv"
    projected_path = output_dir / "projected_ball_candidates.csv"
    write_csv(
        distance_path,
        distance_rows,
        [
            "frame_index",
            "manual_x",
            "manual_y",
            "candidate_x",
            "candidate_y",
            "distance_px",
            "candidate_rank",
            "within_10_px",
            "within_25_px",
            "within_50_px",
            "within_100_px",
            "within_200_px",
        ],
    )
    write_csv(
        filtered_path,
        filtered_rows,
        [
            "frame_index",
            "x",
            "y",
            "selected",
            "filter_reason",
            "score",
            "source_score",
            "distance_reference_px",
            "inside_or_near_court",
            "court_signed_distance",
            "projected_x",
            "projected_y",
        ],
    )
    write_csv(
        projected_path,
        projected_rows,
        ["frame_index", "x", "y", "score", "projected_x", "projected_y", "filter_reason"],
    )
    trajectory_preview = save_filtered_trajectory_preview(filtered_rows, output_dir / "filtered_trajectory_preview.jpg")
    projection_preview = save_court_projection_preview(projected_rows, output_dir / "court_projection_preview.jpg", calibration.get("target_size"))
    overlay_files = save_overlays(labels=labels, distance_rows=distance_rows, filtered_rows=filtered_rows, overlay_dir=overlay_dir)

    avg_distance = comparison.get("nearest_candidate_average_distance")
    median_distance = comparison.get("nearest_candidate_median_distance")
    flags = {
        "candidate_csv_missing": not candidate_csv.exists(),
        "manual_labels_missing": not labels_csv.exists() or not labels,
        "homography_missing": not bool(calibration.get("homography_available")),
        "comparison_failed": bool(candidates and labels and not distance_rows),
        "filtering_failed": bool(candidates and labels and not filtered_rows),
        "projection_failed": bool(calibration.get("homography_available") and filter_summary["selected_candidates"] > 0 and projected_count == 0),
        "nearest_candidates_too_far": bool(median_distance is not None and median_distance > 800),
        "too_many_false_candidates": bool(candidates and labels and len(candidates) / max(len(labels), 1) > 20),
    }
    if flags["too_many_false_candidates"]:
        warnings.append("Automatic candidates still contain many false positives relative to manual labels.")
    if flags["nearest_candidates_too_far"]:
        warnings.append("Nearest automatic candidates are consistently far from manual ball labels.")
    if flags["projection_failed"]:
        warnings.append("Court projection failed for selected candidates.")

    friction = calculate_stage_5_friction_score(
        **flags,
        errors_count=len(errors),
        warnings_count=len(warnings),
    )

    report: dict[str, Any] = {
        "timestamp": utc_timestamp(),
        "stage": "stage_5_ball_candidate_filtering",
        "input_candidate_csv": str(candidate_csv),
        "input_manual_labels_csv": str(labels_csv),
        "calibration_source": str(calibration_report),
        "calibration_status": calibration,
        "homography_status": {
            "homography_available": bool(calibration.get("homography_available")),
            "target_size": calibration.get("target_size"),
        },
        "manual_labels_count": len(labels),
        "automatic_candidates_count": len(candidates),
        "labeled_frames_compared": comparison.get("labeled_frames_compared", 0),
        "nearest_candidate_average_distance": avg_distance,
        "nearest_candidate_median_distance": median_distance,
        "frames_within_10_px": comparison.get("frames_within_10_px", 0),
        "frames_within_25_px": comparison.get("frames_within_25_px", 0),
        "frames_within_50_px": comparison.get("frames_within_50_px", 0),
        "frames_within_100_px": comparison.get("frames_within_100_px", 0),
        "frames_within_200_px": comparison.get("frames_within_200_px", 0),
        "filtered_candidates_count": filter_summary["selected_candidates"],
        "rejected_candidates_count": filter_summary["rejected_candidates"],
        "main_rejection_reasons": filter_summary["main_rejection_reasons"],
        "projected_candidates_count": projected_count,
        "overlay_files_count": len(overlay_files),
        "output_paths": {
            "candidate_label_distances": str(distance_path),
            "filtered_ball_candidates": str(filtered_path),
            "projected_ball_candidates": str(projected_path),
            "filtered_trajectory_preview": trajectory_preview,
            "court_projection_preview": projection_preview,
            "overlays": str(overlay_dir),
        },
        "warnings": warnings,
        "errors": errors,
        "flags": flags,
        "friction": friction,
        "final_verdict": "blocked",
        "recommended_fixes": [],
        "recommended_next_step": "",
        "json_report_path": str(PROJECT_ROOT / "outputs" / "reports" / "stage_5_ball_candidate_filtering_report.json"),
        "markdown_report_path": str(PROJECT_ROOT / "outputs" / "reports" / "stage_5_ball_candidate_filtering_report.md"),
        "log_path": "",
    }
    report["final_verdict"] = determine_verdict(report)
    report["recommended_next_step"] = recommended_next_step(report)
    report["recommended_fixes"] = recommended_fixes(report)

    log_path = write_timestamped_log(
        PROJECT_ROOT,
        "stage_5_ball_candidate_filtering",
        [
            f"timestamp={report['timestamp']}",
            f"verdict={report['final_verdict']}",
            f"friction={friction['score']} ({friction['band']})",
            f"manual_labels={len(labels)}",
            f"automatic_candidates={len(candidates)}",
            f"filtered_candidates={filter_summary['selected_candidates']}",
            f"projected_candidates={projected_count}",
        ],
    )
    report["log_path"] = str(log_path)

    json_path = Path(report["json_report_path"])
    markdown_path = Path(report["markdown_report_path"])
    write_json_report(json_path, report)
    write_markdown_report(markdown_path, "Stage 5 Ball Candidate Filtering and Court Projection Report", build_markdown_sections(report))

    lab_paths, notebook_warning = update_lab_notebook_safely()
    if notebook_warning:
        report["warnings"].append(notebook_warning)
        write_json_report(json_path, report)
        write_markdown_report(markdown_path, "Stage 5 Ball Candidate Filtering and Court Projection Report", build_markdown_sections(report))
        print(f"Warning: {notebook_warning}")

    print_summary(report, lab_paths)
    return 1 if report["final_verdict"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
