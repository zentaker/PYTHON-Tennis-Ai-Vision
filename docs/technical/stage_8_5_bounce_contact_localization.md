# Stage 8.5 - Precise Bounce Contact Localization

This document is designed to be readable as plain text.
It avoids wide Markdown tables.

PURPOSE:
  Stage 8.5 turns manually supported bounce windows into estimated contact
  points.

  A bounce window says a bounce happened over a short temporal range. Future
  line-calling logic needs more than that:
    - best contact frame
    - image-space contact x/y
    - projected court x/y
    - uncertainty
    - line-call readiness

MAIN SCRIPT:
  scripts/run_stage_8_5_bounce_contact_localization.py

MAIN MODULE:
  src/tennis_vision/bounce_contact_localization.py

READS:
  - outputs/timeline/stage_8_2_event_labels/manual_event_windows.csv
  - outputs/timeline/stage_8_3_event_validation/manual_event_windows.csv
  - outputs/timeline/stage_8_1_timeline_validation/expanded_ball_labels.csv
  - outputs/tactical/stage_9_1_projection_coverage/projected_expanded_labels.csv
  - samples/video_01.mov

WRITES:
  - outputs/timeline/stage_8_5_bounce_contact/bounce_contact_points.csv
  - outputs/timeline/stage_8_5_bounce_contact/bounce_contact_candidates.csv
  - outputs/timeline/stage_8_5_bounce_contact/bounce_contact_summary.json
  - outputs/timeline/stage_8_5_bounce_contact/bounce_contact_debug/
  - outputs/timeline/stage_8_5_bounce_contact/bounce_contact_timeline_preview.jpg
  - outputs/reports/stage_8_5_bounce_contact_localization_report.json
  - outputs/reports/stage_8_5_bounce_contact_localization_report.md

METHOD:
  1. Load bounce windows.
  2. Build a small frame search range around each bounce window.
  3. Load image-space ball labels and projected court labels.
  4. Interpolate missing points only as tentative evidence.
  5. Score candidate frames using:
       - window center proximity
       - lowest image-position proxy
       - local motion change
       - projected trajectory turn proxy
       - image label availability
       - projection availability
  6. Select the highest scoring contact frame.
  7. Estimate uncertainty.
  8. Decide whether the contact point is line-call-ready.

IMPORTANT LIMITATION:
  Stage 8.5 is not official line calling.

  It prepares contact-point data for future line-calling work. If the bounce
  is ambiguous, sparse, or poorly projected, it marks the result as not ready
  for line calling.

FUNCTIONS:
  FUNCTION: read_bounce_windows
  FILE: src/tennis_vision/bounce_contact_localization.py
  LINE: see function_inventory.md
  PURPOSE:
    Loads manually supported bounce windows, preferring Stage 8.2 direct
    windows and falling back to Stage 8.3 grouped windows.

  WHY PRODUCT OWNER CARES:
    Keeps event-window labels as the trusted input for contact localization.

  FUNCTION: localize_bounce_contact
  FILE: src/tennis_vision/bounce_contact_localization.py
  LINE: see function_inventory.md
  PURPOSE:
    Scores candidate frames and returns a contact point with uncertainty.

  WHY PRODUCT OWNER CARES:
    Converts a bounce window into the best available contact-frame estimate.

  FUNCTION: line_call_readiness
  FILE: src/tennis_vision/bounce_contact_localization.py
  LINE: see function_inventory.md
  PURPOSE:
    Marks whether a contact estimate is safe to pass to future line-calling
    logic.

  WHY PRODUCT OWNER CARES:
    Prevents broad or uncertain bounce windows from being treated as in/out
    evidence.

PRODUCT OWNER INTERPRETATION:
  Bounce windows are good for replay and event semantics.
  Bounce contact points are needed for future spatial decisions.

  Stage 8.5 separates those concepts and records uncertainty explicitly.
