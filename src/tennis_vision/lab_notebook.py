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
    "stage_8": "stage_8_event_timeline.md",
    "stage_8_1": "stage_8_1_timeline_validation.md",
    "stage_8_2": "stage_8_2_event_labeling.md",
    "stage_8_3": "stage_8_3_event_validation.md",
    "stage_9": "stage_9_tactical_metrics.md",
    "stage_9_1": "stage_9_1_projection_coverage.md",
    "stage_10": "stage_10_analytical_report.md",
    "stage_11": "stage_11_report_package.md",
    "stage_12": "stage_12_replay_schema.md",
    "stage_13": "stage_13_2d_tactical_replay.md",
    "stage_14": "stage_14_side_view_replay.md",
    "stage_14_1": "stage_14_1_side_view_patch.md",
    "stage_14_2": "stage_14_2_side_view_event_disambiguation.md",
    "stage_14_3": "stage_14_3_validated_events_side_view.md",
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
    """Convert row pairs into plain-text-friendly field blocks."""
    lines: list[str] = []
    for field, value in rows:
        lines.append(f"{field}:")
        lines.append(f"  {escape_block_value(not_available(value))}")
        lines.append("")
    return "\n".join(lines).rstrip()


def escape_table_value(value: str) -> str:
    """Escape Markdown table-sensitive values."""
    return value.replace("|", "\\|").replace("\n", "<br>")


def escape_block_value(value: str) -> str:
    """Indent multi-line values for plain-text field blocks."""
    return value.replace("\n", "\n  ")


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


def stage_8_next_step(report: dict[str, Any]) -> str:
    """Return Stage 8 next-step text."""
    next_step = report.get("recommended_next_step")
    if next_step:
        return str(next_step)
    verdict = report.get("final_verdict")
    if verdict == "ready_for_stage_9":
        return "Proceed to Stage 9 tactical metrics and shot zone prototype."
    if verdict == "needs_more_labels":
        return "Proceed to Stage 8.1 expand labels and timeline validation."
    if verdict == "needs_better_event_validation":
        return "Proceed to Stage 8.2 event validation and manual event labeling helper."
    return "Review Stage 8 warnings and rerun after fixing missing inputs."


def stage_8_1_next_step(report: dict[str, Any]) -> str:
    """Return Stage 8.1 next-step text."""
    next_step = report.get("recommended_next_step")
    if next_step:
        return str(next_step)
    verdict = report.get("final_verdict")
    if verdict == "ready_for_stage_9":
        return "Proceed to Stage 9 tactical metrics and shot zone prototype."
    if verdict == "needs_event_labeling":
        return "Proceed to Stage 8.2 manual event labeling helper."
    if verdict == "needs_better_candidate_generation":
        return "Improve candidate generation before timeline validation."
    return "Run Stage 8.1 interactively with more frames, then rerun validation."


def stage_8_2_next_step(report: dict[str, Any]) -> str:
    """Return Stage 8.2 next-step text."""
    next_step = report.get("recommended_next_step")
    if next_step:
        return str(next_step)
    verdict = report.get("final_verdict")
    if verdict == "ready_for_stage_8_3":
        return "Proceed to Stage 8.3: Event Validation and Reclassification."
    if verdict == "ready_with_warnings":
        return "Review manual event label warnings, then proceed to Stage 8.3."
    if verdict == "needs_more_event_labels":
        return "Run Stage 8.2 interactively to collect bounce/hit/no-event/uncertain labels."
    return "Fix Stage 8.2 blockers, then rerun the event labeling helper."


def stage_8_3_next_step(report: dict[str, Any]) -> str:
    """Return Stage 8.3 next-step text."""
    next_step = report.get("recommended_next_step")
    if next_step:
        return str(next_step)
    verdict = report.get("final_verdict")
    if verdict == "ready_for_stage_14_3":
        return "Proceed to Stage 14.3: Side-View Replay with Validated Events."
    if verdict == "ready_with_warnings":
        return "Proceed to Stage 14.3, but collect manual hit labels before confirming hits."
    if verdict == "needs_manual_hit_labels":
        return "Return to Stage 8.2 and collect manual hit labels."
    if verdict == "needs_more_event_labels":
        return "Return to Stage 8.2 and collect more manual event labels."
    return "Fix Stage 8.3 blockers, then rerun event validation."


def stage_9_next_step(report: dict[str, Any]) -> str:
    """Return Stage 9 next-step text."""
    next_step = report.get("recommended_next_step")
    if next_step:
        return str(next_step)
    verdict = report.get("final_verdict")
    if verdict == "ready_for_stage_10":
        return "Proceed to Stage 10 analytical report generator and coaching summary prototype."
    if verdict == "needs_better_projection":
        return "Tune court projection or candidate projection coverage, then rerun Stage 9."
    if verdict == "needs_event_validation":
        return "Return to Stage 8.2 manual event validation."
    return "Review Stage 9 warnings, then decide between Stage 9.1 tuning and more validation."


def stage_9_1_next_step(report: dict[str, Any]) -> str:
    """Return Stage 9.1 next-step text."""
    next_step = report.get("recommended_next_step")
    if next_step:
        return str(next_step)
    verdict = report.get("final_verdict")
    if verdict == "ready_for_stage_10":
        return "Proceed to Stage 10 analytical report generator and coaching summary prototype."
    if verdict == "needs_projection_review":
        return "Review projection bounds, calibration, or court zone tuning before Stage 10."
    if verdict == "needs_more_labels":
        return "Collect more expanded labels, then rerun Stage 9.1."
    return "Fix Stage 9.1 blockers, then rerun projection coverage tuning."


def stage_10_next_step(report: dict[str, Any]) -> str:
    """Return Stage 10 next-step text."""
    next_step = report.get("recommended_next_step")
    if next_step:
        return str(next_step)
    verdict = report.get("final_verdict")
    if verdict == "ready_for_stage_11":
        return "Proceed to Stage 11: Annotated Highlight/Report Package Generator."
    if verdict == "needs_more_validation":
        return "Tune report wording in Stage 10.1 or validate more events before packaging."
    if verdict == "ready_with_warnings":
        return "Proceed cautiously to Stage 11 or Stage 10.1 wording/confidence tuning."
    return "Fix Stage 10 blockers, then rerun the analytical report generator."


def stage_11_next_step(report: dict[str, Any]) -> str:
    """Return Stage 11 next-step text."""
    next_step = report.get("recommended_next_step")
    if next_step:
        return str(next_step)
    verdict = report.get("final_verdict")
    if verdict == "ready_for_stage_12":
        return "Proceed to Stage 12: Synthetic Rally Replay Data Schema."
    if verdict == "ready_with_warnings":
        return "Review optional missing artifacts, then proceed to Stage 12 or Stage 11.1 package polish."
    if verdict == "package_incomplete":
        return "Regenerate missing core reports, then rerun Stage 11."
    return "Fix Stage 11 blockers, then rerun the report package generator."


def stage_12_next_step(report: dict[str, Any]) -> str:
    """Return Stage 12 next-step text."""
    next_step = report.get("recommended_next_step")
    if next_step:
        return str(next_step)
    verdict = report.get("final_verdict")
    if verdict == "ready_for_stage_13":
        return "Proceed to Stage 13: 2D Tactical Replay Renderer."
    if verdict == "ready_with_warnings":
        return "Review missing replay context, then proceed cautiously to Stage 13."
    if verdict == "needs_more_replay_data":
        return "Regenerate missing court, trajectory, player, or event data, then rerun Stage 12."
    return "Fix Stage 12 blockers, then rerun the replay schema generator."


def stage_13_next_step(report: dict[str, Any]) -> str:
    """Return Stage 13 next-step text."""
    next_step = report.get("recommended_next_step")
    if next_step:
        return str(next_step)
    verdict = report.get("final_verdict")
    if verdict == "ready_for_stage_14":
        return "Proceed to Stage 14: Side-View Ball Flight Renderer."
    if verdict == "ready_with_warnings":
        return "Review renderer warnings, then proceed to Stage 14 or Stage 13.1 visual polish."
    if verdict == "needs_more_replay_data":
        return "Regenerate Stage 12 replay schema data, then rerun Stage 13."
    return "Fix Stage 13 blockers, then rerun the 2D tactical replay renderer."


def stage_14_next_step(report: dict[str, Any]) -> str:
    """Return Stage 14 next-step text."""
    next_step = report.get("recommended_next_step")
    if next_step:
        return str(next_step)
    verdict = report.get("final_verdict")
    if verdict == "ready_for_stage_15":
        return "Proceed to Stage 15: Multi-Camera Analytical Replay."
    if verdict == "ready_with_warnings":
        return "Review renderer warnings, then proceed to Stage 15 or Stage 14.1 visual polish."
    if verdict == "needs_more_replay_data":
        return "Regenerate Stage 12 replay data with usable keyframes, then rerun Stage 14."
    return "Fix Stage 14 blockers, then rerun the side-view renderer."


