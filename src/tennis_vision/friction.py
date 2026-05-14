"""Friction scoring for local experiment readiness."""

from __future__ import annotations

from typing import Any


def friction_band(score: int) -> str:
    """Return the friction band for a 0 to 100 score."""
    if score <= 20:
        return "low friction"
    if score <= 50:
        return "medium friction"
    if score <= 80:
        return "high friction"
    return "blocking friction"


def calculate_friction_score(
    *,
    missing_packages: list[str] | None = None,
    missing_folders: list[str] | None = None,
    ffmpeg_missing: bool = False,
    errors_count: int = 0,
    manual_action_required: bool = False,
) -> dict[str, Any]:
    """Calculate a basic Stage 0 friction score from 0 to 100."""
    missing_packages = missing_packages or []
    missing_folders = missing_folders or []

    score = 0
    score += min(len(missing_packages) * 15, 45)
    score += min(len(missing_folders) * 10, 40)
    score += 15 if ffmpeg_missing else 0
    score += min(errors_count * 10, 30)
    score += 20 if manual_action_required else 0
    score = max(0, min(score, 100))

    return {
        "score": score,
        "band": friction_band(score),
        "inputs": {
            "missing_packages": missing_packages,
            "missing_folders": missing_folders,
            "ffmpeg_missing": ffmpeg_missing,
            "errors_count": errors_count,
            "manual_action_required": manual_action_required,
        },
    }


def calculate_stage_1_friction_score(
    *,
    video_missing: bool = False,
    video_open_failed: bool = False,
    metadata_read_failed: bool = False,
    zero_frames_detected: bool = False,
    frames_not_saved: bool = False,
    errors_count: int = 0,
    warnings_count: int = 0,
    manual_action_required: bool = False,
) -> dict[str, Any]:
    """Calculate Stage 1 video loading and frame extraction friction."""
    score = 0
    score += 35 if video_missing else 0
    score += 35 if video_open_failed else 0
    score += 25 if metadata_read_failed else 0
    score += 20 if zero_frames_detected else 0
    score += 35 if frames_not_saved else 0
    score += min(errors_count * 10, 30)
    score += min(warnings_count * 3, 15)
    score += 20 if manual_action_required else 0
    score = max(0, min(score, 100))

    return {
        "score": score,
        "band": friction_band(score),
        "inputs": {
            "video_missing": video_missing,
            "video_open_failed": video_open_failed,
            "metadata_read_failed": metadata_read_failed,
            "zero_frames_detected": zero_frames_detected,
            "frames_not_saved": frames_not_saved,
            "errors_count": errors_count,
            "warnings_count": warnings_count,
            "manual_action_required": manual_action_required,
        },
    }


def calculate_stage_2_friction_score(
    *,
    ultralytics_missing: bool = False,
    model_download_failed: bool = False,
    model_load_failed: bool = False,
    video_open_failed: bool = False,
    no_frames_processed: bool = False,
    no_detections: bool = False,
    inference_too_slow: bool = False,
    errors_count: int = 0,
    warnings_count: int = 0,
    manual_action_required: bool = False,
) -> dict[str, Any]:
    """Calculate Stage 2 YOLO CPU baseline friction."""
    score = 0
    score += 45 if ultralytics_missing else 0
    score += 25 if model_download_failed else 0
    score += 35 if model_load_failed else 0
    score += 35 if video_open_failed else 0
    score += 35 if no_frames_processed else 0
    score += 10 if no_detections else 0
    score += 20 if inference_too_slow else 0
    score += min(errors_count * 10, 30)
    score += min(warnings_count * 3, 15)
    score += 20 if manual_action_required else 0
    score = max(0, min(score, 100))

    return {
        "score": score,
        "band": friction_band(score),
        "inputs": {
            "ultralytics_missing": ultralytics_missing,
            "model_download_failed": model_download_failed,
            "model_load_failed": model_load_failed,
            "video_open_failed": video_open_failed,
            "no_frames_processed": no_frames_processed,
            "no_detections": no_detections,
            "inference_too_slow": inference_too_slow,
            "errors_count": errors_count,
            "warnings_count": warnings_count,
            "manual_action_required": manual_action_required,
        },
    }


