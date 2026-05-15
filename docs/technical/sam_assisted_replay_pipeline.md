# SAM-Assisted Replay Pipeline

PURPOSE
  Provides an experimental SAM/SAM2-assisted alternative for ball localization.
  This is a second candidate path while TrackNet remains the preferred tennis
  ball tracking direction.

SETUP DOC
  docs/technical/sam_assisted_setup.md

PRIMARY COMMAND
  python scripts/run_sam_assisted_replay_pipeline.py

SETUP CHECK
  python scripts/check_sam_assisted_integration.py

INPUTS
  samples/video_01.mov
  configs/manual_annotations/video_01_full_rally.json
  configs/models/sam_assisted_config.json
  outputs/reports/stage_3_court_calibration_probe_report.json

OUTPUTS
  outputs/sam_replay/video_01/ball_tracking_results.csv
  outputs/sam_replay/video_01/projected_ball_positions.csv
  outputs/sam_replay/video_01/event_position_results.csv
  outputs/sam_replay/video_01/replay_schema.json
  outputs/sam_replay/video_01/sam_replay_report.json
  outputs/sam_replay/video_01/sam_replay_report.md
  outputs/reports/sam_assisted_replay_pipeline_report.json
  outputs/reports/sam_assisted_replay_pipeline_report.md

WEIGHT LOCATIONS
  models/sam/weights/sam.pt
  models/sam/weights/sam.pth
  models/sam/weights/sam_vit_b.pth
  models/sam/weights/sam_vit_l.pth
  models/sam/weights/sam_vit_h.pth
  models/sam2/weights/sam2.pt
  models/sam2/weights/sam2.pth
  models/sam2/checkpoints/

DATA CONTRACT
  The Product Owner provides manual event timing.
  SAM/SAM2 may assist segmentation only when:
  - local dependency is installed;
  - compatible weights exist locally;
  - a trusted ball seed point exists near the event window.

  If no seed exists, the pipeline reports:
  blocked_seed_missing

WHY SEEDS MATTER
  SAM is not a tennis ball tracker by itself. It segments from prompts.
  Without a trusted ball prompt, the pipeline must not guess where the ball is.

REPLAY SAFETY
  Only valid sequence-validated event positions may render as physical anchors.
  Suspicious, invalid, or unresolved events stay annotation-only.
  Top-view and side-view replays are skipped if they would require fake
  anchors.

IMPORTANT FUNCTIONS
  FUNCTION: check_availability
  FILE: src/tennis_vision/model_adapters/sam_assisted_adapter.py
  PURPOSE:
    Checks SAM/SAM2 dependencies and local weight files.

  FUNCTION: initialize_prompt
  FILE: src/tennis_vision/model_adapters/sam_assisted_adapter.py
  PURPOSE:
    Finds a trusted seed point near a manual event window.

  FUNCTION: track_clip
  FILE: src/tennis_vision/model_adapters/sam_assisted_adapter.py
  PURPOSE:
    Runs prompt-based SAM segmentation over a local event clip when available.

  FUNCTION: run_sam_assisted_replay_pipeline
  FILE: src/tennis_vision/sam_assisted_replay_pipeline.py
  PURPOSE:
    Runs the full SAM-assisted feasibility path or writes a blocked report.

LIMITATIONS
  SAM/SAM2 is experimental for tennis ball localization.
  It should not be considered equivalent to TrackNet unless it resolves
  positions correctly under tennis-sequence validation.
  It does not use YOLO/HSV fallback.
  It does not download weights.
