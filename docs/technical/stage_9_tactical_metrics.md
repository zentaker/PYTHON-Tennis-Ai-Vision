# Stage 9 - Tactical Metrics

This document is designed to be readable as plain text.
It avoids wide Markdown tables.

STAGE PURPOSE:
  Convert validated trajectory, timeline, player identity, and court
  projection evidence into first-pass tactical placement metrics.

  Outputs are approximate and hypothesis-based. Stage 9 does not perform
  official scoring, official line calling, confirmed shot classification, or
  tactical coaching advice.

MAIN SCRIPT:
  scripts/run_stage_9_tactical_metrics.py

MAIN MODULES:
  - src/tennis_vision/tactical_metrics.py
  - src/tennis_vision/court_zones.py

READS:
  - outputs/timeline/stage_8_1_timeline_validation/validated_event_timeline.csv
  - outputs/timeline/stage_8_1_timeline_validation/expanded_ball_labels.csv
  - outputs/timeline/stage_8_1_timeline_validation/expanded_candidate_validation.csv
  - outputs/timeline/stage_8_event_timeline/rally_segments.csv
  - outputs/ball_tracking/stage_6_trajectory_smoothing/smoothed_trajectory.csv
  - outputs/ball_tracking/stage_5_1_candidate_improvement/projected_improved_candidates.csv
  - outputs/player_tracking/stage_7_1_player_filtering/refined_ball_player_distances.csv

WRITES:
  - outputs/tactical/stage_9_tactical_metrics/ball_zone_assignments.csv
  - outputs/tactical/stage_9_tactical_metrics/shot_direction_estimates.csv
  - outputs/tactical/stage_9_tactical_metrics/rally_tactical_summary.csv
  - outputs/tactical/stage_9_tactical_metrics/tactical_summary.md
  - outputs/tactical/stage_9_tactical_metrics/court_zone_map.jpg
  - outputs/tactical/stage_9_tactical_metrics/ball_placement_map.jpg
  - outputs/tactical/stage_9_tactical_metrics/shot_direction_preview.jpg
  - outputs/reports/stage_9_tactical_metrics_report.json
  - outputs/reports/stage_9_tactical_metrics_report.md

FUNCTIONAL FLOW:
  1. Load validated Stage 8.1 timeline and expanded ball labels.
  2. Load projected candidate coordinates when available.
  3. Assign each visible ball label to an approximate normalized court zone.
  4. Estimate approximate direction between consecutive projected points.
  5. Summarize player association context from Stage 7.1.
  6. Build rally tactical summary rows from Stage 8 rally segments.
  7. Save CSVs, visual previews, JSON/Markdown reports, and lab notebook page.

IMPORTANT FUNCTIONS:
  See docs/technical/function_inventory.md for FILE and LINE references.
  Search that file for: Stage 9

PRODUCT OWNER INTERPRETATION:
  Stage 9 is the first point where the pipeline starts to look like tennis
  analytics instead of raw computer vision. It translates projected ball
  coordinates into zones such as deep/mid/short and left/center/right.

  These metrics are still approximate. They are useful for deciding whether
  a tactical layer is becoming feasible, not for making coaching claims.

CURRENT LIMITATIONS:
  - Zone boundaries are simple normalized-court heuristics.
  - Missing projected coordinates become unknown zones.
  - Direction estimates are approximate and depend on sparse ball points.
  - Event confidence comes from earlier hypothesis stages.

WHERE TO INSPECT CODE:
  Start with scripts/run_stage_9_tactical_metrics.py.
  Then inspect:
  - src/tennis_vision/tactical_metrics.py
  - src/tennis_vision/court_zones.py
  Use the Function Inventory for exact line numbers.
