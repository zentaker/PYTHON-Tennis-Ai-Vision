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

FUNCTION: build_friction_breakdown
FILE: src/tennis_vision/friction_semantics.py
LINE: 10
AREA: Friction

PURPOSE:
  Builds a multi-dimensional friction breakdown for stage reports.

INPUTS:
  - execution, semantic/model, human-loop, product validation, and downstream correction scores/reasons

OUTPUTS:
  - friction_breakdown dictionary

CALLED BY:
  - future ML/CV stage scripts
  - scripts/run_stage_8_4_bounce_candidate_propagation.py

WHY PRODUCT OWNER CARES:
  Prevents successful script execution from being mistaken for successful product or model validation.

HOW TO FIND IT:
  Open src/tennis_vision/friction_semantics.py and go to line 10.
  Search: def build_friction_breakdown

NOTES:
  None.

---

FUNCTION: summarize_friction_breakdown
FILE: src/tennis_vision/friction_semantics.py
LINE: 36
AREA: Friction

PURPOSE:
  Summarizes multi-dimensional friction in one plain-language sentence.

INPUTS:
  - friction_breakdown dictionary

OUTPUTS:
  - summary string

CALLED BY:
  - stage scripts

WHY PRODUCT OWNER CARES:
  Makes semantic/product friction visible in reports and console summaries.

HOW TO FIND IT:
  Open src/tennis_vision/friction_semantics.py and go to line 36.
  Search: def summarize_friction_breakdown

NOTES:
  None.

---

FUNCTION: classify_product_validation_status
FILE: src/tennis_vision/friction_semantics.py
LINE: 52
AREA: Friction

PURPOSE:
  Normalizes product validation status labels.

INPUTS:
  - status text

OUTPUTS:
  - normalized status

CALLED BY:
  - build_friction_breakdown

WHY PRODUCT OWNER CARES:
  Visual/model outputs need explicit Product Owner validation status.

HOW TO FIND IT:
  Open src/tennis_vision/friction_semantics.py and go to line 52.
  Search: def classify_product_validation_status

NOTES:
  None.

---

FUNCTION: classify_human_loop_level
FILE: src/tennis_vision/friction_semantics.py
LINE: 67
AREA: Friction

PURPOSE:
  Classifies human-loop friction from manual labeling and review requirements.

INPUTS:
  - manual labels required flag
  - manual review required flag
  - new manual stage required flag

OUTPUTS:
  - human-loop friction dimension

CALLED BY:
  - scripts/run_stage_8_4_bounce_candidate_propagation.py

WHY PRODUCT OWNER CARES:
  Manual review burden should be visible even when a script runs cleanly.

HOW TO FIND IT:
  Open src/tennis_vision/friction_semantics.py and go to line 67.
  Search: def classify_human_loop_level

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

FUNCTION: calculate_stage_8_2_friction_score
FILE: src/tennis_vision/friction.py
LINE: 613
AREA: Friction

PURPOSE:
  Calculates friction for Stage 8.2 manual event labeling.

INPUTS:
  - stage-specific warning/error/input flags

OUTPUTS:
  - friction score dictionary

CALLED BY:
  - scripts/run_stage_8_2_event_labeling_helper.py

WHY PRODUCT OWNER CARES:
  Prevents failures and uncertainty from being hidden.

HOW TO FIND IT:
  Open src/tennis_vision/friction.py and go to line 613.
  Search: def calculate_stage_8_2_friction_score

NOTES:
  None.

---

FUNCTION: calculate_stage_8_3_friction_score
FILE: src/tennis_vision/friction.py
LINE: 655
AREA: Friction

PURPOSE:
  Calculates friction for Stage 8.3 event validation.

INPUTS:
  - stage-specific warning/error/input flags

OUTPUTS:
  - friction score dictionary

CALLED BY:
  - scripts/run_stage_8_3_event_validation.py

WHY PRODUCT OWNER CARES:
  Prevents failures and uncertainty from being hidden.

HOW TO FIND IT:
  Open src/tennis_vision/friction.py and go to line 655.
  Search: def calculate_stage_8_3_friction_score

NOTES:
  None.

---

FUNCTION: calculate_stage_8_4_friction_score
FILE: src/tennis_vision/friction.py
LINE: 694
AREA: Friction

PURPOSE:
  Calculates friction for Stage 8.4 bounce candidate propagation.

INPUTS:
  - stage-specific warning/error/input flags

OUTPUTS:
  - friction score dictionary

CALLED BY:
  - scripts/run_stage_8_4_bounce_candidate_propagation.py

WHY PRODUCT OWNER CARES:
  Prevents failures and uncertainty from being hidden.

HOW TO FIND IT:
  Open src/tennis_vision/friction.py and go to line 694.
  Search: def calculate_stage_8_4_friction_score

NOTES:
  None.

---

FUNCTION: calculate_stage_9_friction_score
FILE: src/tennis_vision/friction.py
LINE: 733
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
  Open src/tennis_vision/friction.py and go to line 733.
  Search: def calculate_stage_9_friction_score

NOTES:
  None.

---

FUNCTION: calculate_stage_9_1_friction_score
FILE: src/tennis_vision/friction.py
LINE: 778
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
  Open src/tennis_vision/friction.py and go to line 778.
  Search: def calculate_stage_9_1_friction_score

NOTES:
  None.

---

FUNCTION: calculate_stage_10_friction_score
FILE: src/tennis_vision/friction.py
LINE: 817
AREA: Friction

PURPOSE:
  Calculates friction for Stage 10 analytical reporting.

INPUTS:
  - stage-specific warning/error/input flags

OUTPUTS:
  - friction score dictionary

CALLED BY:
  - scripts/run_stage_10_analytical_report.py

WHY PRODUCT OWNER CARES:
  Prevents failures and uncertainty from being hidden.

HOW TO FIND IT:
  Open src/tennis_vision/friction.py and go to line 817.
  Search: def calculate_stage_10_friction_score

NOTES:
  None.

---

FUNCTION: calculate_stage_11_friction_score
FILE: src/tennis_vision/friction.py
LINE: 859
AREA: Friction

PURPOSE:
  Calculates friction for Stage 11 report packaging.

INPUTS:
  - stage-specific warning/error/input flags

OUTPUTS:
  - friction score dictionary

CALLED BY:
  - scripts/run_stage_11_report_package.py

WHY PRODUCT OWNER CARES:
  Prevents failures and uncertainty from being hidden.

HOW TO FIND IT:
  Open src/tennis_vision/friction.py and go to line 859.
  Search: def calculate_stage_11_friction_score

NOTES:
  None.

---

FUNCTION: calculate_stage_12_friction_score
FILE: src/tennis_vision/friction.py
LINE: 901
AREA: Friction

PURPOSE:
  Calculates friction for Stage 12 replay schema generation.

INPUTS:
  - stage-specific warning/error/input flags

OUTPUTS:
  - friction score dictionary

CALLED BY:
  - scripts/run_stage_12_replay_schema.py

WHY PRODUCT OWNER CARES:
  Prevents failures and uncertainty from being hidden.

HOW TO FIND IT:
  Open src/tennis_vision/friction.py and go to line 901.
  Search: def calculate_stage_12_friction_score

NOTES:
  None.

---

FUNCTION: calculate_stage_13_friction_score
FILE: src/tennis_vision/friction.py
LINE: 943
AREA: Friction

PURPOSE:
  Calculates friction for Stage 13 2D tactical replay rendering.

INPUTS:
  - stage-specific warning/error/input flags

OUTPUTS:
  - friction score dictionary

CALLED BY:
  - scripts/run_stage_13_2d_tactical_replay.py

