# Experiment Index

| Stage | Name | Verdict | Friction | Main output | Next step |
|---|---|---|---|---|---|
| Stage 0 | Environment | ready_with_warnings | 15 low friction | outputs/reports/environment_report.md | Proceed to Stage 1 video loading and frame extraction. |
| Stage 1 | Video Probe | ready_for_stage_2 | 0 low friction | outputs/reports/stage_1_video_probe_report.md | Proceed to Stage 2 YOLO CPU baseline. |
| Stage 2 | YOLO CPU Baseline | ready_for_stage_3 | 0 low friction | outputs/reports/stage_2_yolo_cpu_baseline_report.md | Proceed to Stage 3: Court Calibration Probe. |
| Stage 3 | Court Calibration Probe | ready_for_stage_4 | 0 low friction | outputs/reports/stage_3_court_calibration_probe_report.md | Proceed to Stage 4: Ball Tracking Probe. |
| Stage 3.1 | Court Point Selection Helper | ready_to_rerun_stage_3 | 0 low friction | outputs/reports/stage_3_1_court_point_selector_report.md | Rerun Stage 3 to compute the court homography from the saved point coordinates. |
| Stage 4 | Ball Tracking Probe | ready_with_warnings | 21 medium friction | outputs/reports/stage_4_ball_tracking_probe_report.md | Proceed to Stage 5: Ball Candidate Filtering and Court Projection. |
| Stage 4.1 | Manual Ball Labeling Helper | ready_for_stage_5 | 0 low friction | outputs/reports/stage_4_1_ball_labeling_helper_report.md | Proceed to Stage 5: Ball Candidate Filtering and Court Projection. |
| Stage 5 | Ball Candidate Filtering | ready_with_warnings | 21 medium friction | outputs/reports/stage_5_ball_candidate_filtering_report.md | Review Stage 5 warnings, then decide between Stage 6 smoothing or Stage 5.1 detector improvement. |
| Stage 5.1 | Candidate Improvement | ready_for_stage_6 | 0 low friction | outputs/reports/stage_5_1_candidate_improvement_report.md | Proceed to Stage 6: trajectory smoothing and rally/event segmentation probe. |
| Stage 6 | Trajectory Smoothing | ready_for_stage_7 | 3 low friction | outputs/reports/stage_6_trajectory_smoothing_report.md | Proceed to Stage 7: player tracking and ball-player interaction probe. |
| Stage 7 | Player Interaction Probe | ready_with_warnings | 21 medium friction | outputs/reports/stage_7_player_interaction_probe_report.md | Review hypotheses, then choose Stage 7.1 for more labels or Stage 8 for a cautious timeline prototype. |
| Stage 7.1 | Player Filtering | ready_with_warnings | 15 low friction | outputs/reports/stage_7_1_player_filtering_report.md | Review filtered identities; proceed to Stage 8 cautiously or Stage 7.2 if identity confidence is not sufficient. |
| Stage 8 | Event Timeline | ready_with_warnings | 15 low friction | outputs/reports/stage_8_event_timeline_report.md | Proceed to Stage 8.1: expand labels and timeline validation before tactical metrics. |
| Stage 8.1 | Timeline Validation | needs_more_labels | 32 medium friction | outputs/reports/stage_8_1_timeline_validation_report.md | Run Stage 8.1 interactively across more frames, then rerun timeline validation. |
