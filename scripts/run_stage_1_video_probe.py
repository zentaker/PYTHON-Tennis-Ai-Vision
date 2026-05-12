"""Run Stage 1 video loading and frame extraction probe."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from tennis_vision.frame_sampler import extract_frames  # noqa: E402
from tennis_vision.friction import calculate_stage_1_friction_score  # noqa: E402
from tennis_vision.report import (  # noqa: E402
    ensure_output_folders,
    safe_timestamp_for_filename,
    utc_timestamp,
    write_json_report,
    write_markdown_report,
    write_timestamped_log,
)
from tennis_vision.video_io import read_video_metadata  # noqa: E402


PREFERRED_DEFAULT_VIDEOS = (
    PROJECT_ROOT / "samples" / "video_01.mov",
    PROJECT_ROOT / "samples" / "video_01.MOV",
    PROJECT_ROOT / "samples" / "video_01.mp4",
    PROJECT_ROOT / "samples" / "video_01.MP4",
)
SAMPLE_VIDEO_EXTENSIONS = (".mov", ".MOV", ".mp4", ".MP4", ".avi", ".mkv", ".m4v")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stage 1 local video loading and frame extraction probe."
    )
    parser.add_argument(
        "--video",
        type=Path,
        default=None,
        help="Path to a local video file. If omitted, samples/ is auto-detected.",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Extract one frame every N frames. Default: 30.",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=25,
        help="Maximum number of frames to save. Default: 25.",
    )
    return parser.parse_args()


def resolve_video_path(path: Path) -> Path:
    """Resolve relative video paths from the project root."""
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def detect_default_video() -> dict[str, Any]:
    """Find a default sample video without assuming MP4."""
    samples_dir = PROJECT_ROOT / "samples"
    checked_paths: list[str] = []

    for candidate in PREFERRED_DEFAULT_VIDEOS:
        checked_paths.append(str(candidate))
        if candidate.exists() and candidate.is_file():
            return {
                "path": candidate,
                "auto_detected": True,
                "provided_by_cli": False,
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
            "auto_detected": True,
            "provided_by_cli": False,
            "detection_method": "first_supported_video_in_samples",
            "checked_paths": checked_paths,
            "warnings": [
                "Preferred sample names were not found; using the first supported video file in samples/."
            ],
        }

    fallback = PREFERRED_DEFAULT_VIDEOS[0]
    return {
        "path": fallback,
        "auto_detected": False,
        "provided_by_cli": False,
        "detection_method": "not_found_fallback",
        "checked_paths": checked_paths,
        "warnings": [
            "No supported sample video was found in samples/. The default expected path was used for reporting."
        ],
    }


def select_video_path(cli_video: Path | None) -> dict[str, Any]:
    """Select the video path from CLI input or automatic detection."""
    if cli_video is not None:
        path = resolve_video_path(cli_video)
        return {
            "path": path,
            "auto_detected": False,
            "provided_by_cli": True,
            "detection_method": "cli_argument",
            "checked_paths": [str(path)],
            "warnings": [],
        }
    return detect_default_video()


def determine_verdict(report: dict[str, Any]) -> str:
    """Return the Stage 1 final verdict."""
    metadata = report["metadata"]
    extraction = report["frame_extraction"]
    friction_score = report["friction"]["score"]

    has_blocking_errors = bool(report["errors"]) or friction_score >= 81
    ready = (
        metadata["exists"]
        and metadata["opened"]
        and metadata["metadata_readable"]
        and extraction["frames_saved"] > 0
        and not has_blocking_errors
    )

    if ready and not report["warnings"] and friction_score <= 20:
        return "ready_for_stage_2"
    if ready:
        return "ready_with_warnings"
    return "blocked"


def recommended_fixes(report: dict[str, Any]) -> list[str]:
    """Build recommended fixes from Stage 1 outcomes."""
    fixes: list[str] = []
    metadata = report["metadata"]
    extraction = report["frame_extraction"]

    if not metadata["exists"]:
        fixes.append("Place a local sample video at samples/video_01.mov, samples/video_01.mp4, or pass --video PATH.")
    if metadata["exists"] and not metadata["opened"]:
        fixes.append(
            "OpenCV could not read this video. Convert it to MP4/H.264, try another local sample, or install ffmpeg later for conversion support."
        )
    if metadata["opened"] and not metadata["metadata_readable"]:
        fixes.append("Verify the video is not corrupt and contains readable frames.")
    if extraction["frames_saved"] == 0 and metadata["opened"]:
        fixes.append("Try a smaller --interval value or confirm outputs/frames is writable.")
    return fixes


def _bullet_list(items: list[str]) -> str:
    if not items:
        return "- None"
    return "\n".join(f"- {item}" for item in items)


def build_markdown_sections(report: dict[str, Any]) -> list[tuple[str, str]]:
    metadata = report["metadata"]
    extraction = report["frame_extraction"]
    input_selection = report["input_selection"]
    next_step = (
        "Stage 2: YOLO CPU baseline."
        if report["final_verdict"] != "blocked"
        else "Fix the blocking video loading or frame extraction issue first, then rerun Stage 1."
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
            "Input video",
            "\n".join(
                [
                    f"- Detected default video path: `{input_selection['detected_default_video_path']}`",
                    f"- Selected video path: `{input_selection['selected_video_path']}`",
                    f"- Video source: {input_selection['source']}",
                    f"- Path: `{metadata['file_path']}`",
                    f"- File extension: {metadata['file_extension'] or 'unknown'}",
                    f"- File size: {metadata['file_size_mb']} MB",
                    f"- Resolution: {metadata['width']}x{metadata['height']}",
                    f"- FPS: {metadata['fps']}",
                    f"- Frame count: {metadata['frame_count']}",
                    f"- Duration: {metadata['duration_seconds']} seconds",
                    f"- Codec: {metadata['codec'] or 'unknown'}",
                    f"- OpenCV opened successfully: {'yes' if metadata['opened'] else 'no'}",
                ]
            ),
        ),
        (
            "Frame extraction",
            "\n".join(
                [
                    f"- Interval: {extraction['extraction_interval']}",
                    f"- Max frames: {extraction['max_frames']}",
                    f"- Frames saved: {extraction['frames_saved']}",
                    f"- Output folder: `{extraction['output_folder']}`",
                    f"- Time taken: {extraction['extraction_time_seconds']} seconds",
                ]
            ),
        ),
        ("Video read errors", _bullet_list(metadata["errors"])),
        ("Errors", _bullet_list(report["errors"])),
        ("Warnings", _bullet_list(report["warnings"])),
        ("Recommended fixes", _bullet_list(report["recommended_fixes"])),
        ("Next step", next_step),
    ]


def print_summary(report: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    metadata = report["metadata"]
    extraction = report["frame_extraction"]
    input_selection = report["input_selection"]
    next_step = (
        "Stage 2: YOLO CPU baseline"
        if report["final_verdict"] != "blocked"
        else "Fix Stage 1 blockers and rerun the probe"
    )

    try:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title="Stage 1 Video Loading And Frame Extraction")
        table.add_column("Field")
        table.add_column("Value")
        table.add_row("Stage name", "Stage 1 video probe")
        table.add_row("Input video", metadata["file_path"])
        table.add_row("Video source", input_selection["source"])
        table.add_row("Verdict", report["final_verdict"])
        table.add_row(
            "Friction",
            f"{report['friction']['score']} ({report['friction']['band']})",
        )
        table.add_row("Video duration", f"{metadata['duration_seconds']} seconds")
        table.add_row("Resolution", f"{metadata['width']}x{metadata['height']}")
        table.add_row("FPS", str(metadata["fps"]))
        table.add_row("Frames saved", str(extraction["frames_saved"]))
        table.add_row("JSON report", str(json_path))
        table.add_row("Markdown report", str(markdown_path))
        table.add_row("Recommended next step", next_step)
        console.print(table)
    except ImportError:
        print("Stage name: Stage 1 video probe")
        print(f"Input video: {metadata['file_path']}")
        print(f"Video source: {input_selection['source']}")
        print(f"Verdict: {report['final_verdict']}")
        print(f"Friction score: {report['friction']['score']} ({report['friction']['band']})")
        print(f"Video duration: {metadata['duration_seconds']} seconds")
        print(f"Resolution: {metadata['width']}x{metadata['height']}")
        print(f"FPS: {metadata['fps']}")
        print(f"Frames saved: {extraction['frames_saved']}")
        print(f"JSON report: {json_path}")
        print(f"Markdown report: {markdown_path}")
        print(f"Recommended next step: {next_step}")


def update_lab_notebook_safely() -> None:
    """Best-effort lab notebook update that never fails Stage 1."""
    try:
        from tennis_vision.lab_notebook import lab_notebook_paths, update_lab_notebook

        update_lab_notebook(PROJECT_ROOT)
        paths = lab_notebook_paths(PROJECT_ROOT, "stage_1")
        print(f"Lab notebook page: {paths['stage_page']}")
        print(f"Experiment index: {paths['experiment_index']}")
    except Exception as exc:
        print(f"Warning: lab notebook update failed: {exc}")


def main() -> int:
    args = parse_args()
    ensure_output_folders(PROJECT_ROOT)

    selection = select_video_path(args.video)
    video_path = selection["path"]
    run_id = safe_timestamp_for_filename()
    output_folder = PROJECT_ROOT / "outputs" / "frames" / f"stage_1_{run_id}"

    metadata = read_video_metadata(video_path)
    extraction = {
        "frames_attempted": 0,
        "frames_saved": 0,
        "total_frames_read": 0,
        "extraction_interval": args.interval,
        "max_frames": args.max_frames,
        "output_folder": str(output_folder),
        "saved_files": [],
        "extraction_time_seconds": 0.0,
        "errors": [],
        "warnings": [],
    }
    if metadata["exists"] and metadata["opened"]:
        extraction = extract_frames(
            video_path,
            output_folder,
            interval=args.interval,
            max_frames=args.max_frames,
        )

    errors = [*metadata["errors"], *extraction["errors"]]
    warnings = [*selection["warnings"], *metadata["warnings"], *extraction["warnings"]]
    friction = calculate_stage_1_friction_score(
        video_missing=not metadata["exists"],
        video_open_failed=metadata["exists"] and not metadata["opened"],
        metadata_read_failed=metadata["opened"] and not metadata["metadata_readable"],
        zero_frames_detected=metadata["opened"] and (metadata["frame_count"] or 0) == 0,
        frames_not_saved=metadata["opened"] and extraction["frames_saved"] == 0,
        errors_count=len(errors),
        warnings_count=len(warnings),
        manual_action_required=bool(errors),
    )

    report: dict[str, Any] = {
        "timestamp": utc_timestamp(),
        "stage": "stage_1_video_loading_and_frame_extraction",
        "project_root": str(PROJECT_ROOT),
        "input_selection": {
            "source": "cli" if selection["provided_by_cli"] else "auto_detected",
            "provided_by_cli": selection["provided_by_cli"],
            "auto_detected": selection["auto_detected"],
            "detection_method": selection["detection_method"],
            "selected_video_path": str(selection["path"]),
            "detected_default_video_path": str(selection["path"])
            if selection["auto_detected"]
            else None,
            "checked_paths": selection["checked_paths"],
            "supported_extensions": list(SAMPLE_VIDEO_EXTENSIONS),
        },
        "metadata": metadata,
        "frame_extraction": extraction,
        "errors": errors,
        "warnings": warnings,
        "friction": friction,
        "final_verdict": "blocked",
        "recommended_fixes": [],
    }
    report["final_verdict"] = determine_verdict(report)
    report["recommended_fixes"] = recommended_fixes(report)

    json_path = PROJECT_ROOT / "outputs" / "reports" / "stage_1_video_probe_report.json"
    markdown_path = PROJECT_ROOT / "outputs" / "reports" / "stage_1_video_probe_report.md"
    write_json_report(json_path, report)
    write_markdown_report(
        markdown_path,
        "Stage 1 Video Probe Report",
        build_markdown_sections(report),
    )
    log_path = write_timestamped_log(
        PROJECT_ROOT,
        "stage_1_video_probe",
        [
            f"timestamp={report['timestamp']}",
            f"video={metadata['file_path']}",
            f"video_source={report['input_selection']['source']}",
            f"verdict={report['final_verdict']}",
            f"friction={friction['score']} ({friction['band']})",
            f"frames_saved={extraction['frames_saved']}",
            f"json_report={json_path}",
            f"markdown_report={markdown_path}",
        ],
    )
    report["log_path"] = str(log_path)

    print_summary(report, json_path, markdown_path)
    print(f"Log file: {log_path}")
    update_lab_notebook_safely()

    return 1 if report["final_verdict"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