WHY PRODUCT OWNER CARES:
  Prevents failures and uncertainty from being hidden.

HOW TO FIND IT:
  Open src/tennis_vision/friction.py and go to line 943.
  Search: def calculate_stage_13_friction_score

NOTES:
  None.

---

FUNCTION: calculate_stage_14_friction_score
FILE: src/tennis_vision/friction.py
LINE: 985
AREA: Friction

PURPOSE:
  Calculates friction for Stage 14 side-view replay rendering.

INPUTS:
  - stage-specific warning/error/input flags

OUTPUTS:
  - friction score dictionary

CALLED BY:
  - scripts/run_stage_14_side_view_replay.py

WHY PRODUCT OWNER CARES:
  Prevents failures and uncertainty from being hidden.

HOW TO FIND IT:
  Open src/tennis_vision/friction.py and go to line 985.
  Search: def calculate_stage_14_friction_score

NOTES:
  None.

---

FUNCTION: calculate_stage_14_1_friction_score
FILE: src/tennis_vision/friction.py
LINE: 1027
AREA: Friction

PURPOSE:
  Calculates friction for Stage 14.1 side-view semantics patch.

INPUTS:
  - stage-specific warning/error/input flags

OUTPUTS:
  - friction score dictionary

CALLED BY:
  - scripts/run_stage_14_side_view_replay.py

WHY PRODUCT OWNER CARES:
  Prevents failures and uncertainty from being hidden.

HOW TO FIND IT:
  Open src/tennis_vision/friction.py and go to line 1027.
  Search: def calculate_stage_14_1_friction_score

NOTES:
  None.

---

FUNCTION: calculate_stage_14_2_friction_score
FILE: src/tennis_vision/friction.py
LINE: 1069
AREA: Friction

PURPOSE:
  Calculates friction for Stage 14.2 side-view event disambiguation.

INPUTS:
  - stage-specific warning/error/input flags

OUTPUTS:
  - friction score dictionary

CALLED BY:
  - scripts/run_stage_14_side_view_replay.py

WHY PRODUCT OWNER CARES:
  Prevents failures and uncertainty from being hidden.

HOW TO FIND IT:
  Open src/tennis_vision/friction.py and go to line 1069.
  Search: def calculate_stage_14_2_friction_score

NOTES:
  None.

---

FUNCTION: calculate_stage_14_3_friction_score
FILE: src/tennis_vision/friction.py
LINE: 1114
AREA: Friction

PURPOSE:
  Calculates friction for Stage 14.3 validated-event side-view rendering.

INPUTS:
  - stage-specific warning/error/input flags

OUTPUTS:
  - friction score dictionary

CALLED BY:
  - scripts/run_stage_14_side_view_replay.py

WHY PRODUCT OWNER CARES:
  Prevents failures and uncertainty from being hidden.

HOW TO FIND IT:
  Open src/tennis_vision/friction.py and go to line 1114.
  Search: def calculate_stage_14_3_friction_score

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

## Stage 8.2 - Manual Event Labeling

FUNCTION: dedupe_sorted_frame_indices
FILE: src/tennis_vision/event_labeling.py
LINE: 62
AREA: Stage 8.2 - Manual Event Labeling

PURPOSE:
  Sorts selected frame indices and removes duplicates before timeline review.

INPUTS:
  - requested frame indices

OUTPUTS:
  - sorted unique frame indices
  - duplicate count

CALLED BY:
  - scripts/run_stage_8_2_event_labeling_helper.py
  - collect_event_labels_timeline_viewer

WHY PRODUCT OWNER CARES:
  Prevents confusing repeated frames and makes frame order clear during manual labeling.

HOW TO FIND IT:
  Open src/tennis_vision/event_labeling.py and go to line 62.
  Search: def dedupe_sorted_frame_indices

NOTES:
  Added for Stage 8.2.1 timeline viewer UX patch.

---

FUNCTION: collect_event_labels_interactively
FILE: src/tennis_vision/event_labeling.py
LINE: 295
AREA: Stage 8.2 - Manual Event Labeling

PURPOSE:
  Lets the user label bounce, hit, no_event, uncertain, or skipped frames.

INPUTS:
  - video path
  - selected frames
  - ball labels
  - automatic events
  - OpenCV UI settings

OUTPUTS:
  - new manual event labels
  - frames shown
  - warnings
  - errors

CALLED BY:
  - scripts/run_stage_8_2_event_labeling_helper.py

WHY PRODUCT OWNER CARES:
  This creates ground truth for event validation and prevents side-view replay from guessing event semantics.

HOW TO FIND IT:
  Open src/tennis_vision/event_labeling.py and go to line 295.
  Search: def collect_event_labels_interactively

NOTES:
  None.

---

FUNCTION: collect_event_labels_timeline_viewer
FILE: src/tennis_vision/event_labeling.py
LINE: 665
AREA: Stage 8.2 - Manual Event Labeling

PURPOSE:
  Lets the user review a sorted frame window as an editable timeline before saving labels.
  It lazy-loads frames by default, keeps a small resized-frame cache, supports
  review-only navigation, and keeps event point markers hidden unless toggled.

INPUTS:
  - video path
  - selected frames
  - existing manual labels
  - ball labels
  - automatic events
  - overlay settings

OUTPUTS:
  - changed labels
  - deleted frame labels
  - frames loaded
  - duplicate frames removed
  - created/updated/deleted label counts
  - session backup path

CALLED BY:
  - scripts/run_stage_8_2_event_labeling_helper.py

WHY PRODUCT OWNER CARES:
  Tennis bounce/hit labeling requires watching motion before and after an event, then correcting labels when the exact frame becomes clear.

HOW TO FIND IT:
  Open src/tennis_vision/event_labeling.py and go to line 403.
  Search: def collect_event_labels_timeline_viewer

NOTES:
  Automatic ball marker overlays are off by default in this viewer.

---

FUNCTION: audit_event_labels
FILE: src/tennis_vision/event_labeling.py
LINE: 1459
AREA: Stage 8.2 - Manual Event Labeling

PURPOSE:
  Audits manual event labels for stale points, duplicate frame labels, repeated points, and missing event points.

INPUTS:
  - manual event labels
  - optional selected frame list

OUTPUTS:
  - label integrity audit dictionary

CALLED BY:
  - scripts/run_stage_8_2_event_labeling_helper.py

WHY PRODUCT OWNER CARES:
  Bad manual labels become bad ground truth. The audit catches no_event points and stale repeated points before they poison event validation.

HOW TO FIND IT:
  Open src/tennis_vision/event_labeling.py and go to line 1058.
  Search: def audit_event_labels

NOTES:
  Added for Stage 8.2.2 event labeling UX performance and label integrity patch.

---

FUNCTION: compute_frame_difference
FILE: src/tennis_vision/event_labeling.py
LINE: 320
AREA: Stage 8.2 - Manual Event Labeling

PURPOSE:
  Computes a lightweight visual difference score between adjacent selected frames.

INPUTS:
  - previous frame signature
  - current frame signature

OUTPUTS:
  - mean absolute visual difference score

CALLED BY:
  - build_visual_frame_groups

WHY PRODUCT OWNER CARES:
  Helps identify adjacent frames that are visually identical or nearly identical.

HOW TO FIND IT:
  Open src/tennis_vision/event_labeling.py and search: def compute_frame_difference

NOTES:
  Uses resized grayscale frame signatures, not a trained model.

---

FUNCTION: build_visual_frame_groups
FILE: src/tennis_vision/event_labeling.py
LINE: 394
AREA: Stage 8.2 - Manual Event Labeling

PURPOSE:
  Groups selected frames into near-duplicate visual groups.

