# Pipeline Map

This document is plain-text friendly.
It avoids wide Markdown tables so it can be read in VS Code, Notepad,
terminal previews, and raw GitHub view.

PIPELINE FLOW:

Stage 0 Environment Doctor
  -> Stage 1 Video Probe
  -> Stage 2 YOLO CPU Baseline
  -> Stage 3 Court Calibration
  -> Stage 3.1 Court Point Selection
  -> Stage 4 Ball Candidate Probe
  -> Stage 4.1 Manual Ball Labeling
  -> Stage 5 Candidate Filtering and Court Projection
  -> Stage 5.1 Candidate Generation Improvement
  -> Stage 6 Trajectory Smoothing
  -> Stage 7 Player Interaction
  -> Stage 7.1 Player Filtering and Identity
  -> Stage 8 Event Timeline
  -> Stage 8.1 Timeline Validation
  -> Stage 8.2 Manual Event Labeling
  -> Stage 8.3 Event Validation and Reclassification
  -> Stage 8.4 Bounce Candidate Propagation
  -> Stage 9 Tactical Metrics and Shot Zones
  -> Stage 9.1 Projection Coverage
  -> Stage 10 Analytical Report
  -> Stage 11 Report Package
  -> Stage 12 Replay Schema
  -> Stage 13 2D Tactical Replay
  -> Stage 14 Side-View Replay
  -> Stage 14.1 Side-View Height Semantics Patch
  -> Stage 14.2 Side-View Event Disambiguation Patch
  -> Stage 14.3 Side-View Replay with Validated Events

---

STAGE: Stage 0
NAME: Environment Doctor
STATUS: Implemented
MAIN SCRIPT: scripts/doctor.py
MAIN MODULES:
  - src/tennis_vision/environment.py
  - src/tennis_vision/report.py
  - src/tennis_vision/friction.py
READS:
  - local Python environment
  - repo folders
  - package imports
WRITES:
  - outputs/reports/environment_report.json
  - outputs/reports/environment_report.md

---

STAGE: Stage 1
NAME: Video Loading and Frame Extraction
STATUS: Implemented
MAIN SCRIPT: scripts/run_stage_1_video_probe.py
MAIN MODULES:
  - src/tennis_vision/video_io.py
  - src/tennis_vision/frame_sampler.py
READS:
  - samples/video_01.mov or supported sample video
WRITES:
  - outputs/frames/
  - outputs/reports/stage_1_video_probe_report.*

---

STAGE: Stage 2
NAME: YOLO CPU Baseline
STATUS: Implemented
MAIN SCRIPT: scripts/run_stage_2_yolo_cpu_baseline.py
MAIN MODULES:
  - src/tennis_vision/yolo_cpu.py
READS:
  - sample video
  - small YOLO model
WRITES:
  - outputs/annotated/stage_2_yolo_cpu/
  - outputs/reports/stage_2_yolo_cpu_baseline_report.*

---

STAGE: Stage 3
NAME: Court Calibration
STATUS: Implemented
MAIN SCRIPT: scripts/run_stage_3_court_calibration_probe.py
MAIN MODULES:
  - src/tennis_vision/court_calibration.py
READS:
  - configs/court_calibration_sample.json
  - sample video
WRITES:
  - outputs/calibration/stage_3_court_probe/
  - outputs/reports/stage_3_court_calibration_probe_report.*

---

STAGE: Stage 3.1
NAME: Court Point Selection
STATUS: Implemented
MAIN SCRIPT: scripts/run_stage_3_1_court_point_selector.py
MAIN MODULES:
  - src/tennis_vision/court_point_selector.py
READS:
  - Stage 3 calibration reference frame
  - calibration config
WRITES:
  - calibration grid image
  - updated config when interactive selection is used
  - Stage 3.1 reports

---

STAGE: Stage 4
NAME: Ball Candidate Probe
STATUS: Implemented
MAIN SCRIPT: scripts/run_stage_4_ball_tracking_probe.py
MAIN MODULES:
  - src/tennis_vision/ball_tracking_probe.py
READS:
  - sample video
