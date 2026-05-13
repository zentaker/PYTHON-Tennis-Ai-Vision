# Stage 7.1 Court-Aware Player Filtering and Identity Stabilization Report

## Verdict

- Final verdict: ready_with_warnings
- Friction score: 15
- Friction level: low friction

## Inputs

- Player detections CSV: `C:\Users\MSI\Desktop\TennisAiVision\outputs\player_tracking\stage_7_player_interaction\player_detections.csv`
- Player tracks CSV: `C:\Users\MSI\Desktop\TennisAiVision\outputs\player_tracking\stage_7_player_interaction\player_tracks.csv`
- Video path: `C:\Users\MSI\Desktop\TennisAiVision\samples\video_01.mov`
- Calibration/homography availability: True

## Filtering summary

| Metric | Value |
|---|---:|
| input detections | 221 |
| kept detections | 40 |
| rejected detections | 181 |
| input tracks | 14 |
| kept tracks | 2 |
| main players selected | 2 |

## Identity summary

| Player ID | Source tracks | Frames seen | Dominant appearance | Initial side | Notes |
|---|---|---:|---|---|---|
| player_a | player_2 | 20 | upper #b46445, #b46344; lower #bc794e, #bb734d | far_side | Identity is appearance/track based; side is a mutable state. |
| player_b | player_1 | 20 | upper #aa6a4a, #ac6c4a; lower #ad5e37, #ae5e37 | near_side | Identity is appearance/track based; side is a mutable state. |

## Side-state summary

Near/far side is recorded as a mutable state, not as permanent player identity.

## Refined ball-player association

- Refined associations count: 5
- Average distance: 490.912
- Main warnings: Many non-main tracks remain after filtering; Stage 7.2 may improve identity handling.

## Product Owner interpretation

Stage 7.1 reduces noisy people detections with court-aware scoring and creates lightweight clothing-color identity profiles. Player identity is separated from near/far side state, so side can change without redefining the player. The two main player identities are separable enough for the next local timeline prototype.

## Warnings

- Many non-main tracks remain after filtering; Stage 7.2 may improve identity handling.

## Errors

No errors.

## Next step

Review filtered identities; proceed to Stage 8 cautiously or Stage 7.2 if identity confidence is not sufficient.
