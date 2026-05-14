# Function Inventory

This document is designed to be readable as plain text.
It avoids wide Markdown tables because the Product Owner often reviews documentation in TXT/editor view.

Line numbers are generated from the current Python source with `scripts/update_function_inventory.py`.

## Stage 0 - Environment

FUNCTION: run_environment_checks
FILE: src/tennis_vision/environment.py
LINE: 150
AREA: Stage 0 - Environment

PURPOSE:
  Runs the complete local environment check for Python, folders, imports, and ffmpeg.

INPUTS:
  - project root path

OUTPUTS:
  - environment status dictionary

CALLED BY:
  - scripts/doctor.py

WHY PRODUCT OWNER CARES:
  This tells the Product Owner whether local development can continue before video analysis stages run.

HOW TO FIND IT:
  Open src/tennis_vision/environment.py and go to line 150.
  Search: def run_environment_checks

NOTES:
  ffmpeg missing is recorded as warning unless a later stage needs it.

---

FUNCTION: check_required_packages
FILE: src/tennis_vision/environment.py
LINE: 76
AREA: Stage 0 - Environment

PURPOSE:
  Checks whether required Python packages can be imported.

INPUTS:
  - package name list

OUTPUTS:
  - package import status

CALLED BY:
  - run_environment_checks

WHY PRODUCT OWNER CARES:
  Missing packages are common setup friction and should be visible immediately.

HOW TO FIND IT:
  Open src/tennis_vision/environment.py and go to line 76.
  Search: def check_required_packages

NOTES:
  None.

---

FUNCTION: check_ffmpeg
FILE: src/tennis_vision/environment.py
LINE: 98
AREA: Stage 0 - Environment

PURPOSE:
  Checks whether ffmpeg is available from the shell.

INPUTS:
  - none

OUTPUTS:
  - ffmpeg availability and path/status

CALLED BY:
  - run_environment_checks

WHY PRODUCT OWNER CARES:
  Video work may eventually need ffmpeg, but Stage 1 proved MOV reading can work through OpenCV.

HOW TO FIND IT:
  Open src/tennis_vision/environment.py and go to line 98.
  Search: def check_ffmpeg

NOTES:
  None.

---

## Reports

FUNCTION: write_json_report
FILE: src/tennis_vision/report.py
LINE: 35
AREA: Reports

PURPOSE:
  Writes a machine-readable JSON report.

INPUTS:
  - report path
  - report dictionary

OUTPUTS:
  - JSON report file

CALLED BY:
  - stage scripts

WHY PRODUCT OWNER CARES:
  Reports are the durable evidence layer for every experiment.

HOW TO FIND IT:
  Open src/tennis_vision/report.py and go to line 35.
  Search: def write_json_report

NOTES:
  None.

---

FUNCTION: write_markdown_report
FILE: src/tennis_vision/report.py
LINE: 42
AREA: Reports

PURPOSE:
  Writes a human-readable Markdown report.

INPUTS:
  - report path
  - title
  - sections

OUTPUTS:
  - Markdown report file

CALLED BY:
  - stage scripts

WHY PRODUCT OWNER CARES:
  The Product Owner can inspect results without parsing JSON.

HOW TO FIND IT:
  Open src/tennis_vision/report.py and go to line 42.
  Search: def write_markdown_report

NOTES:
  None.

---

## Friction

FUNCTION: friction_band
FILE: src/tennis_vision/friction.py
LINE: 8
AREA: Friction

PURPOSE:
  Converts a numeric friction score into low, medium, high, or blocking.

INPUTS:
  - score from 0 to 100

OUTPUTS:
  - friction band text

CALLED BY:
  - all friction scoring helpers

WHY PRODUCT OWNER CARES:
  Keeps operational risk readable across stages.

HOW TO FIND IT:
  Open src/tennis_vision/friction.py and go to line 8.
  Search: def friction_band

NOTES:
  None.

---

FUNCTION: calculate_stage_1_friction_score
FILE: src/tennis_vision/friction.py
LINE: 52
AREA: Friction

PURPOSE:
  Calculates friction for Stage 1 video loading.

INPUTS:
  - stage-specific warning/error/input flags

OUTPUTS:
  - friction score dictionary

CALLED BY:
  - scripts/run_stage_1_video_probe.py

WHY PRODUCT OWNER CARES:
  Prevents failures and uncertainty from being hidden.

HOW TO FIND IT:
  Open src/tennis_vision/friction.py and go to line 52.
  Search: def calculate_stage_1_friction_score

NOTES:
  None.

---

FUNCTION: calculate_stage_2_friction_score
FILE: src/tennis_vision/friction.py
LINE: 91
AREA: Friction

PURPOSE:
  Calculates friction for Stage 2 YOLO CPU inference.

INPUTS:
  - stage-specific warning/error/input flags

