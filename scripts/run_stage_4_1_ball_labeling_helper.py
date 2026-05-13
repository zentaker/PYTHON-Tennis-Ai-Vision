"""Run Stage 4.1 manual ball labeling helper."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from tennis_vision.ball_labeling import (  # noqa: E402
    build_frame_indices,
    compare_candidates_to_labels,
    label_frames_interactively,
    load_frame_at_index,
    skipped_label,
    write_labels_csv,
    write_labels_json,
)
from tennis_vision.ball_tracking_probe import resize_frame  # noqa: E402
from tennis_vision.friction import calculate_stage_4_1_friction_score  # noqa: E402
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
    parser = argparse.ArgumentParser(description="Stage 4.1 manual tennis ball labeling helper.")
    parser.add_argument("--video", type=Path, default=None, help="Path to a local video file.")
    parser.add_argument("--frames", type=str, default=None, help="Comma-separated frame indices, e.g. 120,150,180.")
    parser.add_argument("--start-frame", type=int, default=None, help="First frame when generating a frame list.")
    parser.add_argument("--interval", type=int, default=30, help="Frame step for generated frame lists.")
    parser.add_argument("--max-frames", type=int, default=8, help="Maximum frames to label.")
    parser.add_argument("--resize-width", type=int, default=1280, help="Display resize width.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "ball_tracking" / "stage_4_1_manual_labels",
        help="Output folder for manual labels.",
    )
    parser.add_argument("--interactive", dest="interactive", action="store_true", help="Open OpenCV click labeling UI.")
    parser.add_argument("--no-interactive", dest="interactive", action="store_false", help="Load frames and write a no-label report without opening a UI.")
    parser.set_defaults(interactive=True)
    return parser.parse_args()


def resolve_path(path: Path) -> Path:
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
        path = resolve_path(cli_video)
        return {
            "path": path,
            "source": "cli",
            "detection_method": "cli_argument",
            "checked_paths": [str(path)],
            "warnings": [],
        }
    return detect_default_video()


def load_frames_without_interaction(
    *,
    video_path: Path,
    frame_indices: list[int],
    output_dir: Path,
    resize_width: int,
) -> dict[str, Any]:
    """Safe verification path: load frames and save skipped rows without opening a GUI."""
    labels: list[dict[str, Any]] = []
    errors: list[str] = []
    warnings = ["Interactive labeling was skipped by --no-interactive; no manual ball labels were created."]
    overlay_dir = output_dir / "label_overlays"
    overlay_dir.mkdir(parents=True, exist_ok=True)
    frames_shown = 0
    for frame_index in frame_indices:
        frame, frame_error = load_frame_at_index(video_path, frame_index)
        if frame_error:
            errors.append(frame_error)
            continue
        frames_shown += 1
        original_height, original_width = frame.shape[:2]
        display, _scale = resize_frame(frame, resize_width)
        display_height, display_width = display.shape[:2]
        labels.append(skipped_label(frame_index, original_width, original_height, display_width, display_height))
    return {
        "labels": labels,
        "frames_shown": frames_shown,
        "quit_requested": False,
        "errors": errors,
        "warnings": warnings,
        "overlay_dir": str(overlay_dir),
    }


def determine_verdict(report: dict[str, Any]) -> str:
    if report["flags"]["frames_cannot_load"] or report["flags"]["no_frames_shown"]:
        return "blocked"
    if report["visible_ball_labels_count"] > 0:
        return "ready_with_warnings" if report["warnings"] else "ready_for_stage_5"
    return "ready_with_warnings"


def recommended_next_step(report: dict[str, Any]) -> str:
    if report["final_verdict"] == "blocked":
        return "Fix video/frame loading first, then rerun Stage 4.1."
    if report["visible_ball_labels_count"] == 0:
        return "Run Stage 4.1 interactively and click the real tennis ball in selected frames."
    return "Proceed to Stage 5: Ball Candidate Filtering and Court Projection."


def recommended_fixes(report: dict[str, Any]) -> list[str]:
    fixes: list[str] = []
    flags = report["flags"]
    if flags["video_missing"]:
        fixes.append("Place the sample video at samples/video_01.mov or pass --video PATH.")
    if flags["frames_cannot_load"] or flags["no_frames_shown"]:
        fixes.append("Use frame indices that exist in the sample video.")
    if flags["no_labels_saved"]:
        fixes.append("Run with --interactive and click the visible tennis ball before pressing s.")
    if flags["candidate_comparison_missing"]:
        fixes.append("Run Stage 4 first to generate ball_candidates.csv if candidate comparison is needed.")
    return fixes


def _bullet_list(items: list[str], empty_text: str) -> str:
    if not items:
        return empty_text
    return "\n".join(f"- {item}" for item in items)


def _labels_table(labels: list[dict[str, Any]]) -> str:
    lines = ["| Frame | Visible | X | Y | Overlay |", "|---:|---|---:|---:|---|"]
    for label in labels:
        lines.append(
            "| {frame} | {visible} | {x} | {y} | {overlay} |".format(
                frame=label.get("frame_index"),
                visible="yes" if label.get("visible") else "no",
                x=label.get("x") if label.get("x") is not None else "Not available",
                y=label.get("y") if label.get("y") is not None else "Not available",
                overlay=label.get("overlay_path") or "Not available",
            )
        )
    return "\n".join(lines)


def _comparison_table(summary: dict[str, Any]) -> str:
    if not summary:
        return "Candidate comparison was not available."
    rows = [
        ("labeled frames compared", summary.get("labeled_frames_compared")),
        ("frames where nearest candidate <= 10 px", summary.get("within_10_px")),
        ("<= 25 px", summary.get("within_25_px")),
        ("<= 50 px", summary.get("within_50_px")),
        ("<= 100 px", summary.get("within_100_px")),
        ("average nearest distance", summary.get("average_nearest_distance")),
        ("median nearest distance", summary.get("median_nearest_distance")),
    ]
    lines = ["| Metric | Value |", "|---|---|"]
    for metric, value in rows:
        lines.append(f"| {metric} | {value if value is not None else 'Not available'} |")
    return "\n".join(lines)


def build_markdown_sections(report: dict[str, Any]) -> list[tuple[str, str]]:
    comparison = report.get("candidate_comparison", {})
    comparison_summary = comparison.get("summary", {}) if comparison.get("available") else {}
    interpretation = (
        "Manual labels are available as ground truth for Stage 5. Candidate comparison can now show whether Stage 4 detections were close to the real ball."
        if report["visible_ball_labels_count"] > 0
        else "No visible ball labels were saved yet. This helper is ready, but Stage 5 needs at least a few manually labeled frames."
    )
    if comparison_summary:
        interpretation += " If nearest distances are large, the Stage 4 heuristic is failing due to false positives or missed detections."
    interpretation += " This remains a validation helper, not production tracking."
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
                    f"- Frame indices: {report['selected_frame_indices']}",
                    f"- Resize width: {report['resize_width']}",
                    f"- Frame source mode: {report['frame_source_mode']}",
                ]
            ),
        ),
        ("Manual labels", _labels_table(report["labels"])),
        ("Candidate comparison", _comparison_table(comparison_summary)),
        (
            "Output",
            "\n".join(
                [
                    f"- Output CSV path: `{report['output_csv_path']}`",
                    f"- Output JSON path: `{report['output_json_path']}`",
                    f"- Overlay folder: `{report['overlay_folder']}`",
                    f"- Comparison CSV path: `{report['comparison_csv_path'] or 'Not available'}`",
                    f"- JSON report: `{report['json_report_path']}`",
                    f"- Markdown report: `{report['markdown_report_path']}`",
                    f"- Log path: `{report['log_path']}`",
                ]
            ),
        ),
        ("Interpretation", interpretation),
        ("Warnings", _bullet_list(report["warnings"], "No warnings.")),
        ("Errors", _bullet_list(report["errors"], "No errors.")),
        ("Recommended fixes", _bullet_list(report["recommended_fixes"], "No fixes required.")),
        ("Next step", report["recommended_next_step"]),
    ]


def print_summary(report: dict[str, Any], lab_paths: dict[str, Path]) -> None:
    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(title="Stage 4.1 Manual Ball Labeling Helper")
        table.add_column("Field")
        table.add_column("Value")
        rows = [
            ("Stage name", "Stage 4.1 manual ball labeling helper"),
            ("Input video", report["video_path"]),
            ("Frames selected", str(report["selected_frame_indices"])),
            ("Frames shown", str(report["frames_shown"])),
            ("Visible labels", str(report["visible_ball_labels_count"])),
            ("Skipped frames", str(report["skipped_frames"])),
            ("Verdict", report["final_verdict"]),
            ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"),
            ("Labels CSV", report["output_csv_path"]),
            ("Labels JSON", report["output_json_path"]),
            ("Comparison CSV", str(report["comparison_csv_path"])),
            ("Lab notebook", str(lab_paths["stage_page"])),
            ("Experiment index", str(lab_paths["experiment_index"])),
            ("Recommended next step", report["recommended_next_step"]),
        ]
        for field, value in rows:
            table.add_row(field, value)
        Console().print(table)
    except ImportError:
        print(f"Stage name: Stage 4.1 manual ball labeling helper")
        print(f"Input video: {report['video_path']}")
        print(f"Frames selected: {report['selected_frame_indices']}")
        print(f"Visible labels: {report['visible_ball_labels_count']}")
        print(f"Verdict: {report['final_verdict']}")
        print(f"Friction: {report['friction']['score']} ({report['friction']['band']})")
        print(f"Labels CSV: {report['output_csv_path']}")
        print(f"Labels JSON: {report['output_json_path']}")
        print(f"Lab notebook: {lab_paths['stage_page']}")


def update_lab_notebook_safely() -> tuple[dict[str, Path], str | None]:
    try:
        from tennis_vision.lab_notebook import lab_notebook_paths, update_lab_notebook

        update_lab_notebook(PROJECT_ROOT)
        return lab_notebook_paths(PROJECT_ROOT, "stage_4_1"), None
    except Exception as exc:
        try:
            from tennis_vision.lab_notebook import lab_notebook_paths

            return lab_notebook_paths(PROJECT_ROOT, "stage_4_1"), f"Lab notebook update failed: {exc}"
        except Exception:
            return {
                "stage_page": PROJECT_ROOT / "docs" / "lab-notebook" / "stage_4_1_ball_labeling_helper.md",
                "experiment_index": PROJECT_ROOT / "docs" / "lab-notebook" / "experiment_index.md",
            }, f"Lab notebook update failed: {exc}"


def main() -> int:
    args = parse_args()
    ensure_output_folders(PROJECT_ROOT)
    selection = select_video_path(args.video)
    video_path = selection["path"]
    output_dir = resolve_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    frame_indices = build_frame_indices(
        frames=args.frames,
        start_frame=args.start_frame,
        interval=args.interval,
        max_frames=args.max_frames,
    )

    if args.interactive:
        labeling = label_frames_interactively(
            video_path=video_path,
            frame_indices=frame_indices,
            output_dir=output_dir,
            resize_width=args.resize_width,
            stage_4_overlay_dir=PROJECT_ROOT / "outputs" / "ball_tracking" / "stage_4_ball_probe" / "ball_candidates_overlay",
        )
    else:
        labeling = load_frames_without_interaction(
            video_path=video_path,
            frame_indices=frame_indices,
            output_dir=output_dir,
            resize_width=args.resize_width,
        )

    labels = labeling["labels"]
    output_csv_path = output_dir / "manual_ball_labels.csv"
    output_json_path = output_dir / "manual_ball_labels.json"
    write_labels_csv(output_csv_path, labels)
    write_labels_json(output_json_path, labels)

    comparison = compare_candidates_to_labels(
        labels=labels,
        candidate_csv_path=PROJECT_ROOT / "outputs" / "ball_tracking" / "stage_4_ball_probe" / "ball_candidates.csv",
        output_csv_path=output_dir / "candidate_label_comparison.csv",
    )

    visible_count = sum(1 for label in labels if label.get("visible"))
    skipped_count = sum(1 for label in labels if not label.get("visible"))
    warnings = [*selection["warnings"], *labeling["warnings"], *comparison["warnings"]]
    errors = [*labeling["errors"], *comparison["errors"]]
    flags = {
        "video_missing": not video_path.exists(),
        "frames_cannot_load": bool(labeling["errors"]) and labeling["frames_shown"] == 0,
        "no_frames_shown": labeling["frames_shown"] == 0,
        "no_labels_saved": visible_count == 0,
        "candidate_comparison_missing": not comparison["available"],
    }
    friction = calculate_stage_4_1_friction_score(
        **flags,
        errors_count=len(errors),
        warnings_count=len(warnings),
    )

    report: dict[str, Any] = {
        "timestamp": utc_timestamp(),
        "stage": "stage_4_1_ball_labeling_helper",
        "video_path": str(video_path),
        "input_selection": {
            "path": str(selection["path"]),
            "source": selection["source"],
            "detection_method": selection["detection_method"],
            "checked_paths": selection["checked_paths"],
        },
        "selected_frame_indices": frame_indices,
        "resize_width": args.resize_width,
        "frame_source_mode": "stage_4_overlay_if_available_else_video_frame",
        "interactive": bool(args.interactive),
        "frames_shown": labeling["frames_shown"],
        "labels_saved": visible_count,
        "visible_ball_labels_count": visible_count,
        "skipped_frames": skipped_count,
        "labels": labels,
        "output_csv_path": str(output_csv_path),
        "output_json_path": str(output_json_path),
        "overlay_folder": labeling["overlay_dir"],
        "comparison_csv_path": comparison["comparison_csv_path"],
        "candidate_comparison": comparison,
        "warnings": warnings,
        "errors": errors,
        "flags": flags,
        "friction": friction,
        "final_verdict": "blocked",
        "recommended_fixes": [],
        "recommended_next_step": "",
        "json_report_path": str(PROJECT_ROOT / "outputs" / "reports" / "stage_4_1_ball_labeling_helper_report.json"),
        "markdown_report_path": str(PROJECT_ROOT / "outputs" / "reports" / "stage_4_1_ball_labeling_helper_report.md"),
        "log_path": "",
    }
    report["final_verdict"] = determine_verdict(report)
    report["recommended_next_step"] = recommended_next_step(report)
    report["recommended_fixes"] = recommended_fixes(report)

    log_path = write_timestamped_log(
        PROJECT_ROOT,
        "stage_4_1_ball_labeling_helper",
        [
            f"timestamp={report['timestamp']}",
            f"video={video_path}",
            f"frames={frame_indices}",
            f"interactive={report['interactive']}",
            f"visible_labels={visible_count}",
            f"verdict={report['final_verdict']}",
            f"friction={friction['score']} ({friction['band']})",
        ],
    )
    report["log_path"] = str(log_path)

    json_path = Path(report["json_report_path"])
    markdown_path = Path(report["markdown_report_path"])
    write_json_report(json_path, report)
    write_markdown_report(markdown_path, "Stage 4.1 Manual Ball Labeling Helper Report", build_markdown_sections(report))

    lab_paths, notebook_warning = update_lab_notebook_safely()
    if notebook_warning:
        report["warnings"].append(notebook_warning)
        write_json_report(json_path, report)
        write_markdown_report(markdown_path, "Stage 4.1 Manual Ball Labeling Helper Report", build_markdown_sections(report))
        print(f"Warning: {notebook_warning}")

    print_summary(report, lab_paths)
    return 1 if report["final_verdict"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
