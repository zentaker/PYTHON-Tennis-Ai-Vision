# Stage 8.3 Event Validation and Reclassification Report

## VERDICT

Final verdict:
  ready_with_warnings

Friction:
  31 (medium friction)

## MANUAL LABEL SUMMARY

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

## AUTOMATIC EVENT SUMMARY

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

Outside manual coverage:
  4

## WHAT CHANGED

Stage 8.3 grouped 3 manual bounce labels into 1 bounce window(s). Automatic events were then validated, downgraded, or left uncertain using those manual labels.

## IMPORTANT LIMITATION

No hit events are confirmed because no manual hit labels were provided.

## OUTPUTS

Manual event windows:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_3_event_validation\manual_event_windows.csv

Event validation results:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_3_event_validation\event_validation_results.csv

Validated event timeline:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_3_event_validation\validated_event_timeline.csv

Validation preview:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_3_event_validation\event_validation_timeline_preview.jpg

## PRODUCT OWNER INTERPRETATION

This stage gives side-view replay a better event truth layer. It prevents raw possible_hit hypotheses from being rendered as contact events when manual labels indicate bounce or no_event evidence.

## WARNINGS

- No hit events are confirmed because no manual hit labels were provided.
- Adjacent manual bounce labels were grouped into bounce windows.

## ERRORS

No errors.

## NEXT STEP

Proceed to Stage 14.3 using validated events, but collect manual hit labels before confirming hits.