OUTPUTS:
  - friction score dictionary

CALLED BY:
  - scripts/run_stage_2_yolo_cpu_baseline.py

WHY PRODUCT OWNER CARES:
  Prevents failures and uncertainty from being hidden.

HOW TO FIND IT:
  Open src/tennis_vision/friction.py and go to line 91.
  Search: def calculate_stage_2_friction_score

NOTES:
  None.

---

FUNCTION: calculate_stage_3_friction_score
FILE: src/tennis_vision/friction.py
LINE: 136
AREA: Friction

PURPOSE:
  Calculates friction for Stage 3 court calibration.

INPUTS:
  - stage-specific warning/error/input flags

OUTPUTS:
  - friction score dictionary

CALLED BY:
  - scripts/run_stage_3_court_calibration_probe.py

WHY PRODUCT OWNER CARES:
  Prevents failures and uncertainty from being hidden.

HOW TO FIND IT:
  Open src/tennis_vision/friction.py and go to line 136.
  Search: def calculate_stage_3_friction_score

NOTES:
  None.

---

FUNCTION: calculate_stage_4_friction_score
FILE: src/tennis_vision/friction.py
LINE: 232
AREA: Friction

PURPOSE:
  Calculates friction for Stage 4 ball candidate probing.

INPUTS:
  - stage-specific warning/error/input flags

OUTPUTS:
  - friction score dictionary

CALLED BY:
  - scripts/run_stage_4_ball_tracking_probe.py

WHY PRODUCT OWNER CARES:
  Prevents failures and uncertainty from being hidden.

HOW TO FIND IT:
  Open src/tennis_vision/friction.py and go to line 232.
  Search: def calculate_stage_4_friction_score

NOTES:
  None.

---

FUNCTION: calculate_stage_5_friction_score
FILE: src/tennis_vision/friction.py
LINE: 310
AREA: Friction

PURPOSE:
  Calculates friction for Stage 5 candidate filtering.

INPUTS:
  - stage-specific warning/error/input flags

OUTPUTS:
  - friction score dictionary

CALLED BY:
  - scripts/run_stage_5_ball_candidate_filtering.py

WHY PRODUCT OWNER CARES:
  Prevents failures and uncertainty from being hidden.

HOW TO FIND IT:
  Open src/tennis_vision/friction.py and go to line 310.
  Search: def calculate_stage_5_friction_score

NOTES:
  None.

---

FUNCTION: calculate_stage_6_friction_score
FILE: src/tennis_vision/friction.py
LINE: 397
AREA: Friction

PURPOSE:
  Calculates friction for Stage 6 trajectory smoothing.

INPUTS:
  - stage-specific warning/error/input flags

OUTPUTS:
  - friction score dictionary

CALLED BY:
  - scripts/run_stage_6_trajectory_smoothing.py

WHY PRODUCT OWNER CARES:
  Prevents failures and uncertainty from being hidden.

HOW TO FIND IT:
  Open src/tennis_vision/friction.py and go to line 397.
  Search: def calculate_stage_6_friction_score

NOTES:
  None.

---

FUNCTION: calculate_stage_7_friction_score
FILE: src/tennis_vision/friction.py
LINE: 436
AREA: Friction

PURPOSE:
  Calculates friction for Stage 7 player interaction.

INPUTS:
  - stage-specific warning/error/input flags

OUTPUTS:
  - friction score dictionary

CALLED BY:
  - scripts/run_stage_7_player_interaction_probe.py

WHY PRODUCT OWNER CARES:
  Prevents failures and uncertainty from being hidden.

HOW TO FIND IT:
  Open src/tennis_vision/friction.py and go to line 436.
  Search: def calculate_stage_7_friction_score

NOTES:
  None.

---

FUNCTION: calculate_stage_8_friction_score
FILE: src/tennis_vision/friction.py
LINE: 529
AREA: Friction

PURPOSE:
  Calculates friction for Stage 8 event timeline.

INPUTS:
  - stage-specific warning/error/input flags

OUTPUTS:
  - friction score dictionary

CALLED BY:
  - scripts/run_stage_8_event_timeline.py

WHY PRODUCT OWNER CARES:
  Prevents failures and uncertainty from being hidden.

HOW TO FIND IT:
  Open src/tennis_vision/friction.py and go to line 529.
  Search: def calculate_stage_8_friction_score

NOTES:
  None.

---

FUNCTION: calculate_stage_8_1_friction_score
FILE: src/tennis_vision/friction.py
LINE: 574
AREA: Friction

PURPOSE:
  Calculates friction for Stage 8.1 timeline validation.

INPUTS:
  - stage-specific warning/error/input flags

OUTPUTS:
  - friction score dictionary

CALLED BY:
  - scripts/run_stage_8_1_expand_labels.py

