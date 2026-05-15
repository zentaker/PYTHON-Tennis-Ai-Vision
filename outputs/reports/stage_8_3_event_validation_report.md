# Stage 8.3 Event Validation and Reclassification Report

## VERDICT

Final verdict:
  ready_with_warnings

Friction:
  3 (low friction)

## MANUAL LABEL SUMMARY

Manual labels:
  58

Bounce labels:
  3

Hit labels:
  1

No-event labels:
  27

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
  9

Outside manual coverage:
  2

## WHAT CHANGED

Stage 8.3 grouped 3 manual bounce labels into 1 bounce window(s). Automatic events were then validated, downgraded, or left uncertain using those manual labels.

## IMPORTANT LIMITATION

Manual hit labels are available for hit validation.

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

- Adjacent manual bounce labels were grouped into bounce windows.

## ERRORS

No errors.

## NEXT STEP

Proceed to Stage 14.3 using validated events, but collect manual hit labels before confirming hits.
