# Stage 6 Trajectory Smoothing and Event Segmentation Probe Report

## Verdict

- Final verdict: ready_for_stage_7
- Friction score: 3
- Friction level: low friction

## Inputs

- Improved candidates CSV: `C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_5_1_candidate_improvement\improved_ball_candidates.csv`
- Projected candidates CSV: `C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_5_1_candidate_improvement\projected_improved_candidates.csv`
- Manual labels CSV: `C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_4_1_manual_labels\manual_ball_labels.csv`
- Calibration/homography availability: True

## Trajectory summary

| Metric | Value |
|---|---|
| trajectory points | 5 |
| interpolated points | 56 |
| frame range | 120 to 180 |
| smoothing method | moving_average_3 |
| image preview path | C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_6_trajectory_smoothing\image_trajectory_preview.jpg |
| court preview path | C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_6_trajectory_smoothing\court_trajectory_preview.jpg |

## Event segmentation summary

| Event type | Count |
|---|---:|
| speed_spike | 1 |
| direction_change | 1 |
| possible_bounce | 1 |
| possible_hit | 2 |
| speed_drop | 1 |

## Output artifacts

- Raw trajectory CSV: `C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_6_trajectory_smoothing\raw_trajectory.csv`
- Smoothed trajectory CSV: `C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_6_trajectory_smoothing\smoothed_trajectory.csv`
- Events CSV: `C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_6_trajectory_smoothing\trajectory_events.csv`
- Image trajectory preview: `C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_6_trajectory_smoothing\image_trajectory_preview.jpg`
- Court trajectory preview: `C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_6_trajectory_smoothing\court_trajectory_preview.jpg`
- Overlay folder: `C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_6_trajectory_smoothing\overlays`

## Product Owner interpretation

Stage 6 builds a first trajectory from improved candidates and smooths it with a moving average. Event segmentation is hypothesis-only. The current sequence is short, so more manual labels would make event segmentation more meaningful. Projection and smoothing are working well enough for a cautious player-interaction probe.

## Warnings

- Only a small number of trajectory points are available; event hypotheses are preliminary.

## Errors

No errors.

## Next step

Proceed to Stage 7: player tracking and ball-player interaction probe.
