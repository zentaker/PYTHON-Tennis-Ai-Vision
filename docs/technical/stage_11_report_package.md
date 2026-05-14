# Stage 11 - Report Package

This document is designed to be readable as plain text.
It avoids wide Markdown tables.

STAGE PURPOSE:
  Package selected analysis outputs into a clean local deliverable that a
  Product Owner, player, or future UI can consume.

  Stage 11 does not create new analysis. It copies or references curated
  artifacts, writes a manifest, records missing optional files, and preserves
  limitations.

MAIN SCRIPT:
  scripts/run_stage_11_report_package.py

MAIN MODULES:
  - src/tennis_vision/report_package.py
  - src/tennis_vision/package_manifest.py

READS:
  - outputs/reports_final/stage_10_analytical_report/
  - outputs/tactical/stage_9_1_projection_coverage/
  - outputs/timeline/stage_8_event_timeline/
  - outputs/player_tracking/stage_7_1_player_filtering/
  - outputs/ball_tracking/stage_6_trajectory_smoothing/
  - outputs/ball_tracking/stage_5_1_candidate_improvement/

WRITES:
  - outputs/report_packages/stage_11_report_package/README.md
  - outputs/report_packages/stage_11_report_package/package_manifest.json
  - outputs/report_packages/stage_11_report_package/package_index.md
  - outputs/report_packages/stage_11_report_package/analysis/
  - outputs/report_packages/stage_11_report_package/data/
  - outputs/report_packages/stage_11_report_package/visuals/
  - outputs/report_packages/stage_11_report_package/notes/
  - outputs/reports/stage_11_report_package_report.json
  - outputs/reports/stage_11_report_package_report.md

FUNCTIONAL FLOW:
  1. Build a curated artifact list from Stage 10, Stage 9.1, Stage 8,
     Stage 7.1, Stage 6, and Stage 5.1 outputs.
  2. Create the report package folder structure.
  3. Copy selected artifacts by default, or reference them when requested.
  4. Write README, package index, limitations, and source artifact notes.
  5. Write package_manifest.json with included and missing artifacts.
  6. Write the Stage 11 pipeline report and update the lab notebook.

IMPORTANT FUNCTIONS:
  See docs/technical/function_inventory.md for FILE and LINE references.
  Search that file for: Stage 11

PRODUCT OWNER INTERPRETATION:
  Stage 11 creates the first shareable bundle from the full analysis pipeline.
  It is meant for review, handoff, and future UI/reporting work.

CURRENT LIMITATIONS:
  - It packages existing outputs only.
  - It does not create a PDF, HTML page, or video highlight yet.
  - Optional missing visuals are recorded instead of blocking the package.
  - The package still preserves all uncertainty from upstream reports.

WHERE TO INSPECT CODE:
  Start with scripts/run_stage_11_report_package.py.
  Then inspect:
  - src/tennis_vision/report_package.py
  - src/tennis_vision/package_manifest.py
  Use the Function Inventory for exact line numbers.
