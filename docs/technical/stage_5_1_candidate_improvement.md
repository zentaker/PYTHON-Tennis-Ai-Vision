# Stage 5.1 - Technical Functional Documentation

## Purpose

Stage 5.1 improves ball candidate generation after Stage 5 showed that automatic candidates were far from manual ball labels. It tests several low-cost local computer vision strategies against the Stage 4.1 manual labels and decides whether handcrafted candidates are good enough for Stage 6 smoothing.

This is not production ball tracking.

## Main files

| Type | Path |
|---|---|
| Script | `scripts/run_stage_5_1_candidate_improvement.py` |
| Candidate module | `src/tennis_vision/ball_candidate_improvement.py` |
| Projection helper | `src/tennis_vision/court_projection.py` |
| Friction scoring | `src/tennis_vision/friction.py` |
| Lab notebook builder | `src/tennis_vision/lab_notebook.py` |

## Functional flow

1. The script reads manual labels from `outputs/ball_tracking/stage_4_1_manual_labels/manual_ball_labels.csv`.
2. It loads only the manually labeled video frames from `samples/video_01.mov`.
3. It also loads nearby frames for each labeled frame so motion differences can be computed.
4. It loads Stage 3 calibration and homography from `outputs/reports/stage_3_court_calibration_probe_report.json`.
5. It runs three candidate strategies: HSV color threshold, motion difference, and hybrid scoring.
6. It evaluates each strategy against manual labels with nearest-candidate distances.
7. It writes a strategy comparison CSV and selects the best-performing strategy.
8. It saves improved candidates, overlays, a strategy preview, and projected candidates if homography is available.
9. It writes JSON and Markdown reports and updates the lab notebook automatically.

## Important functions

| Function | File | Purpose | Inputs | Outputs | Notes |
|---|---|---|---|---|---|
| `load_labeled_frame_bundle` | `src/tennis_vision/ball_candidate_improvement.py` | Load labeled frames and nearby motion frames | Video path, frame indices, resize width | Frame bundles and errors | Search: `def load_labeled_frame_bundle` |
| `generate_hsv_candidates` | `src/tennis_vision/ball_candidate_improvement.py` | Generate yellow/green ball-like blobs | Frame bundle, court polygon | Candidate rows | Uses HSV thresholding |
| `generate_motion_candidates` | `src/tennis_vision/ball_candidate_improvement.py` | Generate small moving-object candidates | Current, previous, next frames | Candidate rows | Helps reduce static false positives |
| `generate_hybrid_candidates` | `src/tennis_vision/ball_candidate_improvement.py` | Merge color and motion signals | Frame bundle, court polygon | Candidate rows | Scores color, motion, shape, court region |
| `evaluate_strategies` | `src/tennis_vision/ball_candidate_improvement.py` | Compare strategies against manual labels | Candidates by strategy, labels | Comparison rows and summaries | Thresholds: 10, 25, 50, 100, 200 px |
| `select_best_candidates` | `src/tennis_vision/ball_candidate_improvement.py` | Select nearest candidate per labeled frame for the best strategy | Candidate rows, labels | Improved candidate rows | Evaluation uses manual labels |
| `add_projection` | `src/tennis_vision/ball_candidate_improvement.py` | Project improved candidates with Stage 3 homography | Candidate rows, matrix | Candidate rows with projected coordinates | Uses `project_image_points` |
| `save_strategy_overlays` | `src/tennis_vision/ball_candidate_improvement.py` | Draw manual label, best candidate, and distance line | Frame bundles, labels, candidates | Overlay images | Search: `def save_strategy_overlays` |
| `main` | `scripts/run_stage_5_1_candidate_improvement.py` | Run the full Stage 5.1 workflow | CLI args | CSVs, previews, reports, notebook update | Search: `def main` |

## Inputs and outputs

Reads:

- `samples/video_01.mov`
- `outputs/ball_tracking/stage_4_1_manual_labels/manual_ball_labels.csv`
- `outputs/reports/stage_3_court_calibration_probe_report.json`
- `outputs/reports/stage_5_ball_candidate_filtering_report.json`

Writes:

- `outputs/ball_tracking/stage_5_1_candidate_improvement/strategy_comparison.csv`
- `outputs/ball_tracking/stage_5_1_candidate_improvement/improved_ball_candidates.csv`
- `outputs/ball_tracking/stage_5_1_candidate_improvement/projected_improved_candidates.csv`
- `outputs/ball_tracking/stage_5_1_candidate_improvement/overlays/`
- `outputs/ball_tracking/stage_5_1_candidate_improvement/strategy_preview.jpg`
- `outputs/ball_tracking/stage_5_1_candidate_improvement/court_projection_preview.jpg`
- `outputs/reports/stage_5_1_candidate_improvement_report.json`
- `outputs/reports/stage_5_1_candidate_improvement_report.md`
- `docs/lab-notebook/stage_5_1_candidate_improvement.md`

## Dependencies

- OpenCV for frame loading, HSV thresholding, motion difference, contours, drawing, and image writing.
- NumPy for masks, arrays, and preview composition.
- Python standard library modules: `argparse`, `csv`, `json`, `math`, `pathlib`, `statistics`, and `collections`.
- `rich` is used only if available for readable console output.

## Product-owner interpretation

Stage 5.1 tells the Product Owner whether local handcrafted computer vision is promising enough to feed a trajectory smoother. Manual labels are treated as ground truth. The key metrics are average nearest-candidate distance, median distance, and frames within 100 or 200 pixels.

If the best strategy gets close enough, Stage 6 can begin as a cautious smoothing probe. If not, the project should avoid smoothing noise and move to Stage 5.2 specialized ball model research.

## Known limitations

- Only a small set of manually labeled frames is evaluated.
- Handcrafted HSV and motion thresholds may be sensitive to lighting, camera angle, and video compression.
- Projection uses image-space centers and does not estimate ball height.
- The best candidate is selected by manual-label distance for evaluation; this is not yet autonomous tracking.
- A good Stage 5.1 result is evidence for a smoothing probe, not proof of production accuracy.

## Where to inspect code

- Stage entrypoint: `scripts/run_stage_5_1_candidate_improvement.py`, search `def main`.
- HSV strategy: `src/tennis_vision/ball_candidate_improvement.py`, search `def generate_hsv_candidates`.
- Motion strategy: `src/tennis_vision/ball_candidate_improvement.py`, search `def generate_motion_candidates`.
- Hybrid strategy: `src/tennis_vision/ball_candidate_improvement.py`, search `def generate_hybrid_candidates`.
- Strategy evaluation: `src/tennis_vision/ball_candidate_improvement.py`, search `def evaluate_strategies`.
