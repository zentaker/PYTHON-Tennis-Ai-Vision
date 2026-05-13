# Stage 8.1 - Timeline Validation

This document is designed to be readable as plain text.
It avoids wide Markdown tables.

STAGE PURPOSE:
  Persist expanded ball labels and validate the Stage 8 timeline against them.
  Interactive mode collects labels; non-interactive mode validates the durable
  label dataset without requiring the user to relabel frames.

MAIN SCRIPT:
  scripts/run_stage_8_1_expand_labels.py

MAIN MODULES:
  - src/tennis_vision/label_expansion.py
  - src/tennis_vision/timeline_validation.py

READS:
  - persisted expanded labels
  - latest timestamped Stage 8.1 label session backup
  - Stage 4.1 fallback manual labels
  - Stage 5.1 improved candidates
  - Stage 8 timeline

WRITES:
  - expanded_ball_labels.csv
  - expanded_ball_labels.json
  - label_sessions/stage_8_1_labels_<timestamp>.csv
  - label_sessions/stage_8_1_labels_<timestamp>.json
  - expanded_candidate_validation.csv
  - timeline_event_validation.csv
  - validated_event_timeline.csv
  - Stage 8.1 reports

LABEL PERSISTENCE FLOW:
  1. Interactive mode writes new manual labels to timestamped session backups.
  2. Interactive mode merges labels into the durable expanded label dataset.
  3. Non-interactive mode reads durable expanded labels first.
  4. If the durable file is missing, non-interactive mode uses the latest
     session backup before falling back to Stage 4.1 labels.
  5. Non-interactive mode must not overwrite a richer expanded dataset with
     fallback-only labels.

IMPORTANT FUNCTIONS:
  See docs/technical/function_inventory.md for FILE and LINE references.
  Search that file for: Stage 8.1

PRODUCT OWNER INTERPRETATION:
  Persist expanded ball labels and validate the Stage 8 timeline against them.
  The stage report and lab notebook record what happened in the latest run.

CURRENT LIMITATIONS:
  - Non-interactive mode must reuse persisted labels; new_labels_count is session-specific.
  - If an older interactive run happened before session backups existed, the
    labels may need to be collected once more.

WHERE TO INSPECT CODE:
  Start with scripts/run_stage_8_1_expand_labels.py.
  Then open the modules listed above.
  Use the Function Inventory for exact line numbers.