def calculate_stage_3_friction_score(
    *,
    config_missing: bool = False,
    video_missing: bool = False,
    frame_load_failed: bool = False,
    calibration_points_missing: bool = False,
    placeholder_points_detected: bool = False,
    invalid_points: bool = False,
    point_order_suspicious: bool = False,
    polygon_self_intersects: bool = False,
    geometrically_invalid: bool = False,
    homography_failed: bool = False,
    errors_count: int = 0,
    warnings_count: int = 0,
) -> dict[str, Any]:
    """Calculate Stage 3 court calibration probe friction."""
    score = 0
    score += 30 if config_missing else 0
    score += 35 if video_missing else 0
    score += 45 if frame_load_failed else 0
    score += 15 if calibration_points_missing else 0
    score += 15 if placeholder_points_detected else 0
    score += 20 if invalid_points else 0
    score += 20 if point_order_suspicious else 0
    score += 35 if polygon_self_intersects else 0
    score += 25 if geometrically_invalid else 0
    score += 20 if homography_failed else 0
    score += min(errors_count * 10, 30)
    score += min(warnings_count * 3, 15)
    score = max(0, min(score, 100))

    return {
        "score": score,
        "band": friction_band(score),
        "inputs": {
            "config_missing": config_missing,
            "video_missing": video_missing,
            "frame_load_failed": frame_load_failed,
            "calibration_points_missing": calibration_points_missing,
            "placeholder_points_detected": placeholder_points_detected,
            "invalid_points": invalid_points,
            "point_order_suspicious": point_order_suspicious,
            "polygon_self_intersects": polygon_self_intersects,
            "geometrically_invalid": geometrically_invalid,
            "homography_failed": homography_failed,
            "errors_count": errors_count,
            "warnings_count": warnings_count,
        },
    }


def calculate_stage_3_1_friction_score(
    *,
    image_missing: bool = False,
    grid_generation_failed: bool = False,
    interactive_unavailable: bool = False,
    no_points_selected: bool = False,
    invalid_points: bool = False,
    point_order_suspicious: bool = False,
    polygon_self_intersects: bool = False,
    config_update_failed: bool = False,
    errors_count: int = 0,
    warnings_count: int = 0,
) -> dict[str, Any]:
    """Calculate Stage 3.1 court point selection helper friction."""
    score = 0
    score += 45 if image_missing else 0
    score += 35 if grid_generation_failed else 0
    score += 10 if interactive_unavailable else 0
    score += 12 if no_points_selected else 0
    score += 20 if invalid_points else 0
    score += 20 if point_order_suspicious else 0
    score += 35 if polygon_self_intersects else 0
    score += 25 if config_update_failed else 0
    score += min(errors_count * 10, 30)
    score += min(warnings_count * 3, 15)
    score = max(0, min(score, 100))

    return {
        "score": score,
        "band": friction_band(score),
        "inputs": {
            "image_missing": image_missing,
            "grid_generation_failed": grid_generation_failed,
            "interactive_unavailable": interactive_unavailable,
            "no_points_selected": no_points_selected,
            "invalid_points": invalid_points,
            "point_order_suspicious": point_order_suspicious,
            "polygon_self_intersects": polygon_self_intersects,
            "config_update_failed": config_update_failed,
            "errors_count": errors_count,
            "warnings_count": warnings_count,
        },
    }