def stage_14_1_next_step(report: dict[str, Any]) -> str:
    """Return Stage 14.1 next-step text."""
    next_step = report.get("recommended_next_step")
    if next_step:
        return str(next_step)
    verdict = report.get("final_verdict")
    if verdict == "ready_for_stage_15":
        return "Proceed to Stage 15: Multi-Camera Analytical Replay."
    if verdict == "needs_more_side_view_tuning":
        return "Tune side-view semantics further before Stage 15."
    if verdict == "ready_with_warnings":
        return "Review warnings, then proceed to Stage 15 or Stage 14.2 polish."
    return "Fix Stage 14.1 blockers, then rerun the side-view patch."


def stage_14_2_next_step(report: dict[str, Any]) -> str:
    """Return Stage 14.2 next-step text."""
    verdict = report.get("final_verdict")
    if verdict == "ready_for_stage_15":
        return "Proceed to Stage 15: Multi-Camera Analytical Replay."
    if verdict == "ready_with_warnings":
        return "Review warnings, then proceed to Stage 15 or Stage 14.3 side-view tuning."
    if verdict == "needs_more_event_disambiguation":
        return "Tune player-aware side-view event semantics before Stage 15."
    return "Fix Stage 14.2 blockers, then rerun the side-view patch."


def stage_14_3_next_step(report: dict[str, Any]) -> str:
    """Return Stage 14.3 next-step text."""
    next_step = report.get("recommended_next_step")
    if next_step:
        return str(next_step)
    verdict = report.get("final_verdict")
    if verdict == "ready_for_stage_15":
        return "Proceed to Stage 15: Multi-Camera Analytical Replay."
    if verdict == "ready_with_warnings":
        return "Proceed cautiously to Stage 15, or collect manual hit labels before rendering confident hit markers."
    if verdict == "needs_more_side_view_tuning":
        return "Tune side-view validated-event rendering before Stage 15."
    if verdict == "needs_more_hit_labels":
        return "Return to Stage 8.2 and collect manual hit labels."
    return "Fix Stage 14.3 blockers, then rerun the side-view renderer."


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


def build_stage_8_document(report: dict[str, Any], project_root: Path) -> dict[str, str]:
    """Build Stage 8 notebook content."""
    json_path = report_path(project_root, "stage_8_event_timeline_report.json")
    markdown_path = report_path(project_root, "stage_8_event_timeline_report.md")
    next_step = stage_8_next_step(report)
    friction = report.get("friction", {})
    outputs = report.get("output_paths", {})

    summary = markdown_table(
        [
            ("Stage", "Stage 8 - Event timeline"),
            ("Verdict", report.get("final_verdict")),
            ("Friction score", friction.get("score")),
            ("Friction level", friction.get("band")),
            ("Timestamp", report.get("timestamp")),
            ("Recommended next step", next_step),
        ]
    )
    input_table = markdown_table(
        [
            ("Trajectory points", report.get("trajectory_points_count")),
            ("Source events", report.get("source_event_count")),
            ("Merge window", report.get("merge_window")),
            ("Inputs used", report.get("inputs_used")),
        ]
    )
    output_table = markdown_table(
        [
            ("JSON report path", json_path),
            ("Markdown report path", markdown_path),
            ("Log", latest_log_for_prefix(project_root, "stage_8_event_timeline_")),
            ("Event timeline CSV", outputs.get("event_timeline_csv")),
            ("Event timeline JSON", outputs.get("event_timeline_json")),
            ("Rally segments CSV", outputs.get("rally_segments_csv")),
            ("Player attribution CSV", outputs.get("player_event_attribution_csv")),
            ("Timeline preview", outputs.get("timeline_preview")),
            ("Court timeline preview", outputs.get("court_timeline_preview")),
        ]
    )
    console_table = markdown_table(
        [
            ("Trajectory points", report.get("trajectory_points_count")),
            ("Source events", report.get("source_event_count")),
            ("Merged timeline events", report.get("merged_timeline_event_count")),
            ("Rally segments", report.get("rally_segments_count")),
            ("Player-attributed events", report.get("player_attributed_events_count")),
            ("Events by type", report.get("events_by_type")),
            ("Verdict", report.get("final_verdict")),
            ("Friction", f"{not_available(friction.get('score'))} ({not_available(friction.get('band'))})"),
        ]
    )
    interpretation = (
        "Stage 8 combines trajectory anchors, event hypotheses, player interactions, and stabilized player identities "
        "into a first event timeline. The timeline preserves uncertainty with possible_* labels and should be treated "
        "as a prototype, not confirmed rally understanding."
    )
    body = stage_document(
        title="Stage 8 - Event Timeline",
        summary=summary,
        input_section=input_table,
        output_section=output_table,
        console_table=console_table,
        warnings=bullet_list(report.get("warnings"), "No warnings."),
        errors=bullet_list(report.get("errors"), "No errors."),
        interpretation=interpretation,
        next_step=next_step,
    )
    entry = history_entry(report, "Stage 8 - Event Timeline", summary, next_step)
    return {"body": body, "entry": entry, "entry_id": not_available(report.get("timestamp"))}


def build_stage_8_1_document(report: dict[str, Any], project_root: Path) -> dict[str, str]:
    """Build Stage 8.1 notebook content."""
    json_path = report_path(project_root, "stage_8_1_timeline_validation_report.json")
    markdown_path = report_path(project_root, "stage_8_1_timeline_validation_report.md")
    next_step = stage_8_1_next_step(report)
    friction = report.get("friction", {})
    outputs = report.get("output_paths", {})

    summary = markdown_table(
        [
            ("Stage", "Stage 8.1 - Timeline validation"),
            ("Verdict", report.get("final_verdict")),
            ("Friction score", friction.get("score")),
            ("Friction level", friction.get("band")),
            ("Timestamp", report.get("timestamp")),
            ("Recommended next step", next_step),
        ]
    )
    input_table = markdown_table(
        [
            ("Mode", report.get("mode")),
            ("Label source used", report.get("label_source_used")),
            ("Expanded label frames", ", ".join(str(frame) for frame in report.get("expanded_label_frames", []))),
            ("Expanded labels loaded", report.get("expanded_labels_loaded_successfully")),
            ("Label persistence status", report.get("label_persistence_status")),
            ("Previous best visible labels", report.get("previous_best_visible_labels_count")),
            ("Existing labels", report.get("existing_labels_count")),
            ("New labels", report.get("new_labels_count")),
            ("Merged labels", report.get("merged_labels_count")),
            ("Merged visible labels", report.get("merged_visible_labels_count", report.get("visible_labels_count"))),
            ("Label frame range", report.get("label_frame_range")),
        ]
    )
    output_table = markdown_table(
        [
            ("JSON report path", json_path),
            ("Markdown report path", markdown_path),
            ("Log", latest_log_for_prefix(project_root, "stage_8_1_timeline_validation_")),
            ("Expanded labels", outputs.get("expanded_labels_csv")),
            ("Latest session backup", report.get("latest_session_path")),
            ("Fallback labels", report.get("fallback_labels_path")),
            ("Candidate validation", outputs.get("expanded_candidate_validation")),
            ("Timeline validation", outputs.get("timeline_event_validation")),
            ("Validated timeline", outputs.get("validated_event_timeline_csv")),
        ]
    )
    console_table = markdown_table(
        [
            ("Existing labels", report.get("existing_labels_count")),
            ("New labels", report.get("new_labels_count")),
            ("Merged visible labels", report.get("merged_visible_labels_count", report.get("visible_labels_count"))),
            ("Average label gap", report.get("average_label_gap")),
            ("Maximum label gap", report.get("maximum_label_gap")),
            ("Candidate average distance", report.get("average_candidate_distance")),
            ("Timeline events validated", report.get("timeline_events_validated")),
            ("Supported events", report.get("supported_events_count")),
            ("Verdict", report.get("final_verdict")),
            ("Friction", f"{not_available(friction.get('score'))} ({not_available(friction.get('band'))})"),
        ]
    )
    interpretation = (
        "Stage 8.1 checks whether the Stage 8 timeline is backed by enough ball-label evidence. "
        "It can run non-interactively using current labels, but sparse coverage should trigger more manual labeling "
        "before tactical metrics."
    )
    body = stage_document(
        title="Stage 8.1 - Timeline Validation",
        summary=summary,
        input_section=input_table,
        output_section=output_table,
        console_table=console_table,
        warnings=bullet_list(report.get("warnings"), "No warnings."),
        errors=bullet_list(report.get("errors"), "No errors."),
        interpretation=interpretation,
        next_step=next_step,
    )
    entry = history_entry(report, "Stage 8.1 - Timeline Validation", summary, next_step)
    return {"body": body, "entry": entry, "entry_id": not_available(report.get("timestamp"))}