WHY PRODUCT OWNER CARES:
  Prevents failures and uncertainty from being hidden.

HOW TO FIND IT:
  Open src/tennis_vision/friction.py and go to line 574.
  Search: def calculate_stage_8_1_friction_score

NOTES:
  None.

---

FUNCTION: calculate_stage_9_friction_score
FILE: src/tennis_vision/friction.py
LINE: 613
AREA: Friction

PURPOSE:
  Calculates friction for Stage 9 tactical metrics.

INPUTS:
  - stage-specific warning/error/input flags

OUTPUTS:
  - friction score dictionary

CALLED BY:
  - scripts/run_stage_9_tactical_metrics.py

WHY PRODUCT OWNER CARES:
  Prevents failures and uncertainty from being hidden.

HOW TO FIND IT:
  Open src/tennis_vision/friction.py and go to line 613.
  Search: def calculate_stage_9_friction_score

NOTES:
  None.

---

FUNCTION: calculate_stage_9_1_friction_score
FILE: src/tennis_vision/friction.py
LINE: 658
AREA: Friction

PURPOSE:
  Calculates friction for Stage 9.1 projection coverage.

INPUTS:
  - stage-specific warning/error/input flags

OUTPUTS:
  - friction score dictionary

CALLED BY:
  - scripts/run_stage_9_1_projection_coverage.py

WHY PRODUCT OWNER CARES:
  Prevents failures and uncertainty from being hidden.

HOW TO FIND IT:
  Open src/tennis_vision/friction.py and go to line 658.
  Search: def calculate_stage_9_1_friction_score

NOTES:
  None.

---

## Stage 1 - Video IO

FUNCTION: read_video_metadata
FILE: src/tennis_vision/video_io.py
LINE: 59
AREA: Stage 1 - Video IO

PURPOSE:
  Reads file size, frame count, FPS, duration, resolution, and codec metadata.

INPUTS:
  - video path

OUTPUTS:
  - metadata dictionary

CALLED BY:
  - scripts/run_stage_1_video_probe.py

WHY PRODUCT OWNER CARES:
  Confirms that the local sample video is readable before later analysis stages.

HOW TO FIND IT:
  Open src/tennis_vision/video_io.py and go to line 59.
  Search: def read_video_metadata

NOTES:
  None.

---

FUNCTION: extract_frames
FILE: src/tennis_vision/frame_sampler.py
LINE: 12
AREA: Stage 1 - Video IO

PURPOSE:
  Extracts JPG frames from a video at a fixed interval.

INPUTS:
  - video path
  - output folder
  - interval
  - max frames

OUTPUTS:
  - saved frames and extraction statistics

CALLED BY:
  - scripts/run_stage_1_video_probe.py

WHY PRODUCT OWNER CARES:
  Frame extraction is the first concrete video-processing capability.

HOW TO FIND IT:
  Open src/tennis_vision/frame_sampler.py and go to line 12.
  Search: def extract_frames

NOTES:
  None.

---

## Stage 2 - YOLO CPU

FUNCTION: load_yolo_model
FILE: src/tennis_vision/yolo_cpu.py
LINE: 16
AREA: Stage 2 - YOLO CPU

PURPOSE:
  Loads a small YOLO model for local CPU inference.

INPUTS:
  - model name

OUTPUTS:
  - YOLO model or load error

CALLED BY:
  - scripts/run_stage_2_yolo_cpu_baseline.py

WHY PRODUCT OWNER CARES:
  Validates whether object detection can run locally without cloud or GPU assumptions.

HOW TO FIND IT:
  Open src/tennis_vision/yolo_cpu.py and go to line 16.
  Search: def load_yolo_model

NOTES:
  None.

---

FUNCTION: run_yolo_cpu_baseline
FILE: src/tennis_vision/yolo_cpu.py
LINE: 98
AREA: Stage 2 - YOLO CPU

PURPOSE:
  Runs limited YOLO CPU inference and saves annotated frames.

INPUTS:
  - video
  - model
  - interval
  - max frames
  - resize width
  - confidence

OUTPUTS:
  - annotated images and detection summary

CALLED BY:
  - scripts/run_stage_2_yolo_cpu_baseline.py

WHY PRODUCT OWNER CARES:
  Proves the local object detection pipeline is technically possible.

HOW TO FIND IT:
  Open src/tennis_vision/yolo_cpu.py and go to line 98.
  Search: def run_yolo_cpu_baseline

NOTES:
  None.

---

## Stage 3 - Court Calibration

FUNCTION: validate_corner_geometry
FILE: src/tennis_vision/court_calibration.py
LINE: 137
AREA: Stage 3 - Court Calibration

PURPOSE:
  Checks point order and crossed court polygon geometry.

INPUTS:
  - manual court corner points

OUTPUTS:
  - geometry validation status

