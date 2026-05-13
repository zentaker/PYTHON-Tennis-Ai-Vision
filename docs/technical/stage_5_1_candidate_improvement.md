# Stage 5.1 - Candidate Generation Improvement

This document is designed to be readable as plain text.
It avoids wide Markdown tables.

STAGE PURPOSE:
  Test improved handcrafted candidate strategies against manual labels.

MAIN SCRIPT:
  scripts/run_stage_5_1_candidate_improvement.py

MAIN MODULES:
  - src/tennis_vision/ball_candidate_improvement.py
  - src/tennis_vision/court_projection.py

READS:
  - sample video
  - manual labels
  - Stage 3 homography

WRITES:
  - strategy_comparison.csv
  - improved_ball_candidates.csv
  - projected_improved_candidates.csv
  - Stage 5.1 reports

IMPORTANT FUNCTIONS:
  See docs/technical/function_inventory.md for FILE and LINE references.
  Search that file for: Stage 5.1

PRODUCT OWNER INTERPRETATION:
  Test improved handcrafted candidate strategies against manual labels.
  The stage report and lab notebook record what happened in the latest run.

CURRENT LIMITATIONS:
  - HSV color performed best on the current sample; this is still not model training.

WHERE TO INSPECT CODE:
  Start with scripts/run_stage_5_1_candidate_improvement.py.
  Then open the modules listed above.
  Use the Function Inventory for exact line numbers.
