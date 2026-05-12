"""Run Stage 2 YOLO CPU baseline on a small local frame sample."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from tennis_vision.friction import calculate_stage_2_friction_score  # noqa: E402
from tennis_vision.report import (  # noqa: E402
    ensure_output_folders,
    safe_timestamp_for_filename,
    utc_timestamp,
    write_json_report,
    write_markdown_report,
    write_timestamped_log,
)
from tennis_vision.video_io import read_video_metadata  # noqa: E402
from tennis_vision.yolo_cpu import run_yolo_cpu_baseline  # noqa: E402


PREFERRED_DEFAULT_VIDEOS = (
    PROJECT_ROOT / "samples" / "video_01.mov",
    PROJECT_ROOT / "samples" / "video_01.MOV",
    PROJECT_ROOT / "samples" / "video_01.mp4",
    PROJECT_ROOT / "samples" / "video_01.MP4",
)
SAMPLE_VIDEO_EXTENSIONS = (".mov", ".MOV", ".mp4", ".MP4", ".avi", ".mkv", ".m4v")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 2 local YOLO CPU baseline.")
    parser.add_argument("--video", type=Path, default=None)
    parser.add_argument("--model", default=None, help="YOLO model name or path.")
    parser.add_argument("--max-frames", type=int, default=10)
    parser.add_argument("--interval", type=int, default=60)
    parser.add_argument("--resize-width", type=int, default=1280)
    parser.add_argument("--confidence", type=float, default=0.25)
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
            discovered.extend(
                path for path in sorted(samples_dir.glob(f"*{extension}")) if path.is_file()
            )
    if discovered:
        return {
            "path": discovered[0],
            "source": "auto_detected",
            "detection_method": "first_supported_video_in_samples",
            "checked_paths": checked_paths,
            "warnings": [
                "Preferred sample names were not found; using the first supported video file in samples/."
            ],
        }

    return {
        "path": PREFERRED_DEFAULT_VIDEOS[0],
        "source": "auto_detected",
        "detection_method": "not_found_fallback",
        "checked_paths": checked_paths,
        "warnings": [
            "No supported sample video was found in samples/. The default expected path was used for reporting."
        ],
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


def determine_verdict(report: dict[str, Any]) -> str:
    result = report["yolo_result"]
    friction_score = report["friction"]["score"]
    has_blocking_errors = bool(report["errors"]) or friction_score >= 81
    ready = (
        not report["flags"]["ultralytics_missing"]
        and not report["flags"]["model_load_failed"]
        and not report["flags"]["video_open_failed"]
        and result["frames_processed"] > 0
        and result["annotated_frames_saved"] > 0
        and not has_blocking_errors
    )
    if not ready:
        return "blocked"
    if report["warnings"] or report["flags"]["no_detections"] or report["flags"]["inference_too_slow"]:
        return "ready_with_warnings"
    return "ready_for_stage_3"


def recommended_fixes(report: dict[str, Any]) -> list[str]:
    fixes: list[str] = []
    flags = report["flags"]
    if flags["ultralytics_missing"]:
        fixes.append("Run: python -m pip install -r requirements.txt")
    if flags["model_download_failed"] or flags["model_load_failed"]:
        fixes.append("Check local network/model cache, then retry with --model yolov8n.pt.")
    if flags["video_open_failed"]:
        fixes.append("Verify samples/video_01.mov exists and can be opened by OpenCV.")
    if flags["no_frames_processed"]:
        fixes.append("Try a smaller --interval value or a shorter local sample video.")
    if flags["no_detections"]:
        fixes.append("No detections is acceptable for Stage 2; Stage 2 validates execution, not tennis ball tracking.")
    if flags["inference_too_slow"]:
        fixes.append("Keep CPU runs small for now; test GPU later only if documented local friction justifies it.")
    return fixes


def _bullet_list(items: list[str], empty: str = "No warnings.") -> str:
    if not items:
        return empty
    return "\n".join(f"- {item}" for item in items)


def _detection_table(counts: dict[str, int]) -> str:
    lines = ["| Class | Count |", "|---|---|"]
    if not counts:
        lines.append("| None | 0 |")
        return "\n".join(lines)
    for class_name, count in counts.items():
        lines.append(f"| {class_name} | {count} |")
    return "\n".join(lines)


def build_markdown_sections(report: dict[str, Any]) -> list[tuple[str, str]]:
    result = report["yolo_result"]
    next_step = report["recommended_next_step"]
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
                    f"- Video path: `{report['input_video_path']}`",
                    f"- Model: {report['model_name']}",
                    f"- Device: {report['device']}",
                    f"- Frame interval: {report['interval']}",
                    f"- Max frames: {report['max_frames']}",
                    f"- Resize width: {report['resize_width']}",
                    f"- Confidence threshold: {report['confidence_threshold']}",
                ]
            ),
        ),
        (
            "Output",
            "\n".join(
                [
                    f"- Annotated output folder: `{result['output_folder']}`",
                    f"- Frames processed: {result['frames_processed']}",
                    f"- Annotated frames saved: {result['annotated_frames_saved']}",
                    f"- JSON report path: `{report['json_report_path']}`",
                    f"- Markdown report path: `{report['markdown_report_path']}`",
                    f"- Log path: `{report['log_path']}`",
                ]
            ),
        ),
        ("Detection summary", _detection_table(result["detection_counts_by_class"])),
        (
            "Runtime",
            "\n".join(
                [
                    f"- Total runtime: {result['total_runtime_seconds']} seconds",
                    f"- Average time per frame: {result['average_inference_time_seconds']} seconds",
                ]
            ),
        ),
        ("Warnings", _bullet_list(report["warnings"], "No warnings.")),
        ("Errors", _bullet_list(report["errors"], "No errors.")),
        (
            "Interpretation",
            (
                "YOLO CPU is viable as a first local baseline because the model loaded, "
                "sampled frames were processed, and annotated frames were saved. This stage "
                "does not solve tennis ball tracking; it only validates local detection "
                "execution and measures CPU friction."
                if report["final_verdict"] != "blocked"
                else "YOLO CPU is not yet validated. Fix the blocking errors before Stage 3."
            ),
        ),
        ("Next step", next_step),
    ]


def print_summary(report: dict[str, Any], lab_paths: dict[str, Path]) -> None:
    result = report["yolo_result"]
    top_classes = ", ".join(
        f"{name}:{count}"
        for name, count in sorted(
            result["detection_counts_by_class"].items(),
            key=lambda item: item[1],
            reverse=True,
        )[:5]
    ) or "None"

    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(title="Stage 2 YOLO CPU Baseline")
        table.add_column("Field")
        table.add_column("Value")
        for field, value in [
            ("Stage name", "Stage 2 YOLO CPU baseline"),
            ("Input video", report["input_video_path"]),
            ("Model", report["model_name"]),
            ("Device", report["device"]),
            ("Verdict", report["final_verdict"]),
            ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"),
            ("Frames processed", str(result["frames_processed"])),
            ("Annotated frames saved", str(result["annotated_frames_saved"])),
            ("Runtime", f"{result['total_runtime_seconds']} seconds"),
            ("Average inference", f"{result['average_inference_time_seconds']} seconds/frame"),
            ("Top detected classes", top_classes),
            ("JSON report", report["json_report_path"]),
            ("Markdown report", report["markdown_report_path"]),
            ("Lab notebook", str(lab_paths["stage_page"])),
            ("Experiment index", str(lab_paths["experiment_index"])),
            ("Recommended next step", report["recommended_next_step"]),
        ]:
            table.add_row(field, value)
        Console().print(table)
    except ImportError:
        print("Stage name: Stage 2 YOLO CPU baseline")
        print(f"Input video: {report['input_video_path']}")
        print(f"Model: {report['model_name']}")
        print(f"Device: {report['device']}")
        print(f"Verdict: {report['final_verdict']}")
        print(f"Friction: {report['friction']['score']} ({report['friction']['band']})")
        print(f"Frames processed: {result['frames_processed']}")
        print(f"Annotated frames saved: {result['annotated_frames_saved']}")
        print(f"Runtime: {result['total_runtime_seconds']} seconds")
        print(f"Average inference: {result['average_inference_time_seconds']} seconds/frame")
        print(f"Top detected classes: {top_classes}")
        print(f"JSON report: {report['json_report_path']}")
        print(f"Markdown report: {report['markdown_report_path']}")
        print(f"Lab notebook: {lab_paths['stage_page']}")
        print(f"Experiment index: {lab_paths['experiment_index']}")
        print(f"Recommended next step: {report['recommended_next_step']}")


def update_lab_notebook_safely() -> tuple[dict[str, Path], str | None]:
    try:
        from tennis_vision.lab_notebook import lab_notebook_paths, update_lab_notebook

        update_lab_notebook(PROJECT_ROOT)
        return lab_notebook_paths(PROJECT_ROOT, "stage_2"), None
    except Exception as exc:
        from tennis_vision.lab_notebook import lab_notebook_paths

        return lab_notebook_paths(PROJECT_ROOT, "stage_2"), f"Lab notebook update failed: {exc}"


def main() -> int:
    args = parse_args()
    ensure_output_folders(PROJECT_ROOT)
    selection = select_video_path(args.video)
    video_path = selection["path"]
    run_id = safe_timestamp_for_filename()
    annotated_folder = PROJECT_ROOT / "outputs" / "annotated" / "stage_2_yolo_cpu" / run_id
    annotated_folder.mkdir(parents=True, exist_ok=True)

    metadata = read_video_metadata(video_path)
    yolo_result = run_yolo_cpu_baseline(
        video_path=video_path,
        output_folder=annotated_folder,
        model_name=args.model,
        max_frames=args.max_frames,
        interval=args.interval,
        resize_width=args.resize_width,
        confidence=args.confidence,
    )

    errors = [*metadata["errors"], *yolo_result["errors"]]
    warnings = [*selection["warnings"], *metadata["warnings"], *yolo_result["warnings"]]
    avg_time = yolo_result["average_inference_time_seconds"]
    flags = {
        "ultralytics_missing": bool(yolo_result["model_status"].get("ultralytics_missing")),
        "model_download_failed": bool(yolo_result["model_status"].get("model_download_failed")),
        "model_load_failed": bool(yolo_result["model_status"].get("model_load_failed")),
        "video_open_failed": metadata["exists"] and not metadata["opened"],
        "no_frames_processed": yolo_result["frames_processed"] == 0,
        "no_detections": yolo_result["frames_processed"] > 0
        and not yolo_result["detection_counts_by_class"],
        "inference_too_slow": avg_time is not None and avg_time > 2.0,
    }
    if flags["no_detections"]:
        warnings.append("YOLO produced no detections in the sampled frames; this does not block Stage 2.")
    if flags["inference_too_slow"]:
        warnings.append("Average CPU inference exceeded 2 seconds per frame.")

    friction = calculate_stage_2_friction_score(
        **flags,
        errors_count=len(errors),
        warnings_count=len(warnings),
        manual_action_required=bool(errors),
    )

    report: dict[str, Any] = {
        "timestamp": utc_timestamp(),
        "stage": "stage_2_yolo_cpu_baseline",
        "input_video_path": str(video_path),
        "input_selection": {
            **selection,
            "path": str(selection["path"]),
        },
        "video_metadata": metadata,
        "model_name": yolo_result["model_name"] or args.model or "yolo11n.pt",
        "device": "cpu",
        "max_frames": args.max_frames,
        "interval": args.interval,
        "resize_width": args.resize_width,
        "confidence_threshold": args.confidence,
        "yolo_result": yolo_result,
        "flags": flags,
        "errors": errors,
        "warnings": warnings,
        "recommended_fixes": [],
        "friction": friction,
        "final_verdict": "blocked",
        "recommended_next_step": "Fix blocking Stage 2 issues, then rerun the YOLO CPU baseline.",
        "json_report_path": str(PROJECT_ROOT / "outputs" / "reports" / "stage_2_yolo_cpu_baseline_report.json"),
        "markdown_report_path": str(PROJECT_ROOT / "outputs" / "reports" / "stage_2_yolo_cpu_baseline_report.md"),
        "log_path": "",
    }
    report["final_verdict"] = determine_verdict(report)
    report["recommended_fixes"] = recommended_fixes(report)
    if report["final_verdict"] == "blocked":
        report["recommended_next_step"] = "Fix blocking Stage 2 issues, then rerun the YOLO CPU baseline."
    elif flags["inference_too_slow"]:
        report["recommended_next_step"] = "Proceed to Stage 3 with small CPU probes; test GPU later only if friction justifies it."
    else:
        report["recommended_next_step"] = "Proceed to Stage 3: Court Calibration Probe."

    json_path = Path(report["json_report_path"])
    markdown_path = Path(report["markdown_report_path"])
    log_path = write_timestamped_log(
        PROJECT_ROOT,
        "stage_2_yolo_cpu_baseline",
        [
            f"timestamp={report['timestamp']}",
            f"video={video_path}",
            f"model={report['model_name']}",
            f"verdict={report['final_verdict']}",
            f"friction={friction['score']} ({friction['band']})",
            f"frames_processed={yolo_result['frames_processed']}",
            f"annotated_frames_saved={yolo_result['annotated_frames_saved']}",
        ],
    )
    report["log_path"] = str(log_path)
    write_json_report(json_path, report)
    write_markdown_report(
        markdown_path,
        "Stage 2 YOLO CPU Baseline Report",
        build_markdown_sections(report),
    )

    lab_paths, notebook_warning = update_lab_notebook_safely()
    if notebook_warning:
        report["warnings"].append(notebook_warning)
        write_json_report(json_path, report)
        write_markdown_report(
            markdown_path,
            "Stage 2 YOLO CPU Baseline Report",
            build_markdown_sections(report),
        )
        print(f"Warning: {notebook_warning}")

    print_summary(report, lab_paths)
    return 1 if report["final_verdict"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