CALLED BY:
  - validate_points

WHY PRODUCT OWNER CARES:
  Prevents inverted court points from creating a false homography.

HOW TO FIND IT:
  Open src/tennis_vision/court_calibration.py and go to line 137.
  Search: def validate_corner_geometry

NOTES:
  None.

---

FUNCTION: compute_homography
FILE: src/tennis_vision/court_calibration.py
LINE: 267
AREA: Stage 3 - Court Calibration

PURPOSE:
  Computes the image-to-normalized-court homography from valid corner points.

INPUTS:
  - validated court points

OUTPUTS:
  - homography matrix/status

CALLED BY:
  - run_court_calibration_probe

WHY PRODUCT OWNER CARES:
  This is the bridge from video pixels to court-space reasoning.

HOW TO FIND IT:
  Open src/tennis_vision/court_calibration.py and go to line 267.
  Search: def compute_homography

NOTES:
  None.

---

## Stage 3.1 - Court Point Selection

FUNCTION: generate_coordinate_grid
FILE: src/tennis_vision/court_point_selector.py
LINE: 28
AREA: Stage 3.1 - Court Point Selection

PURPOSE:
  Draws coordinate grid labels on the calibration reference frame.

INPUTS:
  - reference image
  - grid step

OUTPUTS:
  - grid image

CALLED BY:
  - scripts/run_stage_3_1_court_point_selector.py

WHY PRODUCT OWNER CARES:
  The user can estimate or verify court point coordinates without a frontend.

HOW TO FIND IT:
  Open src/tennis_vision/court_point_selector.py and go to line 28.
  Search: def generate_coordinate_grid

NOTES:
  None.

---

## Stage 4 - Ball Candidate Probe

FUNCTION: detect_ball_candidates
FILE: src/tennis_vision/ball_tracking_probe.py
LINE: 30
AREA: Stage 4 - Ball Candidate Probe

PURPOSE:
  Finds yellow/green blob candidates using OpenCV heuristics.

INPUTS:
  - frame
  - frame index

OUTPUTS:
  - candidate list

CALLED BY:
  - run_ball_tracking_probe

WHY PRODUCT OWNER CARES:
  This showed the first local ball-detection approach produced many false positives.

HOW TO FIND IT:
  Open src/tennis_vision/ball_tracking_probe.py and go to line 30.
  Search: def detect_ball_candidates

NOTES:
  None.

---

## Stage 4.1 - Manual Ball Labeling

FUNCTION: label_frames_interactively
FILE: src/tennis_vision/ball_labeling.py
LINE: 115
AREA: Stage 4.1 - Manual Ball Labeling

PURPOSE:
  Opens OpenCV windows so the user can click the real ball.

INPUTS:
  - video
  - frame indices
  - output dir
  - resize width

OUTPUTS:
  - manual labels and overlays

CALLED BY:
  - scripts/run_stage_4_1_ball_labeling_helper.py
  - scripts/run_stage_8_1_expand_labels.py

WHY PRODUCT OWNER CARES:
  Manual labels create ground truth when automatic detection is noisy.

HOW TO FIND IT:
  Open src/tennis_vision/ball_labeling.py and go to line 115.
  Search: def label_frames_interactively

NOTES:
  None.

---

## Stage 5 - Candidate Filtering and Court Projection

FUNCTION: compare_candidates_to_labels
FILE: src/tennis_vision/ball_candidate_filtering.py
LINE: 80
AREA: Stage 5 - Candidate Filtering and Court Projection

PURPOSE:
  Ranks automatic candidates by distance to manual labels.

INPUTS:
  - candidate rows
  - manual labels

OUTPUTS:
  - distance rows and summary

CALLED BY:
  - scripts/run_stage_5_ball_candidate_filtering.py

WHY PRODUCT OWNER CARES:
  Quantifies whether automatic candidates are actually near the real ball.

HOW TO FIND IT:
  Open src/tennis_vision/ball_candidate_filtering.py and go to line 80.
  Search: def compare_candidates_to_labels

NOTES:
  None.

---

FUNCTION: project_image_points
FILE: src/tennis_vision/court_projection.py
LINE: 64
AREA: Stage 5 - Candidate Filtering and Court Projection

PURPOSE:
  Projects image-space points into normalized court coordinates.

INPUTS:
  - point rows
  - homography matrix

OUTPUTS:
  - projected point rows

CALLED BY:
  - Stage 5 and Stage 5.1 scripts

WHY PRODUCT OWNER CARES:
  Court-space projection is required for SwingVision-style spatial analysis.

HOW TO FIND IT:
  Open src/tennis_vision/court_projection.py and go to line 64.
  Search: def project_image_points

NOTES:
  None.

---

## Stage 5.1 - Candidate Generation Improvement