def build_stage_8_2_document(report: dict[str, Any], project_root: Path) -> dict[str, str]:
    """Build Stage 8.2 notebook content."""
    json_path = report_path(project_root, "stage_8_2_event_labeling_report.json")
    markdown_path = report_path(project_root, "stage_8_2_event_labeling_report.md")
    next_step = stage_8_2_next_step(report)
    friction = report.get("friction", {})

    summary = markdown_table(
        [
            ("Stage", "Stage 8.2 - Manual event labeling"),
            ("Verdict", report.get("final_verdict")),
            ("Friction score", friction.get("score")),
            ("Friction level", friction.get("band")),
            ("Timestamp", report.get("timestamp")),
            ("Recommended next step", next_step),
        ]
    )
    input_table = markdown_table(
        [
            ("Mode", report.get("mode")),
            ("Frames requested", ", ".join(str(frame) for frame in report.get("frames_requested", []))),
            ("Frames shown", report.get("frames_shown")),
            ("Existing labels", report.get("existing_labels_count")),
            ("New labels", report.get("new_labels_count")),
            ("Merged labels", report.get("merged_labels_count")),
        ]
    )
    output_table = markdown_table(
        [
            ("JSON report path", json_path),
            ("Markdown report path", markdown_path),
            ("Manual event labels", report.get("manual_event_labels_path")),
            ("Event comparison", report.get("event_label_comparison_path")),
            ("Event coverage", report.get("event_label_coverage_path")),
            ("Overlay folder", report.get("overlay_folder")),
        ]
    )
    console_table = markdown_table(
        [
            ("Bounce labels", report.get("bounce_count")),
            ("Hit labels", report.get("hit_count")),
            ("No-event labels", report.get("no_event_count")),
            ("Uncertain labels", report.get("uncertain_count")),
            ("Compatible matches", report.get("compatible_matches")),
            ("Mismatches", report.get("mismatches")),
            ("Verdict", report.get("final_verdict")),
            ("Friction", f"{not_available(friction.get('score'))} ({not_available(friction.get('band'))})"),
        ]
    )
    interpretation = (
        "Stage 8.2 creates human event labels for bounce, hit, no_event, and uncertain frames. "
        "This is the missing ground-truth layer needed before event reclassification or more side-view replay tuning."
    )
    body = stage_document(
        title="Stage 8.2 - Manual Bounce / Hit Event Labeling",
        summary=summary,
        input_section=input_table,
        output_section=output_table,
        console_table=console_table,
        warnings=bullet_list(report.get("warnings"), "No warnings."),
        errors=bullet_list(report.get("errors"), "No errors."),
        interpretation=interpretation,
        next_step=next_step,
    )
    entry = history_entry(report, "Stage 8.2 - Manual Event Labeling", summary, next_step)
    return {"body": body, "entry": entry, "entry_id": not_available(report.get("timestamp"))}


def build_stage_8_3_document(report: dict[str, Any], project_root: Path) -> dict[str, str]:
    """Build Stage 8.3 notebook content."""
    json_path = report_path(project_root, "stage_8_3_event_validation_report.json")
    markdown_path = report_path(project_root, "stage_8_3_event_validation_report.md")
    next_step = stage_8_3_next_step(report)
    friction = report.get("friction", {})
    outputs = report.get("output_paths", {})

    summary = markdown_table(
        [
            ("Stage", "Stage 8.3 - Event validation and reclassification"),
            ("Verdict", report.get("final_verdict")),
            ("Friction score", friction.get("score")),
            ("Friction level", friction.get("band")),
            ("Timestamp", report.get("timestamp")),
            ("Recommended next step", next_step),
        ]
    )
    input_table = markdown_table(
        [
            ("Manual labels", report.get("manual_labels_count")),
            ("Bounce labels", report.get("manual_bounce_labels_count")),
            ("Hit labels", report.get("manual_hit_labels_count")),
            ("No-event labels", report.get("manual_no_event_count")),
            ("Uncertain labels", report.get("manual_uncertain_count")),
            ("Bounce windows", report.get("bounce_windows_count")),
        ]
    )
    output_table = markdown_table(
        [
            ("JSON report path", json_path),
            ("Markdown report path", markdown_path),
            ("Manual event windows", outputs.get("manual_event_windows")),
            ("Event validation results", outputs.get("event_validation_results")),
            ("Validated event timeline", outputs.get("validated_event_timeline")),
            ("Validation preview", outputs.get("event_validation_timeline_preview")),
        ]
    )
    console_table = markdown_table(
        [
            ("Automatic events", report.get("automatic_events_count")),
            ("Validated bounces", report.get("validated_bounce_count")),
            ("Validated hits", report.get("validated_hit_count")),
            ("Downgraded hits", report.get("downgraded_hit_count")),
            ("Rejected events", report.get("rejected_events_count")),
            ("Unvalidated events", report.get("unvalidated_events_count")),
            ("Verdict", report.get("final_verdict")),
            ("Friction", f"{not_available(friction.get('score'))} ({not_available(friction.get('band'))})"),
        ]
    )
    interpretation = (
        "Stage 8.3 uses manual event labels to validate or downgrade automatic event hypotheses. "
        "Adjacent bounce labels are grouped into one bounce window so a multi-frame bounce is not treated "
        "as several separate bounces. The validated timeline should be the preferred event source for "
        "side-view replay correction."
    )
    body = stage_document(
        title="Stage 8.3 - Event Validation and Reclassification",
        summary=summary,
        input_section=input_table,
        output_section=output_table,
        console_table=console_table,
        warnings=bullet_list(report.get("warnings"), "No warnings."),
        errors=bullet_list(report.get("errors"), "No errors."),
        interpretation=interpretation,
        next_step=next_step,
    )
    entry = history_entry(report, "Stage 8.3 - Event Validation", summary, next_step)
    return {"body": body, "entry": entry, "entry_id": not_available(report.get("timestamp"))}


def build_stage_9_document(report: dict[str, Any], project_root: Path) -> dict[str, str]:
    """Build Stage 9 notebook content."""
    json_path = report_path(project_root, "stage_9_tactical_metrics_report.json")
    markdown_path = report_path(project_root, "stage_9_tactical_metrics_report.md")
    next_step = stage_9_next_step(report)
    friction = report.get("friction", {})
    outputs = report.get("output_paths", {})

    summary = markdown_table(
        [
            ("Stage", "Stage 9 - Tactical metrics and shot zones"),
            ("Verdict", report.get("final_verdict")),
            ("Friction score", friction.get("score")),
            ("Friction level", friction.get("band")),
            ("Timestamp", report.get("timestamp")),
            ("Recommended next step", next_step),
        ]
    )
    input_table = markdown_table(
        [
            ("Validated timeline", nested_get(report, ("inputs_used", "validated_timeline"))),
            ("Expanded labels", nested_get(report, ("inputs_used", "expanded_labels"))),
            ("Smoothed trajectory", nested_get(report, ("inputs_used", "smoothed_trajectory"))),
            ("Projected candidates", nested_get(report, ("inputs_used", "projected_improved_candidates"))),
            ("Player associations", nested_get(report, ("inputs_used", "refined_player_associations"))),
        ]
    )
    output_table = markdown_table(
        [
            ("JSON report path", json_path),
            ("Markdown report path", markdown_path),
            ("Log", latest_log_for_prefix(project_root, "stage_9_tactical_metrics_")),
            ("Ball zone assignments", outputs.get("ball_zone_assignments_csv")),
            ("Shot direction estimates", outputs.get("shot_direction_estimates_csv")),
            ("Rally tactical summary", outputs.get("rally_tactical_summary_csv")),
            ("Tactical summary", outputs.get("tactical_summary_md")),
            ("Court zone map", outputs.get("court_zone_map")),
            ("Ball placement map", outputs.get("ball_placement_map")),
        ]
    )
    console_table = markdown_table(
        [
            ("Ball points analyzed", report.get("ball_points_analyzed")),
            ("Projected points", report.get("projected_points_count")),
            ("Zone assignments", report.get("zone_assignments_count")),
            ("Unknown zones", report.get("unknown_zone_count")),
            ("Direction estimates", report.get("direction_estimates_count")),
            ("Rally summaries", report.get("rally_summaries_count")),
            ("Verdict", report.get("final_verdict")),
            ("Friction", f"{not_available(friction.get('score'))} ({not_available(friction.get('band'))})"),
        ]
    )
    interpretation = (
        "Stage 9 translates validated ball/timeline/player evidence into first-pass tactical placement signals. "
        "The outputs are approximate and hypothesis-based, not official scoring, line calling, or coaching conclusions."
    )
    body = stage_document(
        title="Stage 9 - Tactical Metrics",
        summary=summary,
        input_section=input_table,
        output_section=output_table,
        console_table=console_table,
        warnings=bullet_list(report.get("warnings"), "No warnings."),
        errors=bullet_list(report.get("errors"), "No errors."),
        interpretation=interpretation,
        next_step=next_step,
    )
    entry = history_entry(report, "Stage 9 - Tactical Metrics", summary, next_step)
    return {"body": body, "entry": entry, "entry_id": not_available(report.get("timestamp"))}


