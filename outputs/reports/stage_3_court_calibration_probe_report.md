# Stage 3 Court Calibration Probe Report

## Verdict

- Final verdict: ready_for_stage_4
- Friction score: 0
- Friction level: low friction

## Input

- Config path: `C:\Users\MSI\Desktop\TennisAiVision\configs\court_calibration_sample.json`
- Video path: `C:\Users\MSI\Desktop\TennisAiVision\samples\video_01.mov`
- Frame index: 120
- Calibration basis: doubles court outer boundary
- Calibration points status: homography_ready

## Output

- Reference frame: `C:\Users\MSI\Desktop\TennisAiVision\outputs\calibration\stage_3_court_probe\calibration_reference_frame.jpg`
- Points overlay: `C:\Users\MSI\Desktop\TennisAiVision\outputs\calibration\stage_3_court_probe\court_points_overlay.jpg`
- Mini-court preview: `C:\Users\MSI\Desktop\TennisAiVision\outputs\calibration\stage_3_court_probe\mini_court_preview.jpg`
- JSON report: `C:\Users\MSI\Desktop\TennisAiVision\outputs\reports\stage_3_court_calibration_probe_report.json`
- Markdown report: `C:\Users\MSI\Desktop\TennisAiVision\outputs\reports\stage_3_court_calibration_probe_report.md`
- Log path: `C:\Users\MSI\Desktop\TennisAiVision\outputs\logs\stage_3_court_calibration_probe_20260512T234914Z.log`

## Court points

| Point | X | Y | Status |
|---|---:|---:|---|
| near_left_corner | 1008.0 | 1719.0 | usable |
| near_right_corner | 3312.0 | 1770.0 | usable |
| far_right_corner | 2781.0 | 549.0 | usable |
| far_left_corner | 1566.0 | 528.0 | usable |

## Point order validation

- near_left_corner.x < near_right_corner.x: True
- far_left_corner.x < far_right_corner.x: True
- Point order valid: True
- Polygon self-intersects: False
- Geometry valid: True

## Homography

Homography was computed from four usable manual court corner points.

## Warnings

No warnings.

## Errors

No errors.

## Interpretation

Valid court points and homography are available, so the project can move to Stage 4.

## Next step

Proceed to Stage 4: Ball Tracking Probe.
