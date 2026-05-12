# Stage 4 Ball Tracking Probe Report

## Verdict

- Final verdict: ready_with_warnings
- Friction score: 21
- Friction level: medium friction

## Input

- Video path: `C:\Users\MSI\Desktop\TennisAiVision\samples\video_01.mov`
- Max frames: 20
- Interval: 15
- Resize width: 1280
- YOLO enabled: no

## Output

- Overlay folder: `C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_4_ball_probe\ball_candidates_overlay`
- Candidate CSV path: `C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_4_ball_probe\ball_candidates.csv`
- Trajectory preview path: `C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_4_ball_probe\trajectory_preview.jpg`
- JSON report: `C:\Users\MSI\Desktop\TennisAiVision\outputs\reports\stage_4_ball_tracking_probe_report.json`
- Markdown report: `C:\Users\MSI\Desktop\TennisAiVision\outputs\reports\stage_4_ball_tracking_probe_report.md`
- Log path: `C:\Users\MSI\Desktop\TennisAiVision\outputs\logs\stage_4_ball_tracking_probe_20260512T235017Z.log`

## Candidate summary

| Metric | Value |
|---|---|
| Frames processed | 20 |
| Total candidates | 160 |
| Frames with candidates | 20 |
| Average candidates per frame | 8.0 |

## Interpretation

The simple OpenCV heuristic found ball-like candidates, but these detections are likely noisy. This validates a local image-space candidate probe, not production ball tracking. Stage 5 should filter candidates by motion and court geometry. Stage 3 homography is available, so future filtering can project candidates into the calibrated court plane.

## Warnings

- Many ball-like candidates were detected per frame; the heuristic is likely noisy and needs Stage 5 filtering.

## Errors

No errors.

## Recommended fixes

- Stage 5 should filter candidates by motion consistency and court position.

## Next step

Proceed to Stage 5: Ball Candidate Filtering and Court Projection.