def build_stage_9_1_document(report: dict[str, Any], project_root: Path) -> dict[str, str]:
    """Build Stage 9.1 notebook content."""
    json_path = report_path(project_root, "stage_9_1_projection_coverage_report.json")
    markdown_path = report_path(project_root, "stage_9_1_projection_coverage_report.md")
    next_step = stage_9_1_next_step(report)
    friction = report.get("friction", {})
    outputs = report.get("output_paths", {})

    summary = markdown_table(
        [
            ("Stage", "Stage 9.1 - Projection coverage and court zone tuning"),
            ("Verdict", report.get("final_verdict")),
            ("Friction score", friction.get("score")),
            ("Friction level", friction.get("band")),
            ("Timestamp", report.get("timestamp")),
            ("Recommended next step", next_step),
        ]
    )
    input_table = markdown_table(
        [
            ("Expanded labels", nested_get(report, ("inputs_used", "expanded_labels"))),
            ("Stage 9 assignments", nested_get(report, ("inputs_used", "stage_9_assignments"))),
            ("Court calibration", nested_get(report, ("inputs_used", "court_calibration"))),
            ("Homography source", nested_get(report, ("inputs_used", "homography_source"))),
        ]
    )
    output_table = markdown_table(
        [
            ("JSON report path", json_path),
            ("Markdown report path", markdown_path),
            ("Log", latest_log_for_prefix(project_root, "stage_9_1_projection_coverage_")),
            ("Projected expanded labels", outputs.get("projected_expanded_labels_csv")),
            ("Tuned zone assignments", outputs.get("tuned_ball_zone_assignments_csv")),
            ("Zone comparison", outputs.get("stage_9_vs_9_1_zone_comparison_csv")),
            ("Projection map", outputs.get("projection_coverage_map")),
            ("Tuned placement map", outputs.get("tuned_ball_placement_map")),
        ]
    )
    console_table = markdown_table(
        [
            ("Stage 9 projected points", report.get("stage_9_projected_points")),
            ("Stage 9 unknown zones", report.get("stage_9_unknown_zones")),
            ("Stage 9.1 projected points", report.get("stage_9_1_projected_points")),
            ("Stage 9.1 unknown zones", report.get("stage_9_1_unknown_zones")),
            ("Unknown zone reduction", report.get("unknown_zone_reduction")),
            ("Projection coverage improvement", report.get("projection_coverage_improvement")),
            ("Verdict", report.get("final_verdict")),
            ("Friction", f"{not_available(friction.get('score'))} ({not_available(friction.get('band'))})"),
        ]
    )
    interpretation = (
        "Stage 9.1 projects expanded manual labels through the Stage 3 homography so tactical zones "
        "are based on court-space coordinates rather than missing projection fields. Outputs remain approximate."
    )
    body = stage_document(
        title="Stage 9.1 - Projection Coverage",
        summary=summary,
        input_section=input_table,
        output_section=output_table,
        console_table=console_table,
        warnings=bullet_list(report.get("warnings"), "No warnings."),
        errors=bullet_list(report.get("errors"), "No errors."),
        interpretation=interpretation,
        next_step=next_step,
    )
    entry = history_entry(report, "Stage 9.1 - Projection Coverage", summary, next_step)
    return {"body": body, "entry": entry, "entry_id": not_available(report.get("timestamp"))}


def build_stage_10_document(report: dict[str, Any], project_root: Path) -> dict[str, str]:
    """Build Stage 10 notebook content."""
    json_path = report_path(project_root, "stage_10_analytical_report_report.json")
    markdown_path = report_path(project_root, "stage_10_analytical_report_report.md")
    next_step = stage_10_next_step(report)
    friction = report.get("friction", {})
    outputs = report.get("output_paths", {})

    summary = markdown_table(
        [
            ("Stage", "Stage 10 - Analytical report and coaching summary prototype"),
            ("Verdict", report.get("final_verdict")),
            ("Confidence level", report.get("confidence_level")),
            ("Friction score", friction.get("score")),
            ("Friction level", friction.get("band")),
            ("Timestamp", report.get("timestamp")),
            ("Recommended next step", next_step),
        ]
    )
    input_table = markdown_table(
        [
            ("Tactical zones", nested_get(report, ("inputs_used", "tactical_zones"))),
            ("Directions", nested_get(report, ("inputs_used", "directions"))),
            ("Rally summary", nested_get(report, ("inputs_used", "rally_summary"))),
            ("Validated timeline", nested_get(report, ("inputs_used", "validated_timeline"))),
            ("Main players", nested_get(report, ("inputs_used", "main_players"))),
        ]
    )
    output_table = markdown_table(
        [
            ("JSON report path", json_path),
            ("Markdown report path", markdown_path),
            ("Log", latest_log_for_prefix(project_root, "stage_10_analytical_report_")),
            ("Analytical report", outputs.get("analytical_report_md")),
            ("Analytical JSON", outputs.get("analytical_report_json")),
            ("Coaching summary", outputs.get("coaching_summary_md")),
            ("Confidence summary", outputs.get("confidence_summary_json")),
            ("Key findings", outputs.get("key_findings_md")),
            ("Visual references", outputs.get("visual_references_md")),
        ]
    )
    console_table = markdown_table(
        [
            ("Labels analyzed", report.get("label_count")),
            ("Projected points", report.get("projected_points_count")),
            ("Unknown zones", report.get("unknown_zone_count")),
            ("Key findings", report.get("key_findings_count")),
            ("Coaching observations", report.get("observations_count")),
            ("Verdict", report.get("final_verdict")),
            ("Friction", f"{not_available(friction.get('score'))} ({not_available(friction.get('band'))})"),
        ]
    )
    interpretation = (
        "Stage 10 converts validated tactical outputs into a player-readable analytical report. "
        "It is deterministic, local, and preserves uncertainty. It does not provide official coaching, "
        "scoring, line calling, or confirmed shot classification."
    )
    body = stage_document(
        title="Stage 10 - Analytical Report",
        summary=summary,
        input_section=input_table,
        output_section=output_table,
        console_table=console_table,
        warnings=bullet_list(report.get("warnings"), "No warnings."),
        errors=bullet_list(report.get("errors"), "No errors."),
        interpretation=interpretation,
        next_step=next_step,
    )
    entry = history_entry(report, "Stage 10 - Analytical Report", summary, next_step)
    return {"body": body, "entry": entry, "entry_id": not_available(report.get("timestamp"))}


def build_stage_11_document(report: dict[str, Any], project_root: Path) -> dict[str, str]:
    """Build Stage 11 notebook content."""
    json_path = report_path(project_root, "stage_11_report_package_report.json")
    markdown_path = report_path(project_root, "stage_11_report_package_report.md")
    next_step = stage_11_next_step(report)
    friction = report.get("friction", {})
    outputs = report.get("output_paths", {})

    summary = markdown_table(
        [
            ("Stage", "Stage 11 - Annotated report package"),
            ("Verdict", report.get("final_verdict")),
            ("Friction score", friction.get("score")),
            ("Friction level", friction.get("band")),
            ("Timestamp", report.get("timestamp")),
            ("Recommended next step", next_step),
        ]
    )
    input_table = markdown_table(
        [
            ("Package root", report.get("package_root")),
            ("Included artifacts", report.get("included_artifact_count")),
            ("Missing artifacts", report.get("missing_artifact_count")),
            ("Core report included", report.get("core_report_included")),
            ("Coaching summary included", report.get("coaching_summary_included")),
        ]
    )
    output_table = markdown_table(
        [
            ("JSON report path", json_path),
            ("Markdown report path", markdown_path),
            ("Log", latest_log_for_prefix(project_root, "stage_11_report_package_")),
            ("Package README", outputs.get("package_readme")),
            ("Package manifest", outputs.get("package_manifest")),
            ("Package index", outputs.get("package_index")),
            ("Analytical report", outputs.get("analytical_report")),
            ("Coaching summary", outputs.get("coaching_summary")),
        ]
    )
    console_table = markdown_table(
        [
            ("Included artifacts", report.get("included_artifact_count")),
            ("Missing artifacts", report.get("missing_artifact_count")),
            ("Visual artifacts", report.get("visual_artifacts_included_count")),
            ("Data artifacts", report.get("data_artifacts_included_count")),
            ("Verdict", report.get("final_verdict")),
            ("Friction", f"{not_available(friction.get('score'))} ({not_available(friction.get('band'))})"),
        ]
    )
    interpretation = (
        "Stage 11 packages the most useful outputs into a clean local deliverable. "
        "It organizes selected reports, visuals, data files, provenance, and limitations without creating new analysis."
    )
    body = stage_document(
        title="Stage 11 - Report Package",
        summary=summary,
        input_section=input_table,
        output_section=output_table,
        console_table=console_table,
        warnings=bullet_list(report.get("warnings"), "No warnings."),
        errors=bullet_list(report.get("errors"), "No errors."),
        interpretation=interpretation,
        next_step=next_step,
    )
    entry = history_entry(report, "Stage 11 - Report Package", summary, next_step)
    return {"body": body, "entry": entry, "entry_id": not_available(report.get("timestamp"))}


