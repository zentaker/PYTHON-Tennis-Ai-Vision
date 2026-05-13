# Stage 4 - Ball Candidate Probe

This document is designed to be readable as plain text.
It avoids wide Markdown tables.

STAGE PURPOSE:
  Generate exploratory ball candidates with lightweight OpenCV heuristics.

MAIN SCRIPT:
  scripts/run_stage_4_ball_tracking_probe.py

MAIN MODULES:
  - src/tennis_vision/ball_tracking_probe.py

READS:
  - sample video

WRITES:
  - outputs/ball_tracking/stage_4_ball_probe/
  - outputs/reports/stage_4_ball_tracking_probe_report.json

IMPORTANT FUNCTIONS:
  See docs/technical/function_inventory.md for FILE and LINE references.
  Search that file for: Stage 4

PRODUCT OWNER INTERPRETATION:
  Generate exploratory ball candidates with lightweight OpenCV heuristics.
  The stage report and lab notebook record what happened in the latest run.

CURRENT LIMITATIONS:
  - This probe produced many false positives and should not be treated as production tracking.

WHERE TO INSPECT CODE:
  Start with scripts/run_stage_4_ball_tracking_probe.py.
  Then open the modules listed above.
  Use the Function Inventory for exact line numbers.
