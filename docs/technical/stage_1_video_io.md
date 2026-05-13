# Stage 1 - Video IO

This document is designed to be readable as plain text.
It avoids wide Markdown tables.

STAGE PURPOSE:
  Load the local tennis sample video, read metadata, and extract sample frames.

MAIN SCRIPT:
  scripts/run_stage_1_video_probe.py

MAIN MODULES:
  - src/tennis_vision/video_io.py
  - src/tennis_vision/frame_sampler.py

READS:
  - samples/video_01.mov or supported sample video

WRITES:
  - outputs/frames/
  - outputs/reports/stage_1_video_probe_report.json
  - outputs/reports/stage_1_video_probe_report.md

IMPORTANT FUNCTIONS:
  See docs/technical/function_inventory.md for FILE and LINE references.
  Search that file for: Stage 1

PRODUCT OWNER INTERPRETATION:
  Load the local tennis sample video, read metadata, and extract sample frames.
  The stage report and lab notebook record what happened in the latest run.

CURRENT LIMITATIONS:
  - This stage validates loading and extraction only, not detection quality.

WHERE TO INSPECT CODE:
  Start with scripts/run_stage_1_video_probe.py.
  Then open the modules listed above.
  Use the Function Inventory for exact line numbers.
