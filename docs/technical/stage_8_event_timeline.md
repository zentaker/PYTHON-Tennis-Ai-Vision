# Stage 8 - Technical Functional Documentation

## Purpose

Stage 8 builds a first shot/event timeline and rally segmentation prototype. It merges ball trajectory anchors, Stage 6 event hypotheses, Stage 7 ball-player interaction hypotheses, and Stage 7.1 stabilized player identities into a structured event timeline.

This stage preserves uncertainty. Events use `possible_*` labels where appropriate and are not official scoring, line calling, bounce detection, or confirmed shot classification.

## Main files

| Type | Path |
|---|---|
| Script | `scripts/run_stage_8_event_timeline.py` |
| Timeline module | `src/tennis_vision/event_timeline.py` |
| Rally segmentation module | `src/tennis_vision/rally_segmentation.py` |
| Friction scoring | `src/tennis_vision/friction.py` |
| Lab notebook updater | `src/tennis_vision/lab_notebook.py` |

## Functional flow

1. Load Stage 6 smoothed trajectory rows from `outputs/ball_tracking/stage_6_trajectory_smoothing/smoothed_trajectory.csv`.
2. Keep non-interpolated trajectory anchors as timeline trajectory points.
3. Load Stage 6 event hypotheses, Stage 7 interaction hypotheses, and Stage 7.1 refined player associations.
4. Normalize events into a shared schema with frame, optional timestamp, event type, source, player identity, side state, ball coordinates, score, reason, and notes.
5. Merge nearby events into timeline clusters using `--merge-window` frames.
6. Attribute events to `player_a` or `player_b` when Stage 7.1 evidence exists near the event frame.
7. Build conservative rally segments from first to last high-confidence trajectory anchor, splitting only on large frame gaps.
8. Write timeline CSV/JSON, rally segment CSV, player attribution CSV, visual previews, reports, and lab notebook updates.

## Important functions

| Function | File | Purpose | Inputs | Outputs | Notes |
|---|---|---|---|---|---|
| `read_smoothed_trajectory` | `src/tennis_vision/event_timeline.py` | Load Stage 6 trajectory rows | smoothed trajectory CSV | trajectory rows and warnings | Search hint: `def read_smoothed_trajectory` |
| `read_stage_events` | `src/tennis_vision/event_timeline.py` | Load Stage 6 event hypotheses | trajectory events CSV | normalized event rows | Search hint: `def read_stage_events` |
| `read_interactions` | `src/tennis_vision/event_timeline.py` | Load Stage 7 interaction hypotheses | interaction CSV | normalized event rows | Search hint: `def read_interactions` |
| `read_refined_associations` | `src/tennis_vision/event_timeline.py` | Load Stage 7.1 identity-aware ball-player associations | refined distances CSV | normalized association rows | Search hint: `def read_refined_associations` |
| `make_trajectory_events` | `src/tennis_vision/event_timeline.py` | Convert non-interpolated trajectory anchors to timeline events | trajectory rows | trajectory-point events | Interpolated rows are excluded |
| `merge_timeline_events` | `src/tennis_vision/event_timeline.py` | Merge nearby event evidence into clusters | events, merge window, FPS | timeline rows | Uses priority ordering for primary event type |
| `build_player_event_attribution` | `src/tennis_vision/event_timeline.py` | Attach stable player identities to timeline events | timeline rows, refined associations | attribution rows | Near/far remains side state |
| `build_rally_segments` | `src/tennis_vision/rally_segmentation.py` | Create conservative rally segments | trajectory anchors, timeline events, FPS | rally segment rows | Prototype only |
| `calculate_stage_8_friction_score` | `src/tennis_vision/friction.py` | Score Stage 8 operational friction | missing/input/output flags | friction dict | Search hint: `def calculate_stage_8_friction_score` |
| `main` | `scripts/run_stage_8_event_timeline.py` | Run Stage 8 end to end | CLI args | outputs, reports, notebook update | Search hint: `def main` |

## Inputs and outputs

Reads:

- `outputs/ball_tracking/stage_6_trajectory_smoothing/smoothed_trajectory.csv`
- `outputs/ball_tracking/stage_6_trajectory_smoothing/trajectory_events.csv`
- `outputs/player_tracking/stage_7_player_interaction/ball_player_interactions.csv`
- `outputs/player_tracking/stage_7_1_player_filtering/main_players.csv`
- `outputs/player_tracking/stage_7_1_player_filtering/player_side_states.csv`
- `outputs/player_tracking/stage_7_1_player_filtering/refined_ball_player_distances.csv`

Writes:

- `outputs/timeline/stage_8_event_timeline/event_timeline.csv`
- `outputs/timeline/stage_8_event_timeline/event_timeline.json`
- `outputs/timeline/stage_8_event_timeline/rally_segments.csv`
- `outputs/timeline/stage_8_event_timeline/player_event_attribution.csv`
- `outputs/timeline/stage_8_event_timeline/timeline_preview.jpg`
- `outputs/timeline/stage_8_event_timeline/court_timeline_preview.jpg`
- `outputs/timeline/stage_8_event_timeline/timeline_summary.md`
- `outputs/reports/stage_8_event_timeline_report.json`
- `outputs/reports/stage_8_event_timeline_report.md`

## Dependencies

- OpenCV
- NumPy
- rich

## Product-owner interpretation

Stage 8 answers whether the current research artifacts can be organized into a readable timeline. It shows how ball motion, player proximity, and player identity can support possible hit/bounce/event hypotheses, while making clear that these are not validated tennis events.

## Known limitations

- The current sample has few high-confidence ball anchors.
- Timeline clustering is heuristic.
- Rally segmentation does not infer point outcome or score.
- Player attribution depends on Stage 7.1 identity quality.
- Events remain hypotheses until manually validated or supported by stronger models.

## Where to inspect code

- `scripts/run_stage_8_event_timeline.py`, search `def main`
- `src/tennis_vision/event_timeline.py`, search `def merge_timeline_events`
- `src/tennis_vision/rally_segmentation.py`, search `def build_rally_segments`
