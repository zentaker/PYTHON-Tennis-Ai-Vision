# Stage 8.5 Precise Bounce Contact Localization

VERDICT
  Final verdict: ready_with_warnings
  Friction: 10 (low friction)

RUN SUMMARY
  Bounce windows processed: 1
  Localized contacts: 0
  Estimated contacts: 1
  Ambiguous contacts: 0
  Line-call-ready contacts: 0
  Average uncertainty frames: 3.0
  Average uncertainty px: 39.2

OUTPUTS
  Contact points: C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_5_bounce_contact\bounce_contact_points.csv
  Candidate frames: C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_5_bounce_contact\bounce_contact_candidates.csv
  Timeline preview: C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_5_bounce_contact\bounce_contact_timeline_preview.jpg

INTERPRETATION
  Bounce windows are temporal evidence. Stage 8.5 converts them into
  contact-point estimates with uncertainty, without claiming official line calling.

NEXT STEP
  Use localized/estimated contact points for Stage 14.4, but reserve future line calling for line_call_ready contacts only.
