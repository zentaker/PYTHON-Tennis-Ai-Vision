# Stage 3 - Technical Functional Documentation

## Purpose

Stage 3 creates the manual court calibration baseline. It loads one video frame, reads court corner points from JSON, validates the point geometry, draws an overlay, and computes a homography when the four doubles-court corners are valid.

## Main Files

- Script: `scripts/run_stage_3_court_calibration_probe.py`
- Module: `src/tennis_vision/court_calibration.py`
- Config: `configs/court_calibration_sample.json`

## Functional Flow

1. The script reads the calibration config and optional CLI overrides.
2. `load_frame_at_index` loads the requested video frame.
3. `validate_points` checks missing, placeholder, out-of-bounds, inverted, or crossed points.
4. `draw_points_overlay` writes the point/polygon overlay.
5. `compute_homography` only runs when point geometry is valid.
6. `generate_mini_court_preview` warps the frame into a normalized preview when homography exists.
7. Reports and lab notebook pages are updated.

## Important Functions

| Function | File | Purpose | Inputs | Outputs | Notes |
|---|---|---|---|---|---|
| `read_calibration_config` | `src/tennis_vision/court_calibration.py` | Load JSON config | config path | config/errors | Search: `def read_calibration_config` |
| `load_frame_at_index` | `src/tennis_vision/court_calibration.py` | Load calibration frame | video path, frame index | frame or error | Search: `def load_frame_at_index` |
| `validate_points` | `src/tennis_vision/court_calibration.py` | Validate point values and geometry | points, frame shape | status dict | Search: `def validate_points` |
| `validate_corner_geometry` | `src/tennis_vision/court_calibration.py` | Validate order and polygon | usable points | geometry dict | Rejects suspicious ordering |
| `quadrilateral_self_intersects` | `src/tennis_vision/court_calibration.py` | Detect crossed polygon | four ordered corners | bool | Prevents X-shaped court |
| `compute_homography` | `src/tennis_vision/court_calibration.py` | Compute image-to-mini-court transform | validation dict | homography dict | Uses OpenCV |
| `run_court_calibration_probe` | `src/tennis_vision/court_calibration.py` | Orchestrate Stage 3 | config/output/project root | result dict | Search: `def run_court_calibration_probe` |
| `main` | `scripts/run_stage_3_court_calibration_probe.py` | Stage 3 entrypoint | CLI args | calibration artifacts, reports | Search: `def main` |

## Inputs And Outputs

Reads:

- `configs/court_calibration_sample.json`
- `samples/video_01.mov`

Writes:

- `outputs/calibration/stage_3_court_probe/calibration_reference_frame.jpg`
- `outputs/calibration/stage_3_court_probe/court_points_overlay.jpg`
- `outputs/calibration/stage_3_court_probe/mini_court_preview.jpg` when valid
- `outputs/reports/stage_3_court_calibration_probe_report.*`
- `docs/lab-notebook/stage_3_court_calibration_probe.md`

## Dependencies

- OpenCV
- NumPy
- pathlib
- rich if available

## Product-Owner Interpretation

Stage 3 answers: "Can the project define a court coordinate transform from manually selected doubles-court corners?"

## Known Limitations

- It is manual calibration, not automatic court detection.
- It uses the doubles court outer boundary. Singles and service-box geometry are later layers.
- It refuses crossed or inverted polygons instead of auto-fixing them.

## Where To Inspect Code

- `src/tennis_vision/court_calibration.py`, search `def run_court_calibration_probe`.
- `src/tennis_vision/court_calibration.py`, search `def validate_corner_geometry`.