def build_stage_12_document(report: dict[str, Any], project_root: Path) -> dict[str, str]:
    """Build Stage 12 notebook content."""
    json_path = report_path(project_root, "stage_12_replay_schema_report.json")
    markdown_path = report_path(project_root, "stage_12_replay_schema_report.md")
    next_step = stage_12_next_step(report)
    friction = report.get("friction", {})
    outputs = report.get("output_paths", {})

    summary = markdown_table(
        [
            ("Stage", "Stage 12 - Synthetic rally replay data schema"),
            ("Verdict", report.get("final_verdict")),
            ("Schema version", report.get("schema_version")),
            ("Friction score", friction.get("score")),
            ("Friction level", friction.get("band")),
            ("Timestamp", report.get("timestamp")),
            ("Recommended next step", next_step),
        ]
    )
    input_table = markdown_table(
        [
            ("Stage 11 manifest", "outputs/report_packages/stage_11_report_package/package_manifest.json"),
            ("Stage 9.1 tactical zones", "outputs/tactical/stage_9_1_projection_coverage/tuned_ball_zone_assignments.csv"),
            ("Stage 8.1 validated timeline", "outputs/timeline/stage_8_1_timeline_validation/validated_event_timeline.csv"),
            ("Stage 7.1 main players", "outputs/player_tracking/stage_7_1_player_filtering/main_players.csv"),
            ("Stage 6 smoothed trajectory", "outputs/ball_tracking/stage_6_trajectory_smoothing/smoothed_trajectory.csv"),
            ("Stage 3 calibration report", "outputs/reports/stage_3_court_calibration_probe_report.json"),
        ]
    )
    output_table = markdown_table(
        [
            ("JSON report path", json_path),
            ("Markdown report path", markdown_path),
            ("Log", latest_log_for_prefix(project_root, "stage_12_replay_schema_")),
            ("Replay schema", outputs.get("replay_schema_json")),
            ("Pretty schema", outputs.get("replay_schema_pretty_md")),
            ("Replay keyframes", outputs.get("replay_keyframes_csv")),
            ("Replay events", outputs.get("replay_events_csv")),
            ("Replay players", outputs.get("replay_players_json")),
            ("Camera presets", outputs.get("replay_camera_presets_json")),
            ("Replay manifest", outputs.get("replay_manifest_json")),
        ]
    )
    console_table = markdown_table(
        [
            ("Replay keyframes", report.get("replay_keyframes_count")),
            ("Players", report.get("players_count")),
            ("Events", report.get("event_count")),
            ("Rally segments", report.get("rally_segments_count")),
            ("Camera presets", report.get("camera_presets_count")),
            ("Visual layers", report.get("visual_layers_count")),
            ("Confidence level", report.get("confidence_level")),
            ("Verdict", report.get("final_verdict")),
            ("Friction", f"{not_available(friction.get('score'))} ({not_available(friction.get('band'))})"),
        ]
    )
    interpretation = (
        "Stage 12 creates the structured replay data contract for future deterministic renderers. "
        "It does not generate video or synthetic images. It preserves possible_* event uncertainty, "
        "player identity limitations, and doubles-boundary court calibration context."
    )
    body = stage_document(
        title="Stage 12 - Synthetic Rally Replay Data Schema",
        summary=summary,
        input_section=input_table,
        output_section=output_table,
        console_table=console_table,
        warnings=bullet_list(report.get("warnings"), "No warnings."),
        errors=bullet_list(report.get("errors"), "No errors."),
        interpretation=interpretation,
        next_step=next_step,
    )
    entry = history_entry(report, "Stage 12 - Replay Schema", summary, next_step)
    return {"body": body, "entry": entry, "entry_id": not_available(report.get("timestamp"))}


def build_stage_13_document(report: dict[str, Any], project_root: Path) -> dict[str, str]:
    """Build Stage 13 notebook content."""
    json_path = report_path(project_root, "stage_13_2d_tactical_replay_report.json")
    markdown_path = report_path(project_root, "stage_13_2d_tactical_replay_report.md")
    next_step = stage_13_next_step(report)
    friction = report.get("friction", {})
    outputs = report.get("output_paths", {})

    summary = markdown_table(
        [
            ("Stage", "Stage 13 - 2D tactical replay renderer"),
            ("Verdict", report.get("final_verdict")),
            ("Schema version", report.get("schema_version")),
            ("Friction score", friction.get("score")),
            ("Friction level", friction.get("band")),
            ("Timestamp", report.get("timestamp")),
            ("Recommended next step", next_step),
        ]
    )
    input_table = markdown_table(
        [
            ("Replay schema", report.get("input_schema_path")),
            ("Keyframes", report.get("keyframes_count")),
            ("Players", report.get("players_count")),
            ("Events", report.get("events_count")),
            ("Renderer", "2d_tactical_replay"),
        ]
    )
    output_table = markdown_table(
        [
            ("JSON report path", json_path),
            ("Markdown report path", markdown_path),
            ("Log", latest_log_for_prefix(project_root, "stage_13_2d_tactical_replay_")),
            ("Frames", outputs.get("frames_dir")),
            ("Video", outputs.get("video_path")),
            ("Contact sheet", outputs.get("contact_sheet_path")),
            ("Final frame", outputs.get("final_frame_path")),
            ("Manifest", outputs.get("renderer_manifest_path")),
            ("Replay summary", outputs.get("replay_summary_path")),
        ]
    )
    console_table = markdown_table(
        [
            ("Frames generated", report.get("frames_generated")),
            ("Video generated", report.get("video_generated")),
            ("Keyframes", report.get("keyframes_count")),
            ("Players", report.get("players_count")),
            ("Events", report.get("events_count")),
            ("Verdict", report.get("final_verdict")),
            ("Friction", f"{not_available(friction.get('score'))} ({not_available(friction.get('band'))})"),
        ]
    )
    interpretation = (
        "Stage 13 is the first generated visual replay from analysis data. "
        "It renders a deterministic 2D tactical court, ball trajectory, players, event markers, and timeline strip. "
        "It is not photorealistic video, broadcast reconstruction, or official line/scoring analysis."
    )
    body = stage_document(
        title="Stage 13 - 2D Tactical Replay Renderer",
        summary=summary,
        input_section=input_table,
        output_section=output_table,
        console_table=console_table,
        warnings=bullet_list(report.get("warnings"), "No warnings."),
        errors=bullet_list(report.get("errors"), "No errors."),
        interpretation=interpretation,
        next_step=next_step,
    )
    entry = history_entry(report, "Stage 13 - 2D Tactical Replay", summary, next_step)
    return {"body": body, "entry": entry, "entry_id": not_available(report.get("timestamp"))}


