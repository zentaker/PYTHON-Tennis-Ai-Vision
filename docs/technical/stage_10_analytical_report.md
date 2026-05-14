# Stage 10 - Analytical Report

This document is designed to be readable as plain text.
It avoids wide Markdown tables.

STAGE PURPOSE:
  Convert validated tactical metrics, event timeline evidence, and player
  context into a readable analytical report and cautious coaching-style
  summary.

  Stage 10 is deterministic and local. It does not call external LLM APIs.
  It does not perform official coaching, scoring, line calling, or confirmed
  shot classification.

MAIN SCRIPT:
  scripts/run_stage_10_analytical_report.py

MAIN MODULES:
  - src/tennis_vision/analytical_report.py
  - src/tennis_vision/coaching_summary.py
  - src/tennis_vision/report_confidence.py

READS:
  - outputs/tactical/stage_9_1_projection_coverage/tuned_ball_zone_assignments.csv
  - outputs/tactical/stage_9_1_projection_coverage/tuned_shot_direction_estimates.csv
  - outputs/tactical/stage_9_1_projection_coverage/tuned_rally_tactical_summary.csv
  - outputs/timeline/stage_8_1_timeline_validation/validated_event_timeline.csv
  - outputs/timeline/stage_8_1_timeline_validation/expanded_ball_labels.csv
  - outputs/timeline/stage_8_1_timeline_validation/expanded_candidate_validation.csv
  - outputs/player_tracking/stage_7_1_player_filtering/main_players.csv
  - outputs/player_tracking/stage_7_1_player_filtering/refined_ball_player_distances.csv

WRITES:
  - outputs/reports_final/stage_10_analytical_report/analytical_report.md
  - outputs/reports_final/stage_10_analytical_report/analytical_report.json
  - outputs/reports_final/stage_10_analytical_report/coaching_summary.md
  - outputs/reports_final/stage_10_analytical_report/confidence_summary.json
  - outputs/reports_final/stage_10_analytical_report/key_findings.md
  - outputs/reports_final/stage_10_analytical_report/visual_references.md
  - outputs/reports/stage_10_analytical_report_report.json
  - outputs/reports/stage_10_analytical_report_report.md

FUNCTIONAL FLOW:
  1. Load Stage 9.1 tuned tactical outputs.
  2. Load Stage 8.1 validated timeline and candidate validation context.
  3. Load Stage 7.1 player identity context when available.
  4. Summarize placement, direction, event, player, and rally evidence.
  5. Score report confidence from labels, projection coverage, candidate
     distance, timeline support, and player identity availability.
  6. Generate cautious coaching-style observations with rule-based wording.
  7. Write the analytical report, JSON summary, coaching summary, key findings,
     confidence summary, visual references, pipeline report, and lab notebook.

IMPORTANT FUNCTIONS:
  See docs/technical/function_inventory.md for FILE and LINE references.
  Search that file for: Stage 10

PRODUCT OWNER INTERPRETATION:
  Stage 10 is the first stage where raw computer vision outputs become a
  readable analysis artifact. It explains what the sample appears to show
  while preserving uncertainty from earlier stages.

CURRENT LIMITATIONS:
  - Report wording is deterministic and rule-based.
  - Coaching-style observations are not official advice.
  - possible_* timeline events remain hypotheses.
  - Confidence depends on the current small labeled sample.
  - Visual assets are referenced, not packaged into a final presentation yet.

WHERE TO INSPECT CODE:
  Start with scripts/run_stage_10_analytical_report.py.
  Then inspect:
  - src/tennis_vision/analytical_report.py
  - src/tennis_vision/coaching_summary.py
  - src/tennis_vision/report_confidence.py
  Use the Function Inventory for exact line numbers.
