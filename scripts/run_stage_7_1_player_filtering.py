"""Run Stage 7.1 court-aware player filtering and identity stabilization."""

from __future__ import annotations

import argparse
import csv
import statistics
import sys
from pathlib import Path
from typing import Any

import cv2


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from tennis_vision.court_projection import load_stage_3_calibration  # noqa: E402
from tennis_vision.friction import calculate_stage_7_1_friction_score  # noqa: E402
from tennis_vision.player_filtering import (  # noqa: E402
    apply_player_identities,
    build_main_players,
    build_side_states,
    read_player_tracks,
    score_track_rows,
    select_main_tracks,
    side_state,
    write_csv,
)
from tennis_vision.player_identity import (  # noqa: E402
    build_identity_profiles,
    compare_identity_profiles,
    save_identity_preview,
    write_matches_csv,
)
from tennis_vision.report import ensure_output_folders, utc_timestamp, write_json_report, write_markdown_report, write_timestamped_log  # noqa: E402


FILTERED_FIELDS = [
    "original_track_id",
    "filtered_track_id",
    "frame_index",
    "bbox_x1",
    "bbox_y1",
    "bbox_x2",
    "bbox_y2",
    "bbox_center_x",
    "bbox_center_y",
    "bottom_center_x",
    "bottom_center_y",
    "confidence",
    "court_region_score",
    "size_score",
    "duration_score",
    "final_player_score",
    "keep",
    "rejection_reason",
]
MAIN_PLAYER_FIELDS = [
    "player_id",
    "source_track_ids",
    "frames_seen",
    "dominant_colors_summary",
    "average_confidence",
    "average_court_score",
    "initial_side_state",
    "notes",
]
SIDE_STATE_FIELDS = ["frame_index", "player_id", "side_state", "x", "y", "projected_x", "projected_y", "source_track_id"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 7.1 court-aware player filtering.")
    parser.add_argument("--detections", type=Path, default=PROJECT_ROOT / "outputs" / "player_tracking" / "stage_7_player_interaction" / "player_detections.csv")
    parser.add_argument("--tracks", type=Path, default=PROJECT_ROOT / "outputs" / "player_tracking" / "stage_7_player_interaction" / "player_tracks.csv")
    parser.add_argument("--video", type=Path, default=PROJECT_ROOT / "samples" / "video_01.mov")
    parser.add_argument("--max-players", type=int, default=2)
    parser.add_argument("--court-margin", type=float, default=450.0)
    parser.add_argument("--min-track-frames", type=int, default=2)
    parser.add_argument("--generate-rejected-debug", action="store_true", default=False)
    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", newline="", encoding="utf-8") as handle:
        return max(0, sum(1 for _line in handle) - 1)


def refine_ball_player_distances(path: Path, filtered_rows: list[dict[str, Any]], output_path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Update Stage 7 ball-player associations with stable player IDs."""
    if not path.exists():
        write_csv(output_path, [], ["frame_index", "ball_x", "ball_y", "nearest_player_id", "nearest_source_track_id", "image_distance_px", "side_state", "identity_confidence", "interaction_score", "notes"])
        return [], [f"Stage 7 ball-player distances CSV not found: {path}"]
    kept_by_source = {row["original_track_id"]: row for row in filtered_rows if row.get("keep")}
    rows: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for item in reader:
            source_track = item.get("nearest_track_id", "")
            kept = kept_by_source.get(source_track)
            rows.append(
                {
                    "frame_index": item.get("frame_index"),
                    "ball_x": item.get("ball_x"),
                    "ball_y": item.get("ball_y"),
                    "nearest_player_id": kept.get("filtered_track_id") if kept else "",
                    "nearest_source_track_id": source_track,
                    "image_distance_px": item.get("image_distance_px"),
                    "side_state": side_state(kept) if kept else "unknown",
                    "identity_confidence": kept.get("final_player_score") if kept else "",
                    "interaction_score": item.get("interaction_score"),
                    "notes": "mapped to stabilized identity" if kept else "nearest Stage 7 track was not selected as a main player",
                }
            )
    write_csv(output_path, rows, ["frame_index", "ball_x", "ball_y", "nearest_player_id", "nearest_source_track_id", "image_distance_px", "side_state", "identity_confidence", "interaction_score", "notes"])
    return rows, []


def save_filtered_overlays(video_path: Path, filtered_rows: list[dict[str, Any]], output_dir: Path) -> list[str]:
    """Save kept-player overlay images."""
    kept = [row for row in filtered_rows if row.get("keep")]
    by_frame: dict[int, list[dict[str, Any]]] = {}
    for row in kept:
        by_frame.setdefault(int(row["frame_index"]), []).append(row)
    output_dir.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []
    capture = cv2.VideoCapture(str(video_path))
    try:
        for frame_index, rows in sorted(by_frame.items()):
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ok, frame = capture.read()
            if not ok:
                continue
            scale = 1280 / frame.shape[1]
            frame = cv2.resize(frame, (1280, int(frame.shape[0] * scale)), interpolation=cv2.INTER_AREA)
            for row in rows:
                x1 = int(round(row["bbox_x1"] * scale))
                y1 = int(round(row["bbox_y1"] * scale))
                x2 = int(round(row["bbox_x2"] * scale))
                y2 = int(round(row["bbox_y2"] * scale))
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
                label = f"{row['filtered_track_id']} {side_state(row)} score={row['final_player_score']:.2f}"
                cv2.putText(frame, label, (x1, max(24, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
            path = output_dir / f"filtered_players_frame_{frame_index:06d}.jpg"
            if cv2.imwrite(str(path), frame):
                saved.append(str(path))
    finally:
        capture.release()
    return saved


def save_rejected_debug(video_path: Path, filtered_rows: list[dict[str, Any]], output_dir: Path) -> list[str]:
    """Save optional rejected detection debug overlays."""
    rejected = [row for row in filtered_rows if not row.get("keep")]
    by_frame: dict[int, list[dict[str, Any]]] = {}
    for row in rejected:
        by_frame.setdefault(int(row["frame_index"]), []).append(row)
    output_dir.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []
    capture = cv2.VideoCapture(str(video_path))
    try:
        for frame_index, rows in sorted(by_frame.items())[:8]:
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ok, frame = capture.read()
            if not ok:
                continue
            scale = 1280 / frame.shape[1]
            frame = cv2.resize(frame, (1280, int(frame.shape[0] * scale)), interpolation=cv2.INTER_AREA)
            for row in rows:
                x1 = int(round(row["bbox_x1"] * scale))
                y1 = int(round(row["bbox_y1"] * scale))
                x2 = int(round(row["bbox_x2"] * scale))
                y2 = int(round(row["bbox_y2"] * scale))
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 1)
            path = output_dir / f"rejected_debug_frame_{frame_index:06d}.jpg"
            if cv2.imwrite(str(path), frame):
                saved.append(str(path))
    finally:
        capture.release()
    return saved


def determine_verdict(report: dict[str, Any]) -> str:
    flags = report["flags"]
    if flags["tracks_missing"] or flags["video_missing"]:
        return "blocked"
    if flags["no_main_players_selected"]:
        return "needs_better_player_tracking"
    if report["main_players_selected"] >= 2 and report["refined_ball_player_associations_count"] > 0:
        return "ready_for_stage_8" if not flags["too_many_unknown_tracks"] else "ready_with_warnings"
    return "ready_with_warnings"


def recommended_next_step(report: dict[str, Any]) -> str:
    if report["final_verdict"] == "ready_for_stage_8":
        return "Proceed to Stage 8: shot/event timeline and rally segmentation prototype."
    if report["final_verdict"] == "needs_better_player_tracking":
        return "Proceed to Stage 7.2: manual player identity labeling helper or player tracking improvement."
    return "Review filtered identities; proceed to Stage 8 cautiously or Stage 7.2 if identity confidence is not sufficient."


def _metric_table(rows: list[tuple[str, Any]]) -> str:
    lines = ["| Metric | Value |", "|---|---:|"]
    for key, value in rows:
        lines.append(f"| {key} | {value if value is not None else 'Not available'} |")
    return "\n".join(lines)


def _identity_table(rows: list[dict[str, Any]]) -> str:
    lines = ["| Player ID | Source tracks | Frames seen | Dominant appearance | Initial side | Notes |", "|---|---|---:|---|---|---|"]
    for row in rows:
        lines.append(f"| {row['player_id']} | {row['source_track_ids']} | {row['frames_seen']} | {row['dominant_colors_summary']} | {row['initial_side_state']} | {row['notes']} |")
    if not rows:
        lines.append("| None | None | 0 | Not available | unknown | No main player selected |")
    return "\n".join(lines)


def _bullet_list(items: list[str], empty_text: str) -> str:
    return empty_text if not items else "\n".join(f"- {item}" for item in items)


def build_markdown_sections(report: dict[str, Any], main_players: list[dict[str, Any]]) -> list[tuple[str, str]]:
    interpretation = (
        "Stage 7.1 reduces noisy people detections with court-aware scoring and creates lightweight clothing-color identity profiles. "
        "Player identity is separated from near/far side state, so side can change without redefining the player. "
    )
    if report["main_players_selected"] >= 2:
        interpretation += "The two main player identities are separable enough for the next local timeline prototype."
    else:
        interpretation += "Player identity remains weak and should be labeled or improved before timeline work."
    return [
        ("Verdict", f"- Final verdict: {report['final_verdict']}\n- Friction score: {report['friction']['score']}\n- Friction level: {report['friction']['band']}"),
        ("Inputs", f"- Player detections CSV: `{report['input_detections_path']}`\n- Player tracks CSV: `{report['input_tracks_path']}`\n- Video path: `{report['input_video_path']}`\n- Calibration/homography availability: {report['homography_available']}"),
        ("Filtering summary", _metric_table([
            ("input detections", report["total_detections_input"]),
            ("kept detections", report["detections_kept"]),
            ("rejected detections", report["detections_rejected"]),
            ("input tracks", report["total_tracks_input"]),
            ("kept tracks", report["tracks_kept"]),
            ("main players selected", report["main_players_selected"]),
        ])),
        ("Identity summary", _identity_table(main_players)),
        ("Side-state summary", "Near/far side is recorded as a mutable state, not as permanent player identity."),
        ("Refined ball-player association", f"- Refined associations count: {report['refined_ball_player_associations_count']}\n- Average distance: {report['refined_average_distance_px']}\n- Main warnings: {', '.join(report['warnings']) if report['warnings'] else 'None'}"),
        ("Product Owner interpretation", interpretation),
        ("Warnings", _bullet_list(report["warnings"], "No warnings.")),
        ("Errors", _bullet_list(report["errors"], "No errors.")),
        ("Next step", report["recommended_next_step"]),
    ]


def update_lab_notebook_safely() -> tuple[dict[str, Path], str | None]:
    try:
        from tennis_vision.lab_notebook import lab_notebook_paths, update_lab_notebook

        update_lab_notebook(PROJECT_ROOT)
        return lab_notebook_paths(PROJECT_ROOT, "stage_7_1"), None
    except Exception as exc:
        try:
            from tennis_vision.lab_notebook import lab_notebook_paths

            return lab_notebook_paths(PROJECT_ROOT, "stage_7_1"), f"Lab notebook update failed: {exc}"
        except Exception:
            return {
                "stage_page": PROJECT_ROOT / "docs" / "lab-notebook" / "stage_7_1_player_filtering.md",
                "experiment_index": PROJECT_ROOT / "docs" / "lab-notebook" / "experiment_index.md",
            }, f"Lab notebook update failed: {exc}"


def print_summary(report: dict[str, Any], lab_paths: dict[str, Path]) -> None:
    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(title="Stage 7.1 Player Filtering")
        table.add_column("Field")
        table.add_column("Value")
        for field, value in [
            ("Verdict", report["final_verdict"]),
            ("Friction", f"{report['friction']['score']} ({report['friction']['band']})"),
            ("Input detections", report["total_detections_input"]),
            ("Kept detections", report["detections_kept"]),
            ("Input tracks", report["total_tracks_input"]),
            ("Kept tracks", report["tracks_kept"]),
            ("Main players", report["main_players_selected"]),
            ("Identities", report["player_identities_created"]),
            ("Refined associations", report["refined_ball_player_associations_count"]),
            ("Lab notebook", str(lab_paths["stage_page"])),
        ]:
            table.add_row(str(field), str(value))
        Console().print(table)
    except ImportError:
        print(f"Verdict: {report['final_verdict']}")


def main() -> int:
    args = parse_args()
    ensure_output_folders(PROJECT_ROOT)
    detections_path = resolve_path(args.detections)
    tracks_path = resolve_path(args.tracks)
    video_path = resolve_path(args.video)
    calibration = load_stage_3_calibration(PROJECT_ROOT / "outputs" / "reports" / "stage_3_court_calibration_probe_report.json")
    output_dir = PROJECT_ROOT / "outputs" / "player_tracking" / "stage_7_1_player_filtering"
    output_dir.mkdir(parents=True, exist_ok=True)

    warnings: list[str] = []
    errors: list[str] = []
    rows, track_errors = read_player_tracks(tracks_path)
    errors.extend(track_errors)
    total_detections = count_csv_rows(detections_path)
    if not detections_path.exists():
        warnings.append(f"Player detections CSV not found: {detections_path}")
    if calibration.get("error") and not calibration.get("homography_available"):
        warnings.append(str(calibration["error"]))

    scored_rows, summaries = score_track_rows(
        rows,
        calibration.get("court_polygon", []),
        court_margin=args.court_margin,
        min_track_frames=args.min_track_frames,
    )
    selected_tracks = select_main_tracks(summaries, max(1, args.max_players))
    filtered_rows = apply_player_identities(scored_rows, selected_tracks)
    profile_path = output_dir / "player_identity_profiles.json"
    profiles, profile_warnings = build_identity_profiles(video_path=video_path, filtered_rows=filtered_rows, output_path=profile_path)
    warnings.extend(profile_warnings)
    matches = compare_identity_profiles(profiles)
    matches_path = output_dir / "player_identity_matches.csv"
    write_matches_csv(matches_path, matches)
    main_players = build_main_players(selected_tracks, summaries, profiles)
    side_states = build_side_states(filtered_rows)

    filtered_detections_path = output_dir / "filtered_player_detections.csv"
    filtered_tracks_path = output_dir / "filtered_player_tracks.csv"
    main_players_path = output_dir / "main_players.csv"
    side_states_path = output_dir / "player_side_states.csv"
    refined_path = output_dir / "refined_ball_player_distances.csv"
    write_csv(filtered_detections_path, filtered_rows, FILTERED_FIELDS)
    write_csv(filtered_tracks_path, [row for row in filtered_rows if row.get("keep")], FILTERED_FIELDS)
    write_csv(main_players_path, main_players, MAIN_PLAYER_FIELDS)
    write_csv(side_states_path, side_states, SIDE_STATE_FIELDS)
    refined_rows, refined_warnings = refine_ball_player_distances(
        PROJECT_ROOT / "outputs" / "player_tracking" / "stage_7_player_interaction" / "ball_player_distances.csv",
        filtered_rows,
        refined_path,
    )
    warnings.extend(refined_warnings)

    overlay_dir = output_dir / "filtered_player_overlays"
    rejected_dir = output_dir / "rejected_detection_debug"
    overlays = save_filtered_overlays(video_path, filtered_rows, overlay_dir) if video_path.exists() else []
    rejected_debug = save_rejected_debug(video_path, filtered_rows, rejected_dir) if args.generate_rejected_debug and video_path.exists() else []
    identity_preview = save_identity_preview(video_path=video_path, filtered_rows=filtered_rows, output_path=output_dir / "player_identity_preview.jpg")
    if filtered_rows and not overlays:
        warnings.append("Filtered player overlays could not be generated.")
    if profiles and not identity_preview:
        warnings.append("Player identity preview could not be generated.")

    kept_rows = [row for row in filtered_rows if row.get("keep")]
    kept_tracks = sorted({row["original_track_id"] for row in kept_rows})
    unknown_tracks = [track_id for track_id in summaries if track_id not in selected_tracks]
    refined_distances = [float(row["image_distance_px"]) for row in refined_rows if row.get("nearest_player_id") and row.get("image_distance_px")]
    flags = {
        "detections_missing": not detections_path.exists(),
        "tracks_missing": not tracks_path.exists() or not rows,
        "video_missing": not video_path.exists(),
        "calibration_missing": not bool(calibration.get("homography_available")),
        "no_main_players_selected": not selected_tracks,
        "too_many_unknown_tracks": len(unknown_tracks) > 4,
        "identity_profiles_failed": bool(selected_tracks and not profiles),
        "refined_association_failed": not any(row.get("nearest_player_id") for row in refined_rows),
        "visualization_failed": bool((kept_rows and not overlays) or (profiles and not identity_preview)),
    }
    if flags["too_many_unknown_tracks"]:
        warnings.append("Many non-main tracks remain after filtering; Stage 7.2 may improve identity handling.")
    if len(selected_tracks) < args.max_players:
        warnings.append("Fewer main players were selected than requested.")

    friction = calculate_stage_7_1_friction_score(**flags, errors_count=len(errors), warnings_count=len(warnings))
    report: dict[str, Any] = {
        "timestamp": utc_timestamp(),
        "stage": "stage_7_1_player_filtering",
        "input_detections_path": str(detections_path),
        "input_tracks_path": str(tracks_path),
        "input_video_path": str(video_path),
        "homography_available": bool(calibration.get("homography_available")),
        "total_detections_input": total_detections,
        "total_tracks_input": len(summaries),
        "detections_kept": len(kept_rows),
        "detections_rejected": max(0, len(filtered_rows) - len(kept_rows)),
        "tracks_kept": len(kept_tracks),
        "main_players_selected": len(main_players),
        "player_identities_created": len(profiles),
        "side_states_generated": len(side_states),
        "refined_ball_player_associations_count": sum(1 for row in refined_rows if row.get("nearest_player_id")),
        "refined_average_distance_px": round(statistics.mean(refined_distances), 3) if refined_distances else None,
        "warnings": warnings,
        "errors": errors,
        "flags": flags,
        "friction": friction,
        "final_verdict": "blocked",
        "recommended_next_step": "",
        "output_paths": {
            "filtered_player_detections": str(filtered_detections_path),
            "filtered_player_tracks": str(filtered_tracks_path),
            "main_players": str(main_players_path),
            "player_identity_profiles": str(profile_path),
            "player_identity_matches": str(matches_path),
            "player_side_states": str(side_states_path),
            "refined_ball_player_distances": str(refined_path),
            "filtered_player_overlays": str(overlay_dir),
            "rejected_detection_debug": str(rejected_dir) if rejected_debug else None,
            "player_identity_preview": identity_preview,
        },
        "json_report_path": str(PROJECT_ROOT / "outputs" / "reports" / "stage_7_1_player_filtering_report.json"),
        "markdown_report_path": str(PROJECT_ROOT / "outputs" / "reports" / "stage_7_1_player_filtering_report.md"),
        "log_path": "",
    }
    report["final_verdict"] = determine_verdict(report)
    report["recommended_next_step"] = recommended_next_step(report)

    log_path = write_timestamped_log(
        PROJECT_ROOT,
        "stage_7_1_player_filtering",
        [
            f"timestamp={report['timestamp']}",
            f"verdict={report['final_verdict']}",
            f"friction={friction['score']} ({friction['band']})",
            f"input_detections={total_detections}",
            f"kept_detections={len(kept_rows)}",
            f"tracks_kept={len(kept_tracks)}",
        ],
    )
    report["log_path"] = str(log_path)
    json_path = Path(report["json_report_path"])
    markdown_path = Path(report["markdown_report_path"])
    write_json_report(json_path, report)
    write_markdown_report(markdown_path, "Stage 7.1 Court-Aware Player Filtering and Identity Stabilization Report", build_markdown_sections(report, main_players))

    lab_paths, notebook_warning = update_lab_notebook_safely()
    if notebook_warning:
        report["warnings"].append(notebook_warning)
        write_json_report(json_path, report)
        write_markdown_report(markdown_path, "Stage 7.1 Court-Aware Player Filtering and Identity Stabilization Report", build_markdown_sections(report, main_players))

    print_summary(report, lab_paths)
    return 1 if report["final_verdict"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