FUNCTION: generate_hsv_candidates
FILE: src/tennis_vision/ball_candidate_improvement.py
LINE: 86
AREA: Stage 5.1 - Candidate Generation Improvement

PURPOSE:
  Generates improved HSV color candidates for labeled frames.

INPUTS:
  - frame bundle
  - court polygon

OUTPUTS:
  - candidate rows

CALLED BY:
  - scripts/run_stage_5_1_candidate_improvement.py

WHY PRODUCT OWNER CARES:
  This strategy dramatically improved ball candidate distance on the sample.

HOW TO FIND IT:
  Open src/tennis_vision/ball_candidate_improvement.py and go to line 86.
  Search: def generate_hsv_candidates

NOTES:
  None.

---

FUNCTION: evaluate_strategies
FILE: src/tennis_vision/ball_candidate_improvement.py
LINE: 310
AREA: Stage 5.1 - Candidate Generation Improvement

PURPOSE:
  Compares candidate generation strategies against manual labels.

INPUTS:
  - candidates by strategy
  - manual labels

OUTPUTS:
  - strategy comparison rows and summaries

CALLED BY:
  - scripts/run_stage_5_1_candidate_improvement.py

WHY PRODUCT OWNER CARES:
  Helps decide whether to advance or improve the detector first.

HOW TO FIND IT:
  Open src/tennis_vision/ball_candidate_improvement.py and go to line 310.
  Search: def evaluate_strategies

NOTES:
  None.

---

## Stage 6 - Trajectory Smoothing

FUNCTION: moving_average_smooth
FILE: src/tennis_vision/trajectory_smoothing.py
LINE: 191
AREA: Stage 6 - Trajectory Smoothing

PURPOSE:
  Smooths raw and projected ball coordinates with a small moving average.

INPUTS:
  - trajectory rows
  - window size

OUTPUTS:
  - smoothed trajectory rows

CALLED BY:
  - scripts/run_stage_6_trajectory_smoothing.py

WHY PRODUCT OWNER CARES:
  Creates a first trajectory without hiding sparse or bad detections.

HOW TO FIND IT:
  Open src/tennis_vision/trajectory_smoothing.py and go to line 191.
  Search: def moving_average_smooth

NOTES:
  None.

---

FUNCTION: detect_events
FILE: src/tennis_vision/event_segmentation.py
LINE: 12
AREA: Stage 6 - Trajectory Smoothing

PURPOSE:
  Creates hypothesis-only event markers from trajectory shape and speed changes.

INPUTS:
  - raw trajectory rows

OUTPUTS:
  - event rows and warnings

CALLED BY:
  - scripts/run_stage_6_trajectory_smoothing.py

WHY PRODUCT OWNER CARES:
  Starts event reasoning while preserving uncertainty.

HOW TO FIND IT:
  Open src/tennis_vision/event_segmentation.py and go to line 12.
  Search: def detect_events

NOTES:
  None.

---

## Stage 7 - Player Interaction

FUNCTION: detect_players
FILE: src/tennis_vision/player_tracking.py
LINE: 59
AREA: Stage 7 - Player Interaction

PURPOSE:
  Runs local YOLO person detection on selected frames.

INPUTS:
  - video
  - frame list
  - model
  - resize width
  - confidence

OUTPUTS:
  - player detection rows

CALLED BY:
  - scripts/run_stage_7_player_interaction_probe.py

WHY PRODUCT OWNER CARES:
  Player locations are needed to interpret possible ball-player interactions.

HOW TO FIND IT:
  Open src/tennis_vision/player_tracking.py and go to line 59.
  Search: def detect_players

NOTES:
  None.

---

FUNCTION: associate_ball_to_players
FILE: src/tennis_vision/ball_player_interaction.py
LINE: 27
AREA: Stage 7 - Player Interaction

PURPOSE:
  Associates ball trajectory points with nearby player tracks.

INPUTS:
  - ball rows
  - player tracks
  - events
  - frame tolerance

OUTPUTS:
  - distance rows, interaction rows, counts

CALLED BY:
  - scripts/run_stage_7_player_interaction_probe.py

WHY PRODUCT OWNER CARES:
  Turns player proximity into possible-hit hypotheses, not confirmed events.

HOW TO FIND IT:
  Open src/tennis_vision/ball_player_interaction.py and go to line 27.
  Search: def associate_ball_to_players

NOTES:
  None.

---

## Stage 7.1 - Player Filtering and Identity

FUNCTION: score_track_rows
FILE: src/tennis_vision/player_filtering.py
LINE: 50
AREA: Stage 7.1 - Player Filtering and Identity

PURPOSE:
  Scores person detections using court, size, duration, and confidence signals.

INPUTS:
  - player track rows
  - court polygon
  - thresholds

OUTPUTS:
  - scored rows and track summaries

CALLED BY:
  - scripts/run_stage_7_1_player_filtering.py

