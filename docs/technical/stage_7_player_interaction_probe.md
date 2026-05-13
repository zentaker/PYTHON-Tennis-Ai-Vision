# Stage 7 - Player Interaction

This document is designed to be readable as plain text.
It avoids wide Markdown tables.

STAGE PURPOSE:
  Detect players and associate ball points with nearby player tracks.

MAIN SCRIPT:
  scripts/run_stage_7_player_interaction_probe.py

MAIN MODULES:
  - src/tennis_vision/player_tracking.py
  - src/tennis_vision/ball_player_interaction.py

READS:
  - sample video
  - Stage 6 trajectory/events

WRITES:
  - player_detections.csv
  - player_tracks.csv
  - ball_player_distances.csv
  - ball_player_interactions.csv
  - Stage 7 reports

IMPORTANT FUNCTIONS:
  See docs/technical/function_inventory.md for FILE and LINE references.
  Search that file for: Stage 7

PRODUCT OWNER INTERPRETATION:
  Detect players and associate ball points with nearby player tracks.
  The stage report and lab notebook record what happened in the latest run.

CURRENT LIMITATIONS:
  - Interactions are hypotheses, not confirmed hits.

WHERE TO INSPECT CODE:
  Start with scripts/run_stage_7_player_interaction_probe.py.
  Then open the modules listed above.
  Use the Function Inventory for exact line numbers.
