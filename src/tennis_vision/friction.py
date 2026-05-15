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


def calculate_stage_8_2_friction_score(
    *,
    video_missing: bool = False,
    no_frames_loaded: bool = False,
    no_event_labels: bool = False,
    no_bounce_or_hit_labels: bool = False,
    comparison_failed: bool = False,
    label_persistence_failed: bool = False,
    manual_action_required: bool = False,
    errors_count: int = 0,
    warnings_count: int = 0,
) -> dict[str, Any]:
    """Calculate Stage 8.2 manual event labeling friction."""
    score = 0
    score += 45 if video_missing else 0
    score += 35 if no_frames_loaded else 0
    score += 25 if no_event_labels else 0
    score += 20 if no_bounce_or_hit_labels else 0
    score += 15 if comparison_failed else 0
    score += 30 if label_persistence_failed else 0
    score += 8 if manual_action_required else 0
    score += min(errors_count * 10, 30)
    score += min(warnings_count * 3, 15)
    score = max(0, min(score, 100))

    return {
        "score": score,
        "band": friction_band(score),
        "inputs": {
            "video_missing": video_missing,
            "no_frames_loaded": no_frames_loaded,
            "no_event_labels": no_event_labels,
            "no_bounce_or_hit_labels": no_bounce_or_hit_labels,
            "comparison_failed": comparison_failed,
            "label_persistence_failed": label_persistence_failed,
            "manual_action_required": manual_action_required,
            "errors_count": errors_count,
            "warnings_count": warnings_count,
        },
    }


def calculate_stage_8_3_friction_score(
    *,
    manual_labels_missing: bool = False,
    no_bounce_or_hit_labels: bool = False,
    no_hit_labels: bool = False,
    many_auto_events_unvalidated: bool = False,
    validation_output_failed: bool = False,
    preview_generation_failed: bool = False,
    errors_count: int = 0,
    warnings_count: int = 0,
) -> dict[str, Any]:
    """Calculate Stage 8.3 event validation and reclassification friction."""
    score = 0
    score += 45 if manual_labels_missing else 0
    score += 30 if no_bounce_or_hit_labels else 0
    score += 10 if no_hit_labels else 0
    score += 15 if many_auto_events_unvalidated else 0
    score += 35 if validation_output_failed else 0
    score += 8 if preview_generation_failed else 0
    score += min(errors_count * 10, 30)
    score += min(warnings_count * 3, 15)
    score = max(0, min(score, 100))

    return {
        "score": score,
        "band": friction_band(score),
        "inputs": {
            "manual_labels_missing": manual_labels_missing,
            "no_bounce_or_hit_labels": no_bounce_or_hit_labels,
            "no_hit_labels": no_hit_labels,
            "many_auto_events_unvalidated": many_auto_events_unvalidated,
            "validation_output_failed": validation_output_failed,
            "preview_generation_failed": preview_generation_failed,
            "errors_count": errors_count,
            "warnings_count": warnings_count,
        },
    }


