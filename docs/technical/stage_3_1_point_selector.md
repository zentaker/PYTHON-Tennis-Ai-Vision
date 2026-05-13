# Stage 3.1 - Court Point Selection

This document is designed to be readable as plain text.
It avoids wide Markdown tables.

STAGE PURPOSE:
  Help the user select or estimate court corner coordinates locally.

MAIN SCRIPT:
  scripts/run_stage_3_1_court_point_selector.py

MAIN MODULES:
  - src/tennis_vision/court_point_selector.py

READS:
  - Stage 3 reference frame
  - court calibration config

WRITES:
  - coordinate grid image
  - updated calibration config when interactive selection is used
  - Stage 3.1 reports

IMPORTANT FUNCTIONS:
  See docs/technical/function_inventory.md for FILE and LINE references.
  Search that file for: Stage 3.1

PRODUCT OWNER INTERPRETATION:
  Help the user select or estimate court corner coordinates locally.
  The stage report and lab notebook record what happened in the latest run.

CURRENT LIMITATIONS:
  - Does not silently auto-correct inverted points.

WHERE TO INSPECT CODE:
  Start with scripts/run_stage_3_1_court_point_selector.py.
  Then open the modules listed above.
  Use the Function Inventory for exact line numbers.
