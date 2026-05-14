# Stage 14.2 - Side-View Event Disambiguation Patch

This document is designed to be readable as plain text.
It avoids wide Markdown tables.

STAGE PURPOSE:
  Improve side-view replay event meaning.

  Stage 14.1 made synthetic height visually coherent, but raw possible_hit
  labels could still appear in court locations that were not plausible relative
  to the attributed player's position. Stage 14.2 separates raw event labels
  from render roles so implausible hits are drawn as uncertain events instead
  of contact points.

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
  - outputs/replay/stage_14_side_view_replay/side_view_semantic_debug.jpg
  - outputs/replay/stage_14_side_view_replay/side_view_manifest.json
  - outputs/replay/stage_14_side_view_replay/side_view_summary.md
  - outputs/reports/stage_14_2_side_view_event_disambiguation_report.json
  - outputs/reports/stage_14_2_side_view_event_disambiguation_report.md

FUNCTIONAL FLOW:
  1. Load replay_schema.json.
  2. Read player identities and side-state/depth data.
  3. Read raw event timeline hypotheses.
  4. Score possible_hit events against the attributed player's court depth.
  5. Preserve raw event labels internally.
  6. Assign side-view render roles:
     - hit_plausible
     - bounce_plausible
     - player_interaction
     - uncertain_event
     - interpolation_only
  7. Downgrade implausible possible_hit events to uncertain_event for
     rendering.
  8. Keep bounce-like events grounded.
  9. Keep ball_near_player as an interaction cue, not as a hit or bounce.
  10. Regenerate frames, MP4, semantic debug image, manifest, summary, and
      Stage 14.2 reports.

IMPORTANT FUNCTIONS:
  See docs/technical/function_inventory.md for FILE and LINE references.
  Search that file for: Stage 14.2

PRODUCT OWNER INTERPRETATION:
  Stage 14.2 makes the side-view replay less misleading. The renderer no
  longer treats every raw possible_hit as a visible hit marker. A possible_hit
  must be plausible relative to player position and court depth before it is
  drawn as a hit. If that evidence is weak, the replay shows uncertainty.

CURRENT LIMITATIONS:
  - This is a plausibility filter, not exact biomechanics.
  - The system still does not measure true 3D ball height.
  - possible_* events remain hypotheses.
  - More manual event labels would improve validation.

WHERE TO INSPECT CODE:
  Start with:
  - src/tennis_vision/ball_flight_estimator.py

  Then inspect:
  - src/tennis_vision/replay_renderer_side_view.py
  - scripts/run_stage_14_side_view_replay.py

  Use the Function Inventory for exact line numbers.
