# Stage 3.1 Court Point Selection Helper Report

## Verdict

- Final verdict: ready_to_rerun_stage_3
- Friction score: 0
- Friction level: low friction

## Input

- Image path: `C:\Users\MSI\Desktop\TennisAiVision\outputs\calibration\stage_3_court_probe\calibration_reference_frame.jpg`
- Config path: `C:\Users\MSI\Desktop\TennisAiVision\configs\court_calibration_sample.json`
- Calibration basis: doubles court outer boundary
- Grid step: 200
- Interactive attempted: yes

## Output

- Grid image: `C:\Users\MSI\Desktop\TennisAiVision\outputs\calibration\stage_3_court_probe\calibration_reference_grid.jpg`
- JSON report: `C:\Users\MSI\Desktop\TennisAiVision\outputs\reports\stage_3_1_court_point_selector_report.json`
- Markdown report: `C:\Users\MSI\Desktop\TennisAiVision\outputs\reports\stage_3_1_court_point_selector_report.md`
- Log path: `C:\Users\MSI\Desktop\TennisAiVision\outputs\logs\stage_3_1_court_point_selector_20260512T234241Z.log`
- Config updated: yes

## Selected points

| Point | X | Y | Status |
|---|---:|---:|---|
| near_left_corner | 1008 | 1719 | valid |
| near_right_corner | 3312 | 1770 | valid |
| far_left_corner | 1566 | 528 | valid |
| far_right_corner | 2781 | 549 | valid |

## Point order validation

- near_left_corner.x < near_right_corner.x: True
- far_left_corner.x < far_right_corner.x: True
- Point order valid: True
- Polygon self-intersects: False
- Geometry valid: True

## Warnings

No warnings.

## Errors

No errors.

## Recommended fixes

No fixes required.

## Interpretation

Four valid court points were saved to the calibration config. Stage 3 can now be rerun to compute homography.

## Next step

Rerun Stage 3 to compute the court homography from the saved point coordinates.
