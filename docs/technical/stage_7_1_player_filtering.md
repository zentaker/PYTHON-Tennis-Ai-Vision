# Stage 7.1 - Player Filtering and Identity

This document is designed to be readable as plain text.
It avoids wide Markdown tables.

STAGE PURPOSE:
  Filter noisy person detections and create stable main-player identities.

MAIN SCRIPT:
  scripts/run_stage_7_1_player_filtering.py

MAIN MODULES:
  - src/tennis_vision/player_filtering.py
  - src/tennis_vision/player_identity.py

READS:
  - Stage 7 detections/tracks
  - sample video
  - court calibration

WRITES:
  - filtered_player_tracks.csv
  - main_players.csv
  - player_identity_profiles.json
  - player_side_states.csv
  - Stage 7.1 reports

IMPORTANT FUNCTIONS:
  See docs/technical/function_inventory.md for FILE and LINE references.
  Search that file for: Stage 7.1

PRODUCT OWNER INTERPRETATION:
  Filter noisy person detections and create stable main-player identities.
  The stage report and lab notebook record what happened in the latest run.

CURRENT LIMITATIONS:
  - Player identity is separate from near/far side state.

WHERE TO INSPECT CODE:
  Start with scripts/run_stage_7_1_player_filtering.py.
  Then open the modules listed above.
  Use the Function Inventory for exact line numbers.
