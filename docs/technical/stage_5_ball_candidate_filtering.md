# Stage 5 - Candidate Filtering and Court Projection

This document is designed to be readable as plain text.
It avoids wide Markdown tables.

STAGE PURPOSE:
  Compare automatic candidates to manual labels, filter candidates, and project them into court space.

MAIN SCRIPT:
  scripts/run_stage_5_ball_candidate_filtering.py

MAIN MODULES:
  - src/tennis_vision/ball_candidate_filtering.py
  - src/tennis_vision/court_projection.py

READS:
  - Stage 4 candidates
  - Stage 4.1 labels
  - Stage 3 homography

WRITES:
  - candidate_label_distances.csv
  - filtered_ball_candidates.csv
  - projected_ball_candidates.csv
  - Stage 5 reports

IMPORTANT FUNCTIONS:
  See docs/technical/function_inventory.md for FILE and LINE references.
  Search that file for: Stage 5

PRODUCT OWNER INTERPRETATION:
  Compare automatic candidates to manual labels, filter candidates, and project them into court space.
  The stage report and lab notebook record what happened in the latest run.

CURRENT LIMITATIONS:
  - Filtering is a baseline, not a learned tracker.

WHERE TO INSPECT CODE:
  Start with scripts/run_stage_5_ball_candidate_filtering.py.
  Then open the modules listed above.
  Use the Function Inventory for exact line numbers.
