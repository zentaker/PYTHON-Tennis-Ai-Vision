# Stage 2 - YOLO CPU Baseline

## Summary

| Field | Value |
|---|---|
| Stage | Stage 2 - YOLO CPU baseline |
| Verdict | ready_for_stage_3 |
| Friction score | 0 |
| Friction level | low friction |
| Timestamp | 2026-05-12T17:19:53+00:00 |
| Recommended next step | Proceed to Stage 3: Court Calibration Probe. |

## Input

| Field | Value |
|---|---|
| Video path | C:\Users\MSI\Desktop\TennisAiVision\tennis-ai-vision\samples\video_01.mov |
| Model | yolo11n.pt |
| Device | cpu |
| Frame interval | 60 |
| Max frames | 10 |
| Resize width | 1280 |
| Confidence threshold | 0.25 |

## Output

| Field | Value |
|---|---|
| JSON report path | C:\Users\MSI\Desktop\TennisAiVision\tennis-ai-vision\outputs\reports\stage_2_yolo_cpu_baseline_report.json |
| Markdown report path | C:\Users\MSI\Desktop\TennisAiVision\tennis-ai-vision\outputs\reports\stage_2_yolo_cpu_baseline_report.md |
| Log | C:\Users\MSI\Desktop\TennisAiVision\tennis-ai-vision\outputs\logs\stage_2_yolo_cpu_baseline_20260512T171953Z.log |
| Annotated frames folder | C:\Users\MSI\Desktop\TennisAiVision\tennis-ai-vision\outputs\annotated\stage_2_yolo_cpu\20260512T171940Z |
| Annotated frames saved | 10 |

## Console-equivalent table

| Field | Value |
|---|---|
| Stage name | Stage 2 YOLO CPU baseline |
| Input video | C:\Users\MSI\Desktop\TennisAiVision\tennis-ai-vision\samples\video_01.mov |
| Model | yolo11n.pt |
| Device | cpu |
| Verdict | ready_for_stage_3 |
| Friction | 0 (low friction) |
| Frames processed | 10 |
| Annotated frames saved | 10 |
| Runtime | 13.312 seconds |
| Average inference | 0.056 seconds/frame |
| Top classes | person: 82, sports ball: 6, chair: 4 |
| Recommended next step | Proceed to Stage 3: Court Calibration Probe. |

## Warnings

No warnings.

## Errors

No errors.

## Interpretation

YOLO CPU execution is validated as a first local baseline. This stage confirms local model loading, CPU inference, annotated frame output, and report generation. It does not validate tennis ball tracking quality.

## Next step

Proceed to Stage 3: Court Calibration Probe.

## Run history

<!-- lab-entry:2026-05-12T17:12:41+00:00 -->

### 2026-05-12T17:12:41+00:00

| Field | Value |
|---|---|
| Stage | Stage 2 - YOLO CPU Baseline |
| Verdict | ready_for_stage_3 |
| Friction score | 0 |
| Friction level | low friction |
| Next step | Proceed to Stage 3: Court Calibration Probe. |

<!-- lab-entry:2026-05-12T17:19:53+00:00 -->

### 2026-05-12T17:19:53+00:00

| Field | Value |
|---|---|
| Stage | Stage 2 - YOLO CPU Baseline |
| Verdict | ready_for_stage_3 |
| Friction score | 0 |
| Friction level | low friction |
| Next step | Proceed to Stage 3: Court Calibration Probe. |