WHY PRODUCT OWNER CARES:
  Filters audience and side people so only the main players remain.

HOW TO FIND IT:
  Open src/tennis_vision/player_filtering.py and go to line 50.
  Search: def score_track_rows

NOTES:
  None.

---

FUNCTION: build_identity_profiles
FILE: src/tennis_vision/player_identity.py
LINE: 15
AREA: Stage 7.1 - Player Filtering and Identity

PURPOSE:
  Builds lightweight clothing-color identity profiles from player crops.

INPUTS:
  - video
  - filtered player rows

OUTPUTS:
  - identity profile JSON and warnings

CALLED BY:
  - scripts/run_stage_7_1_player_filtering.py

WHY PRODUCT OWNER CARES:
  Player identity should not be permanently tied to near/far side.

HOW TO FIND IT:
  Open src/tennis_vision/player_identity.py and go to line 15.
  Search: def build_identity_profiles

NOTES:
  None.

---

## Stage 8 - Event Timeline

FUNCTION: merge_timeline_events
FILE: src/tennis_vision/event_timeline.py
LINE: 169
AREA: Stage 8 - Event Timeline

PURPOSE:
  Merges nearby trajectory, event, and interaction evidence into timeline clusters.

INPUTS:
  - event rows
  - merge window
  - FPS

OUTPUTS:
  - timeline event rows

CALLED BY:
  - scripts/run_stage_8_event_timeline.py

WHY PRODUCT OWNER CARES:
  Creates the first readable rally timeline while preserving uncertainty.

HOW TO FIND IT:
  Open src/tennis_vision/event_timeline.py and go to line 169.
  Search: def merge_timeline_events

NOTES:
  None.

---

FUNCTION: build_rally_segments
FILE: src/tennis_vision/rally_segmentation.py
LINE: 10
AREA: Stage 8 - Event Timeline

PURPOSE:
  Builds conservative rally segments from trajectory anchors.

INPUTS:
  - trajectory rows
  - timeline events
  - FPS

OUTPUTS:
  - rally segment rows

CALLED BY:
  - scripts/run_stage_8_event_timeline.py

WHY PRODUCT OWNER CARES:
  Provides a first segment boundary without inferring score or outcome.

HOW TO FIND IT:
  Open src/tennis_vision/rally_segmentation.py and go to line 10.
  Search: def build_rally_segments

NOTES:
  None.

---

## Stage 8.1 - Timeline Validation

FUNCTION: load_durable_or_fallback_labels
FILE: src/tennis_vision/label_expansion.py
LINE: 81
AREA: Stage 8.1 - Timeline Validation

PURPOSE:
  Loads durable expanded labels first, then latest session backup, then Stage 4.1 fallback labels.

INPUTS:
  - expanded labels path
  - fallback labels path

OUTPUTS:
  - labels
  - source metadata
  - warnings

CALLED BY:
  - scripts/run_stage_8_1_expand_labels.py

WHY PRODUCT OWNER CARES:
  Prevents non-interactive validation from downgrading manual label coverage.

HOW TO FIND IT:
  Open src/tennis_vision/label_expansion.py and go to line 81.
  Search: def load_durable_or_fallback_labels

NOTES:
  None.

---

FUNCTION: write_label_session_backup
FILE: src/tennis_vision/label_expansion.py
LINE: 279
AREA: Stage 8.1 - Timeline Validation

PURPOSE:
  Writes timestamped CSV and JSON backups for labels collected in an interactive session.

INPUTS:
  - session directory
  - timestamp
  - labels

OUTPUTS:
  - backup CSV path
  - backup JSON path

CALLED BY:
  - scripts/run_stage_8_1_expand_labels.py

WHY PRODUCT OWNER CARES:
  Protects manual labeling work from later validation runs or report regeneration.

HOW TO FIND IT:
  Open src/tennis_vision/label_expansion.py and go to line 279.
  Search: def write_label_session_backup

NOTES:
  None.

---

FUNCTION: latest_label_session_csv
FILE: src/tennis_vision/label_expansion.py
LINE: 73
AREA: Stage 8.1 - Timeline Validation

PURPOSE:
  Finds the newest timestamped Stage 8.1 label session backup.

INPUTS:
  - label session directory

OUTPUTS:
  - latest session CSV path or None

CALLED BY:
  - load_durable_or_fallback_labels

WHY PRODUCT OWNER CARES:
  Allows non-interactive validation to recover from a missing or incomplete durable expanded label file.

HOW TO FIND IT:
  Open src/tennis_vision/label_expansion.py and go to line 73.
  Search: def latest_label_session_csv

NOTES:
  None.

---

FUNCTION: validate_timeline_events
FILE: src/tennis_vision/timeline_validation.py
LINE: 95
AREA: Stage 8.1 - Timeline Validation

