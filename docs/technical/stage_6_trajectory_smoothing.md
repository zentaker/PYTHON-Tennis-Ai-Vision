# Stage 6 - Technical Functional Documentation

## Purpose

Stage 6 builds the first ball trajectory from Stage 5.1 improved candidates, smooths it, projects it into court space when projected coordinates are available, and creates simple event hypotheses.

This stage is exploratory. It does not implement production tracking, official line calling, scoring, or confirmed rally segmentation.

## Main files

| Type | Path |
|---|---|
| Script | `scripts/run_stage_6_trajectory_smoothing.py` |
| Trajectory module | `src/tennis_vision/trajectory_smoothing.py` |
| Event module | `src/tennis_vision/event_segmentation.py` |
| Friction scoring | `src/tennis_vision/friction.py` |
| Lab notebook builder | `src/tennis_vision/lab_notebook.py` |

## Functional flow

1. The script reads improved candidates from `outputs/ball_tracking/stage_5_1_candidate_improvement/improved_ball_candidates.csv`.
2. It reads projected candidates from `outputs/ball_tracking/stage_5_1_candidate_improvement/projected_improved_candidates.csv` when available.
3. It reads manual labels for visual comparison.
4. It builds a raw trajectory sorted by frame index.
5. It computes image-space and projected-space deltas and speeds.
6. It optionally interpolates between known points for visualization only.
7. It applies moving-average smoothing to image and projected coordinates.
8. It runs simple speed and direction heuristics to generate event hypotheses.
9. It writes raw trajectory, smoothed trajectory, and event CSV files.
10. It saves image-space and court-space preview images.
11. It writes JSON and Markdown reports and updates the lab notebook automatically.

## Important functions

| Function | File | Purpose | Inputs | Outputs | Notes |
|---|---|---|---|---|---|
| `read_improved_candidates` | `src/tennis_vision/trajectory_smoothing.py` | Load Stage 5.1 candidate rows | Improved candidates CSV | Candidate rows and errors | Search: `def read_improved_candidates` |
| `read_projected_candidates` | `src/tennis_vision/trajectory_smoothing.py` | Load projected candidate coordinates | Projected candidates CSV | Frame-indexed projection rows | Search: `def read_projected_candidates` |
| `build_raw_trajectory` | `src/tennis_vision/trajectory_smoothing.py` | Compute deltas and speeds | Candidate rows, FPS | Raw trajectory rows | Includes image and court-space speeds |
| `interpolate_trajectory` | `src/tennis_vision/trajectory_smoothing.py` | Add visualization-only interpolated rows | Raw rows, enabled flag | Expanded trajectory rows | Interpolated rows are marked |
| `moving_average_smooth` | `src/tennis_vision/trajectory_smoothing.py` | Smooth image/projected coordinates | Trajectory rows, window size | Smoothed rows | Default window size is 3 |
| `detect_events` | `src/tennis_vision/event_segmentation.py` | Detect event hypotheses | Raw trajectory rows | Event rows and warnings | Direction/speed heuristics only |
| `events_by_type` | `src/tennis_vision/event_segmentation.py` | Count event hypotheses | Event rows | Event count dict | Used in console/report summaries |
| `main` | `scripts/run_stage_6_trajectory_smoothing.py` | Run Stage 6 end to end | CLI args | CSVs, previews, reports, notebook update | Search: `def main` |

## Inputs and outputs

Reads:

- `outputs/ball_tracking/stage_5_1_candidate_improvement/improved_ball_candidates.csv`
- `outputs/ball_tracking/stage_5_1_candidate_improvement/projected_improved_candidates.csv`
- `outputs/ball_tracking/stage_4_1_manual_labels/manual_ball_labels.csv`
- `outputs/reports/stage_1_video_probe_report.json` for FPS when available

Writes:

- `outputs/ball_tracking/stage_6_trajectory_smoothing/raw_trajectory.csv`
- `outputs/ball_tracking/stage_6_trajectory_smoothing/smoothed_trajectory.csv`
- `outputs/ball_tracking/stage_6_trajectory_smoothing/trajectory_events.csv`
- `outputs/ball_tracking/stage_6_trajectory_smoothing/image_trajectory_preview.jpg`
- `outputs/ball_tracking/stage_6_trajectory_smoothing/court_trajectory_preview.jpg`
- `outputs/ball_tracking/stage_6_trajectory_smoothing/overlays/`
- `outputs/reports/stage_6_trajectory_smoothing_report.json`
- `outputs/reports/stage_6_trajectory_smoothing_report.md`
- `docs/lab-notebook/stage_6_trajectory_smoothing.md`

## Dependencies

- OpenCV for preview rendering.
- NumPy for preview canvases.
- Python standard library modules: `argparse`, `csv`, `json`, `math`, `pathlib`, and `collections`.
- `rich` is used only if available for readable console output.

## Product-owner interpretation

Stage 6 shows whether the improved candidate sequence can become a coherent early trajectory. It also tests whether simple event hypotheses can be generated from direction and speed changes.

The event CSV should be read as a research probe. It can suggest possible bounces, hits, speed changes, or direction changes, but it does not confirm tennis events.

## Known limitations

- The current trajectory has only a small number of manually validated points.
- Interpolation is for visualization only and does not create high-confidence detections.
- Moving-average smoothing can reduce jitter but cannot repair bad detections.
- Event heuristics are simple and should not be used for scoring or line calls.
- More manual labels may be needed before serious rally segmentation.

## Where to inspect code

- Stage entrypoint: `scripts/run_stage_6_trajectory_smoothing.py`, search `def main`.
- Raw trajectory construction: `src/tennis_vision/trajectory_smoothing.py`, search `def build_raw_trajectory`.
- Smoothing: `src/tennis_vision/trajectory_smoothing.py`, search `def moving_average_smooth`.
- Event hypotheses: `src/tennis_vision/event_segmentation.py`, search `def detect_events`.
