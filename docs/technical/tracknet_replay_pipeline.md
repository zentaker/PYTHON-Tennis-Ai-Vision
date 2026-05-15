# TrackNet Replay Pipeline

PURPOSE
  Provides one integrated command for the next ball-tracking feasibility path.
  It attempts TrackNet-style temporal ball tracking, court projection, manual
  event position resolution, tennis-sequence validation, and replay output.

PRIMARY COMMAND
  python scripts/run_tracknet_replay_pipeline.py

INPUTS
  samples/video_01.mov
  configs/manual_annotations/video_01_full_rally.json
  outputs/reports/stage_3_court_calibration_probe_report.json

OUTPUTS
  outputs/tracknet_replay/video_01/ball_tracking_results.csv
  outputs/tracknet_replay/video_01/projected_ball_positions.csv
  outputs/tracknet_replay/video_01/event_position_results.csv
  outputs/tracknet_replay/video_01/top_view_replay.mp4
  outputs/tracknet_replay/video_01/side_view_replay.mp4
  outputs/tracknet_replay/video_01/replay_schema.json
  outputs/tracknet_replay/video_01/tracknet_replay_report.json
  outputs/tracknet_replay/video_01/tracknet_replay_report.md
  outputs/reports/tracknet_replay_pipeline_report.json
  outputs/reports/tracknet_replay_pipeline_report.md

WEIGHT LOCATIONS
  Place TrackNet weights in one of these locations:
  models/tracknet/weights/tracknet.pt
  models/tracknet/weights/tracknet.pth
  models/tracknet/weights/tracknetv2.pt
  models/tracknet/weights/tracknetv2.pth
  models/tracknet/weights/tracknetv3.pt
  models/tracknet/weights/tracknetv3.pth
  models/tracknet/weights/tracknetv4.pt
  models/tracknet/weights/tracknetv4.pth
  models/tracknet/checkpoints/

  Or pass:
  python scripts/run_tracknet_replay_pipeline.py --tracknet-weights path/to/weights.pt

SETUP CHECK
  python scripts/check_tracknet_integration.py

DATA CONTRACT
  The Product Owner provides event timing and shot type.
  TrackNet must provide ball coordinates over time.
  Stage 3 homography projects coordinates onto the court.
  Tennis-sequence validation decides whether each event can be a physical
  replay anchor.

REAL INFERENCE PATH
  The adapter can run a full PyTorch model saved as a .pt or .pth file when
  that file contains the serialized model object with its architecture.
  It preprocesses temporal clips, tries common TrackNet tensor layouts, decodes
  heatmaps or direct coordinate outputs, and writes per-frame ball positions.

  If a weight file is only a state_dict/checkpoint, the adapter reports:
  architecture_missing

  This is intentional. A state_dict cannot be executed safely without the
  matching TrackNet architecture class and preprocessing details.

BLOCKED MODE
  If weights are missing, the script does not crash and does not fake results.
  It writes empty tracking/projection outputs, unresolved event positions, a
  replay schema, and a blocked report.
  If weights exist but are a state_dict without a matching architecture class,
  the script reports architecture_missing instead of pretending inference works.

IMPORTANT FUNCTIONS
  FUNCTION: run_tracknet_replay_pipeline
  FILE: src/tennis_vision/tracknet_replay_pipeline.py
  PURPOSE:
    Runs the integrated TrackNet path or generates a clear blocked report.

  FUNCTION: find_weights
  FILE: src/tennis_vision/model_adapters/tracknet_adapter.py
  PURPOSE:
    Searches local TrackNet weight locations without downloading anything.

  FUNCTION: track_video_segment
  FILE: src/tennis_vision/model_adapters/tracknet_adapter.py
  PURPOSE:
    Runs temporal TrackNet inference over the manual rally range when a full
    PyTorch model is ready, or refuses cleanly when weights/architecture are
    missing.

  FUNCTION: preprocess_clip
  FILE: src/tennis_vision/model_adapters/tracknet_adapter.py
  PURPOSE:
    Converts OpenCV frames into temporal tensors for common TrackNet layouts.

  FUNCTION: decode_heatmap
  FILE: src/tennis_vision/model_adapters/tracknet_adapter.py
  PURPOSE:
    Converts heatmap or coordinate model output into image-space ball x/y rows.

LIMITATIONS
  This repository still does not include TrackNet weights.
  State-dict weights need a matching architecture wrapper.
  It does not download model weights.
  It does not use YOLO/HSV fallback by default.
  Side-view height is synthetic, not measured 3D physics.
