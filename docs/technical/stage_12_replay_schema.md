# Stage 12 - Synthetic Rally Replay Data Schema

This document is designed to be readable as plain text.
It avoids wide Markdown tables.

STAGE PURPOSE:
  Create the structured data contract for future replay renderers.

  Stage 12 does not generate video, synthetic images, photorealistic players,
  official scoring, or line calling. It packages validated pipeline evidence
  into replay-ready JSON, CSV, and plain-text schema summaries.

MAIN SCRIPT:
  scripts/run_stage_12_replay_schema.py

MAIN MODULES:
  - src/tennis_vision/replay_data_builder.py
  - src/tennis_vision/replay_schema.py
  - src/tennis_vision/replay_camera_presets.py

READS:
  - outputs/report_packages/stage_11_report_package/package_manifest.json
  - outputs/reports_final/stage_10_analytical_report/analytical_report.json
  - outputs/reports_final/stage_10_analytical_report/confidence_summary.json
  - outputs/tactical/stage_9_1_projection_coverage/tuned_ball_zone_assignments.csv
  - outputs/tactical/stage_9_1_projection_coverage/tuned_shot_direction_estimates.csv
  - outputs/tactical/stage_9_1_projection_coverage/tuned_rally_tactical_summary.csv
  - outputs/timeline/stage_8_1_timeline_validation/validated_event_timeline.csv
  - outputs/timeline/stage_8_event_timeline/rally_segments.csv
  - outputs/player_tracking/stage_7_1_player_filtering/main_players.csv
  - outputs/ball_tracking/stage_6_trajectory_smoothing/smoothed_trajectory.csv
  - outputs/reports/stage_3_court_calibration_probe_report.json

WRITES:
  - outputs/replay/stage_12_replay_schema/replay_schema.json
  - outputs/replay/stage_12_replay_schema/replay_schema_pretty.md
  - outputs/replay/stage_12_replay_schema/replay_keyframes.csv
  - outputs/replay/stage_12_replay_schema/replay_events.csv
  - outputs/replay/stage_12_replay_schema/replay_players.json
  - outputs/replay/stage_12_replay_schema/replay_camera_presets.json
  - outputs/replay/stage_12_replay_schema/replay_manifest.json
  - outputs/reports/stage_12_replay_schema_report.json
  - outputs/reports/stage_12_replay_schema_report.md

FUNCTIONAL FLOW:
  1. Load upstream analysis artifacts from Stage 3 through Stage 11.
  2. Build metadata, source video, court model, player, trajectory, event,
     rally, tactical, confidence, camera, visual layer, and renderer hint
     sections.
  3. Preserve uncertainty by keeping possible_* event names and confidence
     limitations.
  4. Write the full replay schema JSON.
  5. Write flat replay keyframe, event, player, camera, and manifest outputs.
  6. Write a plain-text-friendly schema summary.
  7. Write the Stage 12 reports and update the lab notebook.

IMPORTANT FUNCTIONS:
  See docs/technical/function_inventory.md for FILE and LINE references.
  Search that file for: Stage 12

PRODUCT OWNER INTERPRETATION:
  Stage 12 is the bridge from analysis to future replay rendering.
  It answers: "What exactly would a replay renderer consume?"

  The first recommended consumer is a deterministic 2D tactical replay
  renderer. More cinematic or multi-camera renderers can come later, after
  the data contract is stable.

CURRENT LIMITATIONS:
  - No replay video is generated.
  - No ball height or 3D reconstruction is available.
  - Events remain hypotheses.
  - Player identity is clothing/track heuristic, not biometric ID.
  - Court calibration uses the doubles outer boundary.
  - No official scoring or line calling is included.

WHERE TO INSPECT CODE:
  Start with:
  - scripts/run_stage_12_replay_schema.py

  Then inspect:
  - src/tennis_vision/replay_data_builder.py
  - src/tennis_vision/replay_schema.py
  - src/tennis_vision/replay_camera_presets.py

  Use the Function Inventory for exact line numbers.