def calculate_stage_4_friction_score(
    *,
    video_missing: bool = False,
    video_open_failed: bool = False,
    no_frames_processed: bool = False,
    no_ball_candidates: bool = False,
    too_many_false_candidates: bool = False,
    yolo_too_slow: bool = False,
    errors_count: int = 0,
    warnings_count: int = 0,
    manual_action_required: bool = False,
) -> dict[str, Any]:
    """Calculate Stage 4 ball tracking probe friction."""
    score = 0
    score += 35 if video_missing else 0
    score += 40 if video_open_failed else 0
    score += 40 if no_frames_processed else 0
    score += 25 if no_ball_candidates else 0
    score += 18 if too_many_false_candidates else 0
    score += 15 if yolo_too_slow else 0
    score += min(errors_count * 10, 30)
    score += min(warnings_count * 3, 15)
    score += 20 if manual_action_required else 0
    score = max(0, min(score, 100))

    return {
        "score": score,
        "band": friction_band(score),
        "inputs": {
            "video_missing": video_missing,
            "video_open_failed": video_open_failed,
            "no_frames_processed": no_frames_processed,
            "no_ball_candidates": no_ball_candidates,
            "too_many_false_candidates": too_many_false_candidates,
            "yolo_too_slow": yolo_too_slow,
            "errors_count": errors_count,
            "warnings_count": warnings_count,
            "manual_action_required": manual_action_required,
        },
    }


def calculate_stage_4_1_friction_score(
    *,
    video_missing: bool = False,
    frames_cannot_load: bool = False,
    no_frames_shown: bool = False,
    no_labels_saved: bool = False,
    candidate_comparison_missing: bool = False,
    errors_count: int = 0,
    warnings_count: int = 0,
) -> dict[str, Any]:
    """Calculate Stage 4.1 manual ball labeling helper friction."""
    score = 0
    score += 35 if video_missing else 0
    score += 45 if frames_cannot_load else 0
    score += 35 if no_frames_shown else 0
    score += 15 if no_labels_saved else 0
    score += 8 if candidate_comparison_missing else 0
    score += min(errors_count * 10, 30)
    score += min(warnings_count * 3, 15)
    score = max(0, min(score, 100))

    return {
        "score": score,
        "band": friction_band(score),
        "inputs": {
            "video_missing": video_missing,
            "frames_cannot_load": frames_cannot_load,
            "no_frames_shown": no_frames_shown,
            "no_labels_saved": no_labels_saved,
            "candidate_comparison_missing": candidate_comparison_missing,
            "errors_count": errors_count,
            "warnings_count": warnings_count,
        },
    }


def calculate_stage_5_friction_score(
    *,
    candidate_csv_missing: bool = False,
    manual_labels_missing: bool = False,
    homography_missing: bool = False,
    comparison_failed: bool = False,
    filtering_failed: bool = False,
    projection_failed: bool = False,
    nearest_candidates_too_far: bool = False,
    too_many_false_candidates: bool = False,
    errors_count: int = 0,
    warnings_count: int = 0,
) -> dict[str, Any]:
    """Calculate Stage 5 filtering and court projection friction."""
    score = 0
    score += 40 if candidate_csv_missing else 0
    score += 45 if manual_labels_missing else 0
    score += 15 if homography_missing else 0
    score += 30 if comparison_failed else 0
    score += 35 if filtering_failed else 0
    score += 15 if projection_failed else 0
    score += 25 if nearest_candidates_too_far else 0
    score += 18 if too_many_false_candidates else 0
    score += min(errors_count * 10, 30)
    score += min(warnings_count * 3, 15)
    score = max(0, min(score, 100))

    return {
        "score": score,
        "band": friction_band(score),
        "inputs": {
            "candidate_csv_missing": candidate_csv_missing,
            "manual_labels_missing": manual_labels_missing,
            "homography_missing": homography_missing,
            "comparison_failed": comparison_failed,
            "filtering_failed": filtering_failed,
            "projection_failed": projection_failed,
            "nearest_candidates_too_far": nearest_candidates_too_far,
            "too_many_false_candidates": too_many_false_candidates,
            "errors_count": errors_count,
            "warnings_count": warnings_count,
        },
    }


