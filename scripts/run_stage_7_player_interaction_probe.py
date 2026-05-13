"""Run Stage 7 player tracking and ball-player interaction probe."""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path
from typing import Any

import cv2
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from tennis_vision.ball_player_interaction import associate_ball_to_players, read_stage_6_events, write_csv as write_interaction_csv  # noqa: E402
from tennis_vision.court_projection import load_stage_3_calibration  # noqa: E402
from tennis_vision.friction import calculate_stage_7_friction_score  # noqa: E402
from tennis_vision.player_tracking import (  # noqa: E402
    detect_players,
    read_smoothed_trajectory,
    select_analysis_frames,
    track_players,
    write_csv,
)
from tennis_vision.report import ensure_output_folders, utc_timestamp, write_json_report, write_markdown_report, write_timestamped_log  # noqa: E402


PLAYER_FIELDS = [
    "frame_index",
    "track_id",
    "bbox_x1",
    "bbox_y1",
    "bbox_x2",
    "bbox_y2",
    "bbox_center_x",
    "bbox_center_y",
    "confidence",
    "class_name",
    "player_side_guess",
    "projected_x",
    "projected_y",
]
DETECTION_FIELDS = [field for field in PLAYER_FIELDS if field != "track_id"]
ASSOCIATION_FIELDS = [
    "frame_index",
    "ball_x",
    "ball_y",
    "ball_projected_x",
    "ball_projected_y",
    "nearest_track_id",
    "nearest_player_center_x",
    "nearest_player_center_y",
    "image_distance_px",
    "projected_distance",
    "near_player_bbox",
    "interaction_score",
    "interaction_reason",
    "related_stage_6_event",
]
INTERACTION_FIELDS = [
    "frame_index",
    "interaction_type",
    "confidence_like_score",
    "reason",
    "nearest_track_id",
    "image_distance_px",
    "projected_distance",
    "related_stage_6_event",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 7 player tracking and ball-player interaction probe.")
    parser.add_argument("--video", type=Path, default=PROJECT_ROOT / "samples" / "video_01.mov")
    parser.add_argument(
        "--trajectory",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "ball_tracking" / "stage_6_trajectory_smoothing" / "smoothed_trajectory.csv",
    )
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--max-frames", type=int, default=20)
    parser.add_argument("--resize-width", type=int, default=1280)
    parser.add_argument("--confidence", type=float, default=0.25)
    parser.add_argument("--frame-tolerance", type=int, default=5)
    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def determine_verdict(report: dict[str, Any]) -> str:
    flags = report["flags"]
    if flags["smoothed_trajectory_missing"] or flags["video_missing"] or flags["yolo_model_load_failed"]:
        return "blocked"
    if flags["too_few_ball_points"]:
        return "needs_more_ball_labels"
    if flags["no_player_detections"]:
        return "needs_better_player_tracking"
    if report["ball_points_associated_count"] > 0:
        return "ready_with_warnings"
    return "needs_better_player_tracking"


def recommended_next_step(report: dict[str, Any]) -> str:
    verdict = report["final_verdict"]
    if verdict == "ready_for_stage_8":
        return "Proceed to Stage 8: shot/event timeline and rally segmentation prototype."
    if verdict == "needs_more_ball_labels":
        return "Proceed to Stage 7.1: expand manual labels and rerun ball-player interaction."
    if verdict == "needs_better_player_tracking":
        return "Proceed to Stage 7.2: player tracking improvement."
    if verdict == "blocked":
        return "Fix missing Stage 7 inputs or YOLO model loading, then rerun the probe."
    return "Review hypotheses, then choose Stage 7.1 for more labels or Stage 8 for a cautious timeline prototype."


def save_player_overlays(video_path: Path, tracks: list[dict[str, Any]], output_dir: Path, resize_width: int) -> list[str]:
    """Save player detection overlay images."""
    output_dir.mkdir(parents=True, exist_ok=True)
    by_frame: dict[int, list[dict[str, Any]]] = {}
    for track in tracks:
        by_frame.setdefault(int(track["frame_index"]), []).append(track)
    saved: list[str] = []
    capture = cv2.VideoCapture(str(video_path))
    try:
        for frame_index, frame_tracks in sorted(by_frame.items())[:20]:
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ok, frame = capture.read()
            if not ok:
                continue
            original_h, original_w = frame.shape[:2]
            if resize_width and original_w > resize_width:
                scale = resize_width / original_w
                frame = cv2.resize(frame, (resize_width, int(original_h * scale)), interpolation=cv2.INTER_AREA)
            else:
                scale = 1.0
            for track in frame_tracks:
                x1 = int(round(track["bbox_x1"] * scale))
                y1 = int(round(track["bbox_y1"] * scale))
                x2 = int(round(track["bbox_x2"] * scale))
                y2 = int(round(track["bbox_y2"] * scale))
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
                cv2.putText(frame, f"{track['track_id']} {track.get('confidence', '')}", (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
            path = output_dir / f"player_detection_frame_{frame_index:06d}.jpg"
            if cv2.imwrite(str(path), frame):
                saved.append(str(path))
    finally:
        capture.release()
    return saved


def save_interaction_overlays(
    video_path: Path,
    tracks: list[dict[str, Any]],
    associations: list[dict[str, Any]],
    interactions: list[dict[str, Any]],
    output_dir: Path,
    resize_width: int,
) -> list[str]:
    """Save ball-player interaction overlay images."""
    output_dir.mkdir(parents=True, exist_ok=True)
    track_by_key = {(int(track["frame_index"]), track["track_id"]): track for track in tracks}
    interaction_by_frame: dict[int, list[str]] = {}
    for interaction in interactions:
        interaction_by_frame.setdefault(int(interaction["frame_index"]), []).append(interaction["interaction_type"])
    saved: list[str] = []
    capture = cv2.VideoCapture(str(video_path))
    try:
        for association in associations:
            frame_index = int(association["frame_index"])
            track = track_by_key.get((frame_index, association.get("nearest_track_id")))
            if track is None:
                nearby = [item for item in tracks if item["track_id"] == association.get("nearest_track_id")]
                track = min(nearby, key=lambda item: abs(item["frame_index"] - frame_index), default=None)
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ok, frame = capture.read()
            if not ok:
                continue
            original_h, original_w = frame.shape[:2]
            if resize_width and original_w > resize_width:
                scale = resize_width / original_w
                frame = cv2.resize(frame, (resize_width, int(original_h * scale)), interpolation=cv2.INTER_AREA)
            else:
                scale = 1.0
            bx = int(round(float(association["ball_x"]) * scale))
            by = int(round(float(association["ball_y"]) * scale))
            cv2.circle(frame, (bx, by), 8, (0, 0, 255), -1)
            if track:
                cx = int(round(float(track["bbox_center_x"]) * scale))
                cy = int(round(float(track["bbox_center_y"]) * scale))
                cv2.rectangle(
                    frame,
                    (int(round(track["bbox_x1"] * scale)), int(round(track["bbox_y1"] * scale))),
                    (int(round(track["bbox_x2"] * scale)), int(round(track["bbox_y2"] * scale))),
                    (0, 255, 255),
                    2,
                )
                cv2.line(frame, (bx, by), (cx, cy), (255, 255, 255), 2)
            label = ", ".join(interaction_by_frame.get(frame_index, [])) or "association"
            cv2.putText(frame, f"frame {frame_index}: {label}", (24, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
            path = output_dir / f"interaction_frame_{frame_index:06d}.jpg"
            if cv2.imwrite(str(path), frame):
                saved.append(str(path))
    finally:
        capture.release()
    return saved


def save_summary_preview(overlay_paths: list[str], output_path: Path) -> str | None:
    """Save a contact sheet preview."""
    images = [cv2.imread(path) for path in overlay_paths[:6]]
    images = [image for image in images if image is not None]
    if not images:
        return None
    thumb_width = 420
    thumbs = []
    for image in images:
        scale = thumb_width / image.shape[1]
        thumbs.append(cv2.resize(image, (thumb_width, int(image.shape[0] * scale)), interpolation=cv2.INTER_AREA))
    max_h = max(image.shape[0] for image in thumbs)
    padded = []
    for image in thumbs:
        if image.shape[0] < max_h:
            pad = 30 * np.ones((max_h - image.shape[0], image.shape[1], 3), dtype=image.dtype)
            image = np.vstack([image, pad])
        padded.append(image)
    sheet = np.hstack(padded)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if cv2.imwrite(str(output_path), sheet):
        return str(output_path)
    return None


def _metric_table(rows: list[tuple[str, Any]]) -> str:
    lines = ["| Metric | Value |", "|---|---|"]
    for key, value in rows:
        lines.append(f"| {key} | {value if value is not None else 'Not available'} |")
    return "\n".join(lines)


def _interaction_table(counts: dict[str, int]) -> str:
    lines = ["| Interaction type | Count |", "|---|---:|"]
    if not counts:
        lines.append("| None | 0 |")
    for key, value in counts.items():
        lines.append(f"| {key} | {value} |")
    return "\n".join(lines)


def _bullet_list(items: list[str], empty_text: str) -> str:
    return empty_text if not items else "\n".join(f"- {item}" for item in items)


def build_markdown_sections(report: dict[str, Any]) -> list[tuple[str, str]]:
    interpretation = (
        "Stage 7 validates whether local CPU person detection can provide player positions for ball-player proximity hypotheses. "
        "The interactions are not confirmed hits. "
    )
    if report["trajectory_points_count"] <= 5:
        interpretation += "The current ball trajectory is still sparse, so more labels would improve confidence. "
    if report["player_detections_count"] > 0:
        interpretation += "Player detection is viable enough for a local interaction probe."
    else:
        interpretation += "Player tracking needs improvement before interaction reasoning."
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
                    f"- Video path: `{report['input_video_path']}`",
                    f"- Smoothed trajectory path: `{report['input_smoothed_trajectory_path']}`",
                    f"- Manual labels path: `{report['input_manual_labels_path']}`",
                    f"- Calibration/homography availability: {report['homography_available']}",
                ]
            ),
        ),
        (
            "Player detection summary",
            _metric_table(
                [
                    ("frames analyzed", report["frames_analyzed"]),
                    ("player detections", report["player_detections_count"]),
                    ("player tracks", report["player_tracks_count"]),
                    ("YOLO model", report["yolo_model"]),
                    ("device", report["device"]),
                    ("confidence threshold", report["confidence_threshold"]),
                ]
            ),
        ),
        (
            "Ball-player association summary",
            _metric_table(
                [
                    ("ball points associated", report["ball_points_associated_count"]),
                    ("average distance px", report["average_ball_player_distance_px"]),
                    ("minimum distance px", report["minimum_ball_player_distance_px"]),
                    ("frame tolerance", report["frame_tolerance"]),
                    ("interactions found", report["interaction_hypotheses_count"]),
                ]
            ),
        ),
        ("Interaction hypotheses", _interaction_table(report["interactions_by_type"])),
        (
            "Output artifacts",
            "\n".join(
                [
                    f"- Player detections: `{report['output_paths']['player_detections_csv']}`",
                    f"- Player tracks: `{report['output_paths']['player_tracks_csv']}`",
                    f"- Ball-player distances: `{report['output_paths']['ball_player_distances_csv']}`",
                    f"- Interactions: `{report['output_paths']['ball_player_interactions_csv']}`",
                    f"- Player overlays: `{report['output_paths']['player_detection_overlays']}`",
                    f"- Interaction overlays: `{report['output_paths']['interaction_overlays']}`",
                    f"- Summary preview: `{report['output_paths']['summary_preview']}`",
                ]
            ),
        ),
        ("Product Owner interpretation", interpretation),
        ("Warnings", _bullet_list(report["warnings"], "No warnings.")),
        ("Errors", _bullet_list(report["errors"], "No errors.")),
        ("Next step", report["recommended_next_step"]),
    ]


def update_lab_notebook_safely() -> tuple[dict[str, Path], str | None]:
    try:
        from tennis_vision.lab_notebook import lab_notebook_paths, update_lab_notebook

        update_lab_notebook(PROJECT_ROOT)
        return lab_notebook_paths(PROJECT_ROOT, "stage_7"), None
    except Exception as exc:
        try:
            from tennis_vision.lab_notebook import lab_notebook_paths

            return lab_notebook_paths(PROJECT_ROOT, "stage_7"), f"Lab notebook update failed: {exc}"
        except Exception:
            return {
                "stage_page": PROJECT_ROOT / "docs" / "lab-notebook" / "stage_7_player_interaction_probe.md",
                "experiment_index": PROJECT_ROOT / "docs" / "lab-notebook" / "experiment_index.md",
            }, f"Lab notebook update failed: {exc}"


def print_summary(report: dict[str, Any], lab_paths: dict[str, Path]) -> None:
    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(title="Stage 7 Player Interaction Probe")
        table.add_column("Field")
        table.add_column("Value")
        for field, value in [
            ("Verdict", report["final_verdict"]),
            ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"),
            ("Frames analyzed", len(report["frames_analyzed"])),
            ("Player detections", report["player_detections_count"]),
            ("Player tracks", report["player_tracks_count"]),
            ("Associations", report["ball_points_associated_count"]),
            ("Interactions", report["interaction_hypotheses_count"]),
            ("Interactions by type", report["interactions_by_type"]),
            ("Lab notebook", str(lab_paths["stage_page"])),
            ("Recommended next step", report["recommended_next_step"]),
        ]:
            table.add_row(str(field), str(value))
        Console().print(table)
    except ImportError:
        print(f"Verdict: {report['final_verdict']}")
        print(f"Player detections: {report['player_detections_count']}")
        print(f"Interactions: {report['interaction_hypotheses_count']}")


def main() -> int:
    args = parse_args()
    ensure_output_folders(PROJECT_ROOT)
    video_path = resolve_path(args.video)
    trajectory_path = resolve_path(args.trajectory)
    events_path = PROJECT_ROOT / "outputs" / "ball_tracking" / "stage_6_trajectory_smoothing" / "trajectory_events.csv"
    manual_path = PROJECT_ROOT / "outputs" / "ball_tracking" / "stage_4_1_manual_labels" / "manual_ball_labels.csv"
    calibration = load_stage_3_calibration(PROJECT_ROOT / "outputs" / "reports" / "stage_3_court_calibration_probe_report.json")
    output_dir = PROJECT_ROOT / "outputs" / "player_tracking" / "stage_7_player_interaction"
    player_overlay_dir = output_dir / "player_detection_overlays"
    interaction_overlay_dir = output_dir / "interaction_overlays"
    output_dir.mkdir(parents=True, exist_ok=True)

    warnings: list[str] = []
    errors: list[str] = []
    trajectory_rows, trajectory_errors = read_smoothed_trajectory(trajectory_path)
    errors.extend(trajectory_errors)
    events, event_warnings = read_stage_6_events(events_path)
    warnings.extend(event_warnings)
    event_frames = [event["frame_index"] for event in events]
    frames = select_analysis_frames(trajectory_rows, event_frames, args.max_frames) if trajectory_rows else []

    detection_result = detect_players(
        video_path=video_path,
        frame_indices=frames,
        model_name=args.model,
        resize_width=args.resize_width,
        confidence=args.confidence,
        homography_matrix=calibration.get("matrix") if calibration.get("homography_available") else None,
    )
    warnings.extend(detection_result["warnings"])
    errors.extend(detection_result["errors"])
    detections = detection_result["detections"]
    tracks = track_players(detections)
    unique_tracks = sorted({row["track_id"] for row in tracks})
    if len(unique_tracks) > 4:
        warnings.append("Player tracking is approximate and produced several temporary track IDs.")

    associations, interactions, interaction_counts = associate_ball_to_players(
        ball_rows=trajectory_rows,
        player_tracks=tracks,
        stage_6_events=events,
        frame_tolerance=args.frame_tolerance,
    )
    associated = [row for row in associations if row.get("nearest_track_id")]
    distances = [float(row["image_distance_px"]) for row in associated if row.get("image_distance_px") is not None]

    detection_csv = output_dir / "player_detections.csv"
    tracks_csv = output_dir / "player_tracks.csv"
    distances_csv = output_dir / "ball_player_distances.csv"
    interactions_csv = output_dir / "ball_player_interactions.csv"
    write_csv(detection_csv, detections, DETECTION_FIELDS)
    write_csv(tracks_csv, tracks, PLAYER_FIELDS)
    write_interaction_csv(distances_csv, associations, ASSOCIATION_FIELDS)
    write_interaction_csv(interactions_csv, interactions, INTERACTION_FIELDS)

    player_overlays = save_player_overlays(video_path, tracks, player_overlay_dir, args.resize_width) if detections else []
    interaction_overlays = save_interaction_overlays(video_path, tracks, associations, interactions, interaction_overlay_dir, args.resize_width) if associations else []
    summary_preview = save_summary_preview(interaction_overlays or player_overlays, output_dir / "player_interaction_preview.jpg")
    if (detections or associations) and not summary_preview:
        warnings.append("Summary preview could not be created.")
    if len([row for row in trajectory_rows if not row.get("is_interpolated")]) <= 5:
        warnings.append("Ball trajectory is sparse; player-ball interactions are hypotheses only.")

    flags = {
        "smoothed_trajectory_missing": not trajectory_path.exists() or not trajectory_rows,
        "video_missing": not video_path.exists(),
        "yolo_model_load_failed": bool(detection_result.get("model_status", {}).get("model_load_failed")),
        "no_player_detections": not detections,
        "tracking_unreliable": len(unique_tracks) > 4,
        "no_ball_player_associations": not associated,
        "too_few_ball_points": len([row for row in trajectory_rows if not row.get("is_interpolated")]) < 4,
        "visualization_failed": bool((detections or associations) and not summary_preview),
    }
    friction = calculate_stage_7_friction_score(**flags, errors_count=len(errors), warnings_count=len(warnings))

    report: dict[str, Any] = {
        "timestamp": utc_timestamp(),
        "stage": "stage_7_player_interaction_probe",
        "input_video_path": str(video_path),
        "input_smoothed_trajectory_path": str(trajectory_path),
        "input_manual_labels_path": str(manual_path) if manual_path.exists() else None,
        "homography_available": bool(calibration.get("homography_available")),
        "trajectory_points_count": len([row for row in trajectory_rows if not row.get("is_interpolated")]),
        "frames_analyzed": detection_result.get("frames_analyzed", []),
        "yolo_model": detection_result.get("model_name"),
        "device": "cpu",
        "confidence_threshold": args.confidence,
        "frame_tolerance": args.frame_tolerance,
        "player_detections_count": len(detections),
        "player_tracks_count": len(unique_tracks),
        "ball_points_associated_count": len(associated),
        "interaction_hypotheses_count": len(interactions),
        "interactions_by_type": interaction_counts,
        "average_ball_player_distance_px": round(statistics.mean(distances), 3) if distances else None,
        "minimum_ball_player_distance_px": round(min(distances), 3) if distances else None,
        "output_paths": {
            "player_detections_csv": str(detection_csv),
            "player_tracks_csv": str(tracks_csv),
            "ball_player_distances_csv": str(distances_csv),
            "ball_player_interactions_csv": str(interactions_csv),
            "player_detection_overlays": str(player_overlay_dir),
            "interaction_overlays": str(interaction_overlay_dir),
            "summary_preview": summary_preview,
        },
        "warnings": warnings,
        "errors": errors,
        "flags": flags,
        "friction": friction,
        "final_verdict": "blocked",
        "recommended_next_step": "",
        "json_report_path": str(PROJECT_ROOT / "outputs" / "reports" / "stage_7_player_interaction_probe_report.json"),
        "markdown_report_path": str(PROJECT_ROOT / "outputs" / "reports" / "stage_7_player_interaction_probe_report.md"),
        "log_path": "",
    }
    report["final_verdict"] = determine_verdict(report)
    report["recommended_next_step"] = recommended_next_step(report)

    log_path = write_timestamped_log(
        PROJECT_ROOT,
        "stage_7_player_interaction_probe",
        [
            f"timestamp={report['timestamp']}",
            f"verdict={report['final_verdict']}",
            f"friction={friction['score']} ({friction['band']})",
            f"frames_analyzed={len(report['frames_analyzed'])}",
            f"detections={len(detections)}",
            f"associations={len(associated)}",
            f"interactions={len(interactions)}",
        ],
    )
    report["log_path"] = str(log_path)

    json_path = Path(report["json_report_path"])
    markdown_path = Path(report["markdown_report_path"])
    write_json_report(json_path, report)
    write_markdown_report(markdown_path, "Stage 7 Player Tracking and Ball-Player Interaction Probe Report", build_markdown_sections(report))

    lab_paths, notebook_warning = update_lab_notebook_safely()
    if notebook_warning:
        report["warnings"].append(notebook_warning)
        write_json_report(json_path, report)
        write_markdown_report(markdown_path, "Stage 7 Player Tracking and Ball-Player Interaction Probe Report", build_markdown_sections(report))
        print(f"Warning: {notebook_warning}")

    print_summary(report, lab_paths)
    return 1 if report["final_verdict"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