INPUTS:
  - selected frame payloads
  - duplicate threshold

OUTPUTS:
  - frame duplicate audit rows
  - per-frame visual group metadata

CALLED BY:
  - analyze_frame_duplicates
  - collect_event_labels_timeline_viewer

WHY PRODUCT OWNER CARES:
  Lets the user label a temporal event window instead of guessing one exact frame.

HOW TO FIND IT:
  Open src/tennis_vision/event_labeling.py and search: def build_visual_frame_groups

NOTES:
  Added for Stage 8.2.3 frame deduplication and event window labeling.

---

FUNCTION: write_frame_duplicate_audit
FILE: src/tennis_vision/event_labeling.py
LINE: 468
AREA: Stage 8.2 - Manual Event Labeling

PURPOSE:
  Writes frame duplicate audit CSV and Markdown files.

INPUTS:
  - visual frame rows
  - duplicate threshold
  - sequential read flag

OUTPUTS:
  - frame_duplicate_audit.csv
  - frame_duplicate_audit.md
  - audit summary

CALLED BY:
  - scripts/run_stage_8_2_event_labeling_helper.py

WHY PRODUCT OWNER CARES:
  Shows whether confusing adjacent frames are truly near-duplicates.

HOW TO FIND IT:
  Open src/tennis_vision/event_labeling.py and search: def write_frame_duplicate_audit

NOTES:
  Plain-text friendly output.

---

FUNCTION: clean_event_labels_for_integrity
FILE: src/tennis_vision/event_labeling.py
LINE: 1545
AREA: Stage 8.2 - Manual Event Labeling

PURPOSE:
  Clears no_event points and collapses duplicate frame labels after a backup is created.

INPUTS:
  - manual event labels
  - preserve_no_event_points flag

OUTPUTS:
  - cleaned labels
  - cleanup summary

CALLED BY:
  - scripts/run_stage_8_2_event_labeling_helper.py

WHY PRODUCT OWNER CARES:
  Keeps no_event labels from looking like physical ball contact events.

HOW TO FIND IT:
  Open src/tennis_vision/event_labeling.py and go to line 1144.
  Search: def clean_event_labels_for_integrity

NOTES:
  Requires --audit-labels --fix-labels and creates a backup first.

---

FUNCTION: compare_manual_events_to_auto_events
FILE: src/tennis_vision/event_labeling.py
LINE: 689
AREA: Stage 8.2 - Manual Event Labeling

PURPOSE:
  Compares manual event labels against automatic event hypotheses.

INPUTS:
  - manual event labels
  - automatic events
  - candidate window

OUTPUTS:
  - comparison rows
  - match summary

CALLED BY:
  - scripts/run_stage_8_2_event_labeling_helper.py

WHY PRODUCT OWNER CARES:
  This reveals whether the model is confusing hits, bounces, and uncertain interactions.

HOW TO FIND IT:
  Open src/tennis_vision/event_labeling.py and go to line 689.
  Search: def compare_manual_events_to_auto_events

NOTES:
  None.

---

FUNCTION: load_durable_event_labels
FILE: src/tennis_vision/event_labeling.py
LINE: 159
AREA: Stage 8.2 - Manual Event Labeling

PURPOSE:
  Loads persisted manual event labels or the latest timestamped session backup.

INPUTS:
  - manual event labels path

OUTPUTS:
  - labels
  - source metadata
  - warnings

CALLED BY:
  - scripts/run_stage_8_2_event_labeling_helper.py

WHY PRODUCT OWNER CARES:
  Manual event labels should persist and become the default validation source.

HOW TO FIND IT:
  Open src/tennis_vision/event_labeling.py and go to line 159.
  Search: def load_durable_event_labels

NOTES:
  None.

---

FUNCTION: write_event_label_session_backup
FILE: src/tennis_vision/event_labeling.py
LINE: 756
AREA: Stage 8.2 - Manual Event Labeling

PURPOSE:
  Writes timestamped backups for labels collected in an interactive session.

INPUTS:
  - session directory
  - timestamp
  - labels

OUTPUTS:
  - backup CSV and JSON paths

CALLED BY:
  - scripts/run_stage_8_2_event_labeling_helper.py

WHY PRODUCT OWNER CARES:
  Protects manual event labeling work from accidental overwrite.

HOW TO FIND IT:
  Open src/tennis_vision/event_labeling.py and go to line 756.
  Search: def write_event_label_session_backup

NOTES:
  None.

---

## Stage 8.3 - Event Validation

FUNCTION: group_manual_event_windows
FILE: src/tennis_vision/event_validation.py
LINE: 72
AREA: Stage 8.3 - Event Validation

PURPOSE:
  Groups adjacent manual bounce labels into one bounce window.

INPUTS:
  - manual event labels
  - bounce window gap

OUTPUTS:
  - manual event window rows

CALLED BY:
  - scripts/run_stage_8_3_event_validation.py

WHY PRODUCT OWNER CARES:
  A real bounce can span several video frames, so nearby bounce labels should not become separate bounces.

HOW TO FIND IT:
  Open src/tennis_vision/event_validation.py and go to line 72.
  Search: def group_manual_event_windows

NOTES:
  None.

---

FUNCTION: classify_validation_status
FILE: src/tennis_vision/event_validation.py
LINE: 206
AREA: Stage 8.3 - Event Validation

PURPOSE:
  Compares one automatic event with nearby manual labels or windows.

INPUTS:
  - automatic event
  - manual evidence
  - manual hit count
  - frame range
  - validation window

OUTPUTS:
  - validation status
  - reason

CALLED BY:
  - build_validation_results

WHY PRODUCT OWNER CARES:
  This makes the automatic event decision explainable before reclassification.

HOW TO FIND IT:
  Open src/tennis_vision/event_validation.py and go to line 206.
  Search: def classify_validation_status

NOTES:
  None.

---

FUNCTION: reclassify_auto_event
FILE: src/tennis_vision/event_reclassification.py
LINE: 11
AREA: Stage 8.3 - Event Validation

PURPOSE:
  Reclassifies automatic hit/bounce hypotheses using manual event labels.

INPUTS:
  - automatic event
  - validation status
  - nearest manual label
  - manual hit count

OUTPUTS:
  - validated event type
  - render role
  - confidence adjustment
  - reason

CALLED BY:
  - scripts/run_stage_8_3_event_validation.py

WHY PRODUCT OWNER CARES:
  This prevents the renderer from showing implausible hits when manual labels indicate bounce or no-event.

HOW TO FIND IT:
  Open src/tennis_vision/event_reclassification.py and go to line 11.
  Search: def reclassify_auto_event

NOTES:
  None.

---

FUNCTION: build_validated_event_timeline
FILE: src/tennis_vision/event_reclassification.py
LINE: 77
AREA: Stage 8.3 - Event Validation

PURPOSE:
  Builds the downstream validated event timeline from validation results.

INPUTS:
  - event validation result rows

OUTPUTS:
  - validated event timeline rows

CALLED BY:
  - scripts/run_stage_8_3_event_validation.py

WHY PRODUCT OWNER CARES:
  Stage 14.3 can consume this instead of raw possible_hit hypotheses.

HOW TO FIND IT:
  Open src/tennis_vision/event_reclassification.py and go to line 77.
  Search: def build_validated_event_timeline

NOTES:
  None.

---

## Stage 8.4 - Bounce Candidate Propagation

FUNCTION: build_manual_hit_windows
FILE: src/tennis_vision/bounce_candidate_propagation.py
LINE: 65
AREA: Stage 8.4 - Bounce Candidate Propagation

PURPOSE:
  Groups manual hit labels into conservative exclusion windows.

