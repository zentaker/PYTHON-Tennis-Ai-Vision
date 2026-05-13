# Stage 6 - Trajectory Smoothing

This document is designed to be readable as plain text.
It avoids wide Markdown tables.

STAGE PURPOSE:
  Build a first ball trajectory, smooth it, and create hypothesis-only event markers.

MAIN SCRIPT:
  scripts/run_stage_6_trajectory_smoothing.py

MAIN MODULES:
  - src/tennis_vision/trajectory_smoothing.py
  - src/tennis_vision/event_segmentation.py

READS:
  - Stage 5.1 improved candidates
  - projected candidates if available

WRITES:
  - raw_trajectory.csv
  - smoothed_trajectory.csv
  - trajectory_events.csv
  - Stage 6 reports

IMPORTANT FUNCTIONS:
  See docs/technical/function_inventory.md for FILE and LINE references.
  Search that file for: Stage 6

PRODUCT OWNER INTERPRETATION:
  Build a first ball trajectory, smooth it, and create hypothesis-only event markers.
  The stage report and lab notebook record what happened in the latest run.

CURRENT LIMITATIONS:
  - Smoothing must not hide poor detections or sparse data.

WHERE TO INSPECT CODE:
  Start with scripts/run_stage_6_trajectory_smoothing.py.
  Then open the modules listed above.
  Use the Function Inventory for exact line numbers.
