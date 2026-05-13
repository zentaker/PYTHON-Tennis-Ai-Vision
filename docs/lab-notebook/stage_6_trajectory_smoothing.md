# Stage 6 - Trajectory Smoothing

## Summary

| Field | Value |
|---|---|
| Stage | Stage 6 - Trajectory smoothing and event segmentation |
| Verdict | ready_for_stage_7 |
| Friction score | 3 |
| Friction level | low friction |
| Timestamp | 2026-05-13T17:38:47+00:00 |
| Recommended next step | Proceed to Stage 7: player tracking and ball-player interaction probe. |

## Input

| Field | Value |
|---|---|
| Improved candidates CSV | C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_5_1_candidate_improvement\improved_ball_candidates.csv |
| Projected candidates CSV | C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_5_1_candidate_improvement\projected_improved_candidates.csv |
| Manual labels CSV | C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_4_1_manual_labels\manual_ball_labels.csv |
| Projected candidates available | yes |

## Output

| Field | Value |
|---|---|
| JSON report path | C:\Users\MSI\Desktop\TennisAiVision\outputs\reports\stage_6_trajectory_smoothing_report.json |
| Markdown report path | C:\Users\MSI\Desktop\TennisAiVision\outputs\reports\stage_6_trajectory_smoothing_report.md |
| Log | C:\Users\MSI\Desktop\TennisAiVision\outputs\logs\stage_6_trajectory_smoothing_20260513T173847Z.log |
| Raw trajectory CSV | C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_6_trajectory_smoothing\raw_trajectory.csv |
| Smoothed trajectory CSV | C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_6_trajectory_smoothing\smoothed_trajectory.csv |
| Events CSV | C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_6_trajectory_smoothing\trajectory_events.csv |
| Image preview | C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_6_trajectory_smoothing\image_trajectory_preview.jpg |
| Court preview | C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_6_trajectory_smoothing\court_trajectory_preview.jpg |

## Console-equivalent table

| Field | Value |
|---|---|
| Trajectory points | 5 |
| Interpolated points | 56 |
| Events | 6 |
| Events by type | {'direction_change': 1, 'possible_bounce': 1, 'possible_hit': 2, 'speed_drop': 1, 'speed_spike': 1} |
| Smoothing method | moving_average_3 |
| Verdict | ready_for_stage_7 |
| Friction | 3 (low friction) |
| Recommended next step | Proceed to Stage 7: player tracking and ball-player interaction probe. |

## Warnings

- Only a small number of trajectory points are available; event hypotheses are preliminary.

## Errors

No errors.

## Interpretation

Stage 6 creates an initial smoothed trajectory from improved ball candidates and marks event hypotheses. The event output is exploratory and should not be treated as scoring, line calling, or confirmed rally segmentation.

## Next step

Proceed to Stage 7: player tracking and ball-player interaction probe.

## Run history

<!-- lab-entry:2026-05-13T08:33:29+00:00 -->

### 2026-05-13T08:33:29+00:00

| Field | Value |
|---|---|
| Stage | Stage 6 - Trajectory Smoothing |
| Verdict | ready_for_stage_7 |
| Friction score | 3 |
| Friction level | low friction |
| Next step | Proceed to Stage 7: player tracking and ball-player interaction probe. |

<!-- lab-entry:2026-05-13T17:38:47+00:00 -->

### 2026-05-13T17:38:47+00:00

| Field | Value |
|---|---|
| Stage | Stage 6 - Trajectory Smoothing |
| Verdict | ready_for_stage_7 |
| Friction score | 3 |
| Friction level | low friction |
| Next step | Proceed to Stage 7: player tracking and ball-player interaction probe. |
