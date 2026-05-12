# Stage 2 YOLO CPU Baseline Report

## Verdict

- Final verdict: ready_for_stage_3
- Friction score: 0
- Friction level: low friction

## Input

- Video path: `C:\Users\MSI\Desktop\TennisAiVision\tennis-ai-vision\samples\video_01.mov`
- Model: yolo11n.pt
- Device: cpu
- Frame interval: 60
- Max frames: 10
- Resize width: 1280
- Confidence threshold: 0.25

## Output

- Annotated output folder: `C:\Users\MSI\Desktop\TennisAiVision\tennis-ai-vision\outputs\annotated\stage_2_yolo_cpu\20260512T171940Z`
- Frames processed: 10
- Annotated frames saved: 10
- JSON report path: `C:\Users\MSI\Desktop\TennisAiVision\tennis-ai-vision\outputs\reports\stage_2_yolo_cpu_baseline_report.json`
- Markdown report path: `C:\Users\MSI\Desktop\TennisAiVision\tennis-ai-vision\outputs\reports\stage_2_yolo_cpu_baseline_report.md`
- Log path: `C:\Users\MSI\Desktop\TennisAiVision\tennis-ai-vision\outputs\logs\stage_2_yolo_cpu_baseline_20260512T171953Z.log`

## Detection summary

| Class | Count |
|---|---|
| chair | 4 |
| person | 82 |
| sports ball | 6 |

## Runtime

- Total runtime: 13.312 seconds
- Average time per frame: 0.056 seconds

## Warnings

No warnings.

## Errors

No errors.

## Interpretation

YOLO CPU is viable as a first local baseline because the model loaded, sampled frames were processed, and annotated frames were saved. This stage does not solve tennis ball tracking; it only validates local detection execution and measures CPU friction.

## Next step

Proceed to Stage 3: Court Calibration Probe.
