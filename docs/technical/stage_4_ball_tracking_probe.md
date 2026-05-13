# Stage 4 - Technical Functional Documentation

## Purpose

Stage 4 generates exploratory automatic tennis-ball candidates using local OpenCV heuristics. It records whether this simple approach is viable and where it fails.

## Main Files

- Script: `scripts/run_stage_4_ball_tracking_probe.py`
- Module: `src/tennis_vision/ball_tracking_probe.py`

## Functional Flow

1. The script selects the local sample video.
2. It checks the Stage 3 report to see whether homography is available.
3. `run_ball_tracking_probe` samples a small number of frames.
4. Frames are resized.
5. `detect_ball_candidates` applies HSV thresholding and contour/circularity filtering.
6. Candidate overlays and CSV rows are saved.
7. A rough trajectory preview is saved if candidates span enough frames.
8. Optional YOLO reference can run when explicitly enabled.
9. Reports and lab notebook pages are updated.

## Important Functions

| Function | File | Purpose | Inputs | Outputs | Notes |
|---|---|---|---|---|---|
| `run_ball_tracking_probe` | `src/tennis_vision/ball_tracking_probe.py` | Main Stage 4 module flow | video, output folder, sampling options | result dict | Search: `def run_ball_tracking_probe` |
| `detect_ball_candidates` | `src/tennis_vision/ball_tracking_probe.py` | Find ball-like blobs | resized frame, frame index | candidate list | HSV yellow/green threshold |
| `draw_candidates` | `src/tennis_vision/ball_tracking_probe.py` | Render candidate overlay | frame, candidates | overlay image | Search: `def draw_candidates` |
| `write_candidates_csv` | `src/tennis_vision/ball_tracking_probe.py` | Save candidate data | CSV path, candidates | CSV file | Used by Stage 4.1 |
| `save_trajectory_preview` | `src/tennis_vision/ball_tracking_probe.py` | Draw rough candidate path | base frame, candidates | image path or none | Exploratory only |
| `run_yolo_reference` | `src/tennis_vision/ball_tracking_probe.py` | Optional YOLO comparison | sampled frames, confidence | YOLO summary | Off by default |
| `stage_3_spatial_status` | `scripts/run_stage_4_ball_tracking_probe.py` | Check court calibration status | Stage 3 report | spatial status dict | Search: `def stage_3_spatial_status` |
| `main` | `scripts/run_stage_4_ball_tracking_probe.py` | Stage 4 entrypoint | CLI args | candidates, reports | Search: `def main` |

## Inputs And Outputs

Reads:

- `samples/video_01.mov`
- `outputs/reports/stage_3_court_calibration_probe_report.json`

Writes:

- `outputs/ball_tracking/stage_4_ball_probe/ball_candidates_overlay/*.jpg`
- `outputs/ball_tracking/stage_4_ball_probe/ball_candidates.csv`
- `outputs/ball_tracking/stage_4_ball_probe/trajectory_preview.jpg` when possible
- `outputs/reports/stage_4_ball_tracking_probe_report.*`
- `docs/lab-notebook/stage_4_ball_tracking_probe.md`

## Dependencies

- OpenCV
- NumPy
- ultralytics only when optional YOLO reference is enabled
- rich if available

## Product-Owner Interpretation

Stage 4 answers: "Can a simple local heuristic find useful tennis-ball candidates?" Current evidence says it finds many candidates but is noisy.

## Known Limitations

- It does not know the real ball without labels.
- It can detect scoreboard, audience, signage, lights, or court artifacts.
- It is not production tracking.

## Where To Inspect Code

- `src/tennis_vision/ball_tracking_probe.py`, search `def detect_ball_candidates`.
- `scripts/run_stage_4_ball_tracking_probe.py`, search `def main`.