INPUTS:
  - manual event label rows
  - hit window gap
  - padding

OUTPUTS:
  - manual hit windows

CALLED BY:
  - scripts/run_stage_8_4_bounce_candidate_propagation.py

WHY PRODUCT OWNER CARES:
  Prevents the system from proposing a manually reviewed hit region as a bounce.

HOW TO FIND IT:
  Open src/tennis_vision/bounce_candidate_propagation.py and go to line 65.
  Search: def build_manual_hit_windows

NOTES:
  None.

---

FUNCTION: learn_bounce_window_signature
FILE: src/tennis_vision/bounce_candidate_propagation.py
LINE: 39
AREA: Stage 8.4 - Bounce Candidate Propagation

PURPOSE:
  Extracts a local motion signature from manually labeled bounce windows.

INPUTS:
  - motion feature rows
  - manual bounce windows

OUTPUTS:
  - weak bounce signature dictionary

CALLED BY:
  - scripts/run_stage_8_4_bounce_candidate_propagation.py

WHY PRODUCT OWNER CARES:
  This is the first step toward using one manual bounce label to find other bounce candidates automatically.

HOW TO FIND IT:
  Open src/tennis_vision/bounce_candidate_propagation.py and go to line 39.
  Search: def learn_bounce_window_signature

NOTES:
  None.

---

FUNCTION: apply_event_sequence_constraints
FILE: src/tennis_vision/bounce_candidate_propagation.py
LINE: 209
AREA: Stage 8.4 - Bounce Candidate Propagation

PURPOSE:
  Applies hit, no_event, uncertain, and post-hit sequence rules to candidate bounce frames.

INPUTS:
  - candidate rows
  - bounce windows
  - hit windows
  - no_event zones
  - uncertain labels
  - features

OUTPUTS:
  - accepted candidate rows
  - constraint summary

CALLED BY:
  - propose_bounce_candidates

WHY PRODUCT OWNER CARES:
  Keeps candidate propagation aligned with tennis event order instead of only local visual similarity.

HOW TO FIND IT:
  Open src/tennis_vision/bounce_candidate_propagation.py and go to line 209.
  Search: def apply_event_sequence_constraints

NOTES:
  None.

---

FUNCTION: search_next_bounce_after_hit
FILE: src/tennis_vision/bounce_candidate_propagation.py
LINE: 280
AREA: Stage 8.4 - Bounce Candidate Propagation

PURPOSE:
  Finds a manual hit after the known bounce and starts next-bounce search after that hit window.

INPUTS:
  - manual bounce windows
  - manual hit windows
  - feature rows

OUTPUTS:
  - post-hit search context

CALLED BY:
  - apply_event_sequence_constraints

WHY PRODUCT OWNER CARES:
  The next bounce should be searched after the player hit, not at the hit frame.

HOW TO FIND IT:
  Open src/tennis_vision/bounce_candidate_propagation.py and go to line 280.
  Search: def search_next_bounce_after_hit

NOTES:
  None.

---

FUNCTION: propose_bounce_candidates
FILE: src/tennis_vision/bounce_candidate_propagation.py
LINE: 178
AREA: Stage 8.4 - Bounce Candidate Propagation

PURPOSE:
  Scores the rest of the trajectory for likely bounce candidates after event-sequence constraints.

INPUTS:
  - motion feature rows
  - manual bounce windows
  - manual hit windows
  - no_event zones
  - uncertain labels
  - score threshold
  - candidate window gap
  - max candidates

OUTPUTS:
  - candidate windows
  - candidate frame rows
  - constraint summary

CALLED BY:
  - scripts/run_stage_8_4_bounce_candidate_propagation.py

WHY PRODUCT OWNER CARES:
  Reduces manual labeling burden by suggesting events for review.

HOW TO FIND IT:
  Open src/tennis_vision/bounce_candidate_propagation.py and go to line 178.
  Search: def propose_bounce_candidates

NOTES:
  None.

---

FUNCTION: compute_local_motion_features
FILE: src/tennis_vision/bounce_pattern_features.py
LINE: 36
AREA: Stage 8.4 - Bounce Candidate Propagation

PURPOSE:
  Computes proxy movement features for projected ball points.

INPUTS:
  - ball sequence rows

OUTPUTS:
  - feature rows with delta, speed, acceleration proxy, and direction-change signals

CALLED BY:
  - scripts/run_stage_8_4_bounce_candidate_propagation.py

WHY PRODUCT OWNER CARES:
  Bounce propagation needs local motion evidence without claiming physical truth.

HOW TO FIND IT:
  Open src/tennis_vision/bounce_pattern_features.py and go to line 36.
  Search: def compute_local_motion_features

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

## Stage 10 - Analytical Report

FUNCTION: read_stage_inputs
FILE: src/tennis_vision/analytical_report.py
LINE: 27
AREA: Stage 10 - Analytical Report

PURPOSE:
  Loads Stage 10 input files from Stage 9.1, Stage 8.1, Stage 7.1, and Stage 6.

INPUTS:
  - input path map

OUTPUTS:
  - loaded row collections
  - warnings
  - errors

CALLED BY:
  - scripts/run_stage_10_analytical_report.py

WHY PRODUCT OWNER CARES:
  This controls which upstream evidence is used in the final analytical report.

HOW TO FIND IT:
  Open src/tennis_vision/analytical_report.py and go to line 27.
  Search: def read_stage_inputs

NOTES:
  None.

---

FUNCTION: build_analysis_summary
FILE: src/tennis_vision/analytical_report.py
LINE: 137
AREA: Stage 10 - Analytical Report

PURPOSE:
  Builds one structured summary of placement, direction, player, event, and rally evidence.

INPUTS:
  - loaded Stage 10 data

OUTPUTS:
  - summary dictionary

CALLED BY:
  - scripts/run_stage_10_analytical_report.py

WHY PRODUCT OWNER CARES:
  This is the data model behind the player-readable report.

HOW TO FIND IT:
  Open src/tennis_vision/analytical_report.py and go to line 137.
  Search: def build_analysis_summary

NOTES:
  None.

---

FUNCTION: build_plain_language_report
FILE: src/tennis_vision/analytical_report.py
LINE: 147
AREA: Stage 10 - Analytical Report

PURPOSE:
  Converts tactical metrics and validated timeline evidence into a readable report.

INPUTS:
  - summary
  - key findings
  - coaching observations
  - confidence
  - paths
  - verdict

OUTPUTS:
  - plain-text-friendly Markdown report content

CALLED BY:
  - scripts/run_stage_10_analytical_report.py

WHY PRODUCT OWNER CARES:
  This is the first stage where raw analysis becomes a player-readable explanation.

HOW TO FIND IT:
  Open src/tennis_vision/analytical_report.py and go to line 147.
  Search: def build_plain_language_report

NOTES:
  The wording preserves possible_* uncertainty and avoids official coaching claims.

---

FUNCTION: build_coaching_observations
FILE: src/tennis_vision/coaching_summary.py
LINE: 19
AREA: Stage 10 - Analytical Report

PURPOSE:
  Builds cautious rule-based coaching-style observations from the analytical summary.

INPUTS:
  - analysis summary
  - confidence summary

OUTPUTS:
  - observation dictionaries

CALLED BY:
  - scripts/run_stage_10_analytical_report.py

WHY PRODUCT OWNER CARES:
  This gives the Product Owner readable observations without external AI or overclaiming.

HOW TO FIND IT:
  Open src/tennis_vision/coaching_summary.py and go to line 19.
  Search: def build_coaching_observations

NOTES:
  None.

---

FUNCTION: build_key_findings
FILE: src/tennis_vision/coaching_summary.py
LINE: 80
AREA: Stage 10 - Analytical Report

