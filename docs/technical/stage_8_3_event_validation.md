# Stage 8.3 - Event Validation and Reclassification

This document is designed to be readable as plain text.
It avoids wide Markdown tables.

STAGE PURPOSE:
  Validate and reclassify automatic event hypotheses using manual event labels
  from Stage 8.2.

  This stage exists because hit, bounce, and uncertain event semantics were too
  ambiguous for replay rendering. Manual event labels become the evidence layer
  that keeps side-view replay from treating raw possible_hit hypotheses as
  confirmed contacts.

MAIN SCRIPT:
  scripts/run_stage_8_3_event_validation.py

MAIN MODULES:
  - src/tennis_vision/event_validation.py
  - src/tennis_vision/event_reclassification.py

READS:
  - outputs/timeline/stage_8_2_event_labels/manual_event_labels.csv
  - outputs/timeline/stage_8_event_timeline/event_timeline.csv
  - outputs/ball_tracking/stage_6_trajectory_smoothing/trajectory_events.csv
  - outputs/player_tracking/stage_7_player_interaction/ball_player_interactions.csv

WRITES:
  - outputs/timeline/stage_8_3_event_validation/manual_event_windows.csv
  - outputs/timeline/stage_8_3_event_validation/event_validation_results.csv
  - outputs/timeline/stage_8_3_event_validation/validated_event_timeline.csv
  - outputs/timeline/stage_8_3_event_validation/event_validation_summary.json
  - outputs/timeline/stage_8_3_event_validation/event_validation_timeline_preview.jpg
  - outputs/reports/stage_8_3_event_validation_report.json
  - outputs/reports/stage_8_3_event_validation_report.md

FUNCTIONAL FLOW:
  1. Load manual event labels from Stage 8.2.
  2. Normalize labels into bounce, hit, no_event, uncertain, and skipped.
  3. Group nearby bounce labels into bounce windows.
  4. Load automatic event hypotheses from Stage 8, Stage 6, and Stage 7.
  5. Normalize automatic events into auto_possible_hit, auto_possible_bounce,
     auto_ball_near_player, trajectory annotations, or unknown.
  6. Compare each automatic event with nearby manual labels or windows.
  7. Reclassify automatic events into validated, downgraded, rejected, or
     unvalidated roles.
  8. Write a validated event timeline for downstream replay stages.

IMPORTANT FUNCTIONS:
  See docs/technical/function_inventory.md for FILE and LINE references.
  Search that file for: Stage 8.3

PRODUCT OWNER INTERPRETATION:
  Stage 8.3 is the bridge from manual event labeling to corrected replay
  semantics. It treats a bounce as a short window when the user labels adjacent
  frames around contact, and it prevents automatic hit hypotheses from becoming
  confident replay events when manual labels disagree.

CURRENT LIMITATIONS:
  - This does not train a model.
  - This does not implement scoring or line calling.
  - If no manual hit labels exist, no hit can be confirmed.
  - More labels will improve event validation coverage.

WHERE TO INSPECT CODE:
  Start with:
  - src/tennis_vision/event_validation.py

  Then inspect:
  - src/tennis_vision/event_reclassification.py
  - scripts/run_stage_8_3_event_validation.py

  Use the Function Inventory for exact line numbers.
