# Stage 14.3 - Side-View Replay with Validated Events

## Summary

Stage:
  Stage 14.3 - Side-view replay with validated events

Verdict:
  ready_with_warnings

Friction score:
  2

Friction level:
  low friction

Event source used:
  stage_8_3_validated_event_timeline

Stage 8.3 available:
  yes

Timestamp:
  2026-05-14T19:06:59+00:00

Recommended next step:
  Proceed to Stage 15 for multi-camera prototype, or collect manual hit labels before showing confident side-view hit markers.

## Input

Source path:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_3_event_validation\validated_event_timeline.csv

Fallback used:
  no

Validated bounces rendered:
  3

Validated hits rendered:
  0

Downgraded hit annotations:
  6

Rejected events ignored:
  2

Unvalidated annotations:
  13

## Output

JSON report path:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\reports\stage_14_3_validated_events_side_view_report.json

Markdown report path:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\reports\stage_14_3_validated_events_side_view_report.md

Validated events debug:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\replay\stage_14_side_view_replay\side_view_validated_events_debug.jpg

Video:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\replay\stage_14_side_view_replay\side_view_replay.mp4

Frames:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\replay\stage_14_side_view_replay\frames

Manifest:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\replay\stage_14_side_view_replay\side_view_manifest.json

## Console-equivalent table

Frames generated:
  100

Video generated:
  yes

Main path physical-only:
  yes

Annotation band enabled:
  yes

Verdict:
  ready_with_warnings

Friction:
  2 (low friction)

## Warnings

- No validated hit labels are available yet; confident hit markers are not rendered.

## Errors

No errors.

## Interpretation

Stage 14.3 makes the side-view renderer consume the Stage 8.3 validated event timeline first. Validated bounces are physical grounded markers. Raw, downgraded, unvalidated, or rejected hit hypotheses are rendered only as secondary annotations, so the replay no longer presents unconfirmed hits as contacts.

## Next step

Proceed to Stage 15 for multi-camera prototype, or collect manual hit labels before showing confident side-view hit markers.

## Run history

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

<!-- lab-entry:2026-05-14T05:51:30+00:00 -->

### 2026-05-14T05:51:30+00:00

Stage:
  Stage 14.3 - Side-View Replay with Validated Events

Verdict:
  needs_more_side_view_tuning

Friction score:
  32

Friction level:
  medium friction

Next step:
  Tune the side-view renderer so downgraded hits remain annotations only.

<!-- lab-entry:2026-05-14T05:52:04+00:00 -->

### 2026-05-14T05:52:04+00:00

Stage:
  Stage 14.3 - Side-View Replay with Validated Events

Verdict:
  ready_with_warnings

Friction score:
  2

Friction level:
  low friction

Next step:
  Proceed to Stage 15 for multi-camera prototype, or collect manual hit labels before showing confident side-view hit markers.

<!-- lab-entry:2026-05-14T19:06:59+00:00 -->

### 2026-05-14T19:06:59+00:00

Stage:
  Stage 14.3 - Side-View Replay with Validated Events

Verdict:
  ready_with_warnings

Friction score:
  2

Friction level:
  low friction

Next step:
  Proceed to Stage 15 for multi-camera prototype, or collect manual hit labels before showing confident side-view hit markers.
