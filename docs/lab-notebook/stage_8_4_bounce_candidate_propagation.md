# Stage 8.4 - Bounce Candidate Propagation

## Summary

Stage:
  Stage 8.4 - Bounce candidate propagation

Verdict:
  needs_more_post_hit_ball_labels

Friction score:
  31

Friction level:
  medium friction

Timestamp:
  2026-05-14T19:42:48+00:00

Recommended next step:
  Collect more post-hit ball/event labels after the manual hit, then rerun Stage 8.4.

## Input

Manual bounce windows:
  1

Manual bounce labels:
  3

Ball sequence points:
  12

Pattern confidence:
  weak

## Output

JSON report path:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\reports\stage_8_4_bounce_candidate_propagation_report.json

Markdown report path:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\reports\stage_8_4_bounce_candidate_propagation_report.md

Candidate windows:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_4_bounce_candidates\bounce_candidate_windows.csv

Candidate frames:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_4_bounce_candidates\bounce_candidate_frames.csv

Review queue:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_4_bounce_candidates\bounce_review_queue.csv

Proposed bounce events:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_4_bounce_candidates\proposed_bounce_events.csv

Timeline preview:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_4_bounce_candidates\bounce_candidate_timeline_preview.jpg

## Console-equivalent table

Candidate windows:
  0

Candidate frames:
  0

Top candidate frame:
  Not available

Top candidate score:
  Not available

Review queue:
  0

Verdict:
  needs_more_post_hit_ball_labels

Friction:
  31 (medium friction)

## Warnings

- Only one manual bounce window is available; candidate propagation confidence is limited.
- Post-hit next-bounce search is enabled from manual hit labels.
- insufficient_post_hit_trajectory: not enough post-hit ball points are available to propose a reliable next bounce.

## Errors

No errors.

## Interpretation

Stage 8.4 uses manual bounce windows as active-learning signals. It proposes likely additional bounce candidates for review, but it does not validate them or render them as physical bounces.

## Next step

Collect more post-hit ball/event labels after the manual hit, then rerun Stage 8.4.

## Run history

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

<!-- lab-entry:2026-05-14T19:20:47+00:00 -->

### 2026-05-14T19:20:47+00:00

Stage:
  Stage 8.4 - Bounce Candidate Propagation

Verdict:
  ready_for_manual_bounce_review

Friction score:
  12

Friction level:
  low friction

Next step:
  Review proposed bounce candidates with Stage 8.2 interactive labeling, then rerun Stage 8.3 event validation.

<!-- lab-entry:2026-05-14T19:23:06+00:00 -->

### 2026-05-14T19:23:06+00:00

Stage:
  Stage 8.4 - Bounce Candidate Propagation

Verdict:
  ready_for_manual_bounce_review

Friction score:
  12

Friction level:
  low friction

Next step:
  Review proposed bounce candidates with Stage 8.2 interactive labeling, then rerun Stage 8.3 event validation.

<!-- lab-entry:2026-05-14T19:33:19+00:00 -->

### 2026-05-14T19:33:19+00:00

Stage:
  Stage 8.4 - Bounce Candidate Propagation

Verdict:
  ready_for_manual_bounce_review

Friction score:
  12

Friction level:
  low friction

Next step:
  Review proposed bounce candidates with Stage 8.2 interactive labeling, then rerun Stage 8.3 event validation.

<!-- lab-entry:2026-05-14T19:37:58+00:00 -->

### 2026-05-14T19:37:58+00:00

Stage:
  Stage 8.4 - Bounce Candidate Propagation

Verdict:
  ready_with_warnings

Friction score:
  29

Friction level:
  medium friction

Next step:
  Review warnings, then add more manual bounce labels or lower the candidate threshold.

<!-- lab-entry:2026-05-14T19:38:46+00:00 -->

### 2026-05-14T19:38:46+00:00

Stage:
  Stage 8.4 - Bounce Candidate Propagation

Verdict:
  needs_more_post_hit_ball_labels

Friction score:
  31

Friction level:
  medium friction

Next step:
  Collect more post-hit ball/event labels after the manual hit, then rerun Stage 8.4.

<!-- lab-entry:2026-05-14T19:42:48+00:00 -->

### 2026-05-14T19:42:48+00:00

Stage:
  Stage 8.4 - Bounce Candidate Propagation

Verdict:
  needs_more_post_hit_ball_labels

Friction score:
  31

Friction level:
  medium friction

Next step:
  Collect more post-hit ball/event labels after the manual hit, then rerun Stage 8.4.
