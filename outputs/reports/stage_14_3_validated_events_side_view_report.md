# Stage 14.3 Side-View Replay with Validated Events Report

## VERDICT

Final verdict:
  ready_with_warnings

Friction:
  2 (low friction)

Event source used:
  stage_8_3_validated_event_timeline

## VALIDATED EVENT SOURCE

Stage 8.3 available:
  True

Source path:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_3_event_validation\validated_event_timeline.csv

Fallback used:
  False

## RENDERING BEHAVIOR

Validated bounces rendered:
  3

Validated hits rendered:
  0

Downgraded hits shown as annotation:
  6

Rejected events ignored:
  2

Unvalidated events shown as annotation:
  13

Main path physical-only:
  True

Annotation band enabled:
  True

## WHY THIS PATCH EXISTS

Previous side-view versions rendered raw possible_hit hypotheses too strongly. Stage 8.3 now provides validated and reclassified event semantics, so the side-view uses that layer before drawing physical contact markers.

## LIMITATIONS

- no validated hit labels yet
- no true 3D height
- side-view is still synthetic
- bounces are validated from manual labels
- hits remain unconfirmed until manually labeled

## WARNINGS

- No validated hit labels are available yet; confident hit markers are not rendered.

## ERRORS

No errors.

## NEXT STEP

Proceed to Stage 15 for multi-camera prototype, or collect manual hit labels before showing confident side-view hit markers.
