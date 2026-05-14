# Stage 14.3 Side-View Replay with Validated Events

This document is plain-text friendly.
It avoids wide Markdown tables.

PURPOSE:
  Stage 14.3 patches the side-view replay so it uses Stage 8.3 validated
  events before rendering physical contact markers.

WHY THIS MATTERS:
  Earlier side-view versions could show raw possible_hit hypotheses as if they
  were plausible physical hits. Stage 8.3 now provides validated and
  reclassified event semantics, so the renderer should consume that layer
  instead of raw event guesses.

INPUTS:
  - outputs/replay/stage_12_replay_schema/replay_schema.json
  - outputs/timeline/stage_8_3_event_validation/validated_event_timeline.csv

FALLBACK ORDER:
  1. Stage 8.3 validated event timeline
  2. Stage 8.1 validated event timeline
  3. Stage 8 event timeline
  4. Stage 6 trajectory events

RENDERING RULES:
  - validated bounces are grounded physical events
  - validated hits are physical contact events
  - downgraded hits are annotations only
  - rejected events are not physical events
  - unvalidated events are annotations only
  - interpolation remains visual-only motion

CURRENT LIMITATION:
  Stage 8.3 currently has zero validated hit labels.
  The side-view should therefore show no confident hit markers.

OUTPUTS:
  - outputs/replay/stage_14_side_view_replay/side_view_replay.mp4
  - outputs/replay/stage_14_side_view_replay/side_view_validated_events_debug.jpg
  - outputs/replay/stage_14_side_view_replay/side_view_manifest.json
  - outputs/reports/stage_14_3_validated_events_side_view_report.json
  - outputs/reports/stage_14_3_validated_events_side_view_report.md

FUNCTION: load_validated_event_source
FILE: src/tennis_vision/validated_event_source.py
LINE: 18

PURPOSE:
  Loads Stage 8.3 validated events as the preferred source for side-view
  rendering.

INPUTS:
  - project root
  - replay schema
  - optional preferred Stage 8.3 event path

OUTPUTS:
  - normalized event records
  - source metadata
  - render summary
  - warnings and errors

WHY PRODUCT OWNER CARES:
  Prevents raw automatic possible hits from being rendered as physical events.

HOW TO FIND IT:
  Open src/tennis_vision/validated_event_source.py.
  Search: def load_validated_event_source

---

FUNCTION: map_validated_event_to_render_role
FILE: src/tennis_vision/validated_event_source.py
LINE: 74

PURPOSE:
  Converts validated and reclassified event labels into physical or annotation
  render roles.

INPUTS:
  - event row
  - source name
  - replay schema

OUTPUTS:
  - normalized event record with render policy

WHY PRODUCT OWNER CARES:
  Separates real visual contact markers from uncertain model guesses.

HOW TO FIND IT:
  Open src/tennis_vision/validated_event_source.py.
  Search: def map_validated_event_to_render_role

---

FUNCTION: create_validated_events_debug_image
FILE: src/tennis_vision/replay_renderer_side_view.py
LINE: 429

PURPOSE:
  Creates a diagnostic image showing validated-event rendering behavior.

INPUTS:
  - replay schema
  - display points
  - normalized events
  - players
  - output path
  - event source name

OUTPUTS:
  - side_view_validated_events_debug.jpg

WHY PRODUCT OWNER CARES:
  Shows whether validated bounces are grounded and unvalidated hits are only
  annotations.

HOW TO FIND IT:
  Open src/tennis_vision/replay_renderer_side_view.py.
  Search: def create_validated_events_debug_image

---

PRODUCT OWNER INTERPRETATION:
  Stage 14.3 should make the side-view replay less misleading. It does not
  invent confirmed hits. Until manual hit labels exist, hit-like automatic
  events stay visually secondary.
