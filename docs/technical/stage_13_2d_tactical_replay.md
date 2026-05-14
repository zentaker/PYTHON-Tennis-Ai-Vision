# Stage 13 - 2D Tactical Replay Renderer

This document is designed to be readable as plain text.
It avoids wide Markdown tables.

STAGE PURPOSE:
  Render the first deterministic 2D tactical replay from the Stage 12 replay
  schema.

  Stage 13 does not use generative AI, photorealistic video, official scoring,
  official line calling, or 3D ball reconstruction. It visualizes the analysis
  data that already exists.

MAIN SCRIPT:
  scripts/run_stage_13_2d_tactical_replay.py

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
  - outputs/reports/stage_13_2d_tactical_replay_report.json
  - outputs/reports/stage_13_2d_tactical_replay_report.md

FUNCTIONAL FLOW:
  1. Load replay_schema.json.
  2. Extract court model, replay keyframes, players, and events.
  3. Create a mini-court canvas from normalized court coordinates.
  4. Render court boundary, simple grid, ball trail, current ball, player
     markers, possible_* event markers, frame labels, and timeline strip.
  5. Generate one frame per replay display point.
  6. Add visual-only interpolation between keyframes when enabled.
  7. Attempt MP4 export with OpenCV VideoWriter.
  8. Save contact sheet, final frame, renderer manifest, summary, and reports.

IMPORTANT FUNCTIONS:
  See docs/technical/function_inventory.md for FILE and LINE references.
  Search that file for: Stage 13

PRODUCT OWNER INTERPRETATION:
  Stage 13 is the first visual replay generated from analysis data. It is a
  tactical map view, not a reconstructed broadcast or photorealistic video.

  It helps validate whether the replay schema is usable by a renderer and
  whether uncertainty can stay visible in replay form.

CURRENT LIMITATIONS:
  - 2D tactical view only.
  - No true ball height.
  - No photorealistic players.
  - Interpolated points are visual only.
  - possible_* events are hypotheses.
  - MP4 export depends on local OpenCV codec support.

WHERE TO INSPECT CODE:
  Start with:
  - scripts/run_stage_13_2d_tactical_replay.py

  Then inspect:
  - src/tennis_vision/replay_renderer_2d.py
  - src/tennis_vision/replay_visual_styles.py

  Use the Function Inventory for exact line numbers.
