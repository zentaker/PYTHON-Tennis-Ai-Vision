# Stage 3 - Court Calibration

This document is designed to be readable as plain text.
It avoids wide Markdown tables.

STAGE PURPOSE:
  Generate a calibration reference frame and compute homography when manual court points are valid.

MAIN SCRIPT:
  scripts/run_stage_3_court_calibration_probe.py

MAIN MODULES:
  - src/tennis_vision/court_calibration.py

READS:
  - configs/court_calibration_sample.json
  - sample video

WRITES:
  - outputs/calibration/stage_3_court_probe/
  - outputs/reports/stage_3_court_calibration_probe_report.json

IMPORTANT FUNCTIONS:
  See docs/technical/function_inventory.md for FILE and LINE references.
  Search that file for: Stage 3

PRODUCT OWNER INTERPRETATION:
  Generate a calibration reference frame and compute homography when manual court points are valid.
  The stage report and lab notebook record what happened in the latest run.

CURRENT LIMITATIONS:
  - Uses doubles court outer boundary as the baseline.
  - Rejects crossed or inverted corner points.

WHERE TO INSPECT CODE:
  Start with scripts/run_stage_3_court_calibration_probe.py.
  Then open the modules listed above.
  Use the Function Inventory for exact line numbers.
