# Stage 8.4 Bounce Candidate Propagation

This document is plain-text friendly.
It avoids wide Markdown tables.

PURPOSE:
  Stage 8.4 uses manually labeled bounce windows as active-learning signals.
  It proposes additional likely bounce candidates for manual review.

WHAT THIS STAGE DOES:
  - reads Stage 8.3 manual bounce windows
  - reads Stage 8.2 manual hit and no_event labels
  - reads projected ball sequence points
  - extracts local motion proxy features
  - applies tennis event-sequence constraints
  - scores likely bounce-like turning points
  - writes candidate windows and frame rows
  - creates a manual review queue

WHAT THIS STAGE DOES NOT DO:
  - does not validate inferred bounces
  - does not render inferred bounces as physical events
  - does not claim official bounce detection
  - does not perform line calling

INPUTS:
  - outputs/timeline/stage_8_3_event_validation/manual_event_windows.csv
  - outputs/timeline/stage_8_2_event_labels/manual_event_labels.csv
  - outputs/tactical/stage_9_1_projection_coverage/projected_expanded_labels.csv
  - outputs/timeline/stage_8_3_event_validation/validated_event_timeline.csv

OUTPUTS:
  - outputs/timeline/stage_8_4_bounce_candidates/bounce_candidate_windows.csv
  - outputs/timeline/stage_8_4_bounce_candidates/bounce_candidate_frames.csv
  - outputs/timeline/stage_8_4_bounce_candidates/bounce_review_queue.csv
  - outputs/timeline/stage_8_4_bounce_candidates/proposed_bounce_events.csv
  - outputs/timeline/stage_8_4_bounce_candidates/bounce_candidate_timeline_preview.jpg
  - outputs/reports/stage_8_4_bounce_candidate_propagation_report.json
  - outputs/reports/stage_8_4_bounce_candidate_propagation_report.md

FRICTION BREAKDOWN:
  Stage 8.4 reports legacy friction plus multi-dimensional friction:
  - execution friction
  - semantic/model friction
  - human-loop friction
  - product validation status
  - downstream correction friction

  This matters because the script can run successfully while the candidate
  still requires manual review before it is useful product evidence.

FUNCTION: learn_bounce_window_signature
FILE: src/tennis_vision/bounce_candidate_propagation.py
LINE: 39

PURPOSE:
  Extracts a local motion signature from manually labeled bounce windows.

INPUTS:
  - local motion feature rows
  - manual bounce windows

OUTPUTS:
  - weak bounce signature summary

WHY PRODUCT OWNER CARES:
  This is the first step toward using one manual bounce label to find other
  bounce candidates automatically.

HOW TO FIND IT:
  Open src/tennis_vision/bounce_candidate_propagation.py.
  Search: def learn_bounce_window_signature

---

FUNCTION: propose_bounce_candidates
FILE: src/tennis_vision/bounce_candidate_propagation.py
LINE: 124

PURPOSE:
  Scores the rest of the trajectory for likely bounce candidates.

INPUTS:
  - local motion feature rows
  - manual bounce windows
  - score threshold
  - candidate merge gap
  - max candidate count

OUTPUTS:
  - candidate windows
  - candidate frame rows

WHY PRODUCT OWNER CARES:
  Reduces manual labeling burden by suggesting events for review.

HOW TO FIND IT:
  Open src/tennis_vision/bounce_candidate_propagation.py.
  Search: def propose_bounce_candidates

---

PRODUCT OWNER INTERPRETATION:
  Stage 8.4 produces review targets. The proposed events should be checked
  with Stage 8.2 before Stage 8.3 treats them as validated bounce evidence.

EVENT SEQUENCE PATCH:
  Manual hit labels are constraints.
  A bounce candidate cannot be inside or near a manual hit window.
  Explicit no_event labels exclude candidate frames.
  If a hit occurs after a bounce, Stage 8.4 searches for the next bounce after
  that hit window.
  If the post-hit sequence is too short, Stage 8.4 reports that more post-hit
  ball labels are needed.

FUNCTION: build_manual_hit_windows
FILE: src/tennis_vision/bounce_candidate_propagation.py
LINE: 65

PURPOSE:
  Groups manual hit labels into conservative exclusion windows.

WHY PRODUCT OWNER CARES:
  Prevents the system from proposing a manually reviewed hit region as a bounce.

HOW TO FIND IT:
  Open src/tennis_vision/bounce_candidate_propagation.py.
  Search: def build_manual_hit_windows

---

FUNCTION: apply_event_sequence_constraints
FILE: src/tennis_vision/bounce_candidate_propagation.py
LINE: 209

PURPOSE:
  Applies hit, no_event, uncertain, and post-hit sequence rules to candidate
  bounce frames.

WHY PRODUCT OWNER CARES:
  Keeps candidate propagation aligned with tennis event order instead of only
  local visual similarity.

HOW TO FIND IT:
  Open src/tennis_vision/bounce_candidate_propagation.py.
  Search: def apply_event_sequence_constraints

---

FUNCTION: search_next_bounce_after_hit
FILE: src/tennis_vision/bounce_candidate_propagation.py
LINE: 280

PURPOSE:
  Finds a manual hit after the known bounce and starts the next-bounce search
  after that hit window.

WHY PRODUCT OWNER CARES:
  The next bounce should be searched after the player hit, not at the hit frame.

HOW TO FIND IT:
  Open src/tennis_vision/bounce_candidate_propagation.py.
  Search: def search_next_bounce_after_hit