def build_stage_14_document(report: dict[str, Any], project_root: Path) -> dict[str, str]:
    """Build Stage 14 notebook content."""
    json_path = report_path(project_root, "stage_14_side_view_replay_report.json")
    markdown_path = report_path(project_root, "stage_14_side_view_replay_report.md")
    next_step = stage_14_next_step(report)
    friction = report.get("friction", {})
    outputs = report.get("output_paths", {})

    summary = markdown_table(
        [
            ("Stage", "Stage 14 - Side-view ball flight renderer"),
            ("Verdict", report.get("final_verdict")),
            ("Schema version", report.get("schema_version")),
            ("Friction score", friction.get("score")),
            ("Friction level", friction.get("band")),
            ("Timestamp", report.get("timestamp")),
            ("Recommended next step", next_step),
        ]
    )
    input_table = markdown_table(
        [
            ("Replay schema", report.get("input_schema_path")),
            ("Keyframes", report.get("keyframes_count")),
            ("Side-view keyframes", report.get("side_view_keyframes_count")),
            ("Events", report.get("events_count")),
            ("Synthetic height enabled", report.get("synthetic_height_enabled")),
            ("True height available", report.get("true_height_available")),
        ]
    )
    output_table = markdown_table(
        [
            ("JSON report path", json_path),
            ("Markdown report path", markdown_path),
            ("Log", latest_log_for_prefix(project_root, "stage_14_side_view_replay_")),
            ("Frames", outputs.get("frames_dir")),
            ("Video", outputs.get("video_path")),
            ("Contact sheet", outputs.get("contact_sheet_path")),
            ("Final frame", outputs.get("final_frame_path")),
            ("Arc preview", outputs.get("arc_preview_path")),
            ("Manifest", outputs.get("manifest_path")),
            ("Summary", outputs.get("summary_path")),
        ]
    )
    console_table = markdown_table(
        [
            ("Frames generated", report.get("frames_generated")),
            ("Video generated", report.get("video_generated")),
            ("Keyframes", report.get("keyframes_count")),
            ("Side-view keyframes", report.get("side_view_keyframes_count")),
            ("Events", report.get("events_count")),
            ("Synthetic height", report.get("synthetic_height_enabled")),
            ("True height", report.get("true_height_available")),
            ("Verdict", report.get("final_verdict")),
            ("Friction", f"{not_available(friction.get('score'))} ({not_available(friction.get('band'))})"),
        ]
    )
    interpretation = (
        "Stage 14 renders a deterministic side-view analytical replay from the Stage 12 schema. "
        "The height profile is synthetic and estimated for visualization only; it is not measured 3D ball height."
    )
    body = stage_document(
        title="Stage 14 - Side-View Ball Flight Renderer",
        summary=summary,
        input_section=input_table,
        output_section=output_table,
        console_table=console_table,
        warnings=bullet_list(report.get("warnings"), "No warnings."),
        errors=bullet_list(report.get("errors"), "No errors."),
        interpretation=interpretation,
        next_step=next_step,
    )
    entry = history_entry(report, "Stage 14 - Side-View Replay", summary, next_step)
    return {"body": body, "entry": entry, "entry_id": not_available(report.get("timestamp"))}


def build_stage_14_1_document(report: dict[str, Any], project_root: Path) -> dict[str, str]:
    """Build Stage 14.1 notebook content."""
    json_path = report_path(project_root, "stage_14_1_side_view_patch_report.json")
    markdown_path = report_path(project_root, "stage_14_1_side_view_patch_report.md")
    next_step = stage_14_1_next_step(report)
    friction = report.get("friction", {})
    outputs = report.get("output_paths", {})

    summary = markdown_table(
        [
            ("Stage", "Stage 14.1 - Side-view height semantics patch"),
            ("Verdict", report.get("final_verdict")),
            ("Patch applied", report.get("semantic_height_patch_applied")),
            ("Friction score", friction.get("score")),
            ("Friction level", friction.get("band")),
            ("Timestamp", report.get("timestamp")),
            ("Recommended next step", next_step),
        ]
    )
    input_table = markdown_table(
        [
            ("Source stage", report.get("source_stage")),
            ("Bounce grounding", report.get("bounce_grounding_enabled")),
            ("Hit contact band", report.get("hit_contact_band_enabled")),
            ("Interpolated points marked", report.get("interpolated_points_marked")),
            ("Height anchor summary", report.get("height_anchor_summary")),
        ]
    )
    output_table = markdown_table(
        [
            ("JSON report path", json_path),
            ("Markdown report path", markdown_path),
            ("Semantic debug", report.get("semantic_debug_artifact")),
            ("Video", outputs.get("video_path")),
            ("Contact sheet", outputs.get("contact_sheet_path")),
            ("Final frame", outputs.get("final_frame_path")),
            ("Arc preview", outputs.get("arc_preview_path")),
            ("Manifest", outputs.get("manifest_path")),
        ]
    )
    console_table = markdown_table(
        [
            ("Frames generated", report.get("frames_generated")),
            ("Video generated", report.get("video_generated")),
            ("Semantic patch applied", report.get("semantic_height_patch_applied")),
            ("Bounce grounding", report.get("bounce_grounding_enabled")),
            ("Hit contact band", report.get("hit_contact_band_enabled")),
            ("Interpolated points marked", report.get("interpolated_points_marked")),
            ("Verdict", report.get("final_verdict")),
            ("Friction", f"{not_available(friction.get('score'))} ({not_available(friction.get('band'))})"),
        ]
    )
    interpretation = (
        "Stage 14.1 improves the side-view semantics. Bounce-like events are forced near the court surface, "
        "hit-like events use a plausible synthetic contact band, and interpolated points remain visibly synthetic. "
        "The renderer still does not claim measured 3D ball height."
    )
    body = stage_document(
        title="Stage 14.1 - Side-View Height Semantics Patch",
        summary=summary,
        input_section=input_table,
        output_section=output_table,
        console_table=console_table,
        warnings=bullet_list(report.get("warnings"), "No warnings."),
        errors=bullet_list(report.get("errors"), "No errors."),
        interpretation=interpretation,
        next_step=next_step,
    )
    entry = history_entry(report, "Stage 14.1 - Side-View Patch", summary, next_step)
    return {"body": body, "entry": entry, "entry_id": not_available(report.get("timestamp"))}


def build_stage_14_2_document(report: dict[str, Any], project_root: Path) -> dict[str, str]:
    """Build Stage 14.2 notebook content."""
    json_path = report_path(project_root, "stage_14_2_side_view_event_disambiguation_report.json")
    markdown_path = report_path(project_root, "stage_14_2_side_view_event_disambiguation_report.md")
    next_step = stage_14_2_next_step(report)
    friction = report.get("friction", {})
    outputs = report.get("output_paths", {})

    summary = markdown_table(
        [
            ("Stage", "Stage 14.2 - Side-view event disambiguation"),
            ("Verdict", report.get("final_verdict")),
            ("Patch applied", report.get("event_disambiguation_patch_applied")),
            ("Friction score", friction.get("score")),
            ("Friction level", friction.get("band")),
            ("Timestamp", report.get("timestamp")),
            ("Recommended next step", next_step),
        ]
    )
    input_table = markdown_table(
        [
            ("Source stage", report.get("source_stage")),
            ("Player-aware hit validation", report.get("player_aware_hit_validation_enabled")),
            ("Event render roles", report.get("event_render_roles_enabled")),
            ("Implausible hits downgraded", report.get("implausible_hits_downgraded_count")),
            ("Plausible hits", report.get("plausible_hits_count")),
            ("Plausible bounces", report.get("plausible_bounces_count")),
            ("Uncertain events", report.get("uncertain_events_count")),
        ]
    )
    output_table = markdown_table(
        [
            ("JSON report path", json_path),
            ("Markdown report path", markdown_path),
            ("Semantic debug", report.get("semantic_debug_artifact")),
            ("Video", outputs.get("video_path")),
            ("Contact sheet", outputs.get("contact_sheet_path")),
            ("Final frame", outputs.get("final_frame_path")),
            ("Arc preview", outputs.get("arc_preview_path")),
            ("Manifest", outputs.get("manifest_path")),
        ]
    )
    console_table = markdown_table(
        [
            ("Frames generated", report.get("frames_generated")),
            ("Video generated", report.get("video_generated")),
            ("Player-aware hit validation", report.get("player_aware_hit_validation_enabled")),
            ("Event render roles", report.get("event_render_roles_enabled")),
            ("Implausible hits downgraded", report.get("implausible_hits_downgraded_count")),
            ("Verdict", report.get("final_verdict")),
            ("Friction", f"{not_available(friction.get('score'))} ({not_available(friction.get('band'))})"),
        ]
    )
    interpretation = (
        "Stage 14.2 improves side-view event meaning. Raw possible_hit labels are filtered against player "
        "depth and position before they are rendered as hits. Implausible hit labels become uncertain events, "
        "while bounces remain grounded and ball-near-player cues stay separate from hit and bounce markers."
    )
    body = stage_document(
        title="Stage 14.2 - Side-View Event Disambiguation",
        summary=summary,
        input_section=input_table,
        output_section=output_table,
        console_table=console_table,
        warnings=bullet_list(report.get("warnings"), "No warnings."),
        errors=bullet_list(report.get("errors"), "No errors."),
        interpretation=interpretation,
        next_step=next_step,
    )
    entry = history_entry(report, "Stage 14.2 - Side-View Event Disambiguation", summary, next_step)
    return {"body": body, "entry": entry, "entry_id": not_available(report.get("timestamp"))}


