# Stage 0 - Environment

This document is designed to be readable as plain text.
It avoids wide Markdown tables.

STAGE PURPOSE:
  Validate local Python, folders, imports, and ffmpeg availability.

MAIN SCRIPT:
  scripts/doctor.py

MAIN MODULES:
  - src/tennis_vision/environment.py
  - src/tennis_vision/report.py
  - src/tennis_vision/friction.py

READS:
  - local Python environment
  - repo folder structure
  - required package imports

WRITES:
  - outputs/reports/environment_report.json
  - outputs/reports/environment_report.md
  - docs/lab-notebook/stage_0_environment.md

IMPORTANT FUNCTIONS:
  See docs/technical/function_inventory.md for FILE and LINE references.
  Search that file for: Stage 0

PRODUCT OWNER INTERPRETATION:
  Validate local Python, folders, imports, and ffmpeg availability.
  The stage report and lab notebook record what happened in the latest run.

CURRENT LIMITATIONS:
  - ffmpeg can remain a warning until a stage requires it.

WHERE TO INSPECT CODE:
  Start with scripts/doctor.py.
  Then open the modules listed above.
  Use the Function Inventory for exact line numbers.
