# Stage 8.3 - Event Validation and Reclassification

## Summary

Stage:
  Stage 8.3 - Event validation and reclassification

Verdict:
  ready_with_warnings

Friction score:
  31

Friction level:
  medium friction

Timestamp:
  2026-05-14T05:34:56+00:00

Recommended next step:
  Proceed to Stage 14.3 using validated events, but collect manual hit labels before confirming hits.

## Input

Manual labels:
  53

Bounce labels:
  3

Hit labels:
  0

No-event labels:
  23

Uncertain labels:
  3

Bounce windows:
  1

## Output

JSON report path:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\reports\stage_8_3_event_validation_report.json

Markdown report path:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\reports\stage_8_3_event_validation_report.md

Manual event windows:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_3_event_validation\manual_event_windows.csv

Event validation results:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_3_event_validation\event_validation_results.csv

Validated event timeline:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_3_event_validation\validated_event_timeline.csv

Validation preview:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_3_event_validation\event_validation_timeline_preview.jpg

## Console-equivalent table

Automatic events:
  18

Validated bounces:
  3

Validated hits:
  0

Downgraded hits:
  6

Rejected events:
  2

Unvalidated events:
  11

Verdict:
  ready_with_warnings

Friction:
  31 (medium friction)

## Warnings

- No hit events are confirmed because no manual hit labels were provided.
- Adjacent manual bounce labels were grouped into bounce windows.

## Errors

No errors.

## Interpretation

Stage 8.3 uses manual event labels to validate or downgrade automatic event hypotheses. Adjacent bounce labels are grouped into one bounce window so a multi-frame bounce is not treated as several separate bounces. The validated timeline should be the preferred event source for side-view replay correction.

## Next step

Proceed to Stage 14.3 using validated events, but collect manual hit labels before confirming hits.

## Run history

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

<!-- lab-entry:2026-05-14T05:31:48+00:00 -->

### 2026-05-14T05:31:48+00:00

Stage:
  Stage 8.3 - Event Validation

Verdict:
  ready_with_warnings

Friction score:
  31

Friction level:
  medium friction

Next step:
  Proceed to Stage 14.3 using validated events, but collect manual hit labels before confirming hits.

<!-- lab-entry:2026-05-14T05:34:56+00:00 -->

### 2026-05-14T05:34:56+00:00

Stage:
  Stage 8.3 - Event Validation

Verdict:
  ready_with_warnings

Friction score:
  31

Friction level:
  medium friction

Next step:
  Proceed to Stage 14.3 using validated events, but collect manual hit labels before confirming hits.