def calculate_stage_5_1_friction_score(
    *,
    video_missing: bool = False,
    manual_labels_missing: bool = False,
    frame_load_failed: bool = False,
    no_candidates_generated: bool = False,
    no_improvement: bool = False,
    candidates_still_far: bool = False,
    projection_failed: bool = False,
    errors_count: int = 0,
    warnings_count: int = 0,
) -> dict[str, Any]:
    """Calculate Stage 5.1 candidate generation improvement friction."""
    score = 0
    score += 35 if video_missing else 0
    score += 45 if manual_labels_missing else 0
    score += 40 if frame_load_failed else 0
    score += 35 if no_candidates_generated else 0
    score += 25 if no_improvement else 0
    score += 20 if candidates_still_far else 0
    score += 10 if projection_failed else 0
    score += min(errors_count * 10, 30)
    score += min(warnings_count * 3, 15)
    score = max(0, min(score, 100))

    return {
        "score": score,
        "band": friction_band(score),
        "inputs": {
            "video_missing": video_missing,
            "manual_labels_missing": manual_labels_missing,
            "frame_load_failed": frame_load_failed,
            "no_candidates_generated": no_candidates_generated,
            "no_improvement": no_improvement,
            "candidates_still_far": candidates_still_far,
            "projection_failed": projection_failed,
            "errors_count": errors_count,
            "warnings_count": warnings_count,
        },
    }


def calculate_stage_6_friction_score(
    *,
    improved_candidates_missing: bool = False,
    projected_candidates_missing: bool = False,
    too_few_points: bool = False,
    smoothing_failed: bool = False,
    event_detection_unreliable: bool = False,
    projection_preview_failed: bool = False,
    errors_count: int = 0,
    warnings_count: int = 0,
) -> dict[str, Any]:
    """Calculate Stage 6 trajectory smoothing friction."""
    score = 0
    score += 45 if improved_candidates_missing else 0
    score += 10 if projected_candidates_missing else 0
    score += 25 if too_few_points else 0
    score += 35 if smoothing_failed else 0
    score += 15 if event_detection_unreliable else 0
    score += 8 if projection_preview_failed else 0
    score += min(errors_count * 10, 30)
    score += min(warnings_count * 3, 15)
    score = max(0, min(score, 100))

    return {
        "score": score,
        "band": friction_band(score),
        "inputs": {
            "improved_candidates_missing": improved_candidates_missing,
            "projected_candidates_missing": projected_candidates_missing,
            "too_few_points": too_few_points,
            "smoothing_failed": smoothing_failed,
            "event_detection_unreliable": event_detection_unreliable,
            "projection_preview_failed": projection_preview_failed,
            "errors_count": errors_count,
            "warnings_count": warnings_count,
        },
    }


def calculate_stage_7_friction_score(
    *,
    smoothed_trajectory_missing: bool = False,
    video_missing: bool = False,
    yolo_model_load_failed: bool = False,
    no_player_detections: bool = False,
    tracking_unreliable: bool = False,
    no_ball_player_associations: bool = False,
    too_few_ball_points: bool = False,
    visualization_failed: bool = False,
    errors_count: int = 0,
    warnings_count: int = 0,
) -> dict[str, Any]:
    """Calculate Stage 7 player interaction friction."""
    score = 0
    score += 45 if smoothed_trajectory_missing else 0
    score += 35 if video_missing else 0
    score += 35 if yolo_model_load_failed else 0
    score += 30 if no_player_detections else 0
    score += 15 if tracking_unreliable else 0
    score += 25 if no_ball_player_associations else 0
    score += 18 if too_few_ball_points else 0
    score += 8 if visualization_failed else 0
    score += min(errors_count * 10, 30)
    score += min(warnings_count * 3, 15)
    score = max(0, min(score, 100))

    return {
        "score": score,
        "band": friction_band(score),
        "inputs": {
            "smoothed_trajectory_missing": smoothed_trajectory_missing,
            "video_missing": video_missing,
            "yolo_model_load_failed": yolo_model_load_failed,
            "no_player_detections": no_player_detections,
            "tracking_unreliable": tracking_unreliable,
            "no_ball_player_associations": no_ball_player_associations,
            "too_few_ball_points": too_few_ball_points,
            "visualization_failed": visualization_failed,
            "errors_count": errors_count,
            "warnings_count": warnings_count,
        },
    }