PURPOSE:
  Builds short report findings for the executive summary.

INPUTS:
  - analysis summary
  - confidence summary

OUTPUTS:
  - short finding strings

CALLED BY:
  - scripts/run_stage_10_analytical_report.py

WHY PRODUCT OWNER CARES:
  Key findings help a player or Product Owner scan the report quickly.

HOW TO FIND IT:
  Open src/tennis_vision/coaching_summary.py and go to line 80.
  Search: def build_key_findings

NOTES:
  None.

---

FUNCTION: evaluate_report_confidence
FILE: src/tennis_vision/report_confidence.py
LINE: 36
AREA: Stage 10 - Analytical Report

PURPOSE:
  Scores confidence from labels, projection coverage, candidate distance, event support, and player identity context.

INPUTS:
  - evidence counts
  - candidate validation rows

OUTPUTS:
  - confidence level
  - reasons
  - limitations
  - validation steps

CALLED BY:
  - scripts/run_stage_10_analytical_report.py

WHY PRODUCT OWNER CARES:
  This prevents the final report from sounding more certain than the evidence supports.

HOW TO FIND IT:
  Open src/tennis_vision/report_confidence.py and go to line 36.
  Search: def evaluate_report_confidence

NOTES:
  None.

---

## Stage 11 - Report Package

FUNCTION: build_report_package
FILE: src/tennis_vision/report_package.py
LINE: 41
AREA: Stage 11 - Report Package

PURPOSE:
  Collects selected analysis outputs into a clean delivery package.

INPUTS:
  - package root
  - artifact descriptors
  - copy mode

OUTPUTS:
  - updated artifact descriptors
  - warnings

CALLED BY:
  - scripts/run_stage_11_report_package.py

WHY PRODUCT OWNER CARES:
  This creates the first shareable output bundle from the whole analysis pipeline.

HOW TO FIND IT:
  Open src/tennis_vision/report_package.py and go to line 41.
  Search: def build_report_package

NOTES:
  None.

---

FUNCTION: write_package_readme
FILE: src/tennis_vision/report_package.py
LINE: 52
AREA: Stage 11 - Report Package

PURPOSE:
  Writes the package README with status, contents, limitations, and reading order.

INPUTS:
  - README path
  - verdict
  - confidence
  - timestamp
  - next step

OUTPUTS:
  - package README

CALLED BY:
  - scripts/run_stage_11_report_package.py

WHY PRODUCT OWNER CARES:
  The README is the first file a Product Owner should open in the deliverable package.

HOW TO FIND IT:
  Open src/tennis_vision/report_package.py and go to line 52.
  Search: def write_package_readme

NOTES:
  None.

---

FUNCTION: write_package_index
FILE: src/tennis_vision/report_package.py
LINE: 104
AREA: Stage 11 - Report Package

PURPOSE:
  Writes a vertical-block index for every included or missing package artifact.

INPUTS:
  - index path
  - artifact descriptors

OUTPUTS:
  - package_index.md

CALLED BY:
  - scripts/run_stage_11_report_package.py

WHY PRODUCT OWNER CARES:
  This makes the package readable without guessing where files came from.

HOW TO FIND IT:
  Open src/tennis_vision/report_package.py and go to line 104.
  Search: def write_package_index

NOTES:
  None.

---

FUNCTION: build_manifest
FILE: src/tennis_vision/package_manifest.py
LINE: 32
AREA: Stage 11 - Report Package

PURPOSE:
  Builds package_manifest.json with included and missing artifacts.

INPUTS:
  - package metadata
  - artifact descriptors
  - warnings
  - errors

OUTPUTS:
  - manifest dictionary

CALLED BY:
  - scripts/run_stage_11_report_package.py

WHY PRODUCT OWNER CARES:
  The manifest gives future UI/reporting code a structured package inventory.

HOW TO FIND IT:
  Open src/tennis_vision/package_manifest.py and go to line 32.
  Search: def build_manifest

NOTES:
  None.

---

FUNCTION: write_manifest
FILE: src/tennis_vision/package_manifest.py
LINE: 63
AREA: Stage 11 - Report Package

PURPOSE:
  Writes the Stage 11 package manifest JSON.

INPUTS:
  - manifest path
  - manifest dictionary

OUTPUTS:
  - package_manifest.json

CALLED BY:
  - scripts/run_stage_11_report_package.py

WHY PRODUCT OWNER CARES:
  This is the machine-readable handoff file for the package.

HOW TO FIND IT:
  Open src/tennis_vision/package_manifest.py and go to line 63.
  Search: def write_manifest

NOTES:
  None.

---

## Stage 12 - Replay Schema

FUNCTION: load_replay_inputs
FILE: src/tennis_vision/replay_data_builder.py
LINE: 41
AREA: Stage 12 - Replay Schema

PURPOSE:
  Loads upstream court, trajectory, timeline, player, tactical, report, and package data for replay schema generation.

INPUTS:
  - source path dictionary

OUTPUTS:
  - loaded replay source data
  - warnings
  - errors

CALLED BY:
  - scripts/run_stage_12_replay_schema.py

WHY PRODUCT OWNER CARES:
  This gathers the evidence that future replay renderers will consume.

HOW TO FIND IT:
  Open src/tennis_vision/replay_data_builder.py and go to line 41.
  Search: def load_replay_inputs

NOTES:
  None.

---

FUNCTION: build_replay_schema
FILE: src/tennis_vision/replay_data_builder.py
LINE: 286
AREA: Stage 12 - Replay Schema

PURPOSE:
  Builds the replay data contract from court, trajectory, player, timeline and tactical outputs.

INPUTS:
  - loaded replay data
  - source paths
  - timestamp
  - schema version

OUTPUTS:
  - replay schema dictionary

CALLED BY:
  - scripts/run_stage_12_replay_schema.py

WHY PRODUCT OWNER CARES:
  This is the bridge between analysis data and future synthetic replay videos.

HOW TO FIND IT:
  Open src/tennis_vision/replay_data_builder.py and go to line 286.
  Search: def build_replay_schema

NOTES:
  None.

---

FUNCTION: build_ball_trajectory
FILE: src/tennis_vision/replay_data_builder.py
LINE: 172
AREA: Stage 12 - Replay Schema

PURPOSE:
  Builds raw, smoothed, and replay keyframe ball trajectory sections.

INPUTS:
  - Stage 6 trajectory rows
  - Stage 9.1 tuned zone rows

OUTPUTS:
  - raw_ball_points
  - smoothed_ball_points
  - replay_keyframes

CALLED BY:
  - build_replay_schema

WHY PRODUCT OWNER CARES:
  Replay renderers need ball keyframes before any synthetic playback can be built.

HOW TO FIND IT:
  Open src/tennis_vision/replay_data_builder.py and go to line 172.
  Search: def build_ball_trajectory

NOTES:
  None.

---

FUNCTION: build_event_timeline
FILE: src/tennis_vision/replay_data_builder.py
LINE: 208
AREA: Stage 12 - Replay Schema

PURPOSE:
  Converts validated possible_* events into replay event records.

INPUTS:
  - Stage 8.1 validated timeline rows

OUTPUTS:
  - event timeline list

CALLED BY:
  - build_replay_schema

WHY PRODUCT OWNER CARES:
  Future renderers need event markers while preserving uncertainty.

HOW TO FIND IT:
  Open src/tennis_vision/replay_data_builder.py and go to line 208.
  Search: def build_event_timeline

NOTES:
  None.

---

FUNCTION: build_camera_profiles
FILE: src/tennis_vision/replay_camera_presets.py
LINE: 8
AREA: Stage 12 - Replay Schema

