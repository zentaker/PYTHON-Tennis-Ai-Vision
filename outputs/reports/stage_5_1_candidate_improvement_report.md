# Stage 5.1 Ball Candidate Generation Improvement Report

## Verdict

- Final verdict: ready_for_stage_6
- Friction score: 0
- Friction level: low friction

## Baseline

- Stage 5 average nearest distance: 512.558
- Stage 5 median nearest distance: 579.143

## Strategies tested

| Strategy | Avg distance | Median distance | Best frame | Frames <= 100 px | Candidate count |
|---|---:|---:|---:|---:|---:|
| hsv_color | 3.73 | 3.0 | 150 | 5 | 60 |
| motion_difference | 5.053 | 5.101 | 150 | 5 | 60 |
| hybrid | 3.73 | 3.0 | 150 | 5 | 60 |

## Best strategy

Best strategy: `hsv_color`. Average distance: 3.73 px. Improvement over Stage 5 baseline: 508.828 px. This is good enough to begin a limited smoothing probe.

## Visual outputs

| Metric | Value |
|---|---|
| Overlay folder | C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_5_1_candidate_improvement\overlays |
| Strategy preview | C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_5_1_candidate_improvement\strategy_preview.jpg |
| Improved candidates CSV | C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_5_1_candidate_improvement\improved_ball_candidates.csv |
| Projected candidates CSV | C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_5_1_candidate_improvement\projected_improved_candidates.csv |
| Court projection preview | C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_5_1_candidate_improvement\court_projection_preview.jpg |

## Product Owner interpretation

Stage 5.1 tests whether handcrafted local computer vision can improve candidate generation before trajectory smoothing. Manual labels are the ground truth. The improved candidates are close enough for a cautious Stage 6 probe.

## Warnings

No warnings.

## Errors

No errors.

## Next step

Proceed to Stage 6: trajectory smoothing and rally/event segmentation probe.