WRITES:
  - outputs/ball_tracking/stage_4_ball_probe/
  - Stage 4 reports

---

STAGE: Stage 4.1
NAME: Manual Ball Labeling
STATUS: Implemented
MAIN SCRIPT: scripts/run_stage_4_1_ball_labeling_helper.py
MAIN MODULES:
  - src/tennis_vision/ball_labeling.py
READS:
  - sample video
  - optional Stage 4 candidate CSV
WRITES:
  - manual ball labels
  - label overlays
  - Stage 4.1 reports

---

STAGE: Stage 5
NAME: Candidate Filtering and Court Projection
STATUS: Implemented
MAIN SCRIPT: scripts/run_stage_5_ball_candidate_filtering.py
MAIN MODULES:
  - src/tennis_vision/ball_candidate_filtering.py
  - src/tennis_vision/court_projection.py
READS:
  - Stage 4 candidates
  - Stage 4.1 labels
  - Stage 3 homography
WRITES:
  - filtered candidates
  - projected candidates
  - Stage 5 reports

---

STAGE: Stage 5.1
NAME: Candidate Generation Improvement
STATUS: Implemented
MAIN SCRIPT: scripts/run_stage_5_1_candidate_improvement.py
MAIN MODULES:
  - src/tennis_vision/ball_candidate_improvement.py
READS:
  - sample video
  - manual labels
  - Stage 3 homography
WRITES:
  - improved candidates
  - strategy comparisons
  - Stage 5.1 reports

---

STAGE: Stage 6
NAME: Trajectory Smoothing
STATUS: Implemented
MAIN SCRIPT: scripts/run_stage_6_trajectory_smoothing.py
MAIN MODULES:
  - src/tennis_vision/trajectory_smoothing.py
  - src/tennis_vision/event_segmentation.py
READS:
  - Stage 5.1 improved candidates
WRITES:
  - raw trajectory
  - smoothed trajectory
  - event hypotheses
  - Stage 6 reports

---

STAGE: Stage 7
NAME: Player Interaction
STATUS: Implemented
MAIN SCRIPT: scripts/run_stage_7_player_interaction_probe.py
MAIN MODULES:
  - src/tennis_vision/player_tracking.py
  - src/tennis_vision/ball_player_interaction.py
READS:
  - sample video
  - Stage 6 trajectory
WRITES:
  - player detections
  - player tracks
  - ball-player interaction hypotheses
  - Stage 7 reports

---

STAGE: Stage 7.1
NAME: Player Filtering and Identity
STATUS: Implemented
MAIN SCRIPT: scripts/run_stage_7_1_player_filtering.py
MAIN MODULES:
  - src/tennis_vision/player_filtering.py
  - src/tennis_vision/player_identity.py
READS:
  - Stage 7 detections and tracks
  - sample video
  - Stage 3 calibration
WRITES:
  - filtered tracks
  - main player identities
  - side states
  - Stage 7.1 reports

---

STAGE: Stage 8
NAME: Event Timeline
STATUS: Implemented
MAIN SCRIPT: scripts/run_stage_8_event_timeline.py
MAIN MODULES:
  - src/tennis_vision/event_timeline.py
  - src/tennis_vision/rally_segmentation.py
READS:
  - Stage 6 trajectory/events
  - Stage 7 interactions
  - Stage 7.1 identities
WRITES:
  - event timeline
  - rally segments
  - player event attribution
  - Stage 8 reports

---

STAGE: Stage 8.1
NAME: Timeline Validation
STATUS: Implemented
MAIN SCRIPT: scripts/run_stage_8_1_expand_labels.py
MAIN MODULES:
  - src/tennis_vision/label_expansion.py
  - src/tennis_vision/timeline_validation.py
READS:
  - persisted expanded labels
  - Stage 5.1 candidates
  - Stage 8 timeline
WRITES:
  - expanded labels
  - candidate validation
  - validated event timeline
  - Stage 8.1 reports

---

