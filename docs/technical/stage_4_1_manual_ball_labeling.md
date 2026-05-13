# Stage 4.1 - Technical Functional Documentation

## Purpose

Stage 4.1 lets the user manually label the real tennis ball in selected frames. These labels become ground truth for Stage 5 candidate filtering and court projection.

## Main Files

- Script: `scripts/run_stage_4_1_ball_labeling_helper.py`
- Module: `src/tennis_vision/ball_labeling.py`

## Functional Flow

1. The script selects a video and frame indices from CLI arguments.
2. Interactive mode opens an OpenCV window for each selected frame.
3. The user clicks the real ball, saves, skips, undoes, or quits.
4. Display coordinates are converted back to original video coordinates.
5. Manual labels are saved to CSV and JSON.
6. Label overlay images are saved for visible labels.
7. If Stage 4 candidate CSV exists, nearest candidate distances are computed.
8. Reports and lab notebook pages are updated.

## Important Functions

| Function | File | Purpose | Inputs | Outputs | Notes |
|---|---|---|---|---|---|
| `build_frame_indices` | `src/tennis_vision/ball_labeling.py` | Resolve frame list | CLI frame options | frame indices | Search: `def build_frame_indices` |
| `label_frames_interactively` | `src/tennis_vision/ball_labeling.py` | OpenCV click labeling | video, frames, output dir | labels/status | Keys: click, `u`, `s`, `n`, `q` |
| `load_stage_4_display_frame` | `src/tennis_vision/ball_labeling.py` | Use Stage 4 overlay for display if available | overlay dir, frame index | display frame | Original coordinates still saved |
| `write_labels_csv` | `src/tennis_vision/ball_labeling.py` | Save labels CSV | path, labels | CSV file | Ground truth output |
| `write_labels_json` | `src/tennis_vision/ball_labeling.py` | Save labels JSON | path, labels | JSON file | Ground truth output |
| `compare_candidates_to_labels` | `src/tennis_vision/ball_labeling.py` | Compare automatic candidates to labels | labels, Stage 4 CSV | comparison CSV/summary | Thresholds: 10, 25, 50, 100 px |
| `load_frames_without_interaction` | `scripts/run_stage_4_1_ball_labeling_helper.py` | Safe non-GUI verification | video, frames | skipped labels/status | Used with `--no-interactive` |
| `main` | `scripts/run_stage_4_1_ball_labeling_helper.py` | Stage 4.1 entrypoint | CLI args | labels, reports, notebook | Search: `def main` |

## Inputs And Outputs

Reads:

- `samples/video_01.mov`
- Optional Stage 4 overlays under `outputs/ball_tracking/stage_4_ball_probe/ball_candidates_overlay/`
- Optional Stage 4 candidate CSV at `outputs/ball_tracking/stage_4_ball_probe/ball_candidates.csv`

Writes:

- `outputs/ball_tracking/stage_4_1_manual_labels/manual_ball_labels.csv`
- `outputs/ball_tracking/stage_4_1_manual_labels/manual_ball_labels.json`
- `outputs/ball_tracking/stage_4_1_manual_labels/label_overlays/*.jpg`
- `outputs/ball_tracking/stage_4_1_manual_labels/candidate_label_comparison.csv`
- `outputs/reports/stage_4_1_ball_labeling_helper_report.*`
- `docs/lab-notebook/stage_4_1_ball_labeling_helper.md`

## Dependencies

- OpenCV
- Python csv/json/statistics/math
- rich if available

## Product-Owner Interpretation

Stage 4.1 answers: "Where is the real ball in selected frames?" It creates the small truth set needed before improving candidate filtering.

## Known Limitations

- Requires manual clicking for useful labels.
- It does not train a model.
- Non-interactive mode is only a verification path and creates skipped labels.

## Where To Inspect Code

- `src/tennis_vision/ball_labeling.py`, search `def label_frames_interactively`.
- `src/tennis_vision/ball_labeling.py`, search `def compare_candidates_to_labels`.
- `scripts/run_stage_4_1_ball_labeling_helper.py`, search `def main`.
