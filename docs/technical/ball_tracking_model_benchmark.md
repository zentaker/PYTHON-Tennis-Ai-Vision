# Ball Tracking Model Benchmark

PURPOSE
  Rapidly compares ball-position resolution approaches against the same manual
  full-rally timing annotation.

WHY THIS EXISTS
  The manual full-rally replay failure showed that timing was correct, but the
  current local HSV/motion detector selected false-positive ball positions.
  This benchmark separates model choice from replay rendering.

SCRIPT
  scripts/run_ball_tracking_model_benchmark.py

COMMAND
  python scripts/run_ball_tracking_model_benchmark.py

SAFE DEFAULT
  The default command checks TrackNet and SAM availability first and does not
  run baseline_current. The baseline uses OpenCV frame access that can be slow
  or hang on MOV random seeking.

OPTIONS
  --models tracknet_candidate,sam_assisted_candidate
    Runs only the requested adapters.

  --skip-baseline
    Removes baseline_current from the requested model list.

  --include-baseline
    Opts into baseline_current.

  --model-timeout-seconds 20
    Hard timeout per available model adapter.

INPUTS
  configs/manual_annotations/video_01_full_rally.json
  samples/video_01.mov
  outputs/reports/stage_3_court_calibration_probe_report.json

MODELS
  baseline_current
    Uses the existing Stage 5.1 HSV/motion hybrid candidate generator.
    It is opt-in because OpenCV random frame seeking can be slow or hang.

  tracknet_candidate
    Checks for local TrackNet-style code and weights. It does not download
    weights and does not fake inference when unavailable.

  sam_assisted_candidate
    Checks for local SAM/SAM2 dependency and weights. It does not download
    weights and does not fake inference when unavailable.

DATA FLOW
  1. Load manual event timing.
  2. Build a small search window around each event.
  3. Ask each adapter to resolve image-space ball position.
  4. Project image-space position with Stage 3 homography.
  5. Validate the projected position with tennis-sequence rules.
  6. Write per-event and per-model benchmark reports.

OUTPUTS
  outputs/benchmarks/ball_tracking_model_benchmark/model_event_results.csv
  outputs/benchmarks/ball_tracking_model_benchmark/model_summary.csv
  outputs/reports/ball_tracking_model_benchmark_report.json
  outputs/reports/ball_tracking_model_benchmark_report.md

IMPORTANT FUNCTIONS
  FUNCTION: run_benchmark
  FILE: src/tennis_vision/ball_tracking_benchmark.py
  PURPOSE:
    Runs all requested model adapters and writes comparable per-event results.

  FUNCTION: resolve_event_position
  FILE: src/tennis_vision/model_adapters/baseline_ball_adapter.py
  PURPOSE:
    Resolves one event using the current Stage 5.1 local hybrid detector.

  FUNCTION: check_availability
  FILE: src/tennis_vision/model_adapters/tracknet_adapter.py
  PURPOSE:
    Reports whether TrackNet-style code or weights exist locally.

  FUNCTION: check_availability
  FILE: src/tennis_vision/model_adapters/sam_assisted_adapter.py
  PURPOSE:
    Reports whether SAM dependencies and weights exist locally.

LIMITATIONS
  This is a benchmark harness, not a production tracker.
  TrackNet and SAM are not run unless local dependencies, weights, and adapter
  inference code are available.
  The benchmark does not generate replay by default.

RELATED PIPELINE
  scripts/run_tracknet_replay_pipeline.py is the integrated TrackNet replay
  scaffold. It produces a blocked report when TrackNet weights or inference
  code are missing.
