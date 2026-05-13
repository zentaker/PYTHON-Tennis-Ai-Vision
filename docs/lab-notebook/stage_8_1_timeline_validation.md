# Stage 8.1 - Timeline Validation

## Summary

| Field | Value |
|---|---|
| Stage | Stage 8.1 - Timeline validation |
| Verdict | needs_more_labels |
| Friction score | 32 |
| Friction level | medium friction |
| Timestamp | 2026-05-13T20:01:01+00:00 |
| Recommended next step | Run Stage 8.1 interactively across more frames, then rerun timeline validation. |

## Input

| Field | Value |
|---|---|
| Mode | non_interactive |
| Existing labels | 5 |
| New labels | 0 |
| Merged labels | 5 |
| Visible labels | 5 |
| Label frame range | 120 to 180 |

## Output

| Field | Value |
|---|---|
| JSON report path | C:\Users\MSI\Desktop\TennisAiVision\outputs\reports\stage_8_1_timeline_validation_report.json |
| Markdown report path | C:\Users\MSI\Desktop\TennisAiVision\outputs\reports\stage_8_1_timeline_validation_report.md |
| Log | C:\Users\MSI\Desktop\TennisAiVision\outputs\logs\stage_8_1_timeline_validation_20260513T200104Z.log |
| Expanded labels | C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_1_timeline_validation\expanded_ball_labels.csv |
| Candidate validation | C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_1_timeline_validation\expanded_candidate_validation.csv |
| Timeline validation | C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_1_timeline_validation\timeline_event_validation.csv |
| Validated timeline | C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_1_timeline_validation\validated_event_timeline.csv |

## Console-equivalent table

| Field | Value |
|---|---|
| Existing labels | 5 |
| New labels | 0 |
| Visible labels | 5 |
| Average label gap | 15 |
| Maximum label gap | 15 |
| Candidate average distance | 3.73 |
| Timeline events validated | 5 |
| Supported events | 5 |
| Verdict | needs_more_labels |
| Friction | 32 (medium friction) |

## Warnings

- Non-interactive mode used existing labels only; no new labels were collected.
- Label coverage is still sparse for tactical metrics; collect more labels across the rally.

## Errors

No errors.

## Interpretation

Stage 8.1 checks whether the Stage 8 timeline is backed by enough ball-label evidence. It can run non-interactively using current labels, but sparse coverage should trigger more manual labeling before tactical metrics.

## Next step

Run Stage 8.1 interactively across more frames, then rerun timeline validation.

## Run history

<!-- lab-entry:2026-05-13T19:26:22+00:00 -->

### 2026-05-13T19:26:22+00:00

| Field | Value |
|---|---|
| Stage | Stage 8.1 - Timeline Validation |
| Verdict | needs_more_labels |
| Friction score | 32 |
| Friction level | medium friction |
| Next step | Run Stage 8.1 interactively across more frames, then rerun timeline validation. |

<!-- lab-entry:2026-05-13T19:54:35+00:00 -->

### 2026-05-13T19:54:35+00:00

| Field | Value |
|---|---|
| Stage | Stage 8.1 - Timeline Validation |
| Verdict | needs_more_labels |
| Friction score | 32 |
| Friction level | medium friction |
| Next step | Run Stage 8.1 interactively across more frames, then rerun timeline validation. |

<!-- lab-entry:2026-05-13T19:55:15+00:00 -->

### 2026-05-13T19:55:15+00:00

| Field | Value |
|---|---|
| Stage | Stage 8.1 - Timeline Validation |
| Verdict | ready_for_stage_9 |
| Friction score | 0 |
| Friction level | low friction |
| Next step | Proceed to Stage 9: Tactical Metrics and Shot Zone Prototype. |

<!-- lab-entry:2026-05-13T19:56:37+00:00 -->

### 2026-05-13T19:56:37+00:00

| Field | Value |
|---|---|
| Stage | Stage 8.1 - Timeline Validation |
| Verdict | needs_more_labels |
| Friction score | 32 |
| Friction level | medium friction |
| Next step | Run Stage 8.1 interactively across more frames, then rerun timeline validation. |

<!-- lab-entry:2026-05-13T19:59:02+00:00 -->

### 2026-05-13T19:59:02+00:00

| Field | Value |
|---|---|
| Stage | Stage 8.1 - Timeline Validation |
| Verdict | ready_for_stage_9 |
| Friction score | 0 |
| Friction level | low friction |
| Next step | Proceed to Stage 9: Tactical Metrics and Shot Zone Prototype. |

<!-- lab-entry:2026-05-13T20:01:01+00:00 -->

### 2026-05-13T20:01:01+00:00

| Field | Value |
|---|---|
| Stage | Stage 8.1 - Timeline Validation |
| Verdict | needs_more_labels |
| Friction score | 32 |
| Friction level | medium friction |
| Next step | Run Stage 8.1 interactively across more frames, then rerun timeline validation. |
