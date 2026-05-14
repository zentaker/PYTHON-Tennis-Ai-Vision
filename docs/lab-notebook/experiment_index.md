# Experiment Index

This index is designed to be readable in plain text.
Each stage is listed as a short block instead of a wide Markdown table.

STAGE: Stage 0
NAME: Environment
VERDICT: ready_with_warnings
FRICTION: 15 low friction
MAIN OUTPUT: outputs/reports/environment_report.md
NEXT STEP: Proceed to Stage 1 video loading and frame extraction.

---

STAGE: Stage 1
NAME: Video Probe
VERDICT: ready_for_stage_2
FRICTION: 0 low friction
MAIN OUTPUT: outputs/reports/stage_1_video_probe_report.md
NEXT STEP: Proceed to Stage 2 YOLO CPU baseline.

---

STAGE: Stage 2
NAME: YOLO CPU Baseline
VERDICT: ready_for_stage_3
FRICTION: 0 low friction
MAIN OUTPUT: outputs/reports/stage_2_yolo_cpu_baseline_report.md
NEXT STEP: Proceed to Stage 3: Court Calibration Probe.

---

STAGE: Stage 3
NAME: Court Calibration Probe
VERDICT: ready_for_stage_4
FRICTION: 0 low friction
MAIN OUTPUT: outputs/reports/stage_3_court_calibration_probe_report.md
NEXT STEP: Proceed to Stage 4: Ball Tracking Probe.

---

STAGE: Stage 3.1
NAME: Court Point Selection Helper
VERDICT: ready_to_rerun_stage_3
FRICTION: 0 low friction
MAIN OUTPUT: outputs/reports/stage_3_1_court_point_selector_report.md
NEXT STEP: Rerun Stage 3 to compute the court homography from the saved point coordinates.

---

STAGE: Stage 4
NAME: Ball Tracking Probe
VERDICT: ready_with_warnings
FRICTION: 21 medium friction
MAIN OUTPUT: outputs/reports/stage_4_ball_tracking_probe_report.md
NEXT STEP: Proceed to Stage 5: Ball Candidate Filtering and Court Projection.

---

STAGE: Stage 4.1
NAME: Manual Ball Labeling Helper
VERDICT: ready_for_stage_5
FRICTION: 0 low friction
MAIN OUTPUT: outputs/reports/stage_4_1_ball_labeling_helper_report.md
NEXT STEP: Proceed to Stage 5: Ball Candidate Filtering and Court Projection.

---

STAGE: Stage 5
NAME: Ball Candidate Filtering
VERDICT: ready_with_warnings
FRICTION: 21 medium friction
MAIN OUTPUT: outputs/reports/stage_5_ball_candidate_filtering_report.md
NEXT STEP: Review Stage 5 warnings, then decide between Stage 6 smoothing or Stage 5.1 detector improvement.

---

STAGE: Stage 5.1
NAME: Candidate Improvement
VERDICT: ready_for_stage_6
FRICTION: 0 low friction
MAIN OUTPUT: outputs/reports/stage_5_1_candidate_improvement_report.md
NEXT STEP: Proceed to Stage 6: trajectory smoothing and rally/event segmentation probe.

---

STAGE: Stage 6
NAME: Trajectory Smoothing
VERDICT: ready_for_stage_7
FRICTION: 3 low friction
MAIN OUTPUT: outputs/reports/stage_6_trajectory_smoothing_report.md
NEXT STEP: Proceed to Stage 7: player tracking and ball-player interaction probe.

---

STAGE: Stage 7
NAME: Player Interaction Probe
VERDICT: ready_with_warnings
FRICTION: 21 medium friction
MAIN OUTPUT: outputs/reports/stage_7_player_interaction_probe_report.md
NEXT STEP: Review hypotheses, then choose Stage 7.1 for more labels or Stage 8 for a cautious timeline prototype.

---

STAGE: Stage 7.1
NAME: Player Filtering
VERDICT: ready_with_warnings
FRICTION: 15 low friction
MAIN OUTPUT: outputs/reports/stage_7_1_player_filtering_report.md
NEXT STEP: Review filtered identities; proceed to Stage 8 cautiously or Stage 7.2 if identity confidence is not sufficient.

---

STAGE: Stage 8
NAME: Event Timeline
VERDICT: ready_with_warnings
FRICTION: 15 low friction
MAIN OUTPUT: outputs/reports/stage_8_event_timeline_report.md
NEXT STEP: Proceed to Stage 8.1: expand labels and timeline validation before tactical metrics.

---

STAGE: Stage 8.1
NAME: Timeline Validation
VERDICT: ready_for_stage_9
FRICTION: 0 low friction
MAIN OUTPUT: outputs/reports/stage_8_1_timeline_validation_report.md
NEXT STEP: Proceed to Stage 9: Tactical Metrics and Shot Zone Prototype.

---

STAGE: Stage 9
NAME: Tactical Metrics
VERDICT: ready_with_warnings
FRICTION: 15 low friction
MAIN OUTPUT: outputs/reports/stage_9_tactical_metrics_report.md
NEXT STEP: Proceed cautiously to Stage 9.1 court zone tuning or validate more events before Stage 10.

---

STAGE: Stage 9.1
NAME: Projection Coverage
VERDICT: ready_for_stage_10
FRICTION: 0 low friction
MAIN OUTPUT: outputs/reports/stage_9_1_projection_coverage_report.md
NEXT STEP: Proceed to Stage 10: Analytical Report Generator and Coaching Summary Prototype.

---

STAGE: Stage 10
NAME: Analytical Report
VERDICT: ready_for_stage_11
FRICTION: 0 low friction
MAIN OUTPUT: outputs/reports_final/stage_10_analytical_report/analytical_report.md
NEXT STEP: Proceed to Stage 11: Annotated Highlight/Report Package Generator.

---

STAGE: Stage 11
NAME: Report Package
VERDICT: ready_for_stage_12
FRICTION: 0 low friction
MAIN OUTPUT: outputs/report_packages/stage_11_report_package/README.md
NEXT STEP: Proceed to Stage 12: Synthetic Rally Replay Data Schema.

---

STAGE: Stage 12
NAME: Replay Schema
VERDICT: ready_for_stage_13
FRICTION: 0 low friction
MAIN OUTPUT: outputs/replay/stage_12_replay_schema/replay_schema.json
NEXT STEP: Proceed to Stage 13: 2D Tactical Replay Renderer.

---

STAGE: Stage 13
NAME: 2D Tactical Replay
VERDICT: ready_for_stage_14
FRICTION: 0 low friction
MAIN OUTPUT: outputs/replay/stage_13_2d_tactical_replay/tactical_replay_contact_sheet.jpg
NEXT STEP: Proceed to Stage 14: Side-View Ball Flight Renderer.

---

STAGE: Stage 14
NAME: Side-View Replay
VERDICT: ready_for_stage_15
FRICTION: 0 low friction
MAIN OUTPUT: outputs/replay/stage_14_side_view_replay/side_view_arc_preview.jpg
NEXT STEP: Proceed to Stage 15: Multi-Camera Analytical Replay.

---

STAGE: Stage 14.1
NAME: Side-View Patch
VERDICT: ready_for_stage_15
FRICTION: 0 low friction
MAIN OUTPUT: outputs/replay/stage_14_side_view_replay/side_view_semantic_debug.jpg
NEXT STEP: Proceed to Stage 15: Multi-Camera Analytical Replay.

---

