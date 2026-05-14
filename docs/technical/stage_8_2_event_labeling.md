# Stage 8.2 - Manual Bounce / Hit Event Labeling Helper

This document is designed to be readable as plain text.
It avoids wide Markdown tables.

STAGE PURPOSE:
  Create manual ground truth for tennis event semantics.

  Earlier stages have ball labels, player identities, and automatic event
  hypotheses. They do not yet have human labels for true bounce, true hit,
  no_event, or uncertain frames. Stage 8.2 fills that gap.

MAIN SCRIPT:
  scripts/run_stage_8_2_event_labeling_helper.py

MAIN MODULE:
  - src/tennis_vision/event_labeling.py

READS:
  - samples/video_01.mov
  - outputs/timeline/stage_8_1_timeline_validation/expanded_ball_labels.csv
  - outputs/timeline/stage_8_event_timeline/event_timeline.csv
  - outputs/ball_tracking/stage_6_trajectory_smoothing/trajectory_events.csv
  - outputs/player_tracking/stage_7_player_interaction/ball_player_interactions.csv

WRITES:
  - outputs/timeline/stage_8_2_event_labels/manual_event_labels.csv
  - outputs/timeline/stage_8_2_event_labels/manual_event_labels.json
  - outputs/timeline/stage_8_2_event_labels/event_label_comparison.csv
  - outputs/timeline/stage_8_2_event_labels/event_label_coverage.csv
  - outputs/timeline/stage_8_2_event_labels/event_label_overlays/
  - outputs/reports/stage_8_2_event_labeling_report.json
  - outputs/reports/stage_8_2_event_labeling_report.md

FUNCTIONAL FLOW:
  1. Load the sample video.
  2. Load any existing durable manual event labels.
  3. Load expanded ball labels from Stage 8.1.
  4. Load automatic event hypotheses from Stage 8, Stage 6, and Stage 7.
  5. In interactive mode, show selected frames in OpenCV.
  6. Let the user label each frame as:
     - bounce
     - hit
     - no_event
     - uncertain
     - skipped
  7. Save durable labels and timestamped session backups.
  8. Compare manual labels to nearby automatic hypotheses.
  9. Save coverage, overlays, reports, lab notebook, and technical docs.

IMPORTANT FUNCTIONS:
  See docs/technical/function_inventory.md for FILE and LINE references.
  Search that file for: Stage 8.2

PRODUCT OWNER INTERPRETATION:
  Stage 8.2 is the point where the project stops trying to infer ambiguous
  hit/bounce semantics from heuristics alone. The user can create event ground
  truth, then Stage 8.3 can use it to validate or reclassify automatic event
  hypotheses.

CURRENT LIMITATIONS:
  - Non-interactive mode only validates existing labels.
  - It does not train a model.
  - It does not implement scoring or line calling.
  - Hit/bounce labels depend on human review of selected frames.

WHERE TO INSPECT CODE:
  Start with:
  - src/tennis_vision/event_labeling.py

  Then inspect:
  - scripts/run_stage_8_2_event_labeling_helper.py

  Use the Function Inventory for exact line numbers.
