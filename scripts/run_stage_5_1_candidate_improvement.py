"""Run Stage 5.1 ball candidate generation improvement."""

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

from tennis_vision.ball_candidate_filtering import read_manual_labels  # noqa: E402
from tennis_vision.ball_candidate_improvement import (  # noqa: E402
    add_projection,
    evaluate_strategies,
    generate_candidates_for_labels,
    save_strategy_overlays,
    save_strategy_preview,
    select_best_candidates,
    write_csv,
)
from tennis_vision.court_projection import load_stage_3_calibration, save_court_projection_preview  # noqa: E402
from tennis_vision.friction import calculate_stage_5_1_friction_score  # noqa: E402
from tennis_vision.report import (  # noqa: E402
    ensure_output_folders,
    utc_timestamp,
    write_json_report,
    write_markdown_report,
    write_timestamped_log,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 5.1 ball candidate generation improvement.")
    parser.add_argument("--video", type=Path, default=PROJECT_ROOT / "samples" / "video_01.mov")
    parser.add_argument(
        "--labels",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "ball_tracking" / "stage_4_1_manual_labels" / "manual_ball_labels.csv",
    )
    parser.add_argument(
        "--calibration-report",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "reports" / "stage_3_court_calibration_probe_report.json",
    )
    parser.add_argument(
        "--baseline-report",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "reports" / "stage_5_ball_candidate_filtering_report.json",
    )
    parser.add_argument("--resize-width", type=int, default=1280)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "ball_tracking" / "stage_5_1_candidate_improvement",
    )
    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def read_baseline_report(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"available": False, "average_distance": None, "median_distance": None}
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"available": False, "average_distance": None, "median_distance": None}
    return {
        "available": True,
        "average_distance": report.get("nearest_candidate_average_distance"),
        "median_distance": report.get("nearest_candidate_median_distance"),
        "verdict": report.get("final_verdict"),
    }


def determine_verdict(report: dict[str, Any]) -> str:
    flags = report["flags"]
    if flags["video_missing"] or flags["manual_labels_missing"] or flags["frame_load_failed"]:
        return "blocked"
    best_average = report.get("best_average_nearest_distance")
    improvement = report.get("improvement_over_baseline")
    if best_average is None:
        return "blocked"
    if improvement is not None and improvement > 0 and best_average < 150:
        return "ready_for_stage_6"
    if improvement is not None and improvement > 0 and best_average < 450:
        return "ready_with_warnings"
    return "needs_specialized_ball_model"


def recommended_next_step(report: dict[str, Any]) -> str:
    verdict = report["final_verdict"]
    if verdict == "ready_for_stage_6":
        return "Proceed to Stage 6: trajectory smoothing and rally/event segmentation probe."
    if verdict == "blocked":
        return "Fix missing video, manual labels, or frame-loading blockers, then rerun Stage 5.1."
    return "Proceed to Stage 5.2: specialized ball model research and benchmark."


def _metric_table(rows: list[tuple[str, Any]]) -> str:
    lines = ["| Metric | Value |", "|---|---|"]
    for key, value in rows:
        lines.append(f"| {key} | {value if value is not None else 'Not available'} |")
    return "\n".join(lines)


def _strategy_table(rows: list[dict[str, Any]]) -> str:
    lines = ["| Strategy | Avg distance | Median distance | Best frame | Frames <= 100 px | Candidate count |", "|---|---:|---:|---:|---:|---:|"]
    for row in rows:
        lines.append(
            "| {strategy} | {avg} | {median} | {best_frame} | {within_100} | {count} |".format(
                strategy=row.get("strategy"),
                avg=row.get("average_distance") if row.get("average_distance") is not None else "Not available",
                median=row.get("median_distance") if row.get("median_distance") is not None else "Not available",
                best_frame=row.get("best_frame") if row.get("best_frame") is not None else "Not available",
                within_100=row.get("frames_within_100_px", 0),
                count=row.get("candidate_count", 0),
            )
        )
    return "\n".join(lines)