STAGE: Stage 8.2
NAME: Manual Bounce / Hit Event Labeling
STATUS: Implemented
MAIN SCRIPT: scripts/run_stage_8_2_event_labeling_helper.py
MAIN MODULES:
  - src/tennis_vision/event_labeling.py
READS:
  - samples/video_01.mov
  - Stage 8.1 expanded ball labels
  - Stage 8 event timeline
  - Stage 6 trajectory events
  - Stage 7 player interactions
WRITES:
  - manual event labels
  - manual event windows
  - event label comparison
  - event label coverage
  - event label overlays
  - frame duplicate audit
  - Stage 8.2 reports
NOTES:
  - Interactive mode now supports a timeline viewer for bounce/hit labeling.
  - Timeline viewer mode sorts and deduplicates selected frames.
  - Automatic ball marker overlays are off by default so manual review is not obscured.
  - Timeline viewer mode lazy-loads frames by default for faster startup.
  - --audit-labels writes label integrity reports for stale no_event points,
    repeated points, duplicate frame labels, and missing bounce/hit points.
  - --audit-frames writes visual duplicate analysis for selected frame windows.
  - Stage 8.3 can consume user-created Stage 8.2 event windows when available.

---

STAGE: Stage 8.3
NAME: Event Validation and Reclassification
STATUS: Implemented
MAIN SCRIPT: scripts/run_stage_8_3_event_validation.py
MAIN MODULES:
  - src/tennis_vision/event_validation.py
  - src/tennis_vision/event_reclassification.py
READS:
  - Stage 8.2 manual event labels
  - Stage 8 event timeline
  - Stage 6 trajectory events
  - Stage 7 interaction hypotheses
WRITES:
  - manual event windows
  - event validation results
  - validated event timeline
  - event validation preview
  - Stage 8.3 reports

---

STAGE: Stage 8.4
NAME: Bounce Candidate Propagation
STATUS: Current
MAIN SCRIPT: scripts/run_stage_8_4_bounce_candidate_propagation.py
MAIN MODULES:
  - src/tennis_vision/bounce_pattern_features.py
  - src/tennis_vision/bounce_candidate_propagation.py
  - src/tennis_vision/friction_semantics.py
READS:
  - Stage 8.3 manual bounce windows
  - Stage 8.2 manual event labels
  - Stage 9.1 projected expanded labels
WRITES:
  - bounce candidate windows
  - bounce candidate frames
  - bounce review queue
  - proposed unvalidated bounce events
  - Stage 8.4 reports
NOTES:
  Inferred bounce candidates are review proposals only. They are not validated
  bounces and should not be rendered as physical events until manual review.
  The report separates execution friction from semantic/model, human-loop,
  product validation, and downstream correction friction.

---

STAGE: Stage 9
NAME: Tactical Metrics and Shot Zones
STATUS: Implemented
MAIN SCRIPT: scripts/run_stage_9_tactical_metrics.py
MAIN MODULES:
  - src/tennis_vision/tactical_metrics.py
  - src/tennis_vision/court_zones.py
READS:
  - validated Stage 8.1 timeline
  - expanded ball labels
  - Stage 6 smoothed trajectory
  - Stage 5.1 projected candidates
  - Stage 7.1 player associations
WRITES:
  - ball zone assignments
  - shot direction estimates
  - rally tactical summary
  - tactical previews
  - Stage 9 reports

---

STAGE: Stage 9.1
NAME: Projection Coverage and Court Zone Tuning
STATUS: Implemented
MAIN SCRIPT: scripts/run_stage_9_1_projection_coverage.py
MAIN MODULES:
  - src/tennis_vision/projection_coverage.py
  - src/tennis_vision/court_zone_tuning.py
READS:
  - Stage 8.1 expanded labels
  - Stage 9 zone assignments
  - Stage 3 homography report
WRITES:
  - projected expanded labels
  - tuned zone assignments
  - before/after comparison
  - projection coverage previews
  - Stage 9.1 reports

---

STAGE: Stage 10
NAME: Analytical Report and Coaching Summary Prototype
STATUS: Implemented
MAIN SCRIPT: scripts/run_stage_10_analytical_report.py
MAIN MODULES:
  - src/tennis_vision/analytical_report.py
  - src/tennis_vision/coaching_summary.py
  - src/tennis_vision/report_confidence.py