def build_stage_14_3_document(report: dict[str, Any], project_root: Path) -> dict[str, str]:
    """Build Stage 14.3 notebook content."""
    json_path = report_path(project_root, "stage_14_3_validated_events_side_view_report.json")
    markdown_path = report_path(project_root, "stage_14_3_validated_events_side_view_report.md")
    next_step = stage_14_3_next_step(report)
    friction = report.get("friction", {})
    outputs = report.get("output_paths", {})

    summary = markdown_table(
        [
            ("Stage", "Stage 14.3 - Side-view replay with validated events"),
            ("Verdict", report.get("final_verdict")),
            ("Friction score", friction.get("score")),
            ("Friction level", friction.get("band")),
            ("Event source used", report.get("event_source_used")),
            ("Stage 8.3 available", report.get("validated_event_source_available")),
            ("Timestamp", report.get("timestamp")),
            ("Recommended next step", next_step),
        ]
    )
    input_table = markdown_table(
        [
            ("Source path", report.get("event_source_path")),
            ("Fallback used", report.get("fallback_used")),
            ("Validated bounces rendered", report.get("validated_bounces_rendered_count")),
            ("Validated hits rendered", report.get("validated_hits_rendered_count")),
            ("Downgraded hit annotations", report.get("downgraded_hits_annotation_count")),
            ("Rejected events ignored", report.get("rejected_events_ignored_count")),
            ("Unvalidated annotations", report.get("unvalidated_events_annotation_count")),
        ]
    )
    output_table = markdown_table(
        [
            ("JSON report path", json_path),
            ("Markdown report path", markdown_path),
            ("Validated events debug", report.get("validated_events_debug_path")),
            ("Video", outputs.get("video_path")),
            ("Frames", outputs.get("frames_dir")),
            ("Manifest", outputs.get("manifest_path")),
        ]
    )
    console_table = markdown_table(
        [
            ("Frames generated", report.get("frames_generated")),
            ("Video generated", report.get("video_generated")),
            ("Main path physical-only", report.get("main_path_physical_events_only")),
            ("Annotation band enabled", report.get("annotation_band_enabled")),
            ("Verdict", report.get("final_verdict")),
            ("Friction", f"{not_available(friction.get('score'))} ({not_available(friction.get('band'))})"),
        ]
    )
    interpretation = (
        "Stage 14.3 makes the side-view renderer consume the Stage 8.3 validated event timeline first. "
        "Validated bounces are physical grounded markers. Raw, downgraded, unvalidated, or rejected hit hypotheses "
        "are rendered only as secondary annotations, so the replay no longer presents unconfirmed hits as contacts."
    )
    body = stage_document(
        title="Stage 14.3 - Side-View Replay with Validated Events",
        summary=summary,
        input_section=input_table,
        output_section=output_table,
        console_table=console_table,
        warnings=bullet_list(report.get("warnings"), "No warnings."),
        errors=bullet_list(report.get("errors"), "No errors."),
        interpretation=interpretation,
        next_step=next_step,
    )
    entry = history_entry(report, "Stage 14.3 - Side-View Replay with Validated Events", summary, next_step)
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
    history_note = (
        "Older entries are preserved as originally written. "
        "Some historical entries may use legacy Markdown tables so prior run evidence is not erased."
    )
    text = (
        body.rstrip()
        + "\n\n## Run history\n\n"
        + history_note
        + "\n\n"
        + "\n\n".join(item for item in entries if item).rstrip()
        + "\n"
    )
    path.write_text(text, encoding="utf-8")
    return path


