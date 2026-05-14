# Stage 10 Analytical Rally Report

REPORT STATUS
  Verdict: ready_for_stage_11
  Confidence level: medium-high
  Friction: 0 (low friction)
  Data source: Stage 9.1 tuned tactical outputs and validated timeline data.
  Generated at: 2026-05-14T02:07:28+00:00

EXECUTIVE SUMMARY
  - The report analyzed 12 visible ball labels.
  - 12 labels have projected court coordinates.
  - Unknown tactical zones: 0.
  - Confidence level: medium-high.
  - Most frequent prototype zone: far_mid_center (3 points).
  - Rally segments summarized: 1.

WHAT THE SYSTEM ANALYZED
  - Number of ball labels: 12
  - Number of projected ball points: 12
  - Number of rally segments: 1
  - Number of timeline events: 5
  - Number of player identities: 2
  - Projection coverage: 1.0
  - Unknown zones: 0

TACTICAL PLACEMENT SUMMARY
  Depth:
    - short: 2
    - mid: 5
    - deep: 5
    - unknown: 0

  Lateral placement:
    - left: 3
    - center: 8
    - right: 1
    - unknown: 0

  Dominant zones:
    - far_mid_center: 3
    - near_mid_left: 2
    - out_of_bounds: 2

SHOT DIRECTION SUMMARY
  Direction estimates:
    - crosscourt_like: 0
    - down_the_line_like: 2
    - center_like: 7
    - unknown: 2

  Interpretation:
    Direction estimates are approximate and should be read as movement hypotheses.

PLAYER / INTERACTION SUMMARY
  player_a:
    - associated events: 3
    - notes: Identity is appearance/track based; near/far side remains a state.
  player_b:
    - associated events: 2
    - notes: Identity is appearance/track based; near/far side remains a state.
  unknown:
    - associated events: 0
    - notes: Unknown means player attribution was weak or unavailable.

EVENT TIMELINE SUMMARY
  - ball_near_player: 2
  - possible_hit: 3

COACHING-STYLE OBSERVATIONS
  Observation 1:
    What it suggests: In this sample, ball placements appear deep-oriented (5 points).
    Confidence: medium-high
    Limitation: This is a prototype observation from limited labeled frames, not official coaching advice.
  Observation 2:
    What it suggests: The current sample appears center-oriented laterally (8 points).
    Confidence: medium-high
    Limitation: This is a prototype observation from limited labeled frames, not official coaching advice.
  Observation 3:
    What it suggests: Direction estimates are mostly center_like (7 estimates).
    Confidence: medium
    Limitation: Direction estimates are hypothesis-based and depend on sparse projected ball points.

CONFIDENCE AND LIMITATIONS
  Confidence level: medium-high
  Reasons:
    - 12 visible expanded ball labels are available.
    - All visible labels have projected court coordinates and no unknown zones.
    - Candidate validation distance is low on matched frames (2.797 px average).
    - All timeline events in the validated timeline are label-supported.
    - Two main player identities are available from Stage 7.1.

  Limitations:
    - No major limiting factors detected for this prototype report.

NEXT RECOMMENDED STEP
  Proceed to Stage 11: Annotated Highlight/Report Package Generator.

VISUAL REFERENCES
  - tuned_ball_placement_map: C:\Users\MSI\Desktop\TennisAiVision\outputs\tactical\stage_9_1_projection_coverage\tuned_ball_placement_map.jpg
  - projection_coverage_map: C:\Users\MSI\Desktop\TennisAiVision\outputs\tactical\stage_9_1_projection_coverage\projection_coverage_map.jpg
  - timeline_preview: C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_event_timeline\timeline_preview.jpg
  - court_timeline_preview: C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_event_timeline\court_timeline_preview.jpg
  - player_interaction_preview: C:\Users\MSI\Desktop\TennisAiVision\outputs\player_tracking\stage_7_player_interaction\player_interaction_preview.jpg