PURPOSE:
  Checks whether timeline events are supported by nearby expanded ball labels.

INPUTS:
  - timeline rows
  - expanded labels

OUTPUTS:
  - validation rows, validated timeline, summary

CALLED BY:
  - scripts/run_stage_8_1_expand_labels.py

WHY PRODUCT OWNER CARES:
  This is the gate before tactical metrics.

HOW TO FIND IT:
  Open src/tennis_vision/timeline_validation.py and go to line 95.
  Search: def validate_timeline_events

NOTES:
  None.

---

## Stage 9 - Tactical Metrics

FUNCTION: assign_court_zone
FILE: src/tennis_vision/court_zones.py
LINE: 59
AREA: Stage 9 - Tactical Metrics

PURPOSE:
  Assigns a normalized ball point to an approximate tactical court zone.

INPUTS:
  - projected_x
  - projected_y

OUTPUTS:
  - zone id
  - depth
  - lateral lane
  - side
  - confidence-like score

CALLED BY:
  - build_ball_zone_assignments

WHY PRODUCT OWNER CARES:
  This turns raw tracking coordinates into tennis-readable shot placement information.

HOW TO FIND IT:
  Open src/tennis_vision/court_zones.py and go to line 59.
  Search: def assign_court_zone

NOTES:
  None.

---

FUNCTION: classify_depth
FILE: src/tennis_vision/court_zones.py
LINE: 38
AREA: Stage 9 - Tactical Metrics

PURPOSE:
  Classifies a normalized court y coordinate as short, mid, deep, or unknown.

INPUTS:
  - projected_y

OUTPUTS:
  - depth class

CALLED BY:
  - assign_court_zone

WHY PRODUCT OWNER CARES:
  Depth is one of the most important first tactical summaries.

HOW TO FIND IT:
  Open src/tennis_vision/court_zones.py and go to line 38.
  Search: def classify_depth

NOTES:
  None.

---

FUNCTION: build_ball_zone_assignments
FILE: src/tennis_vision/tactical_metrics.py
LINE: 41
AREA: Stage 9 - Tactical Metrics

PURPOSE:
  Combines manual labels, trajectory rows, and projected candidates into zone assignment rows.

INPUTS:
  - expanded labels
  - smoothed trajectory
  - projected candidate rows

OUTPUTS:
  - ball zone assignment rows

CALLED BY:
  - scripts/run_stage_9_tactical_metrics.py

WHY PRODUCT OWNER CARES:
  This is the main bridge from validated ball data to tactical placement outputs.

HOW TO FIND IT:
  Open src/tennis_vision/tactical_metrics.py and go to line 41.
  Search: def build_ball_zone_assignments

NOTES:
  None.

---

FUNCTION: estimate_shot_directions
FILE: src/tennis_vision/tactical_metrics.py
LINE: 81
AREA: Stage 9 - Tactical Metrics

PURPOSE:
  Estimates approximate crosscourt/down-the-line/center-like movement between consecutive ball points.

INPUTS:
  - zone assignment rows

OUTPUTS:
  - shot direction estimate rows

CALLED BY:
  - scripts/run_stage_9_tactical_metrics.py

WHY PRODUCT OWNER CARES:
  Direction estimates are a first tactical signal, but they remain hypothesis-based.

HOW TO FIND IT:
  Open src/tennis_vision/tactical_metrics.py and go to line 81.
  Search: def estimate_shot_directions

NOTES:
  None.

---

FUNCTION: build_rally_tactical_summary
FILE: src/tennis_vision/tactical_metrics.py
LINE: 137
AREA: Stage 9 - Tactical Metrics

PURPOSE:
  Summarizes dominant zone/depth/lane for each rally segment.

INPUTS:
  - rally segment rows
  - zone assignment rows

OUTPUTS:
  - rally tactical summary rows

CALLED BY:
  - scripts/run_stage_9_tactical_metrics.py

WHY PRODUCT OWNER CARES:
  This gives the Product Owner a compact rally-level tactical readout.

HOW TO FIND IT:
  Open src/tennis_vision/tactical_metrics.py and go to line 137.
  Search: def build_rally_tactical_summary

NOTES:
  None.

---

## Stage 9.1 - Projection Coverage

FUNCTION: load_stage_3_homography
FILE: src/tennis_vision/projection_coverage.py
LINE: 42
AREA: Stage 9.1 - Projection Coverage

PURPOSE:
  Loads the Stage 3 image-to-court homography from the calibration report.

INPUTS:
  - Stage 3 calibration report path

OUTPUTS:
  - homography matrix
  - metadata
  - errors

CALLED BY:
  - scripts/run_stage_9_1_projection_coverage.py

WHY PRODUCT OWNER CARES:
  Projection coverage depends on the same validated court calibration used by earlier stages.

