"""Generate a plain-text-friendly technical function inventory."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "docs" / "technical" / "function_inventory.md"


FUNCTIONS: list[dict[str, Any]] = [
    {
        "area": "Stage 0 - Environment",
        "file": "src/tennis_vision/environment.py",
        "function": "run_environment_checks",
        "purpose": "Runs the complete local environment check for Python, folders, imports, and ffmpeg.",
        "inputs": ["project root path"],
        "outputs": ["environment status dictionary"],
        "called_by": ["scripts/doctor.py"],
        "why": "This tells the Product Owner whether local development can continue before video analysis stages run.",
        "notes": "ffmpeg missing is recorded as warning unless a later stage needs it.",
    },
    {
        "area": "Stage 0 - Environment",
        "file": "src/tennis_vision/environment.py",
        "function": "check_required_packages",
        "purpose": "Checks whether required Python packages can be imported.",
        "inputs": ["package name list"],
        "outputs": ["package import status"],
        "called_by": ["run_environment_checks"],
        "why": "Missing packages are common setup friction and should be visible immediately.",
    },
    {
        "area": "Stage 0 - Environment",
        "file": "src/tennis_vision/environment.py",
        "function": "check_ffmpeg",
        "purpose": "Checks whether ffmpeg is available from the shell.",
        "inputs": ["none"],
        "outputs": ["ffmpeg availability and path/status"],
        "called_by": ["run_environment_checks"],
        "why": "Video work may eventually need ffmpeg, but Stage 1 proved MOV reading can work through OpenCV.",
    },
    {
        "area": "Reports",
        "file": "src/tennis_vision/report.py",
        "function": "write_json_report",
        "purpose": "Writes a machine-readable JSON report.",
        "inputs": ["report path", "report dictionary"],
        "outputs": ["JSON report file"],
        "called_by": ["stage scripts"],
        "why": "Reports are the durable evidence layer for every experiment.",
    },
    {
        "area": "Reports",
        "file": "src/tennis_vision/report.py",
        "function": "write_markdown_report",
        "purpose": "Writes a human-readable Markdown report.",
        "inputs": ["report path", "title", "sections"],
        "outputs": ["Markdown report file"],
        "called_by": ["stage scripts"],
        "why": "The Product Owner can inspect results without parsing JSON.",
    },
    {
        "area": "Friction",
        "file": "src/tennis_vision/friction.py",
        "function": "friction_band",
        "purpose": "Converts a numeric friction score into low, medium, high, or blocking.",
        "inputs": ["score from 0 to 100"],
        "outputs": ["friction band text"],
        "called_by": ["all friction scoring helpers"],
        "why": "Keeps operational risk readable across stages.",
    },
    *[
        {
            "area": "Friction",
            "file": "src/tennis_vision/friction.py",
            "function": name,
            "purpose": f"Calculates friction for {label}.",
            "inputs": ["stage-specific warning/error/input flags"],
            "outputs": ["friction score dictionary"],
            "called_by": [script],
            "why": "Prevents failures and uncertainty from being hidden.",
        }
        for name, label, script in [
            ("calculate_stage_1_friction_score", "Stage 1 video loading", "scripts/run_stage_1_video_probe.py"),
            ("calculate_stage_2_friction_score", "Stage 2 YOLO CPU inference", "scripts/run_stage_2_yolo_cpu_baseline.py"),
            ("calculate_stage_3_friction_score", "Stage 3 court calibration", "scripts/run_stage_3_court_calibration_probe.py"),
            ("calculate_stage_4_friction_score", "Stage 4 ball candidate probing", "scripts/run_stage_4_ball_tracking_probe.py"),
            ("calculate_stage_5_friction_score", "Stage 5 candidate filtering", "scripts/run_stage_5_ball_candidate_filtering.py"),
            ("calculate_stage_6_friction_score", "Stage 6 trajectory smoothing", "scripts/run_stage_6_trajectory_smoothing.py"),
            ("calculate_stage_7_friction_score", "Stage 7 player interaction", "scripts/run_stage_7_player_interaction_probe.py"),
            ("calculate_stage_8_friction_score", "Stage 8 event timeline", "scripts/run_stage_8_event_timeline.py"),
            ("calculate_stage_8_1_friction_score", "Stage 8.1 timeline validation", "scripts/run_stage_8_1_expand_labels.py"),
        ]
    ],
    {
        "area": "Stage 1 - Video IO",
        "file": "src/tennis_vision/video_io.py",
        "function": "read_video_metadata",
        "purpose": "Reads file size, frame count, FPS, duration, resolution, and codec metadata.",
        "inputs": ["video path"],
        "outputs": ["metadata dictionary"],
        "called_by": ["scripts/run_stage_1_video_probe.py"],
        "why": "Confirms that the local sample video is readable before later analysis stages.",
    },
    {
        "area": "Stage 1 - Video IO",
        "file": "src/tennis_vision/frame_sampler.py",
        "function": "extract_frames",
        "purpose": "Extracts JPG frames from a video at a fixed interval.",
        "inputs": ["video path", "output folder", "interval", "max frames"],
        "outputs": ["saved frames and extraction statistics"],
        "called_by": ["scripts/run_stage_1_video_probe.py"],
        "why": "Frame extraction is the first concrete video-processing capability.",
    },
    {
        "area": "Stage 2 - YOLO CPU",
        "file": "src/tennis_vision/yolo_cpu.py",
        "function": "load_yolo_model",
        "purpose": "Loads a small YOLO model for local CPU inference.",
        "inputs": ["model name"],
        "outputs": ["YOLO model or load error"],
        "called_by": ["scripts/run_stage_2_yolo_cpu_baseline.py"],
        "why": "Validates whether object detection can run locally without cloud or GPU assumptions.",
    },
    {
        "area": "Stage 2 - YOLO CPU",
        "file": "src/tennis_vision/yolo_cpu.py",
        "function": "run_yolo_cpu_baseline",
        "purpose": "Runs limited YOLO CPU inference and saves annotated frames.",
        "inputs": ["video", "model", "interval", "max frames", "resize width", "confidence"],
        "outputs": ["annotated images and detection summary"],
        "called_by": ["scripts/run_stage_2_yolo_cpu_baseline.py"],
        "why": "Proves the local object detection pipeline is technically possible.",
    },
    {
        "area": "Stage 3 - Court Calibration",
        "file": "src/tennis_vision/court_calibration.py",
        "function": "validate_corner_geometry",
        "purpose": "Checks point order and crossed court polygon geometry.",
        "inputs": ["manual court corner points"],
        "outputs": ["geometry validation status"],
        "called_by": ["validate_points"],
        "why": "Prevents inverted court points from creating a false homography.",
    },
    {
        "area": "Stage 3 - Court Calibration",
        "file": "src/tennis_vision/court_calibration.py",
        "function": "compute_homography",
        "purpose": "Computes the image-to-normalized-court homography from valid corner points.",
        "inputs": ["validated court points"],
        "outputs": ["homography matrix/status"],
        "called_by": ["run_court_calibration_probe"],
        "why": "This is the bridge from video pixels to court-space reasoning.",
    },
    {
        "area": "Stage 3.1 - Court Point Selection",
        "file": "src/tennis_vision/court_point_selector.py",
        "function": "generate_coordinate_grid",
        "purpose": "Draws coordinate grid labels on the calibration reference frame.",
        "inputs": ["reference image", "grid step"],
        "outputs": ["grid image"],
        "called_by": ["scripts/run_stage_3_1_court_point_selector.py"],
        "why": "The user can estimate or verify court point coordinates without a frontend.",
    },
    {
        "area": "Stage 4 - Ball Candidate Probe",
        "file": "src/tennis_vision/ball_tracking_probe.py",
        "function": "detect_ball_candidates",
        "purpose": "Finds yellow/green blob candidates using OpenCV heuristics.",
        "inputs": ["frame", "frame index"],
        "outputs": ["candidate list"],
        "called_by": ["run_ball_tracking_probe"],
        "why": "This showed the first local ball-detection approach produced many false positives.",
    },
    {
        "area": "Stage 4.1 - Manual Ball Labeling",
        "file": "src/tennis_vision/ball_labeling.py",
        "function": "label_frames_interactively",
        "purpose": "Opens OpenCV windows so the user can click the real ball.",
        "inputs": ["video", "frame indices", "output dir", "resize width"],
        "outputs": ["manual labels and overlays"],
        "called_by": ["scripts/run_stage_4_1_ball_labeling_helper.py", "scripts/run_stage_8_1_expand_labels.py"],
        "why": "Manual labels create ground truth when automatic detection is noisy.",
    },
    {
        "area": "Stage 5 - Candidate Filtering and Court Projection",
        "file": "src/tennis_vision/ball_candidate_filtering.py",
        "function": "compare_candidates_to_labels",
        "purpose": "Ranks automatic candidates by distance to manual labels.",
        "inputs": ["candidate rows", "manual labels"],
        "outputs": ["distance rows and summary"],
        "called_by": ["scripts/run_stage_5_ball_candidate_filtering.py"],
        "why": "Quantifies whether automatic candidates are actually near the real ball.",
    },
    {
        "area": "Stage 5 - Candidate Filtering and Court Projection",
        "file": "src/tennis_vision/court_projection.py",
        "function": "project_image_points",
        "purpose": "Projects image-space points into normalized court coordinates.",
        "inputs": ["point rows", "homography matrix"],
        "outputs": ["projected point rows"],
        "called_by": ["Stage 5 and Stage 5.1 scripts"],
        "why": "Court-space projection is required for SwingVision-style spatial analysis.",
    },
    {
        "area": "Stage 5.1 - Candidate Generation Improvement",
        "file": "src/tennis_vision/ball_candidate_improvement.py",
        "function": "generate_hsv_candidates",
        "purpose": "Generates improved HSV color candidates for labeled frames.",
        "inputs": ["frame bundle", "court polygon"],
        "outputs": ["candidate rows"],
        "called_by": ["scripts/run_stage_5_1_candidate_improvement.py"],
        "why": "This strategy dramatically improved ball candidate distance on the sample.",
    },
    {
        "area": "Stage 5.1 - Candidate Generation Improvement",
        "file": "src/tennis_vision/ball_candidate_improvement.py",
        "function": "evaluate_strategies",
        "purpose": "Compares candidate generation strategies against manual labels.",
        "inputs": ["candidates by strategy", "manual labels"],
        "outputs": ["strategy comparison rows and summaries"],
        "called_by": ["scripts/run_stage_5_1_candidate_improvement.py"],
        "why": "Helps decide whether to advance or improve the detector first.",
    },
    {
        "area": "Stage 6 - Trajectory Smoothing",
        "file": "src/tennis_vision/trajectory_smoothing.py",
        "function": "moving_average_smooth",
        "purpose": "Smooths raw and projected ball coordinates with a small moving average.",
        "inputs": ["trajectory rows", "window size"],
        "outputs": ["smoothed trajectory rows"],
        "called_by": ["scripts/run_stage_6_trajectory_smoothing.py"],
        "why": "Creates a first trajectory without hiding sparse or bad detections.",
    },
    {
        "area": "Stage 6 - Trajectory Smoothing",
        "file": "src/tennis_vision/event_segmentation.py",
        "function": "detect_events",
        "purpose": "Creates hypothesis-only event markers from trajectory shape and speed changes.",
        "inputs": ["raw trajectory rows"],
        "outputs": ["event rows and warnings"],
        "called_by": ["scripts/run_stage_6_trajectory_smoothing.py"],
        "why": "Starts event reasoning while preserving uncertainty.",
    },
    {
        "area": "Stage 7 - Player Interaction",
        "file": "src/tennis_vision/player_tracking.py",
        "function": "detect_players",
        "purpose": "Runs local YOLO person detection on selected frames.",
        "inputs": ["video", "frame list", "model", "resize width", "confidence"],
        "outputs": ["player detection rows"],
        "called_by": ["scripts/run_stage_7_player_interaction_probe.py"],
        "why": "Player locations are needed to interpret possible ball-player interactions.",
    },
    {
        "area": "Stage 7 - Player Interaction",
        "file": "src/tennis_vision/ball_player_interaction.py",
        "function": "associate_ball_to_players",
        "purpose": "Associates ball trajectory points with nearby player tracks.",
        "inputs": ["ball rows", "player tracks", "events", "frame tolerance"],
        "outputs": ["distance rows, interaction rows, counts"],
        "called_by": ["scripts/run_stage_7_player_interaction_probe.py"],
        "why": "Turns player proximity into possible-hit hypotheses, not confirmed events.",
    },
    {
        "area": "Stage 7.1 - Player Filtering and Identity",
        "file": "src/tennis_vision/player_filtering.py",
        "function": "score_track_rows",
        "purpose": "Scores person detections using court, size, duration, and confidence signals.",
        "inputs": ["player track rows", "court polygon", "thresholds"],
        "outputs": ["scored rows and track summaries"],
        "called_by": ["scripts/run_stage_7_1_player_filtering.py"],
        "why": "Filters audience and side people so only the main players remain.",
    },
    {
        "area": "Stage 7.1 - Player Filtering and Identity",
        "file": "src/tennis_vision/player_identity.py",
        "function": "build_identity_profiles",
        "purpose": "Builds lightweight clothing-color identity profiles from player crops.",
        "inputs": ["video", "filtered player rows"],
        "outputs": ["identity profile JSON and warnings"],
        "called_by": ["scripts/run_stage_7_1_player_filtering.py"],
        "why": "Player identity should not be permanently tied to near/far side.",
    },
    {
        "area": "Stage 8 - Event Timeline",
        "file": "src/tennis_vision/event_timeline.py",
        "function": "merge_timeline_events",
        "purpose": "Merges nearby trajectory, event, and interaction evidence into timeline clusters.",
        "inputs": ["event rows", "merge window", "FPS"],
        "outputs": ["timeline event rows"],
        "called_by": ["scripts/run_stage_8_event_timeline.py"],
        "why": "Creates the first readable rally timeline while preserving uncertainty.",
    },
    {
        "area": "Stage 8 - Event Timeline",
        "file": "src/tennis_vision/rally_segmentation.py",
        "function": "build_rally_segments",
        "purpose": "Builds conservative rally segments from trajectory anchors.",
        "inputs": ["trajectory rows", "timeline events", "FPS"],
        "outputs": ["rally segment rows"],
        "called_by": ["scripts/run_stage_8_event_timeline.py"],
        "why": "Provides a first segment boundary without inferring score or outcome.",
    },
    {
        "area": "Stage 8.1 - Timeline Validation",
        "file": "src/tennis_vision/label_expansion.py",
        "function": "load_durable_or_fallback_labels",
        "purpose": "Loads durable expanded labels first, then latest session backup, then Stage 4.1 fallback labels.",
        "inputs": ["expanded labels path", "fallback labels path"],
        "outputs": ["labels", "source metadata", "warnings"],
        "called_by": ["scripts/run_stage_8_1_expand_labels.py"],
        "why": "Prevents non-interactive validation from downgrading manual label coverage.",
    },
    {
        "area": "Stage 8.1 - Timeline Validation",
        "file": "src/tennis_vision/label_expansion.py",
        "function": "write_label_session_backup",
        "purpose": "Writes timestamped CSV and JSON backups for labels collected in an interactive session.",
        "inputs": ["session directory", "timestamp", "labels"],
        "outputs": ["backup CSV path", "backup JSON path"],
        "called_by": ["scripts/run_stage_8_1_expand_labels.py"],
        "why": "Protects manual labeling work from later validation runs or report regeneration.",
    },
    {
        "area": "Stage 8.1 - Timeline Validation",
        "file": "src/tennis_vision/label_expansion.py",
        "function": "latest_label_session_csv",
        "purpose": "Finds the newest timestamped Stage 8.1 label session backup.",
        "inputs": ["label session directory"],
        "outputs": ["latest session CSV path or None"],
        "called_by": ["load_durable_or_fallback_labels"],
        "why": "Allows non-interactive validation to recover from a missing or incomplete durable expanded label file.",
    },
    {
        "area": "Stage 8.1 - Timeline Validation",
        "file": "src/tennis_vision/timeline_validation.py",
        "function": "validate_timeline_events",
        "purpose": "Checks whether timeline events are supported by nearby expanded ball labels.",
        "inputs": ["timeline rows", "expanded labels"],
        "outputs": ["validation rows, validated timeline, summary"],
        "called_by": ["scripts/run_stage_8_1_expand_labels.py"],
        "why": "This is the gate before tactical metrics.",
    },
    {
        "area": "Lab Notebook",
        "file": "src/tennis_vision/lab_notebook.py",
        "function": "update_lab_notebook",
        "purpose": "Updates stage lab notebook pages and experiment index from reports.",
        "inputs": ["project root"],
        "outputs": ["lab notebook Markdown pages"],
        "called_by": ["stage scripts", "scripts/update_lab_notebook.py"],
        "why": "Keeps execution evidence current without manual documentation commands.",
    },
]


AREA_ORDER = [
    "Stage 0 - Environment",
    "Reports",
    "Friction",
    "Stage 1 - Video IO",
    "Stage 2 - YOLO CPU",
    "Stage 3 - Court Calibration",
    "Stage 3.1 - Court Point Selection",
    "Stage 4 - Ball Candidate Probe",
    "Stage 4.1 - Manual Ball Labeling",
    "Stage 5 - Candidate Filtering and Court Projection",
    "Stage 5.1 - Candidate Generation Improvement",
    "Stage 6 - Trajectory Smoothing",
    "Stage 7 - Player Interaction",
    "Stage 7.1 - Player Filtering and Identity",
    "Stage 8 - Event Timeline",
    "Stage 8.1 - Timeline Validation",
    "Lab Notebook",
]


def find_line_numbers() -> dict[tuple[str, str], int]:
    """Find function/class line numbers using Python AST."""
    result: dict[tuple[str, str], int] = {}
    for path in sorted((PROJECT_ROOT / "src").rglob("*.py")) + sorted((PROJECT_ROOT / "scripts").glob("*.py")):
        relative = path.relative_to(PROJECT_ROOT).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                result[(relative, node.name)] = node.lineno
    return result


def bullet(items: list[str]) -> str:
    """Render a short bullet list for a vertical block."""
    return "\n".join(f"  - {item}" for item in items)


def render_entry(entry: dict[str, Any], line_numbers: dict[tuple[str, str], int]) -> str:
    """Render one function block."""
    file_path = entry["file"]
    function = entry["function"]
    line = line_numbers.get((file_path, function), "Not available")
    return "\n".join(
        [
            f"FUNCTION: {function}",
            f"FILE: {file_path}",
            f"LINE: {line}",
            f"AREA: {entry['area']}",
            "",
            "PURPOSE:",
            f"  {entry['purpose']}",
            "",
            "INPUTS:",
            bullet(entry.get("inputs", ["Not documented"])),
            "",
            "OUTPUTS:",
            bullet(entry.get("outputs", ["Not documented"])),
            "",
            "CALLED BY:",
            bullet(entry.get("called_by", ["Not documented"])),
            "",
            "WHY PRODUCT OWNER CARES:",
            f"  {entry.get('why', 'This function is part of the project flow.')}",
            "",
            "HOW TO FIND IT:",
            f"  Open {file_path} and go to line {line}.",
            f"  Search: def {function}",
            "",
            "NOTES:",
            f"  {entry.get('notes', 'None.')}",
            "",
            "---",
        ]
    )


def build_inventory() -> str:
    """Build the complete inventory document."""
    line_numbers = find_line_numbers()
    lines = [
        "# Function Inventory",
        "",
        "This document is designed to be readable as plain text.",
        "It avoids wide Markdown tables because the Product Owner often reviews documentation in TXT/editor view.",
        "",
        "Line numbers are generated from the current Python source with `scripts/update_function_inventory.py`.",
        "",
    ]
    for area in AREA_ORDER:
        entries = [entry for entry in FUNCTIONS if entry["area"] == area]
        if not entries:
            continue
        lines.extend([f"## {area}", ""])
        for entry in entries:
            lines.extend([render_entry(entry, line_numbers), ""])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(build_inventory(), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
