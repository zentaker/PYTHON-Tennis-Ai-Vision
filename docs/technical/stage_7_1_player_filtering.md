# Stage 7.1 - Technical Functional Documentation

## Purpose

Stage 7.1 reduces noisy person detections from Stage 7 and stabilizes main-player identity. It uses court-aware geometry, track quality, and lightweight clothing-color appearance profiles.

Near/far court side is a mutable state, not a permanent player identity.

## Main files

| Type | Path |
|---|---|
| Script | `scripts/run_stage_7_1_player_filtering.py` |
| Filtering module | `src/tennis_vision/player_filtering.py` |
| Identity module | `src/tennis_vision/player_identity.py` |
| Friction scoring | `src/tennis_vision/friction.py` |
| Lab notebook builder | `src/tennis_vision/lab_notebook.py` |

## Functional flow

1. Read Stage 7 player detections and player tracks.
2. Load Stage 3 court calibration and homography status.
3. Score each detection using bottom-center court proximity, bbox size, confidence, and track duration.
4. Rank tracks and keep up to two likely main tennis players.
5. Assign stable identities `player_a` and `player_b`.
6. Extract player crops and build lightweight HSV color profiles.
7. Generate side states per frame separately from identity.
8. Rewrite Stage 7 ball-player associations with stabilized player IDs.
9. Save filtered CSVs, identity profiles, overlays, reports, and lab notebook output.

## Important functions

| Function | File | Purpose | Inputs | Outputs | Notes |
|---|---|---|---|---|---|
| `read_player_tracks` | `src/tennis_vision/player_filtering.py` | Load Stage 7 track rows | Player tracks CSV | Track rows and errors | Search: `def read_player_tracks` |
| `score_track_rows` | `src/tennis_vision/player_filtering.py` | Score detections for main-player likelihood | Track rows, court polygon, thresholds | Scored rows and summaries | Uses court, size, duration, confidence |
| `select_main_tracks` | `src/tennis_vision/player_filtering.py` | Select likely main player tracks | Track summaries, max players | Source track IDs | Does not use near/far as identity |
| `apply_player_identities` | `src/tennis_vision/player_filtering.py` | Assign `player_a` / `player_b` identities | Scored rows, selected tracks | Filtered rows | Identity is logical, side is state |
| `build_side_states` | `src/tennis_vision/player_filtering.py` | Estimate near/far side per frame | Filtered rows | Side-state rows | Mutable state |
| `build_identity_profiles` | `src/tennis_vision/player_identity.py` | Build clothing-color profile JSON | Video, filtered rows | Profiles and warnings | Lightweight HSV histogram |
| `compare_identity_profiles` | `src/tennis_vision/player_identity.py` | Compare identity profiles | Profiles | Match rows | Not biometric re-id |
| `main` | `scripts/run_stage_7_1_player_filtering.py` | Run Stage 7.1 end to end | CLI args | CSVs, overlays, reports, notebook update | Search: `def main` |

## Inputs and outputs

Reads:

- `outputs/player_tracking/stage_7_player_interaction/player_detections.csv`
- `outputs/player_tracking/stage_7_player_interaction/player_tracks.csv`
- `outputs/player_tracking/stage_7_player_interaction/ball_player_distances.csv`
- `samples/video_01.mov`
- `outputs/reports/stage_3_court_calibration_probe_report.json`

Writes:

- `outputs/player_tracking/stage_7_1_player_filtering/filtered_player_detections.csv`
- `outputs/player_tracking/stage_7_1_player_filtering/filtered_player_tracks.csv`
- `outputs/player_tracking/stage_7_1_player_filtering/main_players.csv`
- `outputs/player_tracking/stage_7_1_player_filtering/player_identity_profiles.json`
- `outputs/player_tracking/stage_7_1_player_filtering/player_identity_matches.csv`
- `outputs/player_tracking/stage_7_1_player_filtering/player_side_states.csv`
- `outputs/player_tracking/stage_7_1_player_filtering/refined_ball_player_distances.csv`
- `outputs/reports/stage_7_1_player_filtering_report.json`
- `outputs/reports/stage_7_1_player_filtering_report.md`
- `docs/lab-notebook/stage_7_1_player_filtering.md`

## Dependencies

- OpenCV for crop extraction and overlay rendering.
- NumPy for color profile calculations.
- Python standard library modules: `argparse`, `csv`, `json`, `statistics`, and `collections`.

## Product-owner interpretation

Stage 7.1 answers whether the two main tennis players can be separated from audience, officials, and other background people. It also protects a key product requirement: identity should persist by track and clothing cues, while near/far side remains only a current state.

## Known limitations

- Clothing-color identity is not robust person re-identification.
- Track IDs from Stage 7 may already be fragmented.
- Court filtering depends on calibration quality.
- Main-player selection is heuristic and may need manual identity labels later.

## Where to inspect code

- Stage entrypoint: `scripts/run_stage_7_1_player_filtering.py`, search `def main`.
- Court-aware scoring: `src/tennis_vision/player_filtering.py`, search `def score_track_rows`.
- Identity profiles: `src/tennis_vision/player_identity.py`, search `def build_identity_profiles`.
- Side states: `src/tennis_vision/player_filtering.py`, search `def build_side_states`.
