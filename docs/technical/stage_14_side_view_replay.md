# Stage 14 - Side-View Ball Flight Renderer

This document is designed to be readable as plain text.
It avoids wide Markdown tables.

STAGE PURPOSE:
  Render a deterministic side-view analytical visualization from the Stage 12
  replay schema.

  The project does not have measured 3D ball height. Stage 14 therefore uses
  synthetic height for visualization only and labels that limitation clearly.

MAIN SCRIPT:
  scripts/run_stage_14_side_view_replay.py

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
  - outputs/reports/stage_14_side_view_replay_report.json
  - outputs/reports/stage_14_side_view_replay_report.md

FUNCTIONAL FLOW:
  1. Load replay_schema.json.
  2. Extract replay keyframes and event hypotheses.
  3. Convert projected court y coordinates into side-view court depth.
  4. Estimate synthetic ball height for each keyframe.
  5. Interpolate display points when enabled.
  6. Render court depth axis, net, ball arc, current ball, event markers,
     player depth markers, and timeline strip.
  7. Attempt MP4 export with OpenCV VideoWriter.
  8. Save contact sheet, final frame, arc preview, manifest, summary, and
     reports.

IMPORTANT FUNCTIONS:
  See docs/technical/function_inventory.md for FILE and LINE references.
  Search that file for: Stage 14

PRODUCT OWNER INTERPRETATION:
  Stage 14 makes the replay easier to read from a side-view perspective, but
  it does not reconstruct real 3D flight. The height curve is a deterministic
  visual aid based on 2D projected keyframes and event hypotheses.

CURRENT LIMITATIONS:
  - No true 3D reconstruction.
  - No measured ball height.
  - possible_* events are hypotheses.
  - Side-view is analytical visualization only.
  - Not a broadcast reconstruction.
  - MP4 export depends on local OpenCV codec support.

WHERE TO INSPECT CODE:
  Start with:
  - scripts/run_stage_14_side_view_replay.py

  Then inspect:
  - src/tennis_vision/ball_flight_estimator.py
  - src/tennis_vision/replay_renderer_side_view.py

  Use the Function Inventory for exact line numbers.
