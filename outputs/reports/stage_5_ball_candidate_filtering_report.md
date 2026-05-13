# Stage 5 Ball Candidate Filtering and Court Projection Report

## Verdict

- Final verdict: ready_with_warnings
- Friction score: 21
- Friction level: medium friction

## Inputs

- Automatic candidates CSV: `C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_4_ball_probe\ball_candidates.csv`
- Manual labels CSV: `C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_4_1_manual_labels\manual_ball_labels.csv`
- Calibration source: `C:\Users\MSI\Desktop\TennisAiVision\outputs\reports\stage_3_court_calibration_probe_report.json`
- Homography status: True

## Candidate-to-label comparison

| Metric | Value |
|---|---|
| manual labels count | 5 |
| automatic candidates count | 160 |
| labeled frames compared | 5 |
| average nearest distance | 512.558 |
| median nearest distance | 579.143 |
| frames within 10 px | 0 |
| frames within 25 px | 0 |
| frames within 50 px | 0 |
| frames within 100 px | 0 |
| frames within 200 px | 0 |

## Filtered candidates

| Metric | Value |
|---|---|
| selected candidates | 3 |
| rejected candidates | 157 |
| main rejection reasons | {'rejected_by_temporal_or_court_filter': 117, 'rejected_by_manual_label_distance': 40} |

## Court projection

Homography available: True. Projection succeeded for 3 candidates. Preview: `C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_5_filtered_candidates\court_projection_preview.jpg`.

## Interpretation

Stage 5 compares noisy Stage 4 candidates against manual labels and selects a cleaner baseline trajectory. This is still not production tracking. Automatic candidates are not close enough to the manual labels, so a specialized ball model is likely needed. Court projection is working for selected candidates.

## Warnings

- Automatic candidates still contain many false positives relative to manual labels.

## Errors

No errors.

## Recommended fixes

- Use Stage 5 filtering outputs to constrain candidates by court and temporal consistency.

## Next step

Review Stage 5 warnings, then decide between Stage 6 smoothing or Stage 5.1 detector improvement.