PURPOSE:
  Defines deterministic camera presets for future replay renderers.

INPUTS:
  - none

OUTPUTS:
  - camera profile list

CALLED BY:
  - build_replay_schema
  - scripts/run_stage_12_replay_schema.py

WHY PRODUCT OWNER CARES:
  Camera presets define future replay views without implying multi-angle video exists today.

HOW TO FIND IT:
  Open src/tennis_vision/replay_camera_presets.py and go to line 8.
  Search: def build_camera_profiles

NOTES:
  None.

---

FUNCTION: build_visual_layers
FILE: src/tennis_vision/replay_schema.py
LINE: 15
AREA: Stage 12 - Replay Schema

PURPOSE:
  Defines renderer layer contracts for court, players, ball, trajectory, events, zones, timeline, and confidence overlays.

INPUTS:
  - none

OUTPUTS:
  - visual layer list

CALLED BY:
  - build_replay_schema

WHY PRODUCT OWNER CARES:
  Renderer layers make uncertainty and required data explicit before video generation work begins.

HOW TO FIND IT:
  Open src/tennis_vision/replay_schema.py and go to line 15.
  Search: def build_visual_layers

NOTES:
  None.

---

FUNCTION: build_renderer_hints
FILE: src/tennis_vision/replay_schema.py
LINE: 85
AREA: Stage 12 - Replay Schema

PURPOSE:
  Defines deterministic renderer policy, initial renderer recommendation, and uncertainty display rules.

INPUTS:
  - none

OUTPUTS:
  - renderer hints dictionary

CALLED BY:
  - build_replay_schema

WHY PRODUCT OWNER CARES:
  This keeps future replay work local, deterministic, and honest about uncertainty.

HOW TO FIND IT:
  Open src/tennis_vision/replay_schema.py and go to line 85.
  Search: def build_renderer_hints

NOTES:
  None.

---

FUNCTION: build_pretty_markdown
FILE: src/tennis_vision/replay_data_builder.py
LINE: 361
AREA: Stage 12 - Replay Schema

PURPOSE:
  Writes a plain-text-friendly summary of the replay schema.

INPUTS:
  - schema
  - verdict
  - friction
  - next step

OUTPUTS:
  - Markdown text

CALLED BY:
  - scripts/run_stage_12_replay_schema.py

WHY PRODUCT OWNER CARES:
  The Product Owner can inspect what replay-ready data exists without opening JSON.

HOW TO FIND IT:
  Open src/tennis_vision/replay_data_builder.py and go to line 361.
  Search: def build_pretty_markdown

NOTES:
  None.

---

## Stage 13 - 2D Tactical Replay

FUNCTION: load_replay_schema
FILE: src/tennis_vision/replay_renderer_2d.py
LINE: 15
AREA: Stage 13 - 2D Tactical Replay

PURPOSE:
  Loads the Stage 12 replay schema for rendering.

INPUTS:
  - replay schema path

OUTPUTS:
  - schema dictionary
  - warnings
  - errors

CALLED BY:
  - scripts/run_stage_13_2d_tactical_replay.py

WHY PRODUCT OWNER CARES:
  This ensures the renderer consumes the schema contract instead of inventing data.

HOW TO FIND IT:
  Open src/tennis_vision/replay_renderer_2d.py and go to line 15.
  Search: def load_replay_schema

NOTES:
  None.

---

FUNCTION: create_court_canvas
FILE: src/tennis_vision/replay_renderer_2d.py
LINE: 45
AREA: Stage 13 - 2D Tactical Replay

PURPOSE:
  Creates the base image canvas and normalized court coordinate transform.

INPUTS:
  - court model

OUTPUTS:
  - OpenCV image canvas
  - court-to-canvas transform

CALLED BY:
  - render_replay_frame

WHY PRODUCT OWNER CARES:
  This converts court-space analysis data into visible replay coordinates.

HOW TO FIND IT:
  Open src/tennis_vision/replay_renderer_2d.py and go to line 45.
  Search: def create_court_canvas

NOTES:
  None.

---

FUNCTION: render_replay_frame
FILE: src/tennis_vision/replay_renderer_2d.py
LINE: 194
AREA: Stage 13 - 2D Tactical Replay

PURPOSE:
  Renders one deterministic 2D tactical replay frame from court, ball, player and event data.

INPUTS:
  - schema
  - display points
  - current frame index
  - players
  - events

OUTPUTS:
  - rendered OpenCV image

CALLED BY:
  - render_replay_frames

WHY PRODUCT OWNER CARES:
  This is the first step where analysis data becomes a generated visual replay.

HOW TO FIND IT:
  Open src/tennis_vision/replay_renderer_2d.py and go to line 194.
  Search: def render_replay_frame

NOTES:
  None.

---

FUNCTION: render_replay_frames
FILE: src/tennis_vision/replay_renderer_2d.py
LINE: 218
AREA: Stage 13 - 2D Tactical Replay

PURPOSE:
  Renders all replay frames to the Stage 13 frames folder.

INPUTS:
  - schema
  - output directory
  - interpolation settings

OUTPUTS:
  - frame paths
  - render context
  - warnings
  - errors

CALLED BY:
  - scripts/run_stage_13_2d_tactical_replay.py

WHY PRODUCT OWNER CARES:
  Frame rendering is the primary success condition even if MP4 export is unavailable.

HOW TO FIND IT:
  Open src/tennis_vision/replay_renderer_2d.py and go to line 218.
  Search: def render_replay_frames

NOTES:
  None.

---

FUNCTION: export_replay_video
FILE: src/tennis_vision/replay_renderer_2d.py
LINE: 247
AREA: Stage 13 - 2D Tactical Replay

PURPOSE:
  Attempts MP4 export from rendered frames using OpenCV VideoWriter.

INPUTS:
  - frame paths
  - output video path
  - fps

OUTPUTS:
  - video generated flag
  - warnings
  - errors

CALLED BY:
  - scripts/run_stage_13_2d_tactical_replay.py

WHY PRODUCT OWNER CARES:
  Video export is useful but codec-dependent, so it is separated from core frame rendering.

HOW TO FIND IT:
  Open src/tennis_vision/replay_renderer_2d.py and go to line 247.
  Search: def export_replay_video

NOTES:
  None.

---

FUNCTION: build_display_points
FILE: src/tennis_vision/replay_renderer_2d.py
LINE: 306
AREA: Stage 13 - 2D Tactical Replay

PURPOSE:
  Creates measured and visual-only interpolated replay display points.

INPUTS:
  - replay keyframes
  - interpolation settings

OUTPUTS:
  - display point list

CALLED BY:
  - render_replay_frames

WHY PRODUCT OWNER CARES:
  It makes smoother animation possible while marking interpolated points as visual only.

HOW TO FIND IT:
  Open src/tennis_vision/replay_renderer_2d.py and go to line 306.
  Search: def build_display_points

NOTES:
  None.

---

## Stage 14 - Side-View Replay

FUNCTION: estimate_synthetic_height
FILE: src/tennis_vision/ball_flight_estimator.py
LINE: 37
AREA: Stage 14 - Side-View Replay

PURPOSE:
  Creates a synthetic height profile for side-view replay when measured 3D height is unavailable.

INPUTS:
  - sequence index
  - total points
  - nearby event type

OUTPUTS:
  - synthetic height value

CALLED BY:
  - build_side_view_keyframes

WHY PRODUCT OWNER CARES:
  This enables side-view analytical video without pretending the system measured real ball height.

HOW TO FIND IT:
  Open src/tennis_vision/ball_flight_estimator.py and go to line 37.
  Search: def estimate_synthetic_height