def calculate_stage_8_4_friction_score(
    *,
    manual_bounce_missing: bool = False,
    only_one_bounce_window: bool = False,
    trajectory_missing: bool = False,
    no_candidates_found: bool = False,
    review_queue_failed: bool = False,
    preview_generation_failed: bool = False,
    errors_count: int = 0,
    warnings_count: int = 0,
) -> dict[str, Any]:
    """Calculate Stage 8.4 bounce candidate propagation friction."""
    score = 0
    score += 40 if manual_bounce_missing else 0
    score += 10 if only_one_bounce_window else 0
    score += 45 if trajectory_missing else 0
    score += 15 if no_candidates_found else 0
    score += 25 if review_queue_failed else 0
    score += 8 if preview_generation_failed else 0
    score += min(errors_count * 10, 30)
    score += min(warnings_count * 2, 12)
    score = max(0, min(score, 100))

    return {
        "score": score,
        "band": friction_band(score),
        "inputs": {
            "manual_bounce_missing": manual_bounce_missing,
            "only_one_bounce_window": only_one_bounce_window,
            "trajectory_missing": trajectory_missing,
            "no_candidates_found": no_candidates_found,
            "review_queue_failed": review_queue_failed,
            "preview_generation_failed": preview_generation_failed,
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


def calculate_stage_10_friction_score(
    *,
    tactical_data_missing: bool = False,
    report_generation_failed: bool = False,
    coaching_summary_failed: bool = False,
    low_confidence: bool = False,
    sparse_data: bool = False,
    missing_player_context: bool = False,
    missing_event_context: bool = False,
    errors_count: int = 0,
    warnings_count: int = 0,
) -> dict[str, Any]:
    """Calculate Stage 10 analytical report friction."""
    score = 0
    score += 45 if tactical_data_missing else 0
    score += 35 if report_generation_failed else 0
    score += 25 if coaching_summary_failed else 0
    score += 20 if low_confidence else 0
    score += 15 if sparse_data else 0
    score += 8 if missing_player_context else 0
    score += 8 if missing_event_context else 0
    score += min(warnings_count * 3, 15)
    score += min(errors_count * 10, 30)
    score = max(0, min(score, 100))

    return {
        "score": score,
        "band": friction_band(score),
        "inputs": {
            "tactical_data_missing": tactical_data_missing,
            "report_generation_failed": report_generation_failed,
            "coaching_summary_failed": coaching_summary_failed,
            "low_confidence": low_confidence,
            "sparse_data": sparse_data,
            "missing_player_context": missing_player_context,
            "missing_event_context": missing_event_context,
            "warnings_count": warnings_count,
            "errors_count": errors_count,
        },
    }


def calculate_stage_11_friction_score(
    *,
    analytical_report_missing: bool = False,
    coaching_summary_missing: bool = False,
    key_findings_missing: bool = False,
    package_manifest_failed: bool = False,
    missing_core_artifacts: bool = False,
    many_optional_artifacts_missing: bool = False,
    copy_failures: bool = False,
    warnings_count: int = 0,
    errors_count: int = 0,
) -> dict[str, Any]:
    """Calculate Stage 11 report package friction."""
    score = 0
    score += 45 if analytical_report_missing else 0
    score += 35 if coaching_summary_missing else 0
    score += 20 if key_findings_missing else 0
    score += 35 if package_manifest_failed else 0
    score += 40 if missing_core_artifacts else 0
    score += 10 if many_optional_artifacts_missing else 0
    score += 15 if copy_failures else 0
    score += min(warnings_count * 2, 12)
    score += min(errors_count * 10, 30)
    score = max(0, min(score, 100))

    return {
        "score": score,
        "band": friction_band(score),
        "inputs": {
            "analytical_report_missing": analytical_report_missing,
            "coaching_summary_missing": coaching_summary_missing,
            "key_findings_missing": key_findings_missing,
            "package_manifest_failed": package_manifest_failed,
            "missing_core_artifacts": missing_core_artifacts,
            "many_optional_artifacts_missing": many_optional_artifacts_missing,
            "copy_failures": copy_failures,
            "warnings_count": warnings_count,
            "errors_count": errors_count,
        },
    }


def calculate_stage_12_friction_score(
    *,
    stage11_manifest_missing: bool = False,
    court_model_missing: bool = False,
    ball_trajectory_missing: bool = False,
    player_data_missing: bool = False,
    event_timeline_missing: bool = False,
    camera_presets_missing: bool = False,
    schema_write_failed: bool = False,
    warnings_count: int = 0,
    errors_count: int = 0,
) -> dict[str, Any]:
    """Calculate Stage 12 replay schema friction."""
    score = 0
    score += 35 if stage11_manifest_missing else 0
    score += 35 if court_model_missing else 0
    score += 40 if ball_trajectory_missing else 0
    score += 15 if player_data_missing else 0
    score += 15 if event_timeline_missing else 0
    score += 20 if camera_presets_missing else 0
    score += 35 if schema_write_failed else 0
    score += min(warnings_count * 2, 12)
    score += min(errors_count * 10, 30)
    score = max(0, min(score, 100))

    return {
        "score": score,
        "band": friction_band(score),
        "inputs": {
            "stage11_manifest_missing": stage11_manifest_missing,
            "court_model_missing": court_model_missing,
            "ball_trajectory_missing": ball_trajectory_missing,
            "player_data_missing": player_data_missing,
            "event_timeline_missing": event_timeline_missing,
            "camera_presets_missing": camera_presets_missing,
            "schema_write_failed": schema_write_failed,
            "warnings_count": warnings_count,
            "errors_count": errors_count,
        },
    }


def calculate_stage_13_friction_score(
    *,
    replay_schema_missing: bool = False,
    court_model_missing: bool = False,
    keyframes_missing: bool = False,
    render_frames_failed: bool = False,
    video_export_failed: bool = False,
    contact_sheet_failed: bool = False,
    manifest_write_failed: bool = False,
    warnings_count: int = 0,
    errors_count: int = 0,
) -> dict[str, Any]:
    """Calculate Stage 13 2D tactical replay renderer friction."""
    score = 0
    score += 45 if replay_schema_missing else 0
    score += 35 if court_model_missing else 0
    score += 40 if keyframes_missing else 0
    score += 35 if render_frames_failed else 0
    score += 12 if video_export_failed else 0
    score += 10 if contact_sheet_failed else 0
    score += 30 if manifest_write_failed else 0
    score += min(warnings_count * 2, 12)
    score += min(errors_count * 10, 30)
    score = max(0, min(score, 100))

    return {
        "score": score,
        "band": friction_band(score),
        "inputs": {
            "replay_schema_missing": replay_schema_missing,
            "court_model_missing": court_model_missing,
            "keyframes_missing": keyframes_missing,
            "render_frames_failed": render_frames_failed,
            "video_export_failed": video_export_failed,
            "contact_sheet_failed": contact_sheet_failed,
            "manifest_write_failed": manifest_write_failed,
            "warnings_count": warnings_count,
            "errors_count": errors_count,
        },
    }


def calculate_stage_14_friction_score(
    *,
    replay_schema_missing: bool = False,
    keyframes_missing: bool = False,
    side_view_keyframes_missing: bool = False,
    render_frames_failed: bool = False,
    video_export_failed: bool = False,
    contact_sheet_failed: bool = False,
    manifest_write_failed: bool = False,
    warnings_count: int = 0,
    errors_count: int = 0,
) -> dict[str, Any]:
    """Calculate Stage 14 side-view replay renderer friction."""
    score = 0
    score += 45 if replay_schema_missing else 0
    score += 40 if keyframes_missing else 0
    score += 40 if side_view_keyframes_missing else 0
    score += 35 if render_frames_failed else 0
    score += 12 if video_export_failed else 0
    score += 10 if contact_sheet_failed else 0
    score += 30 if manifest_write_failed else 0
    score += min(warnings_count * 2, 12)
    score += min(errors_count * 10, 30)
    score = max(0, min(score, 100))

    return {
        "score": score,
        "band": friction_band(score),
        "inputs": {
            "replay_schema_missing": replay_schema_missing,
            "keyframes_missing": keyframes_missing,
            "side_view_keyframes_missing": side_view_keyframes_missing,
            "render_frames_failed": render_frames_failed,
            "video_export_failed": video_export_failed,
            "contact_sheet_failed": contact_sheet_failed,
            "manifest_write_failed": manifest_write_failed,
            "warnings_count": warnings_count,
            "errors_count": errors_count,
        },
    }


def calculate_stage_14_1_friction_score(
    *,
    replay_schema_missing: bool = False,
    side_view_source_missing: bool = False,
    bounce_grounding_failed: bool = False,
    hit_contact_band_failed: bool = False,
    semantic_debug_generation_failed: bool = False,
    render_frames_failed: bool = False,
    video_export_failed: bool = False,
    warnings_count: int = 0,
    errors_count: int = 0,
) -> dict[str, Any]:
    """Calculate Stage 14.1 side-view height semantics patch friction."""
    score = 0
    score += 45 if replay_schema_missing else 0
    score += 25 if side_view_source_missing else 0
    score += 35 if bounce_grounding_failed else 0
    score += 25 if hit_contact_band_failed else 0
    score += 20 if semantic_debug_generation_failed else 0
    score += 35 if render_frames_failed else 0
    score += 12 if video_export_failed else 0
    score += min(warnings_count * 2, 12)
    score += min(errors_count * 10, 30)
    score = max(0, min(score, 100))

    return {
        "score": score,
        "band": friction_band(score),
        "inputs": {
            "replay_schema_missing": replay_schema_missing,
            "side_view_source_missing": side_view_source_missing,
            "bounce_grounding_failed": bounce_grounding_failed,
            "hit_contact_band_failed": hit_contact_band_failed,
            "semantic_debug_generation_failed": semantic_debug_generation_failed,
            "render_frames_failed": render_frames_failed,
            "video_export_failed": video_export_failed,
            "warnings_count": warnings_count,
            "errors_count": errors_count,
        },
    }


def calculate_stage_14_2_friction_score(
    *,
    replay_schema_missing: bool = False,
    player_data_missing: bool = False,
    player_aware_hit_validation_failed: bool = False,
    implausible_hit_downgrade_failed: bool = False,
    render_role_assignment_failed: bool = False,
    semantic_debug_generation_failed: bool = False,
    render_frames_failed: bool = False,
    video_export_failed: bool = False,
    warnings_count: int = 0,
    errors_count: int = 0,
) -> dict[str, Any]:
    """Calculate Stage 14.2 side-view event disambiguation friction."""
    score = 0
    score += 45 if replay_schema_missing else 0
    score += 20 if player_data_missing else 0
    score += 30 if player_aware_hit_validation_failed else 0
    score += 30 if implausible_hit_downgrade_failed else 0
    score += 25 if render_role_assignment_failed else 0
    score += 20 if semantic_debug_generation_failed else 0
    score += 35 if render_frames_failed else 0
    score += 12 if video_export_failed else 0
    score += min(warnings_count * 2, 12)
    score += min(errors_count * 10, 30)
    score = max(0, min(score, 100))

    return {
        "score": score,
        "band": friction_band(score),
        "inputs": {
            "replay_schema_missing": replay_schema_missing,
            "player_data_missing": player_data_missing,
            "player_aware_hit_validation_failed": player_aware_hit_validation_failed,
            "implausible_hit_downgrade_failed": implausible_hit_downgrade_failed,
            "render_role_assignment_failed": render_role_assignment_failed,
            "semantic_debug_generation_failed": semantic_debug_generation_failed,
            "render_frames_failed": render_frames_failed,
            "video_export_failed": video_export_failed,
            "warnings_count": warnings_count,
            "errors_count": errors_count,
        },
    }


def calculate_stage_14_3_friction_score(
    *,
    replay_schema_missing: bool = False,
    event_source_missing: bool = False,
    validated_event_source_missing: bool = False,
    render_frames_failed: bool = False,
    video_export_failed: bool = False,
    validated_debug_generation_failed: bool = False,
    downgraded_hits_rendered_as_physical: bool = False,
    warnings_count: int = 0,
    errors_count: int = 0,
) -> dict[str, Any]:
    """Calculate Stage 14.3 validated-event side-view friction."""
    score = 0
    score += 45 if replay_schema_missing else 0
    score += 35 if event_source_missing else 0
    score += 12 if validated_event_source_missing else 0
    score += 35 if render_frames_failed else 0
    score += 12 if video_export_failed else 0
    score += 15 if validated_debug_generation_failed else 0
    score += 30 if downgraded_hits_rendered_as_physical else 0
    score += min(warnings_count * 2, 12)
    score += min(errors_count * 10, 30)
    score = max(0, min(score, 100))

    return {
        "score": score,
        "band": friction_band(score),
        "inputs": {
            "replay_schema_missing": replay_schema_missing,
            "event_source_missing": event_source_missing,
            "validated_event_source_missing": validated_event_source_missing,
            "render_frames_failed": render_frames_failed,
            "video_export_failed": video_export_failed,
            "validated_debug_generation_failed": validated_debug_generation_failed,
            "downgraded_hits_rendered_as_physical": downgraded_hits_rendered_as_physical,
            "warnings_count": warnings_count,
            "errors_count": errors_count,
        },
    }
