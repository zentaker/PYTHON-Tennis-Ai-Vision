"""Markdown lab notebook generation from project reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


LAB_NOTEBOOK_DIR = Path("docs") / "lab-notebook"
REPORTS_DIR = Path("outputs") / "reports"
ENTRY_MARKER_PREFIX = "<!-- lab-entry:"
STAGE_NOTEBOOK_FILES = {
    "stage_0": "stage_0_environment.md",
    "stage_1": "stage_1_video_probe.md",
    "stage_2": "stage_2_yolo_cpu_baseline.md",
    "stage_3": "stage_3_court_calibration_probe.md",
    "stage_3_1": "stage_3_1_court_point_selector.md",
    "stage_4": "stage_4_ball_tracking_probe.md",
    "stage_4_1": "stage_4_1_ball_labeling_helper.md",
    "stage_5": "stage_5_ball_candidate_filtering.md",
    "stage_5_1": "stage_5_1_candidate_improvement.md",
    "stage_6": "stage_6_trajectory_smoothing.md",
    "stage_7": "stage_7_player_interaction_probe.md",
    "stage_7_1": "stage_7_1_player_filtering.md",
}


def not_available(value: Any) -> str:
    """Return a display value, falling back to a stable placeholder."""
    if value is None:
        return "Not available"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (list, dict)) and not value:
        return "Not available"
    text = str(value)
    return text if text else "Not available"


def nested_get(data: dict[str, Any], keys: tuple[str, ...], default: Any = None) -> Any:
    """Read nested data without assuming all report fields exist."""
    current: Any = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def read_json_report(path: Path) -> dict[str, Any] | None:
    """Read a JSON report, returning None if it is missing or invalid."""
    try:
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def markdown_table(rows: list[tuple[str, Any]]) -> str:
    """Convert row pairs into a Markdown table."""
    lines = ["| Field | Value |", "|---|---|"]
    for field, value in rows:
        lines.append(f"| {field} | {escape_table_value(not_available(value))} |")
    return "\n".join(lines)


def escape_table_value(value: str) -> str:
    """Escape Markdown table-sensitive values."""
    return value.replace("|", "\\|").replace("\n", "<br>")


def bullet_list(items: Any, empty_text: str) -> str:
    """Render a bullet list from report values."""
    if not items:
        return empty_text
    if not isinstance(items, list):
        return f"- {not_available(items)}"
    return "\n".join(f"- {not_available(item)}" for item in items)


def ensure_lab_notebook_dir(project_root: Path) -> Path:
    """Create the lab notebook directory."""
    path = project_root / LAB_NOTEBOOK_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def lab_notebook_paths(project_root: Path, stage_key: str) -> dict[str, Path]:
    """Return standard lab notebook paths for a stage and the index."""
    notebook_dir = project_root / LAB_NOTEBOOK_DIR
    stage_filename = STAGE_NOTEBOOK_FILES.get(stage_key)
    return {
        "stage_page": notebook_dir / stage_filename if stage_filename else notebook_dir,
        "experiment_index": notebook_dir / "experiment_index.md",
    }


def report_path(project_root: Path, filename: str) -> Path:
    """Return a standard report path."""
    return project_root / REPORTS_DIR / filename


def latest_log_for_prefix(project_root: Path, prefix: str) -> str:
    """Find the newest matching log file for a report family."""
    logs_dir = project_root / "outputs" / "logs"
    if not logs_dir.exists():
        return "Not available"
    logs = sorted(logs_dir.glob(f"{prefix}*.log"), key=lambda path: path.stat().st_mtime)
    return str(logs[-1]) if logs else "Not available"


def stage_0_next_step(report: dict[str, Any]) -> str:
    """Return Stage 0 next-step text."""
    verdict = report.get("final_verdict")
    if verdict == "blocked":
        return "Fix the local environment blockers, then rerun the Stage 0 doctor."
    return "Proceed to Stage 1 video loading and frame extraction."


def stage_1_next_step(report: dict[str, Any]) -> str:
    """Return Stage 1 next-step text."""
    verdict = report.get("final_verdict")
    if verdict == "blocked":
        return "Fix video loading or frame extraction blockers, then rerun Stage 1."
    return "Proceed to Stage 2 YOLO CPU baseline."


def stage_2_next_step(report: dict[str, Any]) -> str:
    """Return Stage 2 next-step text."""
    next_step = report.get("recommended_next_step")
    if next_step:
        return str(next_step)
    if report.get("final_verdict") == "blocked":
        return "Fix YOLO CPU baseline blockers, then rerun Stage 2."
    return "Proceed to Stage 3 court calibration probe."


def stage_3_next_step(report: dict[str, Any]) -> str:
    """Return Stage 3 next-step text."""
    next_step = report.get("recommended_next_step")
    if next_step:
        return str(next_step)
    verdict = report.get("final_verdict")
    if verdict == "ready_for_stage_4":
        return "Proceed to Stage 4 ball tracking probe."
    if verdict == "ready_for_manual_point_selection":
        return "Fill manual court point coordinates, then rerun Stage 3."
    return "Fix Stage 3 calibration blockers, then rerun the probe."


def stage_3_1_next_step(report: dict[str, Any]) -> str:
    """Return Stage 3.1 next-step text."""
    next_step = report.get("recommended_next_step")
    if next_step:
        return str(next_step)
    verdict = report.get("final_verdict")
    if verdict == "ready_to_rerun_stage_3":
        return "Rerun Stage 3 to compute homography from the saved point coordinates."
    if verdict == "ready_with_grid_only":
        return "Use the grid image or interactive selector to fill court point coordinates."
    return "Regenerate the Stage 3 reference frame, then rerun Stage 3.1."


def stage_4_next_step(report: dict[str, Any]) -> str:
    """Return Stage 4 next-step text."""
    next_step = report.get("recommended_next_step")
    if next_step:
        return str(next_step)
    verdict = report.get("final_verdict")
    if verdict in {"ready_for_stage_5", "ready_with_warnings"}:
        return "Proceed to Stage 5 ball candidate filtering and court projection."
    if verdict == "needs_better_ball_model":
        return "Research a specialized tennis ball tracker or GPU-based detector later."
    return "Fix Stage 4 video loading or sampling blockers, then rerun the probe."


def stage_4_1_next_step(report: dict[str, Any]) -> str:
    """Return Stage 4.1 next-step text."""
    next_step = report.get("recommended_next_step")
    if next_step:
        return str(next_step)
    if (report.get("visible_ball_labels_count") or 0) > 0:
        return "Proceed to Stage 5 ball candidate filtering and court projection."
    if report.get("final_verdict") == "blocked":
        return "Fix video/frame loading, then rerun Stage 4.1."
    return "Run Stage 4.1 interactively and label visible ball positions."


def stage_5_next_step(report: dict[str, Any]) -> str:
    """Return Stage 5 next-step text."""
    next_step = report.get("recommended_next_step")
    if next_step:
        return str(next_step)
    if report.get("final_verdict") == "ready_for_stage_6":
        return "Proceed to Stage 6 trajectory smoothing and event/rally segmentation."
    if report.get("final_verdict") == "needs_better_ball_model":
        return "Proceed to Stage 5.1 specialized ball detector research."
    return "Review Stage 5 warnings, then rerun filtering after fixing inputs."


def stage_5_1_next_step(report: dict[str, Any]) -> str:
    """Return Stage 5.1 next-step text."""
    next_step = report.get("recommended_next_step")
    if next_step:
        return str(next_step)
    if report.get("final_verdict") == "ready_for_stage_6":
        return "Proceed to Stage 6 trajectory smoothing and rally/event segmentation."
    if report.get("final_verdict") == "blocked":
        return "Fix Stage 5.1 input blockers, then rerun candidate improvement."
    return "Proceed to Stage 5.2 specialized ball model research and benchmark."


def stage_6_next_step(report: dict[str, Any]) -> str:
    """Return Stage 6 next-step text."""
    next_step = report.get("recommended_next_step")
    if next_step:
        return str(next_step)
    verdict = report.get("final_verdict")
    if verdict == "ready_for_stage_7":
        return "Proceed to Stage 7 player tracking and ball-player interaction probe."
    if verdict == "needs_more_labels":
        return "Proceed to Stage 6.1 expand manual labels and rerun smoothing."
    if verdict == "needs_better_ball_model":
        return "Return to Stage 5.2 specialized ball model research."
    return "Fix Stage 6 blockers, then rerun trajectory smoothing."


def stage_7_next_step(report: dict[str, Any]) -> str:
    """Return Stage 7 next-step text."""
    next_step = report.get("recommended_next_step")
    if next_step:
        return str(next_step)
    verdict = report.get("final_verdict")
    if verdict == "ready_for_stage_8":
        return "Proceed to Stage 8 shot/event timeline and rally segmentation prototype."
    if verdict == "needs_more_ball_labels":
        return "Proceed to Stage 7.1 expand manual labels and rerun player interaction."
    if verdict == "needs_better_player_tracking":
        return "Proceed to Stage 7.2 player tracking improvement."
    return "Review Stage 7 warnings and rerun after fixing blockers."


def stage_7_1_next_step(report: dict[str, Any]) -> str:
    """Return Stage 7.1 next-step text."""
    next_step = report.get("recommended_next_step")
    if next_step:
        return str(next_step)
    if report.get("final_verdict") == "ready_for_stage_8":
        return "Proceed to Stage 8 shot/event timeline and rally segmentation prototype."
    return "Proceed to Stage 7.2 manual player identity labeling helper."


def build_stage_0_document(report: dict[str, Any], project_root: Path) -> dict[str, str]:
    """Build Stage 0 notebook content."""
    json_path = report_path(project_root, "environment_report.json")
    markdown_path = report_path(project_root, "environment_report.md")
    next_step = stage_0_next_step(report)
    friction = report.get("friction", {})

    summary = markdown_table(
        [
            ("Stage", "Stage 0 — Environment and repo foundation"),
            ("Verdict", report.get("final_verdict")),
            ("Friction score", friction.get("score")),
            ("Friction level", friction.get("band")),
            ("Timestamp", report.get("timestamp")),
            ("Recommended next step", next_step),
        ]
    )
    input_table = markdown_table(
        [
            ("Local environment", nested_get(report, ("os", "platform"))),
            ("Python", nested_get(report, ("python", "version"))),
            ("Python executable", nested_get(report, ("python", "executable"))),
            ("Folders missing", len(report.get("missing_folders", []))),
            ("Packages missing", len(report.get("missing_packages", []))),
            ("ffmpeg available", nested_get(report, ("ffmpeg", "available"))),
            ("ffmpeg path", nested_get(report, ("ffmpeg", "path"))),
        ]
    )
    output_table = markdown_table(
        [
            ("JSON report path", json_path),
            ("Markdown report path", markdown_path),
            ("Log", latest_log_for_prefix(project_root, "doctor_")),
        ]
    )
    console_table = markdown_table(
        [
            ("Verdict", report.get("final_verdict")),
            ("Friction", f"{not_available(friction.get('score'))} ({not_available(friction.get('band'))})"),
            ("Missing packages", len(report.get("missing_packages", []))),
            ("Missing folders", len(report.get("missing_folders", []))),
            ("ffmpeg", "available" if nested_get(report, ("ffmpeg", "available")) else "missing"),
            ("Errors", len(report.get("errors", []))),
            ("Warnings", len(report.get("warnings", []))),
        ]
    )
    interpretation = (
        "The local Python environment is usable for the current project stages. "
        "The remaining friction is that ffmpeg is not available from the terminal, "
        "which is a warning for now rather than a blocker."
    )

    body = stage_document(
        title="Stage 0 — Environment",
        summary=summary,
        input_section=input_table,
        output_section=output_table,
        console_table=console_table,
        warnings=bullet_list(report.get("warnings"), "No warnings."),
        errors=bullet_list(report.get("errors"), "No errors."),
        interpretation=interpretation,
        next_step=next_step,
    )
    entry = history_entry(report, "Stage 0 — Environment", summary, next_step)
    return {"body": body, "entry": entry, "entry_id": not_available(report.get("timestamp"))}


def build_stage_1_document(report: dict[str, Any], project_root: Path) -> dict[str, str]:
    """Build Stage 1 notebook content."""
    json_path = report_path(project_root, "stage_1_video_probe_report.json")
    markdown_path = report_path(project_root, "stage_1_video_probe_report.md")
    next_step = stage_1_next_step(report)
    friction = report.get("friction", {})
    metadata = report.get("metadata", {})
    extraction = report.get("frame_extraction", {})
    input_selection = report.get("input_selection", {})

    summary = markdown_table(
        [
            ("Stage", "Stage 1 — Video loading and frame extraction"),
            ("Verdict", report.get("final_verdict")),
            ("Friction score", friction.get("score")),
            ("Friction level", friction.get("band")),
            ("Timestamp", report.get("timestamp")),
            ("Recommended next step", next_step),
        ]
    )
    input_table = markdown_table(
        [
            ("Video path", metadata.get("file_path")),
            ("Video source", input_selection.get("source")),
            ("File extension", metadata.get("file_extension")),
            ("Resolution", f"{not_available(metadata.get('width'))}x{not_available(metadata.get('height'))}"),
            ("FPS", metadata.get("fps")),
            ("Duration seconds", metadata.get("duration_seconds")),
            ("Frame count", metadata.get("frame_count")),
            ("OpenCV opened", metadata.get("opened")),
        ]
    )
    output_table = markdown_table(
        [
            ("JSON report path", json_path),
            ("Markdown report path", markdown_path),
            ("Log", latest_log_for_prefix(project_root, "stage_1_video_probe_")),
            ("Frames folder", extraction.get("output_folder")),
            ("Frames saved", extraction.get("frames_saved")),
        ]
    )
    console_table = markdown_table(
        [
            ("Stage name", "Stage 1 video probe"),
            ("Input video", metadata.get("file_path")),
            ("Video source", input_selection.get("source")),
            ("Verdict", report.get("final_verdict")),
            ("Friction", f"{not_available(friction.get('score'))} ({not_available(friction.get('band'))})"),
            ("Video duration", f"{not_available(metadata.get('duration_seconds'))} seconds"),
            ("Resolution", f"{not_available(metadata.get('width'))}x{not_available(metadata.get('height'))}"),
            ("FPS", metadata.get("fps")),
            ("Frames saved", extraction.get("frames_saved")),
            ("Recommended next step", next_step),
        ]
    )
    interpretation = (
        "Video reading and frame extraction are validated for the current local sample. "
        "OpenCV can read the MOV file, metadata is available, and extracted JPG frames "
        "were written locally."
        if report.get("final_verdict") != "blocked"
        else "Video loading or frame extraction is not yet validated. Review the errors and fixes before Stage 2."
    )

    body = stage_document(
        title="Stage 1 — Video Probe",
        summary=summary,
        input_section=input_table,
        output_section=output_table,
        console_table=console_table,
        warnings=bullet_list(report.get("warnings"), "No warnings."),
        errors=bullet_list(report.get("errors"), "No errors."),
        interpretation=interpretation,
        next_step=next_step,
    )
    entry = history_entry(report, "Stage 1 — Video Probe", summary, next_step)
    return {"body": body, "entry": entry, "entry_id": not_available(report.get("timestamp"))}


def build_stage_2_document(report: dict[str, Any], project_root: Path) -> dict[str, str]:
    """Build Stage 2 notebook content."""
    json_path = report_path(project_root, "stage_2_yolo_cpu_baseline_report.json")
    markdown_path = report_path(project_root, "stage_2_yolo_cpu_baseline_report.md")
    next_step = stage_2_next_step(report)
    friction = report.get("friction", {})
    result = report.get("yolo_result", {})
    counts = result.get("detection_counts_by_class", {})

    summary = markdown_table(
        [
            ("Stage", "Stage 2 - YOLO CPU baseline"),
            ("Verdict", report.get("final_verdict")),
            ("Friction score", friction.get("score")),
            ("Friction level", friction.get("band")),
            ("Timestamp", report.get("timestamp")),
            ("Recommended next step", next_step),
        ]
    )
    input_table = markdown_table(
        [
            ("Video path", report.get("input_video_path")),
            ("Model", report.get("model_name")),
            ("Device", report.get("device")),
            ("Frame interval", report.get("interval")),
            ("Max frames", report.get("max_frames")),
            ("Resize width", report.get("resize_width")),
            ("Confidence threshold", report.get("confidence_threshold")),
        ]
    )
    output_table = markdown_table(
        [
            ("JSON report path", json_path),
            ("Markdown report path", markdown_path),
            ("Log", latest_log_for_prefix(project_root, "stage_2_yolo_cpu_baseline_")),
            ("Annotated frames folder", result.get("output_folder")),
            ("Annotated frames saved", result.get("annotated_frames_saved")),
        ]
    )
    console_table = markdown_table(
        [
            ("Stage name", "Stage 2 YOLO CPU baseline"),
            ("Input video", report.get("input_video_path")),
            ("Model", report.get("model_name")),
            ("Device", report.get("device")),
            ("Verdict", report.get("final_verdict")),
            ("Friction", f"{not_available(friction.get('score'))} ({not_available(friction.get('band'))})"),
            ("Frames processed", result.get("frames_processed")),
            ("Annotated frames saved", result.get("annotated_frames_saved")),
            ("Runtime", f"{not_available(result.get('total_runtime_seconds'))} seconds"),
            ("Average inference", f"{not_available(result.get('average_inference_time_seconds'))} seconds/frame"),
            ("Top classes", top_detection_classes(counts)),
            ("Recommended next step", next_step),
        ]
    )
    interpretation = (
        "YOLO CPU execution is validated as a first local baseline. This stage confirms "
        "local model loading, CPU inference, annotated frame output, and report generation. "
        "It does not validate tennis ball tracking quality."
        if report.get("final_verdict") != "blocked"
        else "YOLO CPU execution is not yet validated. Review the recorded errors and friction before Stage 3."
    )

    body = stage_document(
        title="Stage 2 - YOLO CPU Baseline",
        summary=summary,
        input_section=input_table,
        output_section=output_table,
        console_table=console_table,
        warnings=bullet_list(report.get("warnings"), "No warnings."),
        errors=bullet_list(report.get("errors"), "No errors."),
        interpretation=interpretation,
        next_step=next_step,
    )
    entry = history_entry(report, "Stage 2 - YOLO CPU Baseline", summary, next_step)
    return {"body": body, "entry": entry, "entry_id": not_available(report.get("timestamp"))}


def top_detection_classes(counts: Any) -> str:
    """Return compact top-class text for notebook tables."""
    if not isinstance(counts, dict) or not counts:
        return "None"
    pairs = sorted(counts.items(), key=lambda item: item[1], reverse=True)[:5]
    return ", ".join(f"{name}: {count}" for name, count in pairs)


def build_stage_3_document(report: dict[str, Any], project_root: Path) -> dict[str, str]:
    """Build Stage 3 notebook content."""
    json_path = report_path(project_root, "stage_3_court_calibration_probe_report.json")
    markdown_path = report_path(project_root, "stage_3_court_calibration_probe_report.md")
    next_step = stage_3_next_step(report)
    friction = report.get("friction", {})
    result = report.get("calibration_result", {})
    homography = report.get("homography_status", {})
    geometry = nested_get(report, ("points_status", "geometry"), {})

    summary = markdown_table(
        [
            ("Stage", "Stage 3 - Court calibration probe"),
            ("Verdict", report.get("final_verdict")),
            ("Friction score", friction.get("score")),
            ("Friction level", friction.get("band")),
            ("Timestamp", report.get("timestamp")),
            ("Recommended next step", next_step),
        ]
    )
    input_table = markdown_table(
        [
            ("Config path", report.get("config_path")),
            ("Video path", report.get("video_path")),
            ("Frame index", report.get("frame_index")),
            ("Calibration basis", report.get("calibration_basis")),
            ("Calibration points status", report.get("points_status_summary")),
            ("Point order valid", geometry.get("point_order_valid") if isinstance(geometry, dict) else None),
            ("Polygon self-intersects", geometry.get("polygon_self_intersects") if isinstance(geometry, dict) else None),
        ]
    )
    output_table = markdown_table(
        [
            ("JSON report path", json_path),
            ("Markdown report path", markdown_path),
            ("Log", latest_log_for_prefix(project_root, "stage_3_court_calibration_probe_")),
            ("Reference frame", result.get("reference_frame_path")),
            ("Points overlay", result.get("overlay_path")),
            ("Mini-court preview", result.get("mini_court_preview_path")),
        ]
    )
    console_table = markdown_table(
        [
            ("Stage name", "Stage 3 court calibration probe"),
            ("Config", report.get("config_path")),
            ("Input video", report.get("video_path")),
            ("Frame index", report.get("frame_index")),
            ("Verdict", report.get("final_verdict")),
            ("Friction", f"{not_available(friction.get('score'))} ({not_available(friction.get('band'))})"),
            ("Reference frame", result.get("reference_frame_path")),
            ("Overlay", result.get("overlay_path")),
            ("Homography", "computed" if homography.get("computed") else "not computed"),
            ("Point order valid", geometry.get("point_order_valid") if isinstance(geometry, dict) else None),
            ("Polygon self-intersects", geometry.get("polygon_self_intersects") if isinstance(geometry, dict) else None),
            ("Recommended next step", next_step),
        ]
    )
    interpretation = (
        "The calibration reference frame and overlay are ready for manual point selection. "
        "The placeholder, inverted, or crossed config should be updated with real pixel coordinates before Stage 4."
        if report.get("final_verdict") == "ready_for_manual_point_selection"
        else "Court homography is available, so the project is ready to proceed to ball tracking probes."
        if report.get("final_verdict") == "ready_for_stage_4"
        else "Stage 3 needs attention before court calibration can be trusted."
    )

    body = stage_document(
        title="Stage 3 - Court Calibration Probe",
        summary=summary,
        input_section=input_table,
        output_section=output_table,
        console_table=console_table,
        warnings=bullet_list(report.get("warnings"), "No warnings."),
        errors=bullet_list(report.get("errors"), "No errors."),
        interpretation=interpretation,
        next_step=next_step,
    )
    entry = history_entry(report, "Stage 3 - Court Calibration Probe", summary, next_step)
    return {"body": body, "entry": entry, "entry_id": not_available(report.get("timestamp"))}


def build_stage_3_1_document(report: dict[str, Any], project_root: Path) -> dict[str, str]:
    """Build Stage 3.1 notebook content."""
    json_path = report_path(project_root, "stage_3_1_court_point_selector_report.json")
    markdown_path = report_path(project_root, "stage_3_1_court_point_selector_report.md")
    next_step = stage_3_1_next_step(report)
    friction = report.get("friction", {})
    selected_status = report.get("selected_points_status", {})
    geometry = selected_status.get("geometry", {}) if isinstance(selected_status, dict) else {}

    summary = markdown_table(
        [
            ("Stage", "Stage 3.1 - Court point selection helper"),
            ("Verdict", report.get("final_verdict")),
            ("Friction score", friction.get("score")),
            ("Friction level", friction.get("band")),
            ("Timestamp", report.get("timestamp")),
            ("Recommended next step", next_step),
        ]
    )
    input_table = markdown_table(
        [
            ("Reference image", report.get("image_path")),
            ("Config path", report.get("config_path")),
            ("Calibration basis", report.get("calibration_basis")),
            ("Grid step", report.get("grid_step")),
            ("Interactive attempted", report.get("interactive_attempted")),
            ("Interactive completed", report.get("interactive_completed")),
            ("Point order valid", geometry.get("point_order_valid") if isinstance(geometry, dict) else None),
            ("Polygon self-intersects", geometry.get("polygon_self_intersects") if isinstance(geometry, dict) else None),
        ]
    )
    output_table = markdown_table(
        [
            ("JSON report path", json_path),
            ("Markdown report path", markdown_path),
            ("Log", latest_log_for_prefix(project_root, "stage_3_1_court_point_selector_")),
            ("Grid image", report.get("grid_image_path")),
            ("Config updated", nested_get(report, ("config_update", "updated"))),
            ("Valid selected points", selected_status.get("valid_count")),
            ("Point order valid", geometry.get("point_order_valid") if isinstance(geometry, dict) else None),
            ("Polygon self-intersects", geometry.get("polygon_self_intersects") if isinstance(geometry, dict) else None),
        ]
    )
    console_table = markdown_table(
        [
            ("Stage name", "Stage 3.1 court point selection helper"),
            ("Reference image", report.get("image_path")),
            ("Grid image", report.get("grid_image_path")),
            ("Grid step", report.get("grid_step")),
            ("Interactive completed", report.get("interactive_completed")),
            ("Points valid", report.get("points_valid")),
            ("Config updated", nested_get(report, ("config_update", "updated"))),
            ("Verdict", report.get("final_verdict")),
            ("Friction", f"{not_available(friction.get('score'))} ({not_available(friction.get('band'))})"),
            ("Recommended next step", next_step),
        ]
    )
    interpretation = (
        "The coordinate grid is available, so manual coordinate reading is easier. "
        "No saved point set is required for this helper to be useful."
        if report.get("final_verdict") == "ready_with_grid_only"
        else "Four valid court points were saved to the calibration config. Stage 3 can be rerun to compute homography."
        if report.get("final_verdict") == "ready_to_rerun_stage_3"
        else "The point selection helper is blocked until the Stage 3 reference frame is available."
    )

    body = stage_document(
        title="Stage 3.1 - Court Point Selection Helper",
        summary=summary,
        input_section=input_table,
        output_section=output_table,
        console_table=console_table,
        warnings=bullet_list(report.get("warnings"), "No warnings."),
        errors=bullet_list(report.get("errors"), "No errors."),
        interpretation=interpretation,
        next_step=next_step,
    )
    entry = history_entry(report, "Stage 3.1 - Court Point Selection Helper", summary, next_step)
    return {"body": body, "entry": entry, "entry_id": not_available(report.get("timestamp"))}


def build_stage_4_document(report: dict[str, Any], project_root: Path) -> dict[str, str]:
    """Build Stage 4 notebook content."""
    json_path = report_path(project_root, "stage_4_ball_tracking_probe_report.json")
    markdown_path = report_path(project_root, "stage_4_ball_tracking_probe_report.md")
    next_step = stage_4_next_step(report)
    friction = report.get("friction", {})
    result = report.get("ball_tracking_result", {})

    summary = markdown_table(
        [
            ("Stage", "Stage 4 - Ball tracking probe"),
            ("Verdict", report.get("final_verdict")),
            ("Friction score", friction.get("score")),
            ("Friction level", friction.get("band")),
            ("Timestamp", report.get("timestamp")),
            ("Recommended next step", next_step),
        ]
    )
    input_table = markdown_table(
        [
            ("Video path", report.get("video_path")),
            ("Max frames", report.get("max_frames")),
            ("Interval", report.get("interval")),
            ("Resize width", report.get("resize_width")),
            ("YOLO enabled", report.get("yolo_enabled")),
            ("Stage 3 spatially useful", nested_get(report, ("stage_3_spatial_status", "spatially_useful"))),
        ]
    )
    output_table = markdown_table(
        [
            ("JSON report path", json_path),
            ("Markdown report path", markdown_path),
            ("Log", latest_log_for_prefix(project_root, "stage_4_ball_tracking_probe_")),
            ("Overlay folder", result.get("overlay_folder")),
            ("Candidate CSV", result.get("csv_path")),
            ("Trajectory preview", result.get("trajectory_preview_path")),
        ]
    )
    console_table = markdown_table(
        [
            ("Stage name", "Stage 4 ball tracking probe"),
            ("Input video", report.get("video_path")),
            ("Verdict", report.get("final_verdict")),
            ("Friction", f"{not_available(friction.get('score'))} ({not_available(friction.get('band'))})"),
            ("Frames processed", result.get("frames_processed")),
            ("Ball candidates", result.get("candidate_count")),
            ("Frames with candidates", result.get("frames_with_candidates")),
            ("Average candidates/frame", result.get("average_candidates_per_frame")),
            ("YOLO enabled", report.get("yolo_enabled")),
            ("Recommended next step", next_step),
        ]
    )
    interpretation = (
        "The local OpenCV heuristic found ball-like candidates. The results are exploratory and likely noisy, "
        "but they provide a useful baseline for Stage 5 filtering and court projection."
        if (result.get("candidate_count") or 0) > 0
        else "The local OpenCV heuristic did not find ball candidates in the sampled frames. A specialized tennis ball model may be needed later."
    )

    body = stage_document(
        title="Stage 4 - Ball Tracking Probe",
        summary=summary,
        input_section=input_table,
        output_section=output_table,
        console_table=console_table,
        warnings=bullet_list(report.get("warnings"), "No warnings."),
        errors=bullet_list(report.get("errors"), "No errors."),
        interpretation=interpretation,
        next_step=next_step,
    )
    entry = history_entry(report, "Stage 4 - Ball Tracking Probe", summary, next_step)
    return {"body": body, "entry": entry, "entry_id": not_available(report.get("timestamp"))}


def build_stage_4_1_document(report: dict[str, Any], project_root: Path) -> dict[str, str]:
    """Build Stage 4.1 notebook content."""
    json_path = report_path(project_root, "stage_4_1_ball_labeling_helper_report.json")
    markdown_path = report_path(project_root, "stage_4_1_ball_labeling_helper_report.md")
    next_step = stage_4_1_next_step(report)
    friction = report.get("friction", {})
    comparison = report.get("candidate_comparison", {})
    comparison_summary = comparison.get("summary", {}) if isinstance(comparison, dict) else {}

    summary = markdown_table(
        [
            ("Stage", "Stage 4.1 - Manual ball labeling helper"),
            ("Verdict", report.get("final_verdict")),
            ("Friction score", friction.get("score")),
            ("Friction level", friction.get("band")),
            ("Timestamp", report.get("timestamp")),
            ("Recommended next step", next_step),
        ]
    )
    input_table = markdown_table(
        [
            ("Video path", report.get("video_path")),
            ("Frame indices", report.get("selected_frame_indices")),
            ("Resize width", report.get("resize_width")),
            ("Frame source mode", report.get("frame_source_mode")),
            ("Interactive", report.get("interactive")),
        ]
    )
    output_table = markdown_table(
        [
            ("JSON report path", json_path),
            ("Markdown report path", markdown_path),
            ("Log", latest_log_for_prefix(project_root, "stage_4_1_ball_labeling_helper_")),
            ("Manual labels CSV", report.get("output_csv_path")),
            ("Manual labels JSON", report.get("output_json_path")),
            ("Overlay folder", report.get("overlay_folder")),
            ("Comparison CSV", report.get("comparison_csv_path")),
        ]
    )
    console_table = markdown_table(
        [
            ("Stage name", "Stage 4.1 manual ball labeling helper"),
            ("Input video", report.get("video_path")),
            ("Frames shown", report.get("frames_shown")),
            ("Visible labels", report.get("visible_ball_labels_count")),
            ("Skipped frames", report.get("skipped_frames")),
            ("Compared labels", comparison_summary.get("labeled_frames_compared")),
            ("Average nearest distance", comparison_summary.get("average_nearest_distance")),
            ("Verdict", report.get("final_verdict")),
            ("Friction", f"{not_available(friction.get('score'))} ({not_available(friction.get('band'))})"),
            ("Recommended next step", next_step),
        ]
    )
    interpretation = (
        "Manual ball labels are available as ground truth for filtering and court projection."
        if (report.get("visible_ball_labels_count") or 0) > 0
        else "The helper is available, but visible ball labels have not been collected yet."
    )

    body = stage_document(
        title="Stage 4.1 - Manual Ball Labeling Helper",
        summary=summary,
        input_section=input_table,
        output_section=output_table,
        console_table=console_table,
        warnings=bullet_list(report.get("warnings"), "No warnings."),
        errors=bullet_list(report.get("errors"), "No errors."),
        interpretation=interpretation,
        next_step=next_step,
    )
    entry = history_entry(report, "Stage 4.1 - Manual Ball Labeling Helper", summary, next_step)
    return {"body": body, "entry": entry, "entry_id": not_available(report.get("timestamp"))}


def build_stage_5_document(report: dict[str, Any], project_root: Path) -> dict[str, str]:
    """Build Stage 5 notebook content."""
    json_path = report_path(project_root, "stage_5_ball_candidate_filtering_report.json")
    markdown_path = report_path(project_root, "stage_5_ball_candidate_filtering_report.md")
    next_step = stage_5_next_step(report)
    friction = report.get("friction", {})

    summary = markdown_table(
        [
            ("Stage", "Stage 5 - Ball candidate filtering and court projection"),
            ("Verdict", report.get("final_verdict")),
            ("Friction score", friction.get("score")),
            ("Friction level", friction.get("band")),
            ("Timestamp", report.get("timestamp")),
            ("Recommended next step", next_step),
        ]
    )
    input_table = markdown_table(
        [
            ("Automatic candidates CSV", report.get("input_candidate_csv")),
            ("Manual labels CSV", report.get("input_manual_labels_csv")),
            ("Calibration source", report.get("calibration_source")),
            ("Homography available", nested_get(report, ("homography_status", "homography_available"))),
        ]
    )
    output_table = markdown_table(
        [
            ("JSON report path", json_path),
            ("Markdown report path", markdown_path),
            ("Log", latest_log_for_prefix(project_root, "stage_5_ball_candidate_filtering_")),
            ("Candidate-label distances", nested_get(report, ("output_paths", "candidate_label_distances"))),
            ("Filtered candidates", nested_get(report, ("output_paths", "filtered_ball_candidates"))),
            ("Projected candidates", nested_get(report, ("output_paths", "projected_ball_candidates"))),
            ("Court projection preview", nested_get(report, ("output_paths", "court_projection_preview"))),
        ]
    )
    console_table = markdown_table(
        [
            ("Manual labels", report.get("manual_labels_count")),
            ("Automatic candidates", report.get("automatic_candidates_count")),
            ("Average nearest distance", report.get("nearest_candidate_average_distance")),
            ("Median nearest distance", report.get("nearest_candidate_median_distance")),
            ("Filtered candidates", report.get("filtered_candidates_count")),
            ("Projected candidates", report.get("projected_candidates_count")),
            ("Verdict", report.get("final_verdict")),
            ("Friction", f"{not_available(friction.get('score'))} ({not_available(friction.get('band'))})"),
            ("Recommended next step", next_step),
        ]
    )
    interpretation = (
        "Stage 5 filters noisy automatic candidates against manual labels and projects selected candidates into the calibrated court plane. "
        "It is still a research probe, not production ball tracking."
    )

    body = stage_document(
        title="Stage 5 - Ball Candidate Filtering",
        summary=summary,
        input_section=input_table,
        output_section=output_table,
        console_table=console_table,
        warnings=bullet_list(report.get("warnings"), "No warnings."),
        errors=bullet_list(report.get("errors"), "No errors."),
        interpretation=interpretation,
        next_step=next_step,
    )
    entry = history_entry(report, "Stage 5 - Ball Candidate Filtering", summary, next_step)
    return {"body": body, "entry": entry, "entry_id": not_available(report.get("timestamp"))}


def build_stage_5_1_document(report: dict[str, Any], project_root: Path) -> dict[str, str]:
    """Build Stage 5.1 notebook content."""
    json_path = report_path(project_root, "stage_5_1_candidate_improvement_report.json")
    markdown_path = report_path(project_root, "stage_5_1_candidate_improvement_report.md")
    next_step = stage_5_1_next_step(report)
    friction = report.get("friction", {})
    baseline = report.get("baseline", {})

    summary = markdown_table(
        [
            ("Stage", "Stage 5.1 - Ball candidate generation improvement"),
            ("Verdict", report.get("final_verdict")),
            ("Friction score", friction.get("score")),
            ("Friction level", friction.get("band")),
            ("Timestamp", report.get("timestamp")),
            ("Recommended next step", next_step),
        ]
    )
    input_table = markdown_table(
        [
            ("Video path", report.get("input_video_path")),
            ("Manual labels path", report.get("manual_labels_path")),
            ("Labeled frames count", report.get("labeled_frames_count")),
            ("Strategies tested", ", ".join(report.get("strategies_tested", []))),
            ("Stage 5 baseline average distance", baseline.get("average_distance")),
            ("Homography available", nested_get(report, ("calibration_status", "homography_available"))),
        ]
    )
    output_table = markdown_table(
        [
            ("JSON report path", json_path),
            ("Markdown report path", markdown_path),
            ("Log", latest_log_for_prefix(project_root, "stage_5_1_candidate_improvement_")),
            ("Strategy comparison CSV", nested_get(report, ("output_paths", "strategy_comparison_csv"))),
            ("Improved candidates CSV", nested_get(report, ("output_paths", "improved_candidates_csv"))),
            ("Projected candidates CSV", nested_get(report, ("output_paths", "projected_candidates_csv"))),
            ("Strategy preview", nested_get(report, ("output_paths", "strategy_preview"))),
        ]
    )
    console_table = markdown_table(
        [
            ("Best strategy", report.get("best_strategy")),
            ("Baseline average distance", baseline.get("average_distance")),
            ("Improved average distance", report.get("best_average_nearest_distance")),
            ("Improvement over baseline", report.get("improvement_over_baseline")),
            ("Improved candidates", report.get("improved_candidates_count")),
            ("Projected candidates", report.get("projected_candidates_count")),
            ("Verdict", report.get("final_verdict")),
            ("Friction", f"{not_available(friction.get('score'))} ({not_available(friction.get('band'))})"),
            ("Recommended next step", next_step),
        ]
    )
    interpretation = (
        "Stage 5.1 tests low-cost local computer vision strategies against manual ball labels. "
        "It measures whether handcrafted candidates are close enough for smoothing, without claiming production tracking."
    )

    body = stage_document(
        title="Stage 5.1 - Candidate Improvement",
        summary=summary,
        input_section=input_table,
        output_section=output_table,
        console_table=console_table,
        warnings=bullet_list(report.get("warnings"), "No warnings."),
        errors=bullet_list(report.get("errors"), "No errors."),
        interpretation=interpretation,
        next_step=next_step,
    )
    entry = history_entry(report, "Stage 5.1 - Candidate Improvement", summary, next_step)
    return {"body": body, "entry": entry, "entry_id": not_available(report.get("timestamp"))}


def build_stage_6_document(report: dict[str, Any], project_root: Path) -> dict[str, str]:
    """Build Stage 6 notebook content."""
    json_path = report_path(project_root, "stage_6_trajectory_smoothing_report.json")
    markdown_path = report_path(project_root, "stage_6_trajectory_smoothing_report.md")
    next_step = stage_6_next_step(report)
    friction = report.get("friction", {})

    summary = markdown_table(
        [
            ("Stage", "Stage 6 - Trajectory smoothing and event segmentation"),
            ("Verdict", report.get("final_verdict")),
            ("Friction score", friction.get("score")),
            ("Friction level", friction.get("band")),
            ("Timestamp", report.get("timestamp")),
            ("Recommended next step", next_step),
        ]
    )
    input_table = markdown_table(
        [
            ("Improved candidates CSV", report.get("input_improved_candidates_path")),
            ("Projected candidates CSV", report.get("input_projected_candidates_path")),
            ("Manual labels CSV", report.get("input_manual_labels_path")),
            ("Projected candidates available", report.get("projected_candidates_available")),
        ]
    )
    output_table = markdown_table(
        [
            ("JSON report path", json_path),
            ("Markdown report path", markdown_path),
            ("Log", latest_log_for_prefix(project_root, "stage_6_trajectory_smoothing_")),
            ("Raw trajectory CSV", report.get("raw_trajectory_csv_path")),
            ("Smoothed trajectory CSV", report.get("smoothed_trajectory_csv_path")),
            ("Events CSV", report.get("events_csv_path")),
            ("Image preview", report.get("image_trajectory_preview_path")),
            ("Court preview", report.get("court_trajectory_preview_path")),
        ]
    )
    console_table = markdown_table(
        [
            ("Trajectory points", report.get("trajectory_points_count")),
            ("Interpolated points", report.get("interpolated_points_count")),
            ("Events", report.get("events_count")),
            ("Events by type", report.get("events_by_type")),
            ("Smoothing method", report.get("smoothing_method")),
            ("Verdict", report.get("final_verdict")),
            ("Friction", f"{not_available(friction.get('score'))} ({not_available(friction.get('band'))})"),
            ("Recommended next step", next_step),
        ]
    )
    interpretation = (
        "Stage 6 creates an initial smoothed trajectory from improved ball candidates and marks event hypotheses. "
        "The event output is exploratory and should not be treated as scoring, line calling, or confirmed rally segmentation."
    )

    body = stage_document(
        title="Stage 6 - Trajectory Smoothing",
        summary=summary,
        input_section=input_table,
        output_section=output_table,
        console_table=console_table,
        warnings=bullet_list(report.get("warnings"), "No warnings."),
        errors=bullet_list(report.get("errors"), "No errors."),
        interpretation=interpretation,
        next_step=next_step,
    )
    entry = history_entry(report, "Stage 6 - Trajectory Smoothing", summary, next_step)
    return {"body": body, "entry": entry, "entry_id": not_available(report.get("timestamp"))}


def build_stage_7_document(report: dict[str, Any], project_root: Path) -> dict[str, str]:
    """Build Stage 7 notebook content."""
    json_path = report_path(project_root, "stage_7_player_interaction_probe_report.json")
    markdown_path = report_path(project_root, "stage_7_player_interaction_probe_report.md")
    next_step = stage_7_next_step(report)
    friction = report.get("friction", {})

    summary = markdown_table(
        [
            ("Stage", "Stage 7 - Player tracking and ball-player interaction"),
            ("Verdict", report.get("final_verdict")),
            ("Friction score", friction.get("score")),
            ("Friction level", friction.get("band")),
            ("Timestamp", report.get("timestamp")),
            ("Recommended next step", next_step),
        ]
    )
    input_table = markdown_table(
        [
            ("Video path", report.get("input_video_path")),
            ("Smoothed trajectory path", report.get("input_smoothed_trajectory_path")),
            ("Manual labels path", report.get("input_manual_labels_path")),
            ("Homography available", report.get("homography_available")),
        ]
    )
    output_table = markdown_table(
        [
            ("JSON report path", json_path),
            ("Markdown report path", markdown_path),
            ("Log", latest_log_for_prefix(project_root, "stage_7_player_interaction_probe_")),
            ("Player detections", nested_get(report, ("output_paths", "player_detections_csv"))),
            ("Player tracks", nested_get(report, ("output_paths", "player_tracks_csv"))),
            ("Ball-player distances", nested_get(report, ("output_paths", "ball_player_distances_csv"))),
            ("Interactions", nested_get(report, ("output_paths", "ball_player_interactions_csv"))),
            ("Summary preview", nested_get(report, ("output_paths", "summary_preview"))),
        ]
    )
    console_table = markdown_table(
        [
            ("Frames analyzed", len(report.get("frames_analyzed", []))),
            ("Player detections", report.get("player_detections_count")),
            ("Player tracks", report.get("player_tracks_count")),
            ("Ball-player associations", report.get("ball_points_associated_count")),
            ("Interaction hypotheses", report.get("interaction_hypotheses_count")),
            ("Interactions by type", report.get("interactions_by_type")),
            ("Verdict", report.get("final_verdict")),
            ("Friction", f"{not_available(friction.get('score'))} ({not_available(friction.get('band'))})"),
            ("Recommended next step", next_step),
        ]
    )
    interpretation = (
        "Stage 7 adds local CPU player detection and approximate player tracks so ball-player proximity can support possible-hit hypotheses. "
        "The interactions are exploratory and should not be treated as confirmed hits."
    )

    body = stage_document(
        title="Stage 7 - Player Interaction Probe",
        summary=summary,
        input_section=input_table,
        output_section=output_table,
        console_table=console_table,
        warnings=bullet_list(report.get("warnings"), "No warnings."),
        errors=bullet_list(report.get("errors"), "No errors."),
        interpretation=interpretation,
        next_step=next_step,
    )
    entry = history_entry(report, "Stage 7 - Player Interaction Probe", summary, next_step)
    return {"body": body, "entry": entry, "entry_id": not_available(report.get("timestamp"))}


def build_stage_7_1_document(report: dict[str, Any], project_root: Path) -> dict[str, str]:
    """Build Stage 7.1 notebook content."""
    json_path = report_path(project_root, "stage_7_1_player_filtering_report.json")
    markdown_path = report_path(project_root, "stage_7_1_player_filtering_report.md")
    next_step = stage_7_1_next_step(report)
    friction = report.get("friction", {})

    summary = markdown_table(
        [
            ("Stage", "Stage 7.1 - Court-aware player filtering"),
            ("Verdict", report.get("final_verdict")),
            ("Friction score", friction.get("score")),
            ("Friction level", friction.get("band")),
            ("Timestamp", report.get("timestamp")),
            ("Recommended next step", next_step),
        ]
    )
    input_table = markdown_table(
        [
            ("Player detections CSV", report.get("input_detections_path")),
            ("Player tracks CSV", report.get("input_tracks_path")),
            ("Video path", report.get("input_video_path")),
            ("Homography available", report.get("homography_available")),
        ]
    )
    output_table = markdown_table(
        [
            ("JSON report path", json_path),
            ("Markdown report path", markdown_path),
            ("Log", latest_log_for_prefix(project_root, "stage_7_1_player_filtering_")),
            ("Filtered detections", nested_get(report, ("output_paths", "filtered_player_detections"))),
            ("Filtered tracks", nested_get(report, ("output_paths", "filtered_player_tracks"))),
            ("Main players", nested_get(report, ("output_paths", "main_players"))),
            ("Identity profiles", nested_get(report, ("output_paths", "player_identity_profiles"))),
            ("Side states", nested_get(report, ("output_paths", "player_side_states"))),
        ]
    )
    console_table = markdown_table(
        [
            ("Input detections", report.get("total_detections_input")),
            ("Kept detections", report.get("detections_kept")),
            ("Input tracks", report.get("total_tracks_input")),
            ("Kept tracks", report.get("tracks_kept")),
            ("Main players selected", report.get("main_players_selected")),
            ("Player identities created", report.get("player_identities_created")),
            ("Refined associations", report.get("refined_ball_player_associations_count")),
            ("Verdict", report.get("final_verdict")),
            ("Friction", f"{not_available(friction.get('score'))} ({not_available(friction.get('band'))})"),
        ]
    )
    interpretation = (
        "Stage 7.1 filters noisy people detections and creates stable player_a/player_b identities from track quality and clothing-color cues. "
        "Near/far side is stored as a mutable state, not as permanent identity."
    )
    body = stage_document(
        title="Stage 7.1 - Player Filtering",
        summary=summary,
        input_section=input_table,
        output_section=output_table,
        console_table=console_table,
        warnings=bullet_list(report.get("warnings"), "No warnings."),
        errors=bullet_list(report.get("errors"), "No errors."),
        interpretation=interpretation,
        next_step=next_step,
    )
    entry = history_entry(report, "Stage 7.1 - Player Filtering", summary, next_step)
    return {"body": body, "entry": entry, "entry_id": not_available(report.get("timestamp"))}


def stage_document(
    *,
    title: str,
    summary: str,
    input_section: str,
    output_section: str,
    console_table: str,
    warnings: str,
    errors: str,
    interpretation: str,
    next_step: str,
) -> str:
    """Build the latest stage notebook document body."""
    return "\n\n".join(
        [
            f"# {title}",
            "## Summary\n\n" + summary,
            "## Input\n\n" + input_section,
            "## Output\n\n" + output_section,
            "## Console-equivalent table\n\n" + console_table,
            "## Warnings\n\n" + warnings,
            "## Errors\n\n" + errors,
            "## Interpretation\n\n" + interpretation,
            "## Next step\n\n" + next_step,
        ]
    )


def history_entry(report: dict[str, Any], stage_name: str, summary: str, next_step: str) -> str:
    """Build a compact history entry for a stage file."""
    timestamp = not_available(report.get("timestamp"))
    return "\n\n".join(
        [
            f"<!-- lab-entry:{timestamp} -->",
            f"### {timestamp}",
            markdown_table(
                [
                    ("Stage", stage_name),
                    ("Verdict", report.get("final_verdict")),
                    ("Friction score", nested_get(report, ("friction", "score"))),
                    ("Friction level", nested_get(report, ("friction", "band"))),
                    ("Next step", next_step),
                ]
            ),
        ]
    )


def existing_history(path: Path) -> str:
    """Return preserved run history."""
    if not path.exists():
        return ""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    marker = "## Run history"
    if marker not in text:
        return ""
    history = text.split(marker, 1)[1].strip()
    return history


def write_stage_notebook(path: Path, body: str, entry: str, entry_id: str) -> Path:
    """Write a stage notebook page while preserving prior entries."""
    path.parent.mkdir(parents=True, exist_ok=True)
    history = existing_history(path)
    duplicate_marker = f"<!-- lab-entry:{entry_id} -->"
    should_append = duplicate_marker not in history
    entries = [history]
    if should_append:
        entries.append(entry)
    text = body.rstrip() + "\n\n## Run history\n\n" + "\n\n".join(item for item in entries if item).rstrip() + "\n"
    path.write_text(text, encoding="utf-8")
    return path


def build_experiment_index(stage_summaries: list[dict[str, str]]) -> str:
    """Build the experiment index Markdown file."""
    lines = [
        "# Experiment Index",
        "",
        "| Stage | Name | Verdict | Friction | Main output | Next step |",
        "|---|---|---|---|---|---|",
    ]
    for summary in stage_summaries:
        lines.append(
            "| {stage} | {name} | {verdict} | {friction} | {main_output} | {next_step} |".format(
                stage=escape_table_value(summary["stage"]),
                name=escape_table_value(summary["name"]),
                verdict=escape_table_value(summary["verdict"]),
                friction=escape_table_value(summary["friction"]),
                main_output=escape_table_value(summary["main_output"]),
                next_step=escape_table_value(summary["next_step"]),
            )
        )
    return "\n".join(lines) + "\n"


def build_lab_readme() -> str:
    """Build lab notebook README content."""
    return """# Lab Notebook