NOTES:
  None.

---

FUNCTION: build_side_view_keyframes
FILE: src/tennis_vision/ball_flight_estimator.py
LINE: 254
AREA: Stage 14 - Side-View Replay

PURPOSE:
  Builds side-view keyframes with court depth and synthetic height annotations.

INPUTS:
  - replay schema

OUTPUTS:
  - side-view keyframe rows

CALLED BY:
  - scripts/run_stage_14_side_view_replay.py
  - render_side_view_frames

WHY PRODUCT OWNER CARES:
  This converts the replay schema into the side-view renderer's data model.

HOW TO FIND IT:
  Open src/tennis_vision/ball_flight_estimator.py and go to line 254.
  Search: def build_side_view_keyframes

NOTES:
  None.

---

FUNCTION: interpolate_side_view_motion
FILE: src/tennis_vision/ball_flight_estimator.py
LINE: 309
AREA: Stage 14 - Side-View Replay

PURPOSE:
  Creates visual-only interpolation points between side-view keyframes.

INPUTS:
  - side-view keyframes
  - interpolation settings

OUTPUTS:
  - side-view display points

CALLED BY:
  - render_side_view_frames

WHY PRODUCT OWNER CARES:
  It smooths the animation while keeping interpolated positions distinct from measured keyframes.

HOW TO FIND IT:
  Open src/tennis_vision/ball_flight_estimator.py and go to line 309.
  Search: def interpolate_side_view_motion

NOTES:
  None.

---

FUNCTION: render_side_view_frame
FILE: src/tennis_vision/replay_renderer_side_view.py
LINE: 253
AREA: Stage 14 - Side-View Replay

PURPOSE:
  Renders one side-view ball flight frame with court depth, net, synthetic arc, players, events, and timeline.

INPUTS:
  - schema
  - display points
  - current index
  - players
  - events

OUTPUTS:
  - rendered OpenCV image

CALLED BY:
  - render_side_view_frames

WHY PRODUCT OWNER CARES:
  This creates the first side-view replay visualization from analysis data.

HOW TO FIND IT:
  Open src/tennis_vision/replay_renderer_side_view.py and go to line 253.
  Search: def render_side_view_frame

NOTES:
  None.

---

FUNCTION: render_side_view_frames
FILE: src/tennis_vision/replay_renderer_side_view.py
LINE: 279
AREA: Stage 14 - Side-View Replay

PURPOSE:
  Renders all side-view frames to the Stage 14 frames folder.

INPUTS:
  - schema
  - output directory
  - interpolation settings

OUTPUTS:
  - frame paths
  - render context
  - warnings
  - errors

CALLED BY:
  - scripts/run_stage_14_side_view_replay.py

WHY PRODUCT OWNER CARES:
  Frame rendering is the primary success condition for the side-view replay.

HOW TO FIND IT:
  Open src/tennis_vision/replay_renderer_side_view.py and go to line 279.
  Search: def render_side_view_frames

NOTES:
  None.

---

FUNCTION: export_side_view_video
FILE: src/tennis_vision/replay_renderer_side_view.py
LINE: 313
AREA: Stage 14 - Side-View Replay

PURPOSE:
  Attempts MP4 export from side-view frames using OpenCV VideoWriter.

INPUTS:
  - frame paths
  - output video path
  - fps

OUTPUTS:
  - video generated flag
  - warnings
  - errors

CALLED BY:
  - scripts/run_stage_14_side_view_replay.py

WHY PRODUCT OWNER CARES:
  Video export is useful but codec-dependent, so it is not required for renderer success.

HOW TO FIND IT:
  Open src/tennis_vision/replay_renderer_side_view.py and go to line 313.
  Search: def export_side_view_video

NOTES:
  None.

---

## Stage 14.1 - Side-View Patch

FUNCTION: classify_height_anchor_type
FILE: src/tennis_vision/ball_flight_estimator.py
LINE: 50
AREA: Stage 14.1 - Side-View Patch

PURPOSE:
  Classifies replay events into bounce, hit, interaction, arc, or interpolation height roles.

INPUTS:
  - event type

OUTPUTS:
  - height anchor type

CALLED BY:
  - estimate_synthetic_height
  - build_side_view_keyframes

WHY PRODUCT OWNER CARES:
  This lets the side-view renderer treat bounce and hit moments differently.

HOW TO FIND IT:
  Open src/tennis_vision/ball_flight_estimator.py and go to line 50.
  Search: def classify_height_anchor_type

NOTES:
  None.

---

FUNCTION: enforce_bounce_floor_contact
FILE: src/tennis_vision/ball_flight_estimator.py
LINE: 230
AREA: Stage 14.1 - Side-View Patch

PURPOSE:
  Forces bounce-like events to visually ground near court surface in side-view replay.

INPUTS:
  - synthetic height

OUTPUTS:
  - floor-grounded synthetic height

CALLED BY:
  - estimate_synthetic_height
  - estimate_semantic_height_profile

WHY PRODUCT OWNER CARES:
  This makes the replay visually interpretable as tennis instead of showing floating bounces.

HOW TO FIND IT:
  Open src/tennis_vision/ball_flight_estimator.py and go to line 230.
  Search: def enforce_bounce_floor_contact

NOTES:
  None.

---

FUNCTION: enforce_hit_contact_band
FILE: src/tennis_vision/ball_flight_estimator.py
LINE: 235
AREA: Stage 14.1 - Side-View Patch

PURPOSE:
  Constrains hit-like events to a plausible synthetic contact-height band.

INPUTS:
  - synthetic height

OUTPUTS:
  - contact-band synthetic height

CALLED BY:
  - estimate_synthetic_height
  - estimate_semantic_height_profile

WHY PRODUCT OWNER CARES:
  Hit markers should look plausible without claiming real measured 3D height.

HOW TO FIND IT:
  Open src/tennis_vision/ball_flight_estimator.py and go to line 235.
  Search: def enforce_hit_contact_band

NOTES:
  None.

---

FUNCTION: estimate_semantic_height_profile
FILE: src/tennis_vision/ball_flight_estimator.py
LINE: 192
AREA: Stage 14.1 - Side-View Patch

PURPOSE:
  Creates a semantically constrained synthetic height profile.

INPUTS:
  - side-view point records

OUTPUTS:
  - synthetic height values

CALLED BY:
  - build_side_view_keyframes

WHY PRODUCT OWNER CARES:
  This keeps the side-view useful without pretending the system measured real 3D height.

HOW TO FIND IT:
  Open src/tennis_vision/ball_flight_estimator.py and go to line 192.
  Search: def estimate_semantic_height_profile

NOTES:
  None.

---

FUNCTION: annotate_interpolated_height_points
FILE: src/tennis_vision/ball_flight_estimator.py
LINE: 240
AREA: Stage 14.1 - Side-View Patch

PURPOSE:
  Marks interpolated side-view points as visual estimates.

INPUTS:
  - side-view display points

OUTPUTS:
  - annotated display points

CALLED BY:
  - interpolate_side_view_motion

WHY PRODUCT OWNER CARES:
  Interpolated points must not be mistaken for measured or event-anchored truth.

HOW TO FIND IT:
  Open src/tennis_vision/ball_flight_estimator.py and go to line 240.
  Search: def annotate_interpolated_height_points

NOTES:
  None.

---

FUNCTION: create_semantic_debug_image
FILE: src/tennis_vision/replay_renderer_side_view.py
LINE: 365
AREA: Stage 14.1 - Side-View Patch

PURPOSE:
  Writes a diagnostic side-view image showing semantic anchors and labels.

INPUTS:
  - schema
  - side-view keyframes
  - display points
  - events
  - players
  - output path

