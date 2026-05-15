# Stage 8.2R Event Labeling Workbench

PURPOSE
  Stage 8.2R rebuilds event labeling as training infrastructure instead of a
  simple frame-by-frame helper.

  The workbench separates:
  - frame decode audit
  - visual duplicate grouping
  - clean frame cache
  - timeline/group review
  - event-window labels
  - precise contact candidates
  - uncertainty and label integrity audit
  - compatibility export for Stage 8.3

WHY THIS EXISTS
  The old Stage 8.2 viewer made duplicated or near-duplicated frames feel like
  separate labeling decisions. That is unsafe for bounce/hit ground truth.

  Stage 8.2R makes visual groups and event windows first-class data. A bounce
  window is not treated as an exact contact point. Contact candidates are saved
  separately for future line-call-oriented work.

MAIN SCRIPT
  scripts/run_stage_8_2r_event_labeling_workbench.py

MAIN MODULES
  src/tennis_vision/frame_decode_audit.py
  src/tennis_vision/event_labeling_workbench.py
  src/tennis_vision/event_contact_labels.py

COMMANDS
  Audit frame decoding:
    python scripts/run_stage_8_2r_event_labeling_workbench.py --audit-decode --start-frame 198 --end-frame 288

  Build clean frame cache:
    python scripts/run_stage_8_2r_event_labeling_workbench.py --build-cache --start-frame 198 --end-frame 288

  Open labeling workbench:
    python scripts/run_stage_8_2r_event_labeling_workbench.py --label --start-frame 198 --end-frame 288

  Open review-only workbench:
    python scripts/run_stage_8_2r_event_labeling_workbench.py --review --start-frame 198 --end-frame 288

  Export compatibility files for Stage 8.3:
    python scripts/run_stage_8_2r_event_labeling_workbench.py --export-compat

  Audit workbench labels:
    python scripts/run_stage_8_2r_event_labeling_workbench.py --audit-labels

OUTPUTS
  Workbench outputs:
    outputs/timeline/stage_8_2r_event_labeling_workbench/

  Decode audit:
    outputs/timeline/stage_8_2r_event_labeling_workbench/frame_decode_audit.csv
    outputs/timeline/stage_8_2r_event_labeling_workbench/frame_decode_audit.json
    outputs/timeline/stage_8_2r_event_labeling_workbench/frame_decode_audit.md

  Frame cache:
    outputs/timeline/stage_8_2r_event_labeling_workbench/frame_cache/

  Event windows:
    outputs/timeline/stage_8_2r_event_labeling_workbench/event_windows.csv
    outputs/timeline/stage_8_2r_event_labeling_workbench/event_windows.json

  Contact candidates:
    outputs/timeline/stage_8_2r_event_labeling_workbench/contact_candidates.csv
    outputs/timeline/stage_8_2r_event_labeling_workbench/contact_candidates.json

  Integrity audit:
    outputs/timeline/stage_8_2r_event_labeling_workbench/label_integrity_report.json
    outputs/timeline/stage_8_2r_event_labeling_workbench/label_integrity_report.md

  Stage report:
    outputs/reports/stage_8_2r_event_labeling_workbench_report.json
    outputs/reports/stage_8_2r_event_labeling_workbench_report.md

EVENT WINDOWS
  Event windows are saved separately from frame-level labels.

  Allowed event-window labels:
  - bounce_window
  - hit_window
  - no_event_window
  - uncertain_window

  Window labels include:
  - start frame
  - end frame
  - center frame
  - representative frame
  - frame list
  - visual group id
  - confidence
  - notes

CONTACT CANDIDATES
  Contact candidates are separate from event windows.

  A bounce_window means a bounce occurred across a temporal range.
  A contact_candidate means the user selected or accepted a likely contact
  frame and optional point.

  Future line-calling work should use contact candidates and uncertainty, not
  raw bounce windows.

VISUAL GROUPS
  The decode audit computes compact grayscale signatures and mean absolute
  frame differences. Adjacent near-duplicate frames are grouped into visual
  groups.

  The workbench defaults to visual-group navigation. Raw frames can still be
  inspected, but b/h/n/u labels operate on windows/groups.

IMPORTANT FUNCTIONS

FUNCTION: run_frame_decode_audit
FILE: src/tennis_vision/frame_decode_audit.py
LINE: 161
PURPOSE:
  Audits a selected video range using sequential decode, visual signatures,
  near-duplicate detection, and optional random-seek comparison.

WHY PRODUCT OWNER CARES:
  This determines whether duplicated moments are true video/visual duplicates
  or decode artifacts before labels become training data.

FUNCTION: build_frame_cache
FILE: src/tennis_vision/event_labeling_workbench.py
LINE: 63
PURPOSE:
  Builds a clean resized frame cache using sequential decoding.

WHY PRODUCT OWNER CARES:
  This makes labeling/review open quickly without writing overlays into the
  cached frames.

FUNCTION: run_review_or_label_viewer
FILE: src/tennis_vision/event_labeling_workbench.py
LINE: 193
PURPOSE:
  Opens the clean OpenCV workbench for visual-group review and group-level
  event-window labeling.

WHY PRODUCT OWNER CARES:
  The user labels temporal events as windows instead of guessing between
  duplicate frames.

FUNCTION: build_event_window
FILE: src/tennis_vision/event_contact_labels.py
LINE: 125
PURPOSE:
  Creates one durable event-window record from a frame range or visual group.

WHY PRODUCT OWNER CARES:
  Event windows preserve ambiguity when frame-perfect labeling is unreliable.

FUNCTION: build_contact_candidate
FILE: src/tennis_vision/event_contact_labels.py
LINE: 156
PURPOSE:
  Creates a precise contact candidate tied to an event window.

WHY PRODUCT OWNER CARES:
  This is the bridge from temporal event labeling toward future line-call
  readiness without pretending every bounce window is exact.

FUNCTION: audit_label_integrity
FILE: src/tennis_vision/event_contact_labels.py
LINE: 194
PURPOSE:
  Checks event windows and contact candidates for missing contacts, overlaps,
  no_event/contact conflicts, ambiguity, and line-call readiness.

WHY PRODUCT OWNER CARES:
  Bad labels become bad training data. The audit catches integrity issues
  before downstream event validation.

FUNCTION: export_compatibility
FILE: src/tennis_vision/event_contact_labels.py
LINE: 284
PURPOSE:
  Exports Stage 8.2R labels into the legacy Stage 8.2 paths used by Stage 8.3.

WHY PRODUCT OWNER CARES:
  The rebuilt workbench can feed the existing validation pipeline without
  forcing the old viewer workflow.

LIMITATIONS
  Stage 8.2R does not train a model.
  Stage 8.2R does not perform official line calling.
  Contact candidates may still be ambiguous when duplicate frames exist.
  Product Owner review is still required for final ground truth quality.