HOW TO FIND IT:
  Open src/tennis_vision/projection_coverage.py and go to line 42.
  Search: def load_stage_3_homography

NOTES:
  None.

---

FUNCTION: project_labels_to_court
FILE: src/tennis_vision/projection_coverage.py
LINE: 57
AREA: Stage 9.1 - Projection Coverage

PURPOSE:
  Projects expanded manual ball labels from image pixels into normalized court space.

INPUTS:
  - expanded label rows
  - homography matrix

OUTPUTS:
  - projected label rows with projection status

CALLED BY:
  - scripts/run_stage_9_1_projection_coverage.py

WHY PRODUCT OWNER CARES:
  This reduces unknown tactical zones by giving all validated labels court coordinates when possible.

HOW TO FIND IT:
  Open src/tennis_vision/projection_coverage.py and go to line 57.
  Search: def project_labels_to_court

NOTES:
  Out-of-range projections are preserved as uncertainty instead of forced into confident zones.

---

FUNCTION: calculate_projection_coverage
FILE: src/tennis_vision/projection_coverage.py
LINE: 118
AREA: Stage 9.1 - Projection Coverage

PURPOSE:
  Compares Stage 9 projection coverage with Stage 9.1 projected label coverage.

INPUTS:
  - projected Stage 9.1 labels
  - Stage 9 zone rows

OUTPUTS:
  - before/after projection coverage metrics

CALLED BY:
  - scripts/run_stage_9_1_projection_coverage.py

WHY PRODUCT OWNER CARES:
  Shows whether the unknown-zone problem actually improved.

HOW TO FIND IT:
  Open src/tennis_vision/projection_coverage.py and go to line 118.
  Search: def calculate_projection_coverage

NOTES:
  None.

---

FUNCTION: assign_tuned_court_zone
FILE: src/tennis_vision/court_zone_tuning.py
LINE: 47
AREA: Stage 9.1 - Projection Coverage

PURPOSE:
  Assigns a tuned approximate zone while preserving missing and out-of-bounds uncertainty.

INPUTS:
  - projected_x
  - projected_y
  - optional tuning config

OUTPUTS:
  - tuned zone
  - depth
  - lane
  - confidence-like score
  - notes

CALLED BY:
  - tune_zone_assignments

WHY PRODUCT OWNER CARES:
  This turns improved projection coverage into more readable tactical placement without pretending to be official line calling.

HOW TO FIND IT:
  Open src/tennis_vision/court_zone_tuning.py and go to line 47.
  Search: def assign_tuned_court_zone

NOTES:
  None.

---

FUNCTION: tune_zone_assignments
FILE: src/tennis_vision/court_zone_tuning.py
LINE: 83
AREA: Stage 9.1 - Projection Coverage

PURPOSE:
  Applies tuned zone assignment to every projected expanded label.

INPUTS:
  - merged projected labels and Stage 9 assignment context

OUTPUTS:
  - tuned ball zone assignment rows

CALLED BY:
  - scripts/run_stage_9_1_projection_coverage.py

WHY PRODUCT OWNER CARES:
  This creates the Stage 9.1 replacement zone assignment artifact.

HOW TO FIND IT:
  Open src/tennis_vision/court_zone_tuning.py and go to line 83.
  Search: def tune_zone_assignments

NOTES:
  None.

---

FUNCTION: compare_stage_9_to_9_1
FILE: src/tennis_vision/court_zone_tuning.py
LINE: 125
AREA: Stage 9.1 - Projection Coverage

PURPOSE:
  Builds frame-level before/after comparison rows for Stage 9 and Stage 9.1.

INPUTS:
  - Stage 9 zone rows
  - Stage 9.1 tuned rows

OUTPUTS:
  - comparison rows with improvement status

CALLED BY:
  - scripts/run_stage_9_1_projection_coverage.py

WHY PRODUCT OWNER CARES:
  The Product Owner can see which frames improved from unknown or gained projection.

HOW TO FIND IT:
  Open src/tennis_vision/court_zone_tuning.py and go to line 125.
  Search: def compare_stage_9_to_9_1

NOTES:
  None.

---

## Lab Notebook

FUNCTION: update_lab_notebook
FILE: src/tennis_vision/lab_notebook.py
LINE: 1651
AREA: Lab Notebook

PURPOSE:
  Updates stage lab notebook pages and experiment index from reports.

INPUTS:
  - project root

OUTPUTS:
  - lab notebook Markdown pages

CALLED BY:
  - stage scripts
  - scripts/update_lab_notebook.py

WHY PRODUCT OWNER CARES:
  Keeps execution evidence current without manual documentation commands.

HOW TO FIND IT:
  Open src/tennis_vision/lab_notebook.py and go to line 1651.
  Search: def update_lab_notebook

NOTES:
  None.

---
