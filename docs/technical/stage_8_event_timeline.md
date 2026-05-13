# Stage 8 - Event Timeline

This document is designed to be readable as plain text.
It avoids wide Markdown tables.

STAGE PURPOSE:
  Merge trajectory, event, interaction, and player identity evidence into a first rally timeline.

MAIN SCRIPT:
  scripts/run_stage_8_event_timeline.py

MAIN MODULES:
  - src/tennis_vision/event_timeline.py
  - src/tennis_vision/rally_segmentation.py

READS:
  - Stage 6 trajectory/events
  - Stage 7 interactions
  - Stage 7.1 identities

WRITES:
  - event_timeline.csv
  - event_timeline.json
  - rally_segments.csv
  - player_event_attribution.csv
  - Stage 8 reports

IMPORTANT FUNCTIONS:
  See docs/technical/function_inventory.md for FILE and LINE references.
  Search that file for: Stage 8

PRODUCT OWNER INTERPRETATION:
  Merge trajectory, event, interaction, and player identity evidence into a first rally timeline.
  The stage report and lab notebook record what happened in the latest run.

CURRENT LIMITATIONS:
  - Uses possible_* labels and preserves uncertainty.

WHERE TO INSPECT CODE:
  Start with scripts/run_stage_8_event_timeline.py.
  Then open the modules listed above.
  Use the Function Inventory for exact line numbers.
