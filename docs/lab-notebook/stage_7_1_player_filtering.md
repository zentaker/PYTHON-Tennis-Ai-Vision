# Stage 7.1 - Player Filtering

## Summary

Stage:
  Stage 7.1 - Court-aware player filtering

Verdict:
  ready_with_warnings

Friction score:
  15

Friction level:
  low friction

Timestamp:
  2026-05-13T18:42:29+00:00

Recommended next step:
  Review filtered identities; proceed to Stage 8 cautiously or Stage 7.2 if identity confidence is not sufficient.

## Input

Player detections CSV:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\player_tracking\stage_7_player_interaction\player_detections.csv

Player tracks CSV:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\player_tracking\stage_7_player_interaction\player_tracks.csv

Video path:
  C:\Users\MSI\Desktop\TennisAiVision\samples\video_01.mov

Homography available:
  yes

## Output

JSON report path:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\reports\stage_7_1_player_filtering_report.json

Markdown report path:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\reports\stage_7_1_player_filtering_report.md

Log:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\logs\stage_7_1_player_filtering_20260513T184229Z.log

Filtered detections:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\player_tracking\stage_7_1_player_filtering\filtered_player_detections.csv

Filtered tracks:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\player_tracking\stage_7_1_player_filtering\filtered_player_tracks.csv

Main players:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\player_tracking\stage_7_1_player_filtering\main_players.csv

Identity profiles:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\player_tracking\stage_7_1_player_filtering\player_identity_profiles.json

Side states:
  C:\Users\MSI\Desktop\TennisAiVision\outputs\player_tracking\stage_7_1_player_filtering\player_side_states.csv

## Console-equivalent table

Input detections:
  221

Kept detections:
  40

Input tracks:
  14

Kept tracks:
  2

Main players selected:
  2

Player identities created:
  2

Refined associations:
  5

Verdict:
  ready_with_warnings

Friction:
  15 (low friction)

## Warnings

- Many non-main tracks remain after filtering; Stage 7.2 may improve identity handling.

## Errors

No errors.

## Interpretation

Stage 7.1 filters noisy people detections and creates stable player_a/player_b identities from track quality and clothing-color cues. Near/far side is stored as a mutable state, not as permanent identity.

## Next step

Review filtered identities; proceed to Stage 8 cautiously or Stage 7.2 if identity confidence is not sufficient.

## Run history

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

Older entries are preserved as originally written. Some historical entries may use legacy Markdown tables so prior run evidence is not erased.

<!-- lab-entry:2026-05-13T18:21:57+00:00 -->

### 2026-05-13T18:21:57+00:00

| Field | Value |
|---|---|
| Stage | Stage 7.1 - Player Filtering |
| Verdict | ready_with_warnings |
| Friction score | 15 |
| Friction level | low friction |
| Next step | Review filtered identities; proceed to Stage 8 cautiously or Stage 7.2 if identity confidence is not sufficient. |

<!-- lab-entry:2026-05-13T18:42:29+00:00 -->

### 2026-05-13T18:42:29+00:00

| Field | Value |
|---|---|
| Stage | Stage 7.1 - Player Filtering |
| Verdict | ready_with_warnings |
| Friction score | 15 |
| Friction level | low friction |
| Next step | Review filtered identities; proceed to Stage 8 cautiously or Stage 7.2 if identity confidence is not sufficient. |