READS:
  - Stage 9.1 tuned zones, directions, and rally summary
  - Stage 8.1 validated timeline and expanded labels
  - Stage 7.1 main players and refined associations
  - Stage 6 smoothed trajectory and trajectory events
WRITES:
  - outputs/reports_final/stage_10_analytical_report/analytical_report.md
  - outputs/reports_final/stage_10_analytical_report/coaching_summary.md
  - outputs/reports_final/stage_10_analytical_report/confidence_summary.json
  - outputs/reports/stage_10_analytical_report_report.*

---

STAGE: Stage 11
NAME: Annotated Highlight / Report Package Generator
STATUS: Implemented
MAIN SCRIPT: scripts/run_stage_11_report_package.py
MAIN MODULES:
  - src/tennis_vision/report_package.py
  - src/tennis_vision/package_manifest.py
READS:
  - Stage 10 analytical reports and summaries
  - Stage 9.1 tactical maps and CSVs
  - Stage 8 timeline artifacts
  - Stage 7.1 player identity artifacts
  - Stage 6 trajectory previews and CSVs
WRITES:
  - outputs/report_packages/stage_11_report_package/README.md
  - outputs/report_packages/stage_11_report_package/package_manifest.json
  - outputs/report_packages/stage_11_report_package/package_index.md
  - outputs/report_packages/stage_11_report_package/analysis/
  - outputs/report_packages/stage_11_report_package/data/
  - outputs/report_packages/stage_11_report_package/visuals/
  - outputs/report_packages/stage_11_report_package/notes/
  - outputs/reports/stage_11_report_package_report.*

---

STAGE: Stage 12
NAME: Synthetic Rally Replay Data Schema
STATUS: Implemented
MAIN SCRIPT: scripts/run_stage_12_replay_schema.py
MAIN MODULES:
  - src/tennis_vision/replay_data_builder.py
  - src/tennis_vision/replay_schema.py
  - src/tennis_vision/replay_camera_presets.py
READS:
  - Stage 11 package manifest
  - Stage 10 analytical report and confidence summary
  - Stage 9.1 tactical zones and projected labels
  - Stage 8.1 validated timeline and expanded labels
  - Stage 8 rally segments and event timeline
  - Stage 7.1 main players and side states
  - Stage 6 trajectory data
  - Stage 3 calibration
WRITES:
  - outputs/replay/stage_12_replay_schema/replay_schema.json
  - outputs/replay/stage_12_replay_schema/replay_schema_pretty.md
  - outputs/replay/stage_12_replay_schema/replay_keyframes.csv
  - outputs/replay/stage_12_replay_schema/replay_events.csv
  - outputs/replay/stage_12_replay_schema/replay_players.json
  - outputs/replay/stage_12_replay_schema/replay_camera_presets.json
  - outputs/replay/stage_12_replay_schema/replay_manifest.json
  - outputs/reports/stage_12_replay_schema_report.*

---

STAGE: Stage 13
NAME: 2D Tactical Replay Renderer
STATUS: Implemented
MAIN SCRIPT: scripts/run_stage_13_2d_tactical_replay.py
MAIN MODULES:
  - src/tennis_vision/replay_renderer_2d.py
  - src/tennis_vision/replay_visual_styles.py
READS:
  - outputs/replay/stage_12_replay_schema/replay_schema.json
WRITES:
  - outputs/replay/stage_13_2d_tactical_replay/frames/
  - outputs/replay/stage_13_2d_tactical_replay/tactical_replay.mp4
  - outputs/replay/stage_13_2d_tactical_replay/tactical_replay_contact_sheet.jpg
  - outputs/replay/stage_13_2d_tactical_replay/tactical_replay_final_frame.jpg
  - outputs/replay/stage_13_2d_tactical_replay/renderer_manifest.json
  - outputs/replay/stage_13_2d_tactical_replay/replay_summary.md
  - outputs/reports/stage_13_2d_tactical_replay_report.*

---

