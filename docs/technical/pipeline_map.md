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
  -> Stage 9 Tactical Metrics and Shot Zones

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
