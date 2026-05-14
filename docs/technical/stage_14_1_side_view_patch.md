# Stage 14.1 - Side-View Height Semantics Patch

This document is designed to be readable as plain text.
It avoids wide Markdown tables.

STAGE PURPOSE:
  Improve Stage 14 side-view replay semantics so the synthetic ball height
  reads more like tennis.

  The patch grounds bounce-like events near the court surface, keeps hit-like
  events in a plausible contact band, and marks interpolated points as visual
  interpolation.

MAIN SCRIPT:
  scripts/run_stage_14_side_view_replay.py

MAIN MODULES:
  - src/tennis_vision/ball_flight_estimator.py
  - src/tennis_vision/replay_renderer_side_view.py

READS:
  - outputs/replay/stage_12_replay_schema/replay_schema.json

WRITES:
  - outputs/replay/stage_14_side_view_replay/side_view_semantic_debug.jpg
  - outputs/replay/stage_14_side_view_replay/side_view_manifest.json
  - outputs/replay/stage_14_side_view_replay/side_view_summary.md
  - outputs/reports/stage_14_1_side_view_patch_report.json
  - outputs/reports/stage_14_1_side_view_patch_report.md

FUNCTIONAL FLOW:
  1. Load the replay schema.
  2. Build side-view keyframes.
  3. Classify each keyframe as bounce_grounded, hit_contact,
     interaction_cue, arc_estimate, or visual_interpolation.
  4. Force bounce-like events to floor height.
  5. Force hit-like events to a plausible synthetic contact-height band.
  6. Keep ball_near_player as an interaction cue, not a forced hit or bounce.
  7. Mark interpolated points as visual-only.
  8. Regenerate side-view frames, MP4, manifest, summary, and semantic debug
     image.

IMPORTANT FUNCTIONS:
  See docs/technical/function_inventory.md for FILE and LINE references.
  Search that file for: Stage 14.1

PRODUCT OWNER INTERPRETATION:
  Stage 14.1 fixes a visual meaning problem. The previous side-view renderer
  could be technically valid while making bounce-like events appear to float.
  This patch makes the replay easier to read as tennis while still saying
  synthetic height is not measured 3D height.

CURRENT LIMITATIONS:
  - Height remains synthetic.
  - No real 3D reconstruction is performed.
  - possible_* events remain hypotheses.
  - The patch improves visual semantics, not scientific flight physics.

WHERE TO INSPECT CODE:
  Start with:
  - src/tennis_vision/ball_flight_estimator.py

  Then inspect:
  - src/tennis_vision/replay_renderer_side_view.py
  - scripts/run_stage_14_side_view_replay.py

  Use the Function Inventory for exact line numbers.
