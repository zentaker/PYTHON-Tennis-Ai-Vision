# Stage 5.1 - Candidate Improvement

## Summary

| Field | Value |
|---|---|
| Stage | Stage 5.1 - Ball candidate generation improvement |
| Verdict | ready_for_stage_6 |
| Friction score | 0 |
| Friction level | low friction |
| Timestamp | 2026-05-13T08:13:58+00:00 |
| Recommended next step | Proceed to Stage 6: trajectory smoothing and rally/event segmentation probe. |

## Input

| Field | Value |
|---|---|
| Video path | C:\Users\MSI\Desktop\TennisAiVision\samples\video_01.mov |
| Manual labels path | C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_4_1_manual_labels\manual_ball_labels.csv |
| Labeled frames count | 5 |
| Strategies tested | hsv_color, motion_difference, hybrid |
| Stage 5 baseline average distance | 512.558 |
| Homography available | yes |

## Output

| Field | Value |
|---|---|
| JSON report path | C:\Users\MSI\Desktop\TennisAiVision\outputs\reports\stage_5_1_candidate_improvement_report.json |
| Markdown report path | C:\Users\MSI\Desktop\TennisAiVision\outputs\reports\stage_5_1_candidate_improvement_report.md |
| Log | C:\Users\MSI\Desktop\TennisAiVision\outputs\logs\stage_5_1_candidate_improvement_20260513T081358Z.log |
| Strategy comparison CSV | C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_5_1_candidate_improvement\strategy_comparison.csv |
| Improved candidates CSV | C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_5_1_candidate_improvement\improved_ball_candidates.csv |
| Projected candidates CSV | C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_5_1_candidate_improvement\projected_improved_candidates.csv |
| Strategy preview | C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_5_1_candidate_improvement\strategy_preview.jpg |

## Console-equivalent table

| Field | Value |
|---|---|
| Best strategy | hsv_color |
| Baseline average distance | 512.558 |
| Improved average distance | 3.73 |
| Improvement over baseline | 508.828 |
| Improved candidates | 5 |
| Projected candidates | 5 |
| Verdict | ready_for_stage_6 |
| Friction | 0 (low friction) |
| Recommended next step | Proceed to Stage 6: trajectory smoothing and rally/event segmentation probe. |

## Warnings

No warnings.

## Errors

No errors.

## Interpretation

Stage 5.1 tests low-cost local computer vision strategies against manual ball labels. It measures whether handcrafted candidates are close enough for smoothing, without claiming production tracking.

## Next step

Proceed to Stage 6: trajectory smoothing and rally/event segmentation probe.

## Run history

<!-- lab-entry:2026-05-13T08:10:39+00:00 -->

### 2026-05-13T08:10:39+00:00

| Field | Value |
|---|---|
| Stage | Stage 5.1 - Candidate Improvement |
| Verdict | ready_for_stage_6 |
| Friction score | 0 |
| Friction level | low friction |
| Next step | Proceed to Stage 6: trajectory smoothing and rally/event segmentation probe. |

<!-- lab-entry:2026-05-13T08:13:58+00:00 -->

### 2026-05-13T08:13:58+00:00

| Field | Value |
|---|---|
| Stage | Stage 5.1 - Candidate Improvement |
| Verdict | ready_for_stage_6 |
| Friction score | 0 |
| Friction level | low friction |
| Next step | Proceed to Stage 6: trajectory smoothing and rally/event segmentation probe. |
