# Stage 3.1 - Technical Functional Documentation

## Purpose

Stage 3.1 helps the user produce valid manual court corner coordinates without a frontend. It generates a coordinate grid and can open an OpenCV click selector.

## Main Files

- Script: `scripts/run_stage_3_1_court_point_selector.py`
- Module: `src/tennis_vision/court_point_selector.py`

## Functional Flow

1. The script reads the Stage 3 reference image.
2. It always attempts to generate `calibration_reference_grid.jpg`.
3. If interactive mode is enabled, OpenCV opens the reference frame.
4. The user clicks corners in order: near left, near right, far left, far right.
5. Selected points are validated using the same geometry rules as Stage 3.
6. Valid points update `configs/court_calibration_sample.json`.
7. Reports and lab notebook pages are updated.

## Important Functions

| Function | File | Purpose | Inputs | Outputs | Notes |
|---|---|---|---|---|---|
| `generate_coordinate_grid` | `src/tennis_vision/court_point_selector.py` | Draw coordinate grid | reference image, grid step | grid image/result | Search: `def generate_coordinate_grid` |
| `select_court_points_interactively` | `src/tennis_vision/court_point_selector.py` | OpenCV click workflow | image path | selected points | Keys: `u`, `s`, `q` |
| `validate_selected_points` | `src/tennis_vision/court_point_selector.py` | Validate selected corners | points | validation dict | Calls court geometry validator |
| `update_calibration_config` | `src/tennis_vision/court_point_selector.py` | Save selected points | config path, points | updated config | No silent auto-swapping |
| `main` | `scripts/run_stage_3_1_court_point_selector.py` | Stage 3.1 entrypoint | CLI args | grid, optional config update, reports | Search: `def main` |

## Inputs And Outputs

Reads:

- `outputs/calibration/stage_3_court_probe/calibration_reference_frame.jpg`
- `configs/court_calibration_sample.json`

Writes:

- `outputs/calibration/stage_3_court_probe/calibration_reference_grid.jpg`
- updated `configs/court_calibration_sample.json` when valid points are saved
- `outputs/reports/stage_3_1_court_point_selector_report.*`
- `docs/lab-notebook/stage_3_1_court_point_selector.md`

## Dependencies

- OpenCV
- pathlib
- rich if available

## Product-Owner Interpretation

Stage 3.1 answers: "How do I get court corner pixel coordinates without guessing from an image?"

## Known Limitations

- It requires a local display for interactive clicking.
- Grid-only mode helps estimate coordinates but does not create a homography.

## Where To Inspect Code

- `src/tennis_vision/court_point_selector.py`, search `def select_court_points_interactively`.
- `scripts/run_stage_3_1_court_point_selector.py`, search `def main`.