OUTPUTS:
  - semantic debug image

CALLED BY:
  - scripts/run_stage_14_side_view_replay.py

WHY PRODUCT OWNER CARES:
  The Product Owner can inspect whether bounces are grounded and hits/interpolation are labeled clearly.

HOW TO FIND IT:
  Open src/tennis_vision/replay_renderer_side_view.py and go to line 365.
  Search: def create_semantic_debug_image

NOTES:
  None.

---

## Stage 14.2 - Side-View Event Disambiguation

FUNCTION: estimate_player_contact_window
FILE: src/tennis_vision/ball_flight_estimator.py
LINE: 74
AREA: Stage 14.2 - Side-View Event Disambiguation

PURPOSE:
  Estimates a conservative court-depth window where a player could plausibly contact the ball.

INPUTS:
  - player record
  - event frame
  - depth tolerance

OUTPUTS:
  - player contact window dictionary

CALLED BY:
  - score_hit_plausibility

WHY PRODUCT OWNER CARES:
  Hit labels should be constrained by where the player actually is, not only by ball trajectory shape.

HOW TO FIND IT:
  Open src/tennis_vision/ball_flight_estimator.py and go to line 74.
  Search: def estimate_player_contact_window

NOTES:
  None.

---

FUNCTION: is_hit_plausible_for_player
FILE: src/tennis_vision/ball_flight_estimator.py
LINE: 138
AREA: Stage 14.2 - Side-View Event Disambiguation

PURPOSE:
  Tests whether a candidate hit is plausible relative to player position and court depth.

INPUTS:
  - event record
  - players
  - depth tolerance

OUTPUTS:
  - boolean plausibility result

CALLED BY:
  - classify_event_semantic_role

WHY PRODUCT OWNER CARES:
  This prevents the renderer from labeling clearly implausible in-court positions as hits.

HOW TO FIND IT:
  Open src/tennis_vision/ball_flight_estimator.py and go to line 138.
  Search: def is_hit_plausible_for_player

NOTES:
  None.

---

FUNCTION: score_hit_plausibility
FILE: src/tennis_vision/ball_flight_estimator.py
LINE: 97
AREA: Stage 14.2 - Side-View Event Disambiguation

PURPOSE:
  Scores possible_hit events against attributed player depth.

INPUTS:
  - event record
  - players
  - depth tolerance

OUTPUTS:
  - plausibility score and explanation

CALLED BY:
  - is_hit_plausible_for_player
  - downgrade_implausible_hits

WHY PRODUCT OWNER CARES:
  The Product Owner can see why a hit label was accepted or downgraded.

HOW TO FIND IT:
  Open src/tennis_vision/ball_flight_estimator.py and go to line 97.
  Search: def score_hit_plausibility

NOTES:
  None.

---

FUNCTION: downgrade_implausible_hits
FILE: src/tennis_vision/ball_flight_estimator.py
LINE: 143
AREA: Stage 14.2 - Side-View Event Disambiguation

PURPOSE:
  Assigns render roles and downgrades raw possible_hit events that fail player-aware plausibility.

INPUTS:
  - event records
  - player records

OUTPUTS:
  - enriched events
  - render-role summary

CALLED BY:
  - build_side_view_keyframes
  - render_side_view_frames
  - scripts/run_stage_14_side_view_replay.py

WHY PRODUCT OWNER CARES:
  It preserves raw event evidence while avoiding misleading hit labels in the replay.

HOW TO FIND IT:
  Open src/tennis_vision/ball_flight_estimator.py and go to line 143.
  Search: def downgrade_implausible_hits

NOTES:
  None.

---

FUNCTION: assign_event_render_role
FILE: src/tennis_vision/replay_renderer_side_view.py
LINE: 490
AREA: Stage 14.2 - Side-View Event Disambiguation

PURPOSE:
  Separates raw event labels from final side-view render roles.

INPUTS:
  - event record

OUTPUTS:
  - render role

CALLED BY:
  - render_event_markers
  - render_timeline_strip

WHY PRODUCT OWNER CARES:
  This makes the side-view easier to read and prevents ambiguous tennis interpretation.

HOW TO FIND IT:
  Open src/tennis_vision/replay_renderer_side_view.py and go to line 490.
  Search: def assign_event_render_role

NOTES:
  None.

---

## Stage 14.3 - Validated Events Side-View

FUNCTION: load_validated_event_source
FILE: src/tennis_vision/validated_event_source.py
LINE: 18
AREA: Stage 14.3 - Validated Events Side-View

PURPOSE:
  Loads Stage 8.3 validated events as the preferred source for side-view rendering.

INPUTS:
  - project root
  - replay schema
  - optional preferred Stage 8.3 path

OUTPUTS:
  - normalized events
  - source metadata
  - warnings
  - errors
  - render summary

CALLED BY:
  - scripts/run_stage_14_side_view_replay.py

WHY PRODUCT OWNER CARES:
  Prevents raw automatic possible hits from being rendered as physical events.

HOW TO FIND IT:
  Open src/tennis_vision/validated_event_source.py and go to line 18.
  Search: def load_validated_event_source

NOTES:
  None.

---

FUNCTION: map_validated_event_to_render_role
FILE: src/tennis_vision/validated_event_source.py
LINE: 74
AREA: Stage 14.3 - Validated Events Side-View

PURPOSE:
  Converts validated and reclassified event labels into physical or annotation render roles.

INPUTS:
  - event row
  - source name
  - replay schema

OUTPUTS:
  - normalized event record with render policy

CALLED BY:
  - load_validated_event_source

WHY PRODUCT OWNER CARES:
  Separates real visual contact markers from uncertain model guesses.

HOW TO FIND IT:
  Open src/tennis_vision/validated_event_source.py and go to line 74.
  Search: def map_validated_event_to_render_role

NOTES:
  None.

---

FUNCTION: summarize_validated_render_events
FILE: src/tennis_vision/validated_event_source.py
LINE: 161
AREA: Stage 14.3 - Validated Events Side-View

PURPOSE:
  Counts validated bounces, validated hits, downgraded hit annotations, rejected events, and unvalidated annotations.

INPUTS:
  - normalized event records

OUTPUTS:
  - render count summary

CALLED BY:
  - scripts/run_stage_14_side_view_replay.py

WHY PRODUCT OWNER CARES:
  The Product Owner can confirm that no unvalidated hit is being rendered as a physical contact.

HOW TO FIND IT:
  Open src/tennis_vision/validated_event_source.py and go to line 161.
  Search: def summarize_validated_render_events

NOTES:
  None.

---

FUNCTION: create_validated_events_debug_image
FILE: src/tennis_vision/replay_renderer_side_view.py
LINE: 429
AREA: Stage 14.3 - Validated Events Side-View

PURPOSE:
  Creates a debug image showing the main ball path, validated event source, and annotation policy.

INPUTS:
  - schema
  - display points
  - events
  - players
  - output path
  - event source

OUTPUTS:
  - validated-event debug image

CALLED BY:
  - scripts/run_stage_14_side_view_replay.py

WHY PRODUCT OWNER CARES:
  This lets the Product Owner verify that validated bounces are grounded and unvalidated hits are annotations only.

HOW TO FIND IT:
  Open src/tennis_vision/replay_renderer_side_view.py and go to line 429.
  Search: def create_validated_events_debug_image

NOTES:
  None.

---

## Lab Notebook

FUNCTION: update_lab_notebook
FILE: src/tennis_vision/lab_notebook.py
LINE: 2613
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
  Open src/tennis_vision/lab_notebook.py and go to line 2613.
  Search: def update_lab_notebook

NOTES:
  None.

---
