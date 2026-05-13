# Stage 4.1 Manual Ball Labeling Helper Report

## Verdict

- Final verdict: ready_for_stage_5
- Friction score: 0
- Friction level: low friction

## Input

- Video path: `C:\Users\MSI\Desktop\TennisAiVision\samples\video_01.mov`
- Frame indices: [120, 135, 150, 165, 180]
- Resize width: 1280
- Frame source mode: stage_4_overlay_if_available_else_video_frame

## Manual labels

| Frame | Visible | X | Y | Overlay |
|---:|---|---:|---:|---|
| 120 | yes | 2181.0 | 492.0 | C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_4_1_manual_labels\label_overlays\manual_ball_label_frame_000120.jpg |
| 135 | yes | 2043.0 | 762.0 | C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_4_1_manual_labels\label_overlays\manual_ball_label_frame_000135.jpg |
| 150 | yes | 1905.0 | 1149.0 | C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_4_1_manual_labels\label_overlays\manual_ball_label_frame_000150.jpg |
| 165 | yes | 1794.0 | 1164.0 | C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_4_1_manual_labels\label_overlays\manual_ball_label_frame_000165.jpg |
| 180 | yes | 1674.0 | 1248.0 | C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_4_1_manual_labels\label_overlays\manual_ball_label_frame_000180.jpg |

## Candidate comparison

| Metric | Value |
|---|---|
| labeled frames compared | 5 |
| frames where nearest candidate <= 10 px | 0 |
| <= 25 px | 0 |
| <= 50 px | 0 |
| <= 100 px | 0 |
| average nearest distance | 512.56 |
| median nearest distance | 579.14 |

## Output

- Output CSV path: `C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_4_1_manual_labels\manual_ball_labels.csv`
- Output JSON path: `C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_4_1_manual_labels\manual_ball_labels.json`
- Overlay folder: `C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_4_1_manual_labels\label_overlays`
- Comparison CSV path: `C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_4_1_manual_labels\candidate_label_comparison.csv`
- JSON report: `C:\Users\MSI\Desktop\TennisAiVision\outputs\reports\stage_4_1_ball_labeling_helper_report.json`
- Markdown report: `C:\Users\MSI\Desktop\TennisAiVision\outputs\reports\stage_4_1_ball_labeling_helper_report.md`
- Log path: `C:\Users\MSI\Desktop\TennisAiVision\outputs\logs\stage_4_1_ball_labeling_helper_20260513T072719Z.log`

## Interpretation

Manual labels are available as ground truth for Stage 5. Candidate comparison can now show whether Stage 4 detections were close to the real ball. If nearest distances are large, the Stage 4 heuristic is failing due to false positives or missed detections. This remains a validation helper, not production tracking.

## Warnings

No warnings.

## Errors

No errors.

## Recommended fixes

No fixes required.

## Next step

Proceed to Stage 5: Ball Candidate Filtering and Court Projection.
