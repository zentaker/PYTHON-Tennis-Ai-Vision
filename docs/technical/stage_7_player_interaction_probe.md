# Stage 7 - Technical Functional Documentation

## Purpose

Stage 7 adds local player detection and approximate player tracking so ball-player proximity can support possible interaction hypotheses. It uses Stage 6 ball trajectory data and CPU YOLO person detection on a small set of sampled frames.

This stage does not confirm hits, scoring, line calls, or rally events.

## Main files

| Type | Path |
|---|---|
| Script | `scripts/run_stage_7_player_interaction_probe.py` |
| Player tracking module | `src/tennis_vision/player_tracking.py` |
| Interaction module | `src/tennis_vision/ball_player_interaction.py` |
| Friction scoring | `src/tennis_vision/friction.py` |
| Lab notebook builder | `src/tennis_vision/lab_notebook.py` |

## Functional flow

1. The script reads Stage 6 smoothed trajectory rows.
2. It reads Stage 6 event hypotheses when available.
3. It selects a small set of trajectory/event frames and does not process the full video.
4. It loads the small YOLO model through the existing Stage 2 YOLO utility.
5. It runs CPU YOLO person detection on selected frames.
6. It projects player foot/center proxies into court space when Stage 3 homography is available.
7. It assigns approximate track IDs with nearest-center frame-to-frame matching.
8. It associates ball trajectory points to nearest player tracks within a frame tolerance.
9. It creates interaction hypotheses such as `ball_near_player` and `possible_hit_window`.
10. It saves CSVs, overlays, reports, and lab notebook updates.

## Important functions

| Function | File | Purpose | Inputs | Outputs | Notes |
|---|---|---|---|---|---|
| `read_smoothed_trajectory` | `src/tennis_vision/player_tracking.py` | Load Stage 6 ball trajectory | Smoothed trajectory CSV | Ball rows and errors | Search: `def read_smoothed_trajectory` |
| `select_analysis_frames` | `src/tennis_vision/player_tracking.py` | Select limited frames for YOLO | Trajectory rows, event frames, max frames | Frame indices | Avoids full-video processing |
| `detect_players` | `src/tennis_vision/player_tracking.py` | Run YOLO person detection on CPU | Video, frames, model, resize, confidence | Detection result dict | Detects `person` only |
| `track_players` | `src/tennis_vision/player_tracking.py` | Assign approximate track IDs | Detections | Player track rows | Lightweight nearest-center matching |
| `read_stage_6_events` | `src/tennis_vision/ball_player_interaction.py` | Load Stage 6 event hypotheses | Events CSV | Event rows and warnings | Search: `def read_stage_6_events` |
| `associate_ball_to_players` | `src/tennis_vision/ball_player_interaction.py` | Match ball points to nearest player tracks | Ball rows, tracks, events, tolerance | Associations, interactions, counts | Hypotheses only |
| `build_interactions` | `src/tennis_vision/ball_player_interaction.py` | Create ball-player interaction hypotheses | Association rows | Interaction rows | Does not confirm hits |
| `main` | `scripts/run_stage_7_player_interaction_probe.py` | Run Stage 7 end to end | CLI args | CSVs, overlays, reports, notebook update | Search: `def main` |

## Inputs and outputs

Reads:

- `samples/video_01.mov`
- `outputs/ball_tracking/stage_6_trajectory_smoothing/smoothed_trajectory.csv`
- `outputs/ball_tracking/stage_6_trajectory_smoothing/trajectory_events.csv`
- `outputs/ball_tracking/stage_4_1_manual_labels/manual_ball_labels.csv`
- `outputs/reports/stage_3_court_calibration_probe_report.json`

Writes:

- `outputs/player_tracking/stage_7_player_interaction/player_detections.csv`
- `outputs/player_tracking/stage_7_player_interaction/player_tracks.csv`
- `outputs/player_tracking/stage_7_player_interaction/ball_player_distances.csv`
- `outputs/player_tracking/stage_7_player_interaction/ball_player_interactions.csv`
- `outputs/player_tracking/stage_7_player_interaction/player_detection_overlays/`
- `outputs/player_tracking/stage_7_player_interaction/interaction_overlays/`
- `outputs/player_tracking/stage_7_player_interaction/player_interaction_preview.jpg`
- `outputs/reports/stage_7_player_interaction_probe_report.json`
- `outputs/reports/stage_7_player_interaction_probe_report.md`
- `docs/lab-notebook/stage_7_player_interaction_probe.md`

## Dependencies

- OpenCV for frame loading and overlay rendering.
- NumPy for preview contact sheet composition.
- Ultralytics YOLO from Stage 2 for CPU person detection.
- Python standard library modules: `argparse`, `csv`, `math`, `pathlib`, `statistics`, and `collections`.

## Product-owner interpretation

Stage 7 tests whether local player detection can provide enough spatial context to interpret ball trajectory events. If player detections and ball-player associations exist, the project can begin a cautious Stage 8 shot/event timeline prototype.

Any `possible_hit_window` row is a hypothesis. It means the ball is near a player around a trajectory/event cue, not that a hit is confirmed.

## Known limitations

- Track IDs are approximate and may switch.
- YOLO person boxes may include non-player people in the scene.
- Ball trajectory still has few high-confidence points.
- Player projection uses a simple bbox proxy, not footpoint calibration.
- Interaction hypotheses are not validated tennis events.

## Where to inspect code

- Stage entrypoint: `scripts/run_stage_7_player_interaction_probe.py`, search `def main`.
- Player detection: `src/tennis_vision/player_tracking.py`, search `def detect_players`.
- Tracking: `src/tennis_vision/player_tracking.py`, search `def track_players`.
- Association: `src/tennis_vision/ball_player_interaction.py`, search `def associate_ball_to_players`.
- Interaction logic: `src/tennis_vision/ball_player_interaction.py`, search `def build_interactions`.