This folder is the persistent project lab notebook for Tennis AI Vision.

The notebook records technical friction, inputs, outputs, decisions, warnings, errors, and validation results for each stage. This matters because the project is not only building a local tennis video analysis pipeline; it is also learning where the local workflow succeeds, where it struggles, and what should happen next.

The normal workflow is automatic:

1. Codex implements or modifies a stage.
2. Codex runs the relevant stage script.
3. The stage script generates JSON and Markdown reports.
4. The stage script updates `docs/lab-notebook/` automatically.
5. Codex verifies the stage page and `experiment_index.md`.

The manual update command exists only as a fallback/debug utility, not as the normal user workflow:

```powershell
python scripts\\update_lab_notebook.py
```

Stage scripts update the notebook automatically after they write their normal reports. If notebook generation fails, the stage script should continue and print a warning. Stage pages keep a run history so previous entries are preserved.

Future stages must call the lab notebook updater automatically at the end of their stage script. They should write JSON reports under `outputs/reports/`, include verdict and friction fields, then add a builder in `src/tennis_vision/lab_notebook.py` so the result appears in this notebook and the experiment index.
"""


def update_lab_notebook(project_root: Path) -> list[Path]:
    """Update all known lab notebook pages from available reports."""
    notebook_dir = ensure_lab_notebook_dir(project_root)
    written: list[Path] = []
    stage_summaries: list[dict[str, str]] = []

    stage_0_report = read_json_report(report_path(project_root, "environment_report.json"))
    if stage_0_report is not None:
        document = build_stage_0_document(stage_0_report, project_root)
        stage_path = notebook_dir / "stage_0_environment.md"
        written.append(
            write_stage_notebook(
                stage_path,
                document["body"],
                document["entry"],
                document["entry_id"],
            )
        )
        stage_summaries.append(
            {
                "stage": "Stage 0",
                "name": "Environment",
                "verdict": not_available(stage_0_report.get("final_verdict")),
                "friction": f"{not_available(nested_get(stage_0_report, ('friction', 'score')))} {not_available(nested_get(stage_0_report, ('friction', 'band')))}",
                "main_output": "outputs/reports/environment_report.md",
                "next_step": stage_0_next_step(stage_0_report),
            }
        )

    stage_1_report = read_json_report(report_path(project_root, "stage_1_video_probe_report.json"))
    if stage_1_report is not None:
        document = build_stage_1_document(stage_1_report, project_root)
        stage_path = notebook_dir / "stage_1_video_probe.md"
        written.append(
            write_stage_notebook(
                stage_path,
                document["body"],
                document["entry"],
                document["entry_id"],
            )
        )
        stage_summaries.append(
            {
                "stage": "Stage 1",
                "name": "Video Probe",
                "verdict": not_available(stage_1_report.get("final_verdict")),
                "friction": f"{not_available(nested_get(stage_1_report, ('friction', 'score')))} {not_available(nested_get(stage_1_report, ('friction', 'band')))}",
                "main_output": "outputs/reports/stage_1_video_probe_report.md",
                "next_step": stage_1_next_step(stage_1_report),
            }
        )

    stage_2_report = read_json_report(report_path(project_root, "stage_2_yolo_cpu_baseline_report.json"))
    if stage_2_report is not None:
        document = build_stage_2_document(stage_2_report, project_root)
        stage_path = notebook_dir / "stage_2_yolo_cpu_baseline.md"
        written.append(
            write_stage_notebook(
                stage_path,
                document["body"],
                document["entry"],
                document["entry_id"],
            )
        )
        stage_summaries.append(
            {
                "stage": "Stage 2",
                "name": "YOLO CPU Baseline",
                "verdict": not_available(stage_2_report.get("final_verdict")),
                "friction": f"{not_available(nested_get(stage_2_report, ('friction', 'score')))} {not_available(nested_get(stage_2_report, ('friction', 'band')))}",
                "main_output": "outputs/reports/stage_2_yolo_cpu_baseline_report.md",
                "next_step": stage_2_next_step(stage_2_report),
            }
        )

    stage_3_report = read_json_report(report_path(project_root, "stage_3_court_calibration_probe_report.json"))
    if stage_3_report is not None:
        document = build_stage_3_document(stage_3_report, project_root)
        stage_path = notebook_dir / "stage_3_court_calibration_probe.md"
        written.append(
            write_stage_notebook(
                stage_path,
                document["body"],
                document["entry"],
                document["entry_id"],
            )
        )
        stage_summaries.append(
            {
                "stage": "Stage 3",
                "name": "Court Calibration Probe",
                "verdict": not_available(stage_3_report.get("final_verdict")),
                "friction": f"{not_available(nested_get(stage_3_report, ('friction', 'score')))} {not_available(nested_get(stage_3_report, ('friction', 'band')))}",
                "main_output": "outputs/reports/stage_3_court_calibration_probe_report.md",
                "next_step": stage_3_next_step(stage_3_report),
            }
        )

    stage_3_1_report = read_json_report(report_path(project_root, "stage_3_1_court_point_selector_report.json"))
    if stage_3_1_report is not None:
        document = build_stage_3_1_document(stage_3_1_report, project_root)
        stage_path = notebook_dir / "stage_3_1_court_point_selector.md"
        written.append(
            write_stage_notebook(
                stage_path,
                document["body"],
                document["entry"],
                document["entry_id"],
            )
        )
        stage_summaries.append(
            {
                "stage": "Stage 3.1",
                "name": "Court Point Selection Helper",
                "verdict": not_available(stage_3_1_report.get("final_verdict")),
                "friction": f"{not_available(nested_get(stage_3_1_report, ('friction', 'score')))} {not_available(nested_get(stage_3_1_report, ('friction', 'band')))}",
                "main_output": "outputs/reports/stage_3_1_court_point_selector_report.md",
                "next_step": stage_3_1_next_step(stage_3_1_report),
            }
        )

    stage_4_report = read_json_report(report_path(project_root, "stage_4_ball_tracking_probe_report.json"))
    if stage_4_report is not None:
        document = build_stage_4_document(stage_4_report, project_root)
        stage_path = notebook_dir / "stage_4_ball_tracking_probe.md"
        written.append(
            write_stage_notebook(
                stage_path,
                document["body"],
                document["entry"],
                document["entry_id"],
            )
        )
        stage_summaries.append(
            {
                "stage": "Stage 4",
                "name": "Ball Tracking Probe",
                "verdict": not_available(stage_4_report.get("final_verdict")),
                "friction": f"{not_available(nested_get(stage_4_report, ('friction', 'score')))} {not_available(nested_get(stage_4_report, ('friction', 'band')))}",
                "main_output": "outputs/reports/stage_4_ball_tracking_probe_report.md",
                "next_step": stage_4_next_step(stage_4_report),
            }
        )

    stage_4_1_report = read_json_report(report_path(project_root, "stage_4_1_ball_labeling_helper_report.json"))
    if stage_4_1_report is not None:
        document = build_stage_4_1_document(stage_4_1_report, project_root)
        stage_path = notebook_dir / "stage_4_1_ball_labeling_helper.md"
        written.append(
            write_stage_notebook(
                stage_path,
                document["body"],
                document["entry"],
                document["entry_id"],
            )
        )
        stage_summaries.append(
            {
                "stage": "Stage 4.1",
                "name": "Manual Ball Labeling Helper",
                "verdict": not_available(stage_4_1_report.get("final_verdict")),
                "friction": f"{not_available(nested_get(stage_4_1_report, ('friction', 'score')))} {not_available(nested_get(stage_4_1_report, ('friction', 'band')))}",
                "main_output": "outputs/reports/stage_4_1_ball_labeling_helper_report.md",
                "next_step": stage_4_1_next_step(stage_4_1_report),
            }
        )

    stage_5_report = read_json_report(report_path(project_root, "stage_5_ball_candidate_filtering_report.json"))
    if stage_5_report is not None:
        document = build_stage_5_document(stage_5_report, project_root)
        stage_path = notebook_dir / "stage_5_ball_candidate_filtering.md"
        written.append(
            write_stage_notebook(
                stage_path,
                document["body"],
                document["entry"],
                document["entry_id"],
            )
        )
        stage_summaries.append(
            {
                "stage": "Stage 5",
                "name": "Ball Candidate Filtering",
                "verdict": not_available(stage_5_report.get("final_verdict")),
                "friction": f"{not_available(nested_get(stage_5_report, ('friction', 'score')))} {not_available(nested_get(stage_5_report, ('friction', 'band')))}",
                "main_output": "outputs/reports/stage_5_ball_candidate_filtering_report.md",
                "next_step": stage_5_next_step(stage_5_report),
            }
        )

    stage_5_1_report = read_json_report(report_path(project_root, "stage_5_1_candidate_improvement_report.json"))
    if stage_5_1_report is not None:
        document = build_stage_5_1_document(stage_5_1_report, project_root)
        stage_path = notebook_dir / "stage_5_1_candidate_improvement.md"
        written.append(
            write_stage_notebook(
                stage_path,
                document["body"],
                document["entry"],
                document["entry_id"],
            )
        )
        stage_summaries.append(
            {
                "stage": "Stage 5.1",
                "name": "Candidate Improvement",
                "verdict": not_available(stage_5_1_report.get("final_verdict")),
                "friction": f"{not_available(nested_get(stage_5_1_report, ('friction', 'score')))} {not_available(nested_get(stage_5_1_report, ('friction', 'band')))}",
                "main_output": "outputs/reports/stage_5_1_candidate_improvement_report.md",
                "next_step": stage_5_1_next_step(stage_5_1_report),
            }
        )

    stage_6_report = read_json_report(report_path(project_root, "stage_6_trajectory_smoothing_report.json"))
    if stage_6_report is not None:
        document = build_stage_6_document(stage_6_report, project_root)
        stage_path = notebook_dir / "stage_6_trajectory_smoothing.md"
        written.append(
            write_stage_notebook(
                stage_path,
                document["body"],
                document["entry"],
                document["entry_id"],
            )
        )
        stage_summaries.append(
            {
                "stage": "Stage 6",
                "name": "Trajectory Smoothing",
                "verdict": not_available(stage_6_report.get("final_verdict")),
                "friction": f"{not_available(nested_get(stage_6_report, ('friction', 'score')))} {not_available(nested_get(stage_6_report, ('friction', 'band')))}",
                "main_output": "outputs/reports/stage_6_trajectory_smoothing_report.md",
                "next_step": stage_6_next_step(stage_6_report),
            }
        )

    stage_7_report = read_json_report(report_path(project_root, "stage_7_player_interaction_probe_report.json"))
    if stage_7_report is not None:
        document = build_stage_7_document(stage_7_report, project_root)
        stage_path = notebook_dir / "stage_7_player_interaction_probe.md"
        written.append(
            write_stage_notebook(
                stage_path,
                document["body"],
                document["entry"],
                document["entry_id"],
            )
        )
        stage_summaries.append(
            {
                "stage": "Stage 7",
                "name": "Player Interaction Probe",
                "verdict": not_available(stage_7_report.get("final_verdict")),
                "friction": f"{not_available(nested_get(stage_7_report, ('friction', 'score')))} {not_available(nested_get(stage_7_report, ('friction', 'band')))}",
                "main_output": "outputs/reports/stage_7_player_interaction_probe_report.md",
                "next_step": stage_7_next_step(stage_7_report),
            }
        )

    stage_7_1_report = read_json_report(report_path(project_root, "stage_7_1_player_filtering_report.json"))
    if stage_7_1_report is not None:
        document = build_stage_7_1_document(stage_7_1_report, project_root)
        stage_path = notebook_dir / "stage_7_1_player_filtering.md"
        written.append(write_stage_notebook(stage_path, document["body"], document["entry"], document["entry_id"]))
        stage_summaries.append(
            {
                "stage": "Stage 7.1",
                "name": "Player Filtering",
                "verdict": not_available(stage_7_1_report.get("final_verdict")),
                "friction": f"{not_available(nested_get(stage_7_1_report, ('friction', 'score')))} {not_available(nested_get(stage_7_1_report, ('friction', 'band')))}",
                "main_output": "outputs/reports/stage_7_1_player_filtering_report.md",
                "next_step": stage_7_1_next_step(stage_7_1_report),
            }
        )

    index_path = notebook_dir / "experiment_index.md"
    index_path.write_text(build_experiment_index(stage_summaries), encoding="utf-8")
    written.append(index_path)

    readme_path = notebook_dir / "README.md"
    readme_path.write_text(build_lab_readme(), encoding="utf-8")
    written.append(readme_path)

    return written