def calculate_stage_7_1_friction_score(
    *,
    detections_missing: bool = False,
    tracks_missing: bool = False,
    video_missing: bool = False,
    calibration_missing: bool = False,
    no_main_players_selected: bool = False,
    too_many_unknown_tracks: bool = False,
    identity_profiles_failed: bool = False,
    refined_association_failed: bool = False,
    visualization_failed: bool = False,
    errors_count: int = 0,
    warnings_count: int = 0,
) -> dict[str, Any]:
    """Calculate Stage 7.1 filtering and identity friction."""
    score = 0
    score += 35 if detections_missing else 0
    score += 45 if tracks_missing else 0
    score += 35 if video_missing else 0
    score += 10 if calibration_missing else 0
    score += 40 if no_main_players_selected else 0
    score += 12 if too_many_unknown_tracks else 0
    score += 18 if identity_profiles_failed else 0
    score += 15 if refined_association_failed else 0
    score += 8 if visualization_failed else 0
    score += min(errors_count * 10, 30)
    score += min(warnings_count * 3, 15)
    score = max(0, min(score, 100))

    return {
        "score": score,
        "band": friction_band(score),
        "inputs": {
            "detections_missing": detections_missing,
            "tracks_missing": tracks_missing,
            "video_missing": video_missing,
            "calibration_missing": calibration_missing,
            "no_main_players_selected": no_main_players_selected,
            "too_many_unknown_tracks": too_many_unknown_tracks,
            "identity_profiles_failed": identity_profiles_failed,
            "refined_association_failed": refined_association_failed,
            "visualization_failed": visualization_failed,
            "errors_count": errors_count,
            "warnings_count": warnings_count,
        },
    }


def calculate_stage_8_friction_score(
    *,
    trajectory_missing: bool = False,
    source_events_missing: bool = False,
    player_identity_missing: bool = False,
    no_timeline_events: bool = False,
    no_rally_segments: bool = False,
    player_attribution_failed: bool = False,
    visual_generation_failed: bool = False,
    too_few_points: bool = False,
    errors_count: int = 0,
    warnings_count: int = 0,
) -> dict[str, Any]:
    """Calculate Stage 8 event timeline and rally segmentation friction."""
    score = 0
    score += 45 if trajectory_missing else 0
    score += 10 if source_events_missing else 0
    score += 10 if player_identity_missing else 0
    score += 40 if no_timeline_events else 0
    score += 30 if no_rally_segments else 0
    score += 12 if player_attribution_failed else 0
    score += 8 if visual_generation_failed else 0
    score += 12 if too_few_points else 0
    score += min(errors_count * 10, 30)
    score += min(warnings_count * 3, 15)
    score = max(0, min(score, 100))

    return {
        "score": score,
        "band": friction_band(score),
        "inputs": {
            "trajectory_missing": trajectory_missing,
            "source_events_missing": source_events_missing,
            "player_identity_missing": player_identity_missing,
            "no_timeline_events": no_timeline_events,
            "no_rally_segments": no_rally_segments,
            "player_attribution_failed": player_attribution_failed,
            "visual_generation_failed": visual_generation_failed,
            "too_few_points": too_few_points,
            "errors_count": errors_count,
            "warnings_count": warnings_count,
        },
    }


