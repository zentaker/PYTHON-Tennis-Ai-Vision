# Stage 7 Player Tracking and Ball-Player Interaction Probe Report

## Verdict

- Final verdict: ready_with_warnings
- Friction score: 21
- Friction level: medium friction

## Inputs

- Video path: `C:\Users\MSI\Desktop\TennisAiVision\samples\video_01.mov`
- Smoothed trajectory path: `C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_6_trajectory_smoothing\smoothed_trajectory.csv`
- Manual labels path: `C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_4_1_manual_labels\manual_ball_labels.csv`
- Calibration/homography availability: True

## Player detection summary

| Metric | Value |
|---|---|
| frames analyzed | [120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 150, 165, 180] |
| player detections | 221 |
| player tracks | 14 |
| YOLO model | yolo11n.pt |
| device | cpu |
| confidence threshold | 0.25 |

## Ball-player association summary

| Metric | Value |
|---|---|
| ball points associated | 5 |
| average distance px | 490.912 |
| minimum distance px | 114.183 |
| frame tolerance | 5 |
| interactions found | 7 |

## Interaction hypotheses

| Interaction type | Count |
|---|---:|
| ball_near_player | 2 |
| possible_hit_window | 1 |
| ball_leaving_player | 2 |
| ball_approaching_player | 2 |

## Output artifacts

- Player detections: `C:\Users\MSI\Desktop\TennisAiVision\outputs\player_tracking\stage_7_player_interaction\player_detections.csv`
- Player tracks: `C:\Users\MSI\Desktop\TennisAiVision\outputs\player_tracking\stage_7_player_interaction\player_tracks.csv`
- Ball-player distances: `C:\Users\MSI\Desktop\TennisAiVision\outputs\player_tracking\stage_7_player_interaction\ball_player_distances.csv`
- Interactions: `C:\Users\MSI\Desktop\TennisAiVision\outputs\player_tracking\stage_7_player_interaction\ball_player_interactions.csv`
- Player overlays: `C:\Users\MSI\Desktop\TennisAiVision\outputs\player_tracking\stage_7_player_interaction\player_detection_overlays`
- Interaction overlays: `C:\Users\MSI\Desktop\TennisAiVision\outputs\player_tracking\stage_7_player_interaction\interaction_overlays`
- Summary preview: `C:\Users\MSI\Desktop\TennisAiVision\outputs\player_tracking\stage_7_player_interaction\player_interaction_preview.jpg`

## Product Owner interpretation

Stage 7 validates whether local CPU person detection can provide player positions for ball-player proximity hypotheses. The interactions are not confirmed hits. The current ball trajectory is still sparse, so more labels would improve confidence. Player detection is viable enough for a local interaction probe.

## Warnings

- Player tracking is approximate and produced several temporary track IDs.
- Ball trajectory is sparse; player-ball interactions are hypotheses only.

## Errors

No errors.

## Next step

Review hypotheses, then choose Stage 7.1 for more labels or Stage 8 for a cautious timeline prototype.
