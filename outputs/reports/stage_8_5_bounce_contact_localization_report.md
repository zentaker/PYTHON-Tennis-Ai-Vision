# Stage 8.5 Precise Bounce Contact Localization Report

## VERDICT

Final verdict:
  ready_with_warnings

Friction:
  10 (low friction)

## WHY THIS STAGE EXISTS

Bounce windows are not enough for future in/out detection. Stage 8.5 estimates a contact frame and contact point, then records uncertainty and line-call readiness.

## BOUNCE CONTACT SUMMARY

Bounce windows:
  1

Localized contacts:
  0

Estimated contacts:
  1

Ambiguous contacts:
  0

Line-call-ready contacts:
  0

Average uncertainty frames:
  3.0

Average uncertainty px:
  39.2

## IMPORTANT LIMITATION

This is not official line calling. It estimates contact points and uncertainty. Future line calling should use only line_call_ready contact points.

## OUTPUTS

Contact points:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_5_bounce_contact\bounce_contact_points.csv

Candidate frames:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_5_bounce_contact\bounce_contact_candidates.csv

Summary:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_5_bounce_contact\bounce_contact_summary.json

Debug overlays:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_5_bounce_contact\bounce_contact_debug

Timeline preview:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_5_bounce_contact\bounce_contact_timeline_preview.jpg

## WARNINGS

- Stage 8.2 manual_event_windows.csv had no bounce windows; Stage 8.5 used Stage 8.3 manual_event_windows.csv as fallback.

## ERRORS

No errors.

## NEXT STEP

Use localized/estimated contact points for Stage 14.4, but reserve future line calling for line_call_ready contacts only.
