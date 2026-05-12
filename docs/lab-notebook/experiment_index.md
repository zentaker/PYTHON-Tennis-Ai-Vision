# Experiment Index

| Stage | Name | Verdict | Friction | Main output | Next step |
|---|---|---|---|---|---|
| Stage 0 | Environment | ready_with_warnings | 15 low friction | outputs/reports/environment_report.md | Proceed to Stage 1 video loading and frame extraction. |
| Stage 1 | Video Probe | ready_for_stage_2 | 0 low friction | outputs/reports/stage_1_video_probe_report.md | Proceed to Stage 2 YOLO CPU baseline. |
| Stage 2 | YOLO CPU Baseline | ready_for_stage_3 | 0 low friction | outputs/reports/stage_2_yolo_cpu_baseline_report.md | Proceed to Stage 3: Court Calibration Probe. |
| Stage 3 | Court Calibration Probe | ready_for_stage_4 | 0 low friction | outputs/reports/stage_3_court_calibration_probe_report.md | Proceed to Stage 4: Ball Tracking Probe. |
| Stage 3.1 | Court Point Selection Helper | ready_to_rerun_stage_3 | 0 low friction | outputs/reports/stage_3_1_court_point_selector_report.md | Rerun Stage 3 to compute the court homography from the saved point coordinates. |
| Stage 4 | Ball Tracking Probe | ready_with_warnings | 21 medium friction | outputs/reports/stage_4_ball_tracking_probe_report.md | Proceed to Stage 5: Ball Candidate Filtering and Court Projection. |
