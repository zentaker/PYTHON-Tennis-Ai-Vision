# Stage 9.1 - Projection Coverage

This document is designed to be readable as plain text.
It avoids wide Markdown tables.

STAGE PURPOSE:
  Improve tactical zone coverage by projecting all expanded manual ball
  labels through the Stage 3 court homography.

  Stage 9.1 exists because Stage 9 analyzed 12 ball points but only 5 had
  projected coordinates, which caused 7 unknown tactical zones.

MAIN SCRIPT:
  scripts/run_stage_9_1_projection_coverage.py

MAIN MODULES:
  - src/tennis_vision/projection_coverage.py
  - src/tennis_vision/court_zone_tuning.py

READS:
  - outputs/timeline/stage_8_1_timeline_validation/expanded_ball_labels.csv
  - outputs/tactical/stage_9_tactical_metrics/ball_zone_assignments.csv
  - outputs/reports/stage_3_court_calibration_probe_report.json
  - outputs/timeline/stage_8_event_timeline/rally_segments.csv

WRITES:
  - outputs/tactical/stage_9_1_projection_coverage/projected_expanded_labels.csv
  - outputs/tactical/stage_9_1_projection_coverage/tuned_ball_zone_assignments.csv
  - outputs/tactical/stage_9_1_projection_coverage/stage_9_vs_9_1_zone_comparison.csv
  - outputs/tactical/stage_9_1_projection_coverage/tuned_shot_direction_estimates.csv
  - outputs/tactical/stage_9_1_projection_coverage/tuned_rally_tactical_summary.csv
  - outputs/tactical/stage_9_1_projection_coverage/projection_coverage_map.jpg
  - outputs/tactical/stage_9_1_projection_coverage/tuned_ball_placement_map.jpg
  - outputs/reports/stage_9_1_projection_coverage_report.json
  - outputs/reports/stage_9_1_projection_coverage_report.md

FUNCTIONAL FLOW:
  1. Load expanded ball labels from Stage 8.1.
  2. Load Stage 3 homography.
  3. Project each label from image coordinates into normalized court space.
  4. Merge projected labels with the original Stage 9 zone assignments.
  5. Assign tuned zones and preserve out-of-bounds uncertainty.
  6. Compare Stage 9 vs Stage 9.1 projected coverage and unknown zones.
  7. Regenerate lightweight direction and rally summaries.
  8. Save reports, previews, lab notebook, and technical documentation.

IMPORTANT FUNCTIONS:
  See docs/technical/function_inventory.md for FILE and LINE references.
  Search that file for: Stage 9.1

PRODUCT OWNER INTERPRETATION:
  Stage 9.1 makes tactical metrics more useful by reducing unknown zones.
  It does this by projecting manual labels directly instead of depending only
  on previously projected candidate frames.

CURRENT LIMITATIONS:
  - Projection quality still depends on the Stage 3 homography.
  - Points outside the tuned court range are labeled as out_of_bounds, not
    silently forced into confident zones.
  - Outputs remain approximate and are not official line calls.

WHERE TO INSPECT CODE:
  Start with scripts/run_stage_9_1_projection_coverage.py.
  Then inspect:
  - src/tennis_vision/projection_coverage.py
  - src/tennis_vision/court_zone_tuning.py
  Use the Function Inventory for exact line numbers.
