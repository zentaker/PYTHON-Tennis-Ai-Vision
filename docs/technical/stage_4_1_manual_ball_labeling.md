# Stage 4.1 - Manual Ball Labeling

This document is designed to be readable as plain text.
It avoids wide Markdown tables.

STAGE PURPOSE:
  Let the user click true ball positions to create ground-truth labels.

MAIN SCRIPT:
  scripts/run_stage_4_1_ball_labeling_helper.py

MAIN MODULES:
  - src/tennis_vision/ball_labeling.py

READS:
  - sample video
  - optional Stage 4 candidate CSV

WRITES:
  - manual_ball_labels.csv
  - manual_ball_labels.json
  - label overlays
  - Stage 4.1 reports

IMPORTANT FUNCTIONS:
  See docs/technical/function_inventory.md for FILE and LINE references.
  Search that file for: Stage 4.1

PRODUCT OWNER INTERPRETATION:
  Let the user click true ball positions to create ground-truth labels.
  The stage report and lab notebook record what happened in the latest run.

CURRENT LIMITATIONS:
  - Manual labels are ground truth for validating noisy automatic candidates.

WHERE TO INSPECT CODE:
  Start with scripts/run_stage_4_1_ball_labeling_helper.py.
  Then open the modules listed above.
  Use the Function Inventory for exact line numbers.
