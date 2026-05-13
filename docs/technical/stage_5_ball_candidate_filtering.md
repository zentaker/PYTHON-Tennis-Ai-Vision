# Stage 5 - Technical Functional Documentation

## Purpose

Stage 5 compares noisy automatic ball candidates from Stage 4 against manual ball labels from Stage 4.1, filters candidates into a cleaner baseline trajectory, and projects selected candidates into the calibrated court plane when Stage 3 homography is available.

This is a validation and measurement stage. It does not claim production ball tracking.

## Main files

| Type | Path |
|---|---|
| Script | `scripts/run_stage_5_ball_candidate_filtering.py` |
| Filtering module | `src/tennis_vision/ball_candidate_filtering.py` |
| Projection module | `src/tennis_vision/court_projection.py` |
| Friction scoring | `src/tennis_vision/friction.py` |
| Lab notebook builder | `src/tennis_vision/lab_notebook.py` |

## Functional flow

1. The stage script reads Stage 4 automatic candidates from `outputs/ball_tracking/stage_4_ball_probe/ball_candidates.csv`.
2. It reads visible manual ball labels from `outputs/ball_tracking/stage_4_1_manual_labels/manual_ball_labels.csv`.
3. It reads Stage 3 calibration and homography status from `outputs/reports/stage_3_court_calibration_probe_report.json`.
4. For each manual label, it ranks automatic candidates in the same frame by pixel distance.
5. It writes candidate-to-label distances and threshold flags for 10, 25, 50, 100, and 200 pixels.
6. It selects a first-pass filtered candidate trajectory using manual-label distance, court geometry, heuristic score, and temporal consistency.
7. If homography is valid, it projects selected image-space points into normalized court coordinates.
8. It saves CSV outputs, preview images, JSON and Markdown reports, and updates the lab notebook automatically.

## Important functions

| Function | File | Purpose | Inputs | Outputs | Notes |
|---|---|---|---|---|---|
| `read_ball_candidates` | `src/tennis_vision/ball_candidate_filtering.py` | Load Stage 4 automatic candidate CSV | Candidate CSV path | Candidate rows and errors | Search: `def read_ball_candidates` |
| `read_manual_labels` | `src/tennis_vision/ball_candidate_filtering.py` | Load visible Stage 4.1 manual labels | Manual labels CSV path | Label rows and errors | Search: `def read_manual_labels` |
| `compare_candidates_to_labels` | `src/tennis_vision/ball_candidate_filtering.py` | Rank candidates against labels by distance | Candidates and labels | Distance rows and summary metrics | Search: `def compare_candidates_to_labels` |
| `filter_candidates` | `src/tennis_vision/ball_candidate_filtering.py` | Select baseline filtered candidates | Candidates, labels, court polygon | Filtered rows and rejection summary | Baseline logic only, not learned tracking |
| `interpolate_expected_point` | `src/tennis_vision/ball_candidate_filtering.py` | Estimate expected position between labeled anchors | Frame index, selected anchors | Expected x/y or none | Used for unlabeled frames |
| `add_projection_to_rows` | `src/tennis_vision/ball_candidate_filtering.py` | Merge projected court coordinates into selected rows | Filtered rows, homography matrix | Updated rows and projected count | Calls `project_image_points` |
| `load_stage_3_calibration` | `src/tennis_vision/court_projection.py` | Load homography and court polygon from Stage 3 report | Stage 3 report path | Calibration status dict | Search: `def load_stage_3_calibration` |
| `project_image_points` | `src/tennis_vision/court_projection.py` | Project image points into normalized court plane | Image points, homography matrix | Projected point rows | Uses OpenCV perspective transform |
| `point_inside_or_near_polygon` | `src/tennis_vision/court_projection.py` | Check whether candidate is inside or near calibrated court polygon | Point, polygon, margin | Geometry status | Helps reject obvious non-play-area candidates |
| `save_court_projection_preview` | `src/tennis_vision/court_projection.py` | Draw selected projected candidates on a mini-court | Projected rows, output path, target size | Preview image path or none | Search: `def save_court_projection_preview` |
| `main` | `scripts/run_stage_5_ball_candidate_filtering.py` | Run Stage 5 end to end | CLI args | Reports, CSVs, previews, notebook update | Search: `def main` |

## Inputs and outputs

Reads:

- `outputs/ball_tracking/stage_4_ball_probe/ball_candidates.csv`
- `outputs/ball_tracking/stage_4_1_manual_labels/manual_ball_labels.csv`
- `outputs/reports/stage_3_court_calibration_probe_report.json`

Writes:

- `outputs/ball_tracking/stage_5_filtered_candidates/candidate_label_distances.csv`
- `outputs/ball_tracking/stage_5_filtered_candidates/filtered_ball_candidates.csv`
- `outputs/ball_tracking/stage_5_filtered_candidates/projected_ball_candidates.csv`
- `outputs/ball_tracking/stage_5_filtered_candidates/filtered_trajectory_preview.jpg`
- `outputs/ball_tracking/stage_5_filtered_candidates/court_projection_preview.jpg`
- `outputs/ball_tracking/stage_5_filtered_candidates/overlays/`
- `outputs/reports/stage_5_ball_candidate_filtering_report.json`
- `outputs/reports/stage_5_ball_candidate_filtering_report.md`
- `docs/lab-notebook/stage_5_ball_candidate_filtering.md`

## Dependencies

- OpenCV (`cv2`) for geometry, projection, and preview image writing.
- NumPy for matrix and image array handling.
- Python standard library modules: `argparse`, `csv`, `math`, `pathlib`, `statistics`, and `collections`.
- `rich` is used only if available for readable console output.

## Product-owner interpretation

Stage 5 answers three practical questions:

- Are Stage 4 automatic candidates close to the manually labeled real ball?
- Can a simple filter reduce false positives enough to produce a plausible trajectory?
- Does the calibrated court homography project selected ball candidates into the court plane?

If candidates are near the manual labels and projection works, the project can move toward Stage 6 smoothing and event/rally segmentation. If candidates are consistently far away, the next sensible path is Stage 5.1: improve candidate generation or research a specialized tennis ball detector.

## Known limitations

- The filter is hand-built and uses a small ground-truth set.
- Projection uses image-space ball centers; it does not estimate ball height above the court.
- Manual labels cover only a few frames, so unlabeled-frame filtering is approximate.
- A successful projection does not mean production-ready tracking.
- If Stage 4 candidates miss the actual ball, Stage 5 cannot recover the true trajectory by filtering alone.

## Where to inspect code

- Stage entrypoint: `scripts/run_stage_5_ball_candidate_filtering.py`, search `def main`.
- Candidate comparison: `src/tennis_vision/ball_candidate_filtering.py`, search `def compare_candidates_to_labels`.
- Filtering logic: `src/tennis_vision/ball_candidate_filtering.py`, search `def filter_candidates`.
- Court projection: `src/tennis_vision/court_projection.py`, search `def project_image_points`.
- Mini-court preview: `src/tennis_vision/court_projection.py`, search `def save_court_projection_preview`.