STAGE: Stage 14
NAME: Side-View Ball Flight Renderer
STATUS: Implemented
MAIN SCRIPT: scripts/run_stage_14_side_view_replay.py
MAIN MODULES:
  - src/tennis_vision/ball_flight_estimator.py
  - src/tennis_vision/replay_renderer_side_view.py
READS:
  - outputs/replay/stage_12_replay_schema/replay_schema.json
WRITES:
  - outputs/replay/stage_14_side_view_replay/frames/
  - outputs/replay/stage_14_side_view_replay/side_view_replay.mp4
  - outputs/replay/stage_14_side_view_replay/side_view_contact_sheet.jpg
  - outputs/replay/stage_14_side_view_replay/side_view_final_frame.jpg
  - outputs/replay/stage_14_side_view_replay/side_view_arc_preview.jpg
  - outputs/replay/stage_14_side_view_replay/side_view_manifest.json
  - outputs/replay/stage_14_side_view_replay/side_view_summary.md
  - outputs/reports/stage_14_side_view_replay_report.*

---

STAGE: Stage 14.1
NAME: Side-View Height Semantics Patch
STATUS: Implemented
MAIN SCRIPT: scripts/run_stage_14_side_view_replay.py
MAIN MODULES:
  - src/tennis_vision/ball_flight_estimator.py
  - src/tennis_vision/replay_renderer_side_view.py
READS:
  - outputs/replay/stage_12_replay_schema/replay_schema.json
  - Stage 14 side-view renderer logic
WRITES:
  - outputs/replay/stage_14_side_view_replay/side_view_semantic_debug.jpg
  - outputs/replay/stage_14_side_view_replay/side_view_manifest.json
  - outputs/replay/stage_14_side_view_replay/side_view_summary.md
  - outputs/reports/stage_14_1_side_view_patch_report.*
  - docs/lab-notebook/stage_14_1_side_view_patch.md

---

STAGE: Stage 14.2
NAME: Side-View Event Disambiguation Patch
STATUS: Implemented
MAIN SCRIPT: scripts/run_stage_14_side_view_replay.py
MAIN MODULES:
  - src/tennis_vision/ball_flight_estimator.py
  - src/tennis_vision/replay_renderer_side_view.py
READS:
  - outputs/replay/stage_12_replay_schema/replay_schema.json
  - Stage 14.1 side-view renderer logic
  - Stage 7.1 player side-state data inside replay_schema.json
WRITES:
  - outputs/replay/stage_14_side_view_replay/side_view_semantic_debug.jpg
  - outputs/replay/stage_14_side_view_replay/side_view_manifest.json
  - outputs/replay/stage_14_side_view_replay/side_view_summary.md
  - outputs/reports/stage_14_2_side_view_event_disambiguation_report.*
  - docs/lab-notebook/stage_14_2_side_view_event_disambiguation.md

---

STAGE: Stage 14.3
NAME: Side-View Replay with Validated Events
STATUS: Current
MAIN SCRIPT: scripts/run_stage_14_side_view_replay.py
MAIN MODULES:
  - src/tennis_vision/validated_event_source.py
  - src/tennis_vision/ball_flight_estimator.py
  - src/tennis_vision/replay_renderer_side_view.py
READS:
  - outputs/replay/stage_12_replay_schema/replay_schema.json
  - outputs/timeline/stage_8_3_event_validation/validated_event_timeline.csv
WRITES:
  - outputs/replay/stage_14_side_view_replay/side_view_validated_events_debug.jpg
  - outputs/replay/stage_14_side_view_replay/side_view_manifest.json
  - outputs/reports/stage_14_3_validated_events_side_view_report.*
  - docs/lab-notebook/stage_14_3_validated_events_side_view.md
NOTES:
  Stage 14.3 uses validated event semantics before rendering physical side-view
  contact markers. Downgraded, rejected, and unvalidated hits are annotations
  only.

---

STAGE: Stage 8.5
NAME: Precise Bounce Contact Localization
STATUS: Current
MAIN SCRIPT: scripts/run_stage_8_5_bounce_contact_localization.py
MAIN MODULES:
  - src/tennis_vision/bounce_contact_localization.py