def _bullet_list(items: list[str], empty_text: str) -> str:
    return empty_text if not items else "\n".join(f"- {item}" for item in items)


def build_markdown_sections(report: dict[str, Any]) -> list[tuple[str, str]]:
    baseline = report["baseline"]
    best = (
        f"Best strategy: `{report['best_strategy']}`. "
        f"Average distance: {report['best_average_nearest_distance']} px. "
        f"Improvement over Stage 5 baseline: {report['improvement_over_baseline']} px. "
    )
    if report["final_verdict"] == "ready_for_stage_6":
        best += "This is good enough to begin a limited smoothing probe."
    else:
        best += "This is not strong enough to treat as production tracking."

    interpretation = (
        "Stage 5.1 tests whether handcrafted local computer vision can improve candidate generation before trajectory smoothing. "
        "Manual labels are the ground truth. "
    )
    if report["final_verdict"] == "ready_for_stage_6":
        interpretation += "The improved candidates are close enough for a cautious Stage 6 probe."
    else:
        interpretation += "The result suggests specialized tennis-ball detection may still be needed for a SwingVision-style system."

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
            "Baseline",
            "\n".join(
                [
                    f"- Stage 5 average nearest distance: {baseline.get('average_distance')}",
                    f"- Stage 5 median nearest distance: {baseline.get('median_distance')}",
                ]
            ),
        ),
        ("Strategies tested", _strategy_table(report["strategy_summaries"])),
        ("Best strategy", best),
        (
            "Visual outputs",
            _metric_table(
                [
                    ("Overlay folder", report["output_paths"]["overlay_folder"]),
                    ("Strategy preview", report["output_paths"]["strategy_preview"]),
                    ("Improved candidates CSV", report["output_paths"]["improved_candidates_csv"]),
                    ("Projected candidates CSV", report["output_paths"]["projected_candidates_csv"]),
                    ("Court projection preview", report["output_paths"]["court_projection_preview"]),
                ]
            ),
        ),
        ("Product Owner interpretation", interpretation),
        ("Warnings", _bullet_list(report["warnings"], "No warnings.")),
        ("Errors", _bullet_list(report["errors"], "No errors.")),
        ("Next step", report["recommended_next_step"]),
    ]


def print_summary(report: dict[str, Any], lab_paths: dict[str, Path]) -> None:
    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(title="Stage 5.1 Candidate Improvement")
        table.add_column("Field")
        table.add_column("Value")
        rows = [
            ("Verdict", report["final_verdict"]),
            ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"),
            ("Strategies", ", ".join(report["strategies_tested"])),
            ("Best strategy", str(report["best_strategy"])),
            ("Baseline avg", str(report["baseline"].get("average_distance"))),
            ("Improved avg", str(report["best_average_nearest_distance"])),
            ("Improvement", str(report["improvement_over_baseline"])),
            ("Improved candidates", str(report["improved_candidates_count"])),
            ("Projected candidates", str(report["projected_candidates_count"])),
            ("Lab notebook", str(lab_paths["stage_page"])),
            ("Recommended next step", report["recommended_next_step"]),
        ]
        for field, value in rows:
            table.add_row(field, value)
        Console().print(table)
    except ImportError:
        print(f"Verdict: {report['final_verdict']}")
        print(f"Best strategy: {report['best_strategy']}")
        print(f"Improved average: {report['best_average_nearest_distance']}")
        print(f"Lab notebook: {lab_paths['stage_page']}")


def update_lab_notebook_safely() -> tuple[dict[str, Path], str | None]:
    try:
        from tennis_vision.lab_notebook import lab_notebook_paths, update_lab_notebook

        update_lab_notebook(PROJECT_ROOT)
        return lab_notebook_paths(PROJECT_ROOT, "stage_5_1"), None
    except Exception as exc:
        try:
            from tennis_vision.lab_notebook import lab_notebook_paths

            return lab_notebook_paths(PROJECT_ROOT, "stage_5_1"), f"Lab notebook update failed: {exc}"
        except Exception:
            return {
                "stage_page": PROJECT_ROOT / "docs" / "lab-notebook" / "stage_5_1_candidate_improvement.md",
                "experiment_index": PROJECT_ROOT / "docs" / "lab-notebook" / "experiment_index.md",
            }, f"Lab notebook update failed: {exc}"


