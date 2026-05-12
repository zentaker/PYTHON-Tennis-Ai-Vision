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

    index_path = notebook_dir / "experiment_index.md"
    index_path.write_text(build_experiment_index(stage_summaries), encoding="utf-8")
    written.append(index_path)

    readme_path = notebook_dir / "README.md"
    readme_path.write_text(build_lab_readme(), encoding="utf-8")
    written.append(readme_path)

    return written