READS:
  - outputs/timeline/stage_8_2_event_labels/manual_event_windows.csv
  - outputs/timeline/stage_8_3_event_validation/manual_event_windows.csv
  - outputs/timeline/stage_8_1_timeline_validation/expanded_ball_labels.csv
  - outputs/tactical/stage_9_1_projection_coverage/projected_expanded_labels.csv
  - samples/video_01.mov
WRITES:
  - outputs/timeline/stage_8_5_bounce_contact/bounce_contact_points.csv
  - outputs/timeline/stage_8_5_bounce_contact/bounce_contact_candidates.csv
  - outputs/timeline/stage_8_5_bounce_contact/bounce_contact_summary.json
  - outputs/timeline/stage_8_5_bounce_contact/bounce_contact_debug/
  - outputs/reports/stage_8_5_bounce_contact_localization_report.*
NOTES:
  Stage 8.5 separates temporal bounce windows from spatial contact
  localization. It does not perform official line calling.

---

STAGE: Stage 8.2R
NAME: Event Labeling Workbench Rebuild
STATUS: Current labeling infrastructure
MAIN SCRIPT: scripts/run_stage_8_2r_event_labeling_workbench.py
MAIN MODULES:
  - src/tennis_vision/frame_decode_audit.py
  - src/tennis_vision/event_labeling_workbench.py
  - src/tennis_vision/event_contact_labels.py
READS:
  - samples/video_01.mov
  - outputs/timeline/stage_8_2r_event_labeling_workbench/event_windows.csv
  - outputs/timeline/stage_8_2r_event_labeling_workbench/contact_candidates.csv
WRITES:
  - outputs/timeline/stage_8_2r_event_labeling_workbench/frame_decode_audit.*
  - outputs/timeline/stage_8_2r_event_labeling_workbench/frame_cache/
  - outputs/timeline/stage_8_2r_event_labeling_workbench/event_windows.*
  - outputs/timeline/stage_8_2r_event_labeling_workbench/contact_candidates.*
  - outputs/timeline/stage_8_2r_event_labeling_workbench/label_integrity_report.*
  - outputs/reports/stage_8_2r_event_labeling_workbench_report.*
  - docs/lab-notebook/stage_8_2r_event_labeling_workbench.md
NOTES:
  Stage 8.2R replaces frame-perfect event labeling with decode audit, visual
  groups, temporal event windows, contact candidates, uncertainty, and label
  integrity checks. It exports compatibility files for Stage 8.3 when labels
  exist.

---

STAGE: Manual Full-Rally Replay
NAME: Manual Timing, Resolved Positions, Curved Side View
STATUS: Current replay calibration path for samples/video_01.mov
MAIN SCRIPT: scripts/run_full_rally_manual_replay.py
MAIN MODULES:
  - src/tennis_vision/manual_event_position_resolver.py
  - src/tennis_vision/side_view_curve_model.py
READS:
  - configs/manual_annotations/video_01_full_rally.json
  - samples/video_01.mov
  - outputs/reports/stage_3_court_calibration_probe_report.json
  - outputs/timeline/stage_8_1_timeline_validation/expanded_ball_labels.csv
  - outputs/tactical/stage_9_1_projection_coverage/projected_expanded_labels.csv
WRITES:
  - outputs/replay/manual_full_rally/resolved_manual_events.csv
  - outputs/replay/manual_full_rally/full_rally_event_timeline.csv
  - outputs/replay/manual_full_rally/replay_schema.json
  - outputs/replay/manual_full_rally/top_view_replay.mp4
  - outputs/replay/manual_full_rally/side_view_replay.mp4
  - outputs/replay/manual_full_rally/side_view_curve_segments.csv
  - outputs/reports/manual_full_rally_replay_report.*
NOTES:
  The Product Owner supplies event timing and shot type only. The system
  resolves ball positions locally near each event, projects them to court
  coordinates, and renders side-view trajectories as synthetic curves. These
  curves are visual approximations, not measured 3D physics.