def main() -> int:
    args = parse_args()
    ensure_output_folders(PROJECT_ROOT)
    video_path = resolve_path(args.video)
    labels_path = resolve_path(args.labels)
    calibration_report = resolve_path(args.calibration_report)
    baseline_report = resolve_path(args.baseline_report)
    output_dir = resolve_path(args.output_dir)
    overlay_dir = output_dir / "overlays"
    output_dir.mkdir(parents=True, exist_ok=True)

    warnings: list[str] = []
    errors: list[str] = []
    labels, label_errors = read_manual_labels(labels_path)
    errors.extend(label_errors)
    baseline = read_baseline_report(baseline_report)
    if not baseline["available"]:
        warnings.append("Stage 5 baseline report was not available; improvement cannot be fully measured.")
    calibration = load_stage_3_calibration(calibration_report)
    if calibration.get("error") and not calibration.get("homography_available"):
        warnings.append(str(calibration["error"]))

    result = {"bundles": {}, "candidates_by_strategy": {}, "strategies": [], "errors": []}
    if video_path.exists() and labels:
        result = generate_candidates_for_labels(
            video_path=video_path,
            labels=labels,
            court_polygon=calibration.get("court_polygon", []),
            resize_width=args.resize_width,
        )
        errors.extend(result.get("errors", []))

    comparison_rows, strategy_summaries, best_summary = evaluate_strategies(result["candidates_by_strategy"], labels) if labels else ([], [], None)
    best_strategy = best_summary.get("strategy") if best_summary else None
    best_candidates_raw = select_best_candidates(result["candidates_by_strategy"].get(best_strategy, []), labels) if best_strategy else []
    best_candidates, projected_count = add_projection(best_candidates_raw, calibration.get("matrix")) if calibration.get("homography_available") else (best_candidates_raw, 0)

    comparison_path = output_dir / "strategy_comparison.csv"
    improved_path = output_dir / "improved_ball_candidates.csv"
    projected_path = output_dir / "projected_improved_candidates.csv"
    write_csv(
        comparison_path,
        comparison_rows,
        [
            "strategy",
            "frame_index",
            "manual_x",
            "manual_y",
            "nearest_candidate_x",
            "nearest_candidate_y",
            "nearest_distance_px",
            "candidate_count",
            "within_10_px",
            "within_25_px",
            "within_50_px",
            "within_100_px",
            "within_200_px",
        ],
    )
    candidate_fields = [
        "frame_index",
        "x",
        "y",
        "radius",
        "area",
        "strategy",
        "score",
        "distance_to_manual_label",
        "projected_x",
        "projected_y",
    ]
    write_csv(improved_path, best_candidates, candidate_fields)
    projected_rows = [candidate for candidate in best_candidates if candidate.get("projected_x") is not None]
    write_csv(projected_path, projected_rows, candidate_fields)

    overlays = save_strategy_overlays(
        bundles=result["bundles"],
        labels=labels,
        best_candidates=best_candidates,
        output_dir=overlay_dir,
    )
    strategy_preview = save_strategy_preview(overlays, output_dir / "strategy_preview.jpg")
    projection_preview = save_court_projection_preview(projected_rows, output_dir / "court_projection_preview.jpg", calibration.get("target_size"))

    baseline_avg = baseline.get("average_distance")
    best_avg = best_summary.get("average_distance") if best_summary else None
    improvement = round(float(baseline_avg) - float(best_avg), 3) if baseline_avg is not None and best_avg is not None else None
    if best_avg is not None and best_avg >= 150:
        warnings.append("Improved candidates are still too far from manual labels for confident trajectory smoothing.")
    if improvement is not None and improvement <= 0:
        warnings.append("Improved strategies did not beat the Stage 5 baseline average distance.")

    flags = {
        "video_missing": not video_path.exists(),
        "manual_labels_missing": not labels_path.exists() or not labels,
        "frame_load_failed": bool(labels and not result["bundles"]),
        "no_candidates_generated": not any(result["candidates_by_strategy"].values()) if result["candidates_by_strategy"] else True,
        "no_improvement": bool(improvement is not None and improvement <= 0),
        "candidates_still_far": bool(best_avg is not None and best_avg >= 150),
        "projection_failed": bool(calibration.get("homography_available") and best_candidates and projected_count == 0),
    }
    friction = calculate_stage_5_1_friction_score(**flags, errors_count=len(errors), warnings_count=len(warnings))

    report: dict[str, Any] = {
        "timestamp": utc_timestamp(),
        "stage": "stage_5_1_candidate_improvement",
        "input_video_path": str(video_path),
        "manual_labels_path": str(labels_path),
        "labeled_frames_count": len(labels),
        "labeled_frames": [label["frame_index"] for label in labels],
        "strategies_tested": result["strategies"],
        "baseline": baseline,
        "best_strategy": best_strategy,
        "best_average_nearest_distance": best_avg,
        "best_median_nearest_distance": best_summary.get("median_distance") if best_summary else None,
        "improvement_over_baseline": improvement,
        "frames_within_10_px": best_summary.get("frames_within_10_px", 0) if best_summary else 0,
        "frames_within_25_px": best_summary.get("frames_within_25_px", 0) if best_summary else 0,
        "frames_within_50_px": best_summary.get("frames_within_50_px", 0) if best_summary else 0,
        "frames_within_100_px": best_summary.get("frames_within_100_px", 0) if best_summary else 0,
        "frames_within_200_px": best_summary.get("frames_within_200_px", 0) if best_summary else 0,
        "strategy_summaries": strategy_summaries,
        "improved_candidates_count": len(best_candidates),
        "projected_candidates_count": projected_count,
        "calibration_status": {
            "homography_available": bool(calibration.get("homography_available")),
            "court_polygon_available": bool(calibration.get("court_polygon")),
        },
        "output_paths": {
            "strategy_comparison_csv": str(comparison_path),
            "improved_candidates_csv": str(improved_path),
            "projected_candidates_csv": str(projected_path),
            "overlay_folder": str(overlay_dir),
            "strategy_preview": strategy_preview,
            "court_projection_preview": projection_preview,
        },
        "warnings": warnings,
        "errors": errors,
        "flags": flags,
        "friction": friction,
        "final_verdict": "blocked",
        "recommended_next_step": "",
        "json_report_path": str(PROJECT_ROOT / "outputs" / "reports" / "stage_5_1_candidate_improvement_report.json"),
        "markdown_report_path": str(PROJECT_ROOT / "outputs" / "reports" / "stage_5_1_candidate_improvement_report.md"),
        "log_path": "",
    }
    report["final_verdict"] = determine_verdict(report)
    report["recommended_next_step"] = recommended_next_step(report)

    log_path = write_timestamped_log(
        PROJECT_ROOT,
        "stage_5_1_candidate_improvement",
        [
            f"timestamp={report['timestamp']}",
            f"verdict={report['final_verdict']}",
            f"friction={friction['score']} ({friction['band']})",
            f"best_strategy={best_strategy}",
            f"baseline_avg={baseline_avg}",
            f"improved_avg={best_avg}",
            f"improvement={improvement}",
        ],
    )
    report["log_path"] = str(log_path)

    json_path = Path(report["json_report_path"])
    markdown_path = Path(report["markdown_report_path"])
    write_json_report(json_path, report)
    write_markdown_report(markdown_path, "Stage 5.1 Ball Candidate Generation Improvement Report", build_markdown_sections(report))

    lab_paths, notebook_warning = update_lab_notebook_safely()
    if notebook_warning:
        report["warnings"].append(notebook_warning)
        write_json_report(json_path, report)
        write_markdown_report(markdown_path, "Stage 5.1 Ball Candidate Generation Improvement Report", build_markdown_sections(report))
        print(f"Warning: {notebook_warning}")

    print_summary(report, lab_paths)
    return 1 if report["final_verdict"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