def calculate_stage_8_1_friction_score(
    *,
    labels_missing: bool = False,
    timeline_missing: bool = False,
    candidate_validation_failed: bool = False,
    sparse_label_coverage: bool = False,
    event_validation_unsupported: bool = False,
    manual_action_required: bool = False,
    errors_count: int = 0,
    warnings_count: int = 0,
) -> dict[str, Any]:
    """Calculate Stage 8.1 label expansion and timeline validation friction."""
    score = 0
    score += 45 if labels_missing else 0
    score += 45 if timeline_missing else 0
    score += 25 if candidate_validation_failed else 0
    score += 18 if sparse_label_coverage else 0
    score += 18 if event_validation_unsupported else 0
    score += 8 if manual_action_required else 0
    score += min(errors_count * 10, 30)
    score += min(warnings_count * 3, 15)
    score = max(0, min(score, 100))

    return {
        "score": score,
        "band": friction_band(score),
        "inputs": {
            "labels_missing": labels_missing,
            "timeline_missing": timeline_missing,
            "candidate_validation_failed": candidate_validation_failed,
            "sparse_label_coverage": sparse_label_coverage,
            "event_validation_unsupported": event_validation_unsupported,
            "manual_action_required": manual_action_required,
            "errors_count": errors_count,
            "warnings_count": warnings_count,
        },
    }


def calculate_stage_9_friction_score(
    *,
    validated_timeline_missing: bool = False,
    projected_points_missing: bool = False,
    too_few_ball_points: bool = False,
    zone_assignment_failed: bool = False,
    too_many_unknown_zones: bool = False,
    direction_estimation_unreliable: bool = False,
    rally_summary_failed: bool = False,
    visual_generation_failed: bool = False,
    errors_count: int = 0,
    warnings_count: int = 0,
) -> dict[str, Any]:
    """Calculate Stage 9 tactical metrics friction."""
    score = 0
    score += 45 if validated_timeline_missing else 0
    score += 30 if projected_points_missing else 0
    score += 18 if too_few_ball_points else 0
    score += 35 if zone_assignment_failed else 0
    score += 12 if too_many_unknown_zones else 0
    score += 10 if direction_estimation_unreliable else 0
    score += 25 if rally_summary_failed else 0
    score += 8 if visual_generation_failed else 0
    score += min(errors_count * 10, 30)
    score += min(warnings_count * 3, 15)
    score = max(0, min(score, 100))

    return {
        "score": score,
        "band": friction_band(score),
        "inputs": {
            "validated_timeline_missing": validated_timeline_missing,
            "projected_points_missing": projected_points_missing,
            "too_few_ball_points": too_few_ball_points,
            "zone_assignment_failed": zone_assignment_failed,
            "too_many_unknown_zones": too_many_unknown_zones,
            "direction_estimation_unreliable": direction_estimation_unreliable,
            "rally_summary_failed": rally_summary_failed,
            "visual_generation_failed": visual_generation_failed,
            "errors_count": errors_count,
            "warnings_count": warnings_count,
        },
    }


def calculate_stage_9_1_friction_score(
    *,
    expanded_labels_missing: bool = False,
    homography_missing: bool = False,
    projection_failed: bool = False,
    many_out_of_bounds_points: bool = False,
    unknown_zones_not_reduced: bool = False,
    visual_generation_failed: bool = False,
    warnings_count: int = 0,
    errors_count: int = 0,
) -> dict[str, Any]:
    """Calculate Stage 9.1 projection coverage and zone tuning friction."""
    score = 0
    score += 45 if expanded_labels_missing else 0
    score += 45 if homography_missing else 0
    score += 30 if projection_failed else 0
    score += 15 if many_out_of_bounds_points else 0
    score += 25 if unknown_zones_not_reduced else 0
    score += 8 if visual_generation_failed else 0
    score += min(warnings_count * 3, 15)
    score += min(errors_count * 10, 30)
    score = max(0, min(score, 100))

    return {
        "score": score,
        "band": friction_band(score),
        "inputs": {
            "expanded_labels_missing": expanded_labels_missing,
            "homography_missing": homography_missing,
            "projection_failed": projection_failed,
            "many_out_of_bounds_points": many_out_of_bounds_points,
            "unknown_zones_not_reduced": unknown_zones_not_reduced,
            "visual_generation_failed": visual_generation_failed,
            "warnings_count": warnings_count,
            "errors_count": errors_count,
        },
    }
