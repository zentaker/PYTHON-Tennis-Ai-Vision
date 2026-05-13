# Stage 2 - YOLO CPU

This document is designed to be readable as plain text.
It avoids wide Markdown tables.

STAGE PURPOSE:
  Validate that a small YOLO model can run locally on CPU.

MAIN SCRIPT:
  scripts/run_stage_2_yolo_cpu_baseline.py

MAIN MODULES:
  - src/tennis_vision/yolo_cpu.py

READS:
  - sample video
  - small YOLO model

WRITES:
  - outputs/annotated/stage_2_yolo_cpu/
  - outputs/reports/stage_2_yolo_cpu_baseline_report.json

IMPORTANT FUNCTIONS:
  See docs/technical/function_inventory.md for FILE and LINE references.
  Search that file for: Stage 2

PRODUCT OWNER INTERPRETATION:
  Validate that a small YOLO model can run locally on CPU.
  The stage report and lab notebook record what happened in the latest run.

CURRENT LIMITATIONS:
  - This is a CPU baseline, not a tennis-ball tracker.

WHERE TO INSPECT CODE:
  Start with scripts/run_stage_2_yolo_cpu_baseline.py.
  Then open the modules listed above.
  Use the Function Inventory for exact line numbers.
