# Stage 8.4 Bounce Candidate Propagation Report

## VERDICT

Final verdict:
  needs_more_post_hit_ball_labels

Friction:
  31 (medium friction)

## WHY THIS STAGE EXISTS

The system should not require the user to label every bounce manually. This stage uses the existing manual bounce window, manual hit labels, no_event labels, and tennis sequence constraints to propose other likely bounce candidates.

## INPUTS

Manual bounce windows:
  1

Manual hit labels:
  1

No-event labels:
  27

Ball sequence points:
  12

Validated event timeline:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_3_event_validation\validated_event_timeline.csv

Projected labels:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\tactical\stage_9_1_projection_coverage\projected_expanded_labels.csv

## BOUNCE PATTERN SUMMARY

Manual bounce labels:
  3

Bounce windows:
  1

Pattern confidence:
  weak

Notes:
  Only one bounce window is available; propagation is a review aid, not validation.

## CANDIDATE SUMMARY

Candidate windows proposed:
  0

Candidate frames proposed:
  0

Top candidate frame:
  Not available

Top candidate score:
  Not available

Review queue:
  0

Candidates excluded by hit labels:
  1

Candidates excluded by no_event labels:
  0

Post-hit search enabled:
  True

Insufficient post-hit trajectory:
  True

## FRICTION BREAKDOWN

Execution friction:
  31 (medium friction) - Stage 8.4 script ran and generated its expected output files.

Semantic/model friction:
  70 (high friction) - Bounce candidates are event-sequence constrained; prior motion-only candidate frames near manual hits are excluded.

Human-loop friction:
  45 (medium friction) - manual labels required; new manual or validation stage required; user already inspected and labeled the mistaken hit-region candidate.

Product validation:
  failed_previous_candidate - The previous top candidate was near a manual hit and is now excluded.

Downstream correction friction:
  50 (medium friction) - Stage 8.4 exists because earlier side-view/event semantics needed extra repair and active validation.

## IMPORTANT LIMITATION

Inferred bounce candidates are not validated bounces. They require manual review before being rendered as physical bounce events.

## WARNINGS

- Only one manual bounce window is available; candidate propagation confidence is limited.
- Post-hit next-bounce search is enabled from manual hit labels.
- insufficient_post_hit_trajectory: not enough post-hit ball points are available to propose a reliable next bounce.

## ERRORS

No errors.

## NEXT STEP

Collect more post-hit ball/event labels after the manual hit, then rerun Stage 8.4.
