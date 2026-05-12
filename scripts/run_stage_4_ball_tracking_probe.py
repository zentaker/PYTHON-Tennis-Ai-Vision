"""Run Stage 4 local ball tracking probe."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from tennis_vision.ball_tracking_probe import run_ball_tracking_probe  # noqa: E402
from tennis_vision.friction import calculate_stage_4_friction_score  # noqa: E402
from tennis_vision.lab_notebook import read_json_report  # noqa: E402
from tennis_vision.report import (  # noqa: E402
    ensure_output_folders,
    utc_timestamp,
    write_json_report,
    write_markdown_report,
    write_timestamped_log,
)


PREFERRED_DEFAULT_VIDEOS = (
    PROJECT_ROOT / "samples" / "video_01.mov",
    PROJECT_ROOT / "samples" / "video_01.MOV",
    PROJECT_ROOT / "samples" / "video_01.mp4",
    PROJECT_ROOT / "samples" / "video_01.MP4",
)
SAMPLE_VIDEO_EXTENSIONS = (".mov", ".MOV", ".mp4", ".MP4", ".avi", ".mkv", ".m4v")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 4 local ball tracking probe.")
    parser.add_argument("--video", type=Path, default=None, help="Path to a local video file.")
    parser.add_argument("--max-frames", type=int, default=20, help="Maximum sampled frames to process.")
    parser.add_argument("--interval", type=int, default=15, help="Process one frame every N video frames.")
    parser.add_argument("--resize-width", type=int, default=1280, help="Resize sampled frames to this width.")
    parser.add_argument("--use-yolo", dest="use_yolo", action="store_true", help="Run optional YOLO reference pass.")
    parser.add_argument("--no-yolo", dest="use_yolo", action="store_false", help="Disable YOLO reference pass.")
    parser.add_argument("--confidence", type=float, default=0.25, help="YOLO confidence threshold if enabled.")
    parser.set_defaults(use_yolo=False)
    return parser.parse_args()


def resolve_video_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def detect_default_video() -> dict[str, Any]:
    samples_dir = PROJECT_ROOT / "samples"
    checked_paths: list[str] = []
    for candidate in PREFERRED_DEFAULT_VIDEOS:
        checked_paths.append(str(candidate))
        if candidate.exists() and candidate.is_file():
            return {
                "path": candidate,
                "source": "auto_detected",
                "detection_method": "preferred_default",
                "checked_paths": checked_paths,
                "warnings": [],
            }

    discovered: list[Path] = []
    if samples_dir.exists():
        for extension in SAMPLE_VIDEO_EXTENSIONS:
            discovered.extend(path for path in sorted(samples_dir.glob(f"*{extension}")) if path.is_file())
    if discovered:
        return {
            "path": discovered[0],
            "source": "auto_detected",
            "detection_method": "first_supported_video_in_samples",
            "checked_paths": checked_paths,
            "warnings": ["Preferred sample names were not found; using the first supported video file in samples/."],
        }

    return {
        "path": PREFERRED_DEFAULT_VIDEOS[0],
        "source": "not_found_fallback",
        "detection_method": "not_found_fallback",
        "checked_paths": checked_paths,
        "warnings": ["No supported sample video was found in samples/."],
    }


def select_video_path(cli_video: Path | None) -> dict[str, Any]:
    if cli_video is not None:
        path = resolve_video_path(cli_video)
        return {
            "path": path,
            "source": "cli",
            "detection_method": "cli_argument",
            "checked_paths": [str(path)],
            "warnings": [],
        }
    return detect_default_video()


def stage_3_spatial_status() -> dict[str, Any]:
    report = read_json_report(PROJECT_ROOT / "outputs" / "reports" / "stage_3_court_calibration_probe_report.json")
    if report is None:
        return {
            "stage_3_report_found": False,
            "spatially_useful": False,
            "warning": "Stage 3 report was not found; Stage 4 detections are image-space only.",
        }
    useful = report.get("final_verdict") == "ready_for_stage_4" and bool(report.get("homography_status", {}).get("computed"))
    return {
        "stage_3_report_found": True,
        "stage_3_verdict": report.get("final_verdict"),
        "homography_computed": bool(report.get("homography_status", {}).get("computed")),
        "spatially_useful": useful,
        "warning": None if useful else "Stage 3 homography is not valid; Stage 4 detections are image-space only.",
    }


def determine_verdict(report: dict[str, Any]) -> str:
    flags = report["flags"]
    if flags["video_missing"] or flags["video_open_failed"] or flags["no_frames_processed"]:
        return "blocked"
    if flags["no_ball_candidates"]:
        return "needs_better_ball_model"
    if report["warnings"] or flags["too_many_false_candidates"] or flags["yolo_too_slow"]:
        return "ready_with_warnings"
    return "ready_for_stage_5"


def recommended_next_step(report: dict[str, Any]) -> str:
    verdict = report["final_verdict"]
    if verdict in {"ready_for_stage_5", "ready_with_warnings"}:
        return "Proceed to Stage 5: Ball Candidate Filtering and Court Projection."
    if verdict == "needs_better_ball_model":
        return "Research a specialized tennis ball tracker or GPU-based model later; keep this heuristic as a documented baseline."
    return "Fix video loading or frame sampling blockers, then rerun Stage 4."


def recommended_fixes(report: dict[str, Any]) -> list[str]:
    fixes: list[str] = []
    flags = report["flags"]
    if flags["video_missing"]:
        fixes.append("Place the sample video at samples/video_01.mov or pass --video PATH.")
    if flags["video_open_failed"]:
        fixes.append("Confirm OpenCV can read the local video or convert it to MP4/H.264 later.")
    if flags["no_frames_processed"]:
        fixes.append("Try a smaller --interval or --max-frames value that fits the video length.")
    if flags["no_ball_candidates"]:
        fixes.append("Try a smaller resize width, different HSV thresholds in code, or a specialized tennis ball model later.")
    if flags["too_many_false_candidates"]:
        fixes.append("Stage 5 should filter candidates by motion consistency and court position.")
    if flags["yolo_too_slow"]:
        fixes.append("Keep YOLO optional; consider GPU only after local CPU friction is documented.")
    return fixes


def _bullet_list(items: list[str], empty_text: str = "No warnings.") -> str:
    if not items:
        return empty_text
    return "\n".join(f"- {item}" for item in items)


def _candidate_metric_table(result: dict[str, Any]) -> str:
    rows = [
        ("Frames processed", result["frames_processed"]),
        ("Total candidates", result["candidate_count"]),
        ("Frames with candidates", result["frames_with_candidates"]),
        ("Average candidates per frame", result["average_candidates_per_frame"]),
    ]
    lines = ["| Metric | Value |", "|---|---|"]
    for metric, value in rows:
        lines.append(f"| {metric} | {value} |")
    return "\n".join(lines)


def build_markdown_sections(report: dict[str, Any]) -> list[tuple[str, str]]:
    result = report["ball_tracking_result"]
    interpretation = (
        "The simple OpenCV heuristic found ball-like candidates, but these detections are likely noisy. "
        "This validates a local image-space candidate probe, not production ball tracking. Stage 5 should filter candidates by motion and court geometry."
        if result["candidate_count"] > 0
        else "The simple OpenCV heuristic did not find ball candidates in the sampled frames. A specialized tennis ball model or GPU-backed detector may be needed later."
    )
    if report["stage_3_spatial_status"].get("spatially_useful"):
        interpretation += " Stage 3 homography is available, so future filtering can project candidates into the calibrated court plane."
    else:
        interpretation += " Stage 3 homography is not available, so these results should be treated as image-space only."
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
                    f"- Video path: `{report['video_path']}`",
                    f"- Max frames: {report['max_frames']}",
                    f"- Interval: {report['interval']}",
                    f"- Resize width: {report['resize_width']}",
                    f"- YOLO enabled: {'yes' if report['yolo_enabled'] else 'no'}",
                ]
            ),
        ),
        (
            "Output",
            "\n".join(
                [
                    f"- Overlay folder: `{result['overlay_folder']}`",
                    f"- Candidate CSV path: `{result['csv_path']}`",
                    f"- Trajectory preview path: `{result['trajectory_preview_path'] or 'Not created'}`",
                    f"- JSON report: `{report['json_report_path']}`",
                    f"- Markdown report: `{report['markdown_report_path']}`",
                    f"- Log path: `{report['log_path']}`",
                ]
            ),
        ),
        ("Candidate summary", _candidate_metric_table(result)),
        ("Interpretation", interpretation),
        ("Warnings", _bullet_list(report["warnings"], "No warnings.")),
        ("Errors", _bullet_list(report["errors"], "No errors.")),
        ("Recommended fixes", _bullet_list(report["recommended_fixes"], "No fixes required.")),
        ("Next step", report["recommended_next_step"]),
    ]


def print_summary(report: dict[str, Any], lab_paths: dict[str, Path]) -> None:
    result = report["ball_tracking_result"]
    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(title="Stage 4 Ball Tracking Probe")
        table.add_column("Field")
        table.add_column("Value")
        rows = [
            ("Stage name", "Stage 4 ball tracking probe"),
            ("Input video", report["video_path"]),
            ("Verdict", report["final_verdict"]),
            ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"),
            ("Frames processed", str(result["frames_processed"])),
            ("Ball candidates", str(result["candidate_count"])),
            ("Frames with candidates", str(result["frames_with_candidates"])),
            ("Average candidates/frame", str(result["average_candidates_per_frame"])),
            ("YOLO enabled", "yes" if report["yolo_enabled"] else "no"),
            ("Overlay folder", result["overlay_folder"]),
            ("Candidate CSV", result["csv_path"]),
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
        print("Stage name: Stage 4 ball tracking probe")
        print(f"Input video: {report['video_path']}")
        print(f"Verdict: {report['final_verdict']}")
        print(f"Friction: {report['friction']['score']} ({report['friction']['band']})")
        print(f"Frames processed: {result['frames_processed']}")
        print(f"Ball candidates: {result['candidate_count']}")
        print(f"Overlay folder: {result['overlay_folder']}")
        print(f"Candidate CSV: {result['csv_path']}")
        print(f"Lab notebook: {lab_paths['stage_page']}")
        print(f"Experiment index: {lab_paths['experiment_index']}")
        print(f"Recommended next step: {report['recommended_next_step']}")


def update_lab_notebook_safely() -> tuple[dict[str, Path], str | None]:
    try:
        from tennis_vision.lab_notebook import lab_notebook_paths, update_lab_notebook

        update_lab_notebook(PROJECT_ROOT)
        return lab_notebook_paths(PROJECT_ROOT, "stage_4"), None
    except Exception as exc:
        try:
            from tennis_vision.lab_notebook import lab_notebook_paths

            return lab_notebook_paths(PROJECT_ROOT, "stage_4"), f"Lab notebook update failed: {exc}"
        except Exception:
            return {
                "stage_page": PROJECT_ROOT / "docs" / "lab-notebook" / "stage_4_ball_tracking_probe.md",
                "experiment_index": PROJECT_ROOT / "docs" / "lab-notebook" / "experiment_index.md",
            }, f"Lab notebook update failed: {exc}"


def main() -> int:
    args = parse_args()
    ensure_output_folders(PROJECT_ROOT)
    selection = select_video_path(args.video)
    video_path = selection["path"]
    output_folder = PROJECT_ROOT / "outputs" / "ball_tracking" / "stage_4_ball_probe"

    spatial_status = stage_3_spatial_status()
    result = run_ball_tracking_probe(
        video_path=video_path,
        output_folder=output_folder,
        max_frames=args.max_frames,
        interval=args.interval,
        resize_width=args.resize_width,
        use_yolo=args.use_yolo,
        confidence=args.confidence,
    )

    warnings = [*selection["warnings"], *result["warnings"]]
    if spatial_status.get("warning"):
        warnings.append(spatial_status["warning"])
    errors = list(result["errors"])
    yolo_reference = result.get("yolo_reference", {})
    yolo_average = yolo_reference.get("average_seconds_per_frame") if isinstance(yolo_reference, dict) else None
    flags = {
        "video_missing": not video_path.exists(),
        "video_open_failed": video_path.exists() and any("OpenCV could not open" in error for error in errors),
        "no_frames_processed": result["frames_processed"] == 0,
        "no_ball_candidates": result["frames_processed"] > 0 and result["candidate_count"] == 0,
        "too_many_false_candidates": result["average_candidates_per_frame"] > 6,
        "yolo_too_slow": bool(args.use_yolo and yolo_average is not None and yolo_average > 2.0),
    }
    if flags["too_many_false_candidates"]:
        warnings.append(
            "Many ball-like candidates were detected per frame; the heuristic is likely noisy and needs Stage 5 filtering."
        )
    if flags["yolo_too_slow"]:
        warnings.append("Optional YOLO reference inference was slow on CPU.")
    friction = calculate_stage_4_friction_score(
        **flags,
        errors_count=len(errors),
        warnings_count=len(warnings),
        manual_action_required=flags["no_ball_candidates"],
    )

    report: dict[str, Any] = {
        "timestamp": utc_timestamp(),
        "stage": "stage_4_ball_tracking_probe",
        "video_path": str(video_path),
        "input_selection": {
            "path": str(selection["path"]),
            "source": selection["source"],
            "detection_method": selection["detection_method"],
            "checked_paths": selection["checked_paths"],
            "warnings": selection["warnings"],
        },
        "max_frames": args.max_frames,
        "interval": args.interval,
        "resize_width": args.resize_width,
        "confidence": args.confidence,
        "yolo_enabled": bool(args.use_yolo),
        "stage_3_spatial_status": spatial_status,
        "frames_processed": result["frames_processed"],
        "candidate_count": result["candidate_count"],
        "candidate_count_by_frame": result["candidate_count_by_frame"],
        "average_candidates_per_frame": result["average_candidates_per_frame"],
        "csv_path": result["csv_path"],
        "overlay_folder": result["overlay_folder"],
        "trajectory_preview_path": result["trajectory_preview_path"],
        "ball_tracking_result": result,
        "flags": flags,
        "warnings": warnings,
        "errors": errors,
        "recommended_fixes": [],
        "friction": friction,
        "final_verdict": "blocked",
        "recommended_next_step": "",
        "json_report_path": str(PROJECT_ROOT / "outputs" / "reports" / "stage_4_ball_tracking_probe_report.json"),
        "markdown_report_path": str(PROJECT_ROOT / "outputs" / "reports" / "stage_4_ball_tracking_probe_report.md"),
        "log_path": "",
    }
    report["final_verdict"] = determine_verdict(report)
    report["recommended_next_step"] = recommended_next_step(report)
    report["recommended_fixes"] = recommended_fixes(report)

    log_path = write_timestamped_log(
        PROJECT_ROOT,
        "stage_4_ball_tracking_probe",
        [
            f"timestamp={report['timestamp']}",
            f"video={video_path}",
            f"verdict={report['final_verdict']}",
            f"friction={friction['score']} ({friction['band']})",
            f"frames_processed={result['frames_processed']}",
            f"candidate_count={result['candidate_count']}",
            f"overlay_folder={result['overlay_folder']}",
            f"csv_path={result['csv_path']}",
        ],
    )
    report["log_path"] = str(log_path)

    json_path = Path(report["json_report_path"])
    markdown_path = Path(report["markdown_report_path"])
    write_json_report(json_path, report)
    write_markdown_report(markdown_path, "Stage 4 Ball Tracking Probe Report", build_markdown_sections(report))

    lab_paths, notebook_warning = update_lab_notebook_safely()
    if notebook_warning:
        report["warnings"].append(notebook_warning)
        write_json_report(json_path, report)
        write_markdown_report(markdown_path, "Stage 4 Ball Tracking Probe Report", build_markdown_sections(report))
        print(f"Warning: {notebook_warning}")

    print_summary(report, lab_paths)
    return 1 if report["final_verdict"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