def build_experiment_index(stage_summaries: list[dict[str, str]]) -> str:
    """Build the experiment index Markdown file in a plain-text-friendly format."""
    lines = [
        "# Experiment Index",
        "",
        "This index is designed to be readable in plain text.",
        "Each stage is listed as a short block instead of a wide Markdown table.",
        "",
    ]
    for summary in stage_summaries:
        lines.extend(
            [
                f"STAGE: {summary['stage']}",
                f"NAME: {summary['name']}",
                f"VERDICT: {summary['verdict']}",
                f"FRICTION: {summary['friction']}",
                f"MAIN OUTPUT: {summary['main_output']}",
                f"NEXT STEP: {summary['next_step']}",
                "",
                "---",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def build_lab_readme() -> str:
    """Build lab notebook README content."""
    return """# Lab Notebook

This folder is the persistent project lab notebook for Tennis AI Vision.

The notebook records technical friction, inputs, outputs, decisions, warnings, errors, and validation results for each stage. This matters because the project is not only building a local tennis video analysis pipeline; it is also learning where the local workflow succeeds, where it struggles, and what should happen next.

The notebook is plain-text friendly. Stage summaries use short field blocks instead of wide Markdown tables so they can be read in VS Code, Notepad, terminal previews, or raw GitHub view.

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

    stage_8_report = read_json_report(report_path(project_root, "stage_8_event_timeline_report.json"))
    if stage_8_report is not None:
        document = build_stage_8_document(stage_8_report, project_root)
        stage_path = notebook_dir / "stage_8_event_timeline.md"
        written.append(write_stage_notebook(stage_path, document["body"], document["entry"], document["entry_id"]))
        stage_summaries.append(
            {
                "stage": "Stage 8",
                "name": "Event Timeline",
                "verdict": not_available(stage_8_report.get("final_verdict")),
                "friction": f"{not_available(nested_get(stage_8_report, ('friction', 'score')))} {not_available(nested_get(stage_8_report, ('friction', 'band')))}",
                "main_output": "outputs/reports/stage_8_event_timeline_report.md",
                "next_step": stage_8_next_step(stage_8_report),
            }
        )

    stage_8_1_report = read_json_report(report_path(project_root, "stage_8_1_timeline_validation_report.json"))
    if stage_8_1_report is not None:
        document = build_stage_8_1_document(stage_8_1_report, project_root)
        stage_path = notebook_dir / "stage_8_1_timeline_validation.md"
        written.append(write_stage_notebook(stage_path, document["body"], document["entry"], document["entry_id"]))
        stage_summaries.append(
            {
                "stage": "Stage 8.1",
                "name": "Timeline Validation",
                "verdict": not_available(stage_8_1_report.get("final_verdict")),
                "friction": f"{not_available(nested_get(stage_8_1_report, ('friction', 'score')))} {not_available(nested_get(stage_8_1_report, ('friction', 'band')))}",
                "main_output": "outputs/reports/stage_8_1_timeline_validation_report.md",
                "next_step": stage_8_1_next_step(stage_8_1_report),
            }
        )

    stage_8_2_report = read_json_report(report_path(project_root, "stage_8_2_event_labeling_report.json"))
    if stage_8_2_report is not None:
        document = build_stage_8_2_document(stage_8_2_report, project_root)
        stage_path = notebook_dir / "stage_8_2_event_labeling.md"
        written.append(write_stage_notebook(stage_path, document["body"], document["entry"], document["entry_id"]))
        stage_summaries.append(
            {
                "stage": "Stage 8.2",
                "name": "Manual Event Labeling",
                "verdict": not_available(stage_8_2_report.get("final_verdict")),
                "friction": f"{not_available(nested_get(stage_8_2_report, ('friction', 'score')))} {not_available(nested_get(stage_8_2_report, ('friction', 'band')))}",
                "main_output": "outputs/reports/stage_8_2_event_labeling_report.md",
                "next_step": stage_8_2_next_step(stage_8_2_report),
            }
        )

    stage_8_3_report = read_json_report(report_path(project_root, "stage_8_3_event_validation_report.json"))
    if stage_8_3_report is not None:
        document = build_stage_8_3_document(stage_8_3_report, project_root)
        stage_path = notebook_dir / "stage_8_3_event_validation.md"
        written.append(write_stage_notebook(stage_path, document["body"], document["entry"], document["entry_id"]))
        stage_summaries.append(
            {
                "stage": "Stage 8.3",
                "name": "Event Validation",
                "verdict": not_available(stage_8_3_report.get("final_verdict")),
                "friction": f"{not_available(nested_get(stage_8_3_report, ('friction', 'score')))} {not_available(nested_get(stage_8_3_report, ('friction', 'band')))}",
                "main_output": "outputs/timeline/stage_8_3_event_validation/validated_event_timeline.csv",
                "next_step": stage_8_3_next_step(stage_8_3_report),
            }
        )

    stage_9_report = read_json_report(report_path(project_root, "stage_9_tactical_metrics_report.json"))
    if stage_9_report is not None:
        document = build_stage_9_document(stage_9_report, project_root)
        stage_path = notebook_dir / "stage_9_tactical_metrics.md"
        written.append(write_stage_notebook(stage_path, document["body"], document["entry"], document["entry_id"]))
        stage_summaries.append(
            {
                "stage": "Stage 9",
                "name": "Tactical Metrics",
                "verdict": not_available(stage_9_report.get("final_verdict")),
                "friction": f"{not_available(nested_get(stage_9_report, ('friction', 'score')))} {not_available(nested_get(stage_9_report, ('friction', 'band')))}",
                "main_output": "outputs/reports/stage_9_tactical_metrics_report.md",
                "next_step": stage_9_next_step(stage_9_report),
            }
        )

    stage_9_1_report = read_json_report(report_path(project_root, "stage_9_1_projection_coverage_report.json"))
    if stage_9_1_report is not None:
        document = build_stage_9_1_document(stage_9_1_report, project_root)
        stage_path = notebook_dir / "stage_9_1_projection_coverage.md"
        written.append(write_stage_notebook(stage_path, document["body"], document["entry"], document["entry_id"]))
        stage_summaries.append(
            {
                "stage": "Stage 9.1",
                "name": "Projection Coverage",
                "verdict": not_available(stage_9_1_report.get("final_verdict")),
                "friction": f"{not_available(nested_get(stage_9_1_report, ('friction', 'score')))} {not_available(nested_get(stage_9_1_report, ('friction', 'band')))}",
                "main_output": "outputs/reports/stage_9_1_projection_coverage_report.md",
                "next_step": stage_9_1_next_step(stage_9_1_report),
            }
        )

    stage_10_report = read_json_report(report_path(project_root, "stage_10_analytical_report_report.json"))
    if stage_10_report is not None:
        document = build_stage_10_document(stage_10_report, project_root)
        stage_path = notebook_dir / "stage_10_analytical_report.md"
        written.append(write_stage_notebook(stage_path, document["body"], document["entry"], document["entry_id"]))
        stage_summaries.append(
            {
                "stage": "Stage 10",
                "name": "Analytical Report",
                "verdict": not_available(stage_10_report.get("final_verdict")),
                "friction": f"{not_available(nested_get(stage_10_report, ('friction', 'score')))} {not_available(nested_get(stage_10_report, ('friction', 'band')))}",
                "main_output": "outputs/reports_final/stage_10_analytical_report/analytical_report.md",
                "next_step": stage_10_next_step(stage_10_report),
            }
        )

    stage_11_report = read_json_report(report_path(project_root, "stage_11_report_package_report.json"))
    if stage_11_report is not None:
        document = build_stage_11_document(stage_11_report, project_root)
        stage_path = notebook_dir / "stage_11_report_package.md"
        written.append(write_stage_notebook(stage_path, document["body"], document["entry"], document["entry_id"]))
        stage_summaries.append(
            {
                "stage": "Stage 11",
                "name": "Report Package",
                "verdict": not_available(stage_11_report.get("final_verdict")),
                "friction": f"{not_available(nested_get(stage_11_report, ('friction', 'score')))} {not_available(nested_get(stage_11_report, ('friction', 'band')))}",
                "main_output": "outputs/report_packages/stage_11_report_package/README.md",
                "next_step": stage_11_next_step(stage_11_report),
            }
        )

    stage_12_report = read_json_report(report_path(project_root, "stage_12_replay_schema_report.json"))
    if stage_12_report is not None:
        document = build_stage_12_document(stage_12_report, project_root)
        stage_path = notebook_dir / "stage_12_replay_schema.md"
        written.append(write_stage_notebook(stage_path, document["body"], document["entry"], document["entry_id"]))
        stage_summaries.append(
            {
                "stage": "Stage 12",
                "name": "Replay Schema",
                "verdict": not_available(stage_12_report.get("final_verdict")),
                "friction": f"{not_available(nested_get(stage_12_report, ('friction', 'score')))} {not_available(nested_get(stage_12_report, ('friction', 'band')))}",
                "main_output": "outputs/replay/stage_12_replay_schema/replay_schema.json",
                "next_step": stage_12_next_step(stage_12_report),
            }
        )

    stage_13_report = read_json_report(report_path(project_root, "stage_13_2d_tactical_replay_report.json"))
    if stage_13_report is not None:
        document = build_stage_13_document(stage_13_report, project_root)
        stage_path = notebook_dir / "stage_13_2d_tactical_replay.md"
        written.append(write_stage_notebook(stage_path, document["body"], document["entry"], document["entry_id"]))
        stage_summaries.append(
            {
                "stage": "Stage 13",
                "name": "2D Tactical Replay",
                "verdict": not_available(stage_13_report.get("final_verdict")),
                "friction": f"{not_available(nested_get(stage_13_report, ('friction', 'score')))} {not_available(nested_get(stage_13_report, ('friction', 'band')))}",
                "main_output": "outputs/replay/stage_13_2d_tactical_replay/tactical_replay_contact_sheet.jpg",
                "next_step": stage_13_next_step(stage_13_report),
            }
        )

    stage_14_report = read_json_report(report_path(project_root, "stage_14_side_view_replay_report.json"))
    if stage_14_report is not None:
        document = build_stage_14_document(stage_14_report, project_root)
        stage_path = notebook_dir / "stage_14_side_view_replay.md"
        written.append(write_stage_notebook(stage_path, document["body"], document["entry"], document["entry_id"]))
        stage_summaries.append(
            {
                "stage": "Stage 14",
                "name": "Side-View Replay",
                "verdict": not_available(stage_14_report.get("final_verdict")),
                "friction": f"{not_available(nested_get(stage_14_report, ('friction', 'score')))} {not_available(nested_get(stage_14_report, ('friction', 'band')))}",
                "main_output": "outputs/replay/stage_14_side_view_replay/side_view_arc_preview.jpg",
                "next_step": stage_14_next_step(stage_14_report),
            }
        )

    stage_14_1_report = read_json_report(report_path(project_root, "stage_14_1_side_view_patch_report.json"))
    if stage_14_1_report is not None:
        document = build_stage_14_1_document(stage_14_1_report, project_root)
        stage_path = notebook_dir / "stage_14_1_side_view_patch.md"
        written.append(write_stage_notebook(stage_path, document["body"], document["entry"], document["entry_id"]))
        stage_summaries.append(
            {
                "stage": "Stage 14.1",
                "name": "Side-View Patch",
                "verdict": not_available(stage_14_1_report.get("final_verdict")),
                "friction": f"{not_available(nested_get(stage_14_1_report, ('friction', 'score')))} {not_available(nested_get(stage_14_1_report, ('friction', 'band')))}",
                "main_output": "outputs/replay/stage_14_side_view_replay/side_view_semantic_debug.jpg",
                "next_step": stage_14_1_next_step(stage_14_1_report),
            }
        )

    stage_14_2_report = read_json_report(report_path(project_root, "stage_14_2_side_view_event_disambiguation_report.json"))
    if stage_14_2_report is not None:
        document = build_stage_14_2_document(stage_14_2_report, project_root)
        stage_path = notebook_dir / "stage_14_2_side_view_event_disambiguation.md"
        written.append(write_stage_notebook(stage_path, document["body"], document["entry"], document["entry_id"]))
        stage_summaries.append(
            {
                "stage": "Stage 14.2",
                "name": "Side-View Event Disambiguation",
                "verdict": not_available(stage_14_2_report.get("final_verdict")),
                "friction": f"{not_available(nested_get(stage_14_2_report, ('friction', 'score')))} {not_available(nested_get(stage_14_2_report, ('friction', 'band')))}",
                "main_output": "outputs/replay/stage_14_side_view_replay/side_view_semantic_debug.jpg",
                "next_step": stage_14_2_next_step(stage_14_2_report),
            }
        )

    stage_14_3_report = read_json_report(report_path(project_root, "stage_14_3_validated_events_side_view_report.json"))
    if stage_14_3_report is not None:
        document = build_stage_14_3_document(stage_14_3_report, project_root)
        stage_path = notebook_dir / "stage_14_3_validated_events_side_view.md"
        written.append(write_stage_notebook(stage_path, document["body"], document["entry"], document["entry_id"]))
        stage_summaries.append(
            {
                "stage": "Stage 14.3",
                "name": "Side-View Validated Events",
                "verdict": not_available(stage_14_3_report.get("final_verdict")),
                "friction": f"{not_available(nested_get(stage_14_3_report, ('friction', 'score')))} {not_available(nested_get(stage_14_3_report, ('friction', 'band')))}",
                "main_output": "outputs/replay/stage_14_side_view_replay/side_view_validated_events_debug.jpg",
                "next_step": stage_14_3_next_step(stage_14_3_report),
            }
        )

    index_path = notebook_dir / "experiment_index.md"
    index_path.write_text(build_experiment_index(stage_summaries), encoding="utf-8")
    written.append(index_path)

    readme_path = notebook_dir / "README.md"
    readme_path.write_text(build_lab_readme(), encoding="utf-8")
    written.append(readme_path)

    return written
