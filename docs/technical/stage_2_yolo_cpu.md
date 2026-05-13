# Stage 2 - Technical Functional Documentation

## Purpose

Stage 2 validates that a small YOLO model can run locally on CPU against sampled video frames and save annotated outputs.

## Main Files

- Script: `scripts/run_stage_2_yolo_cpu_baseline.py`
- Modules: `src/tennis_vision/yolo_cpu.py`, `src/tennis_vision/video_io.py`, `src/tennis_vision/friction.py`

## Functional Flow

1. The script selects a local sample video.
2. `load_yolo_model` loads `yolo11n.pt` by default or falls back according to the module logic.
3. `run_yolo_cpu_baseline` samples a limited number of frames.
4. Frames are resized for CPU practicality.
5. YOLO inference runs on `device="cpu"`.
6. Annotated frames, detection counts, runtime stats, reports, and lab notebook entries are written.

## Important Functions

| Function | File | Purpose | Inputs | Outputs | Notes |
|---|---|---|---|---|---|
| `load_yolo_model` | `src/tennis_vision/yolo_cpu.py` | Load small YOLO model | model name | model status | Search: `def load_yolo_model` |
| `resize_frame` | `src/tennis_vision/yolo_cpu.py` | Reduce frame width | frame, width | resized frame | CPU cost control |
| `_collect_detections` | `src/tennis_vision/yolo_cpu.py` | Convert YOLO results to counts | YOLO result, class names | counts, confidences | Search: `def _collect_detections` |
| `run_yolo_cpu_baseline` | `src/tennis_vision/yolo_cpu.py` | Run inference and save annotations | video, model, sampling options | result dict | Search: `def run_yolo_cpu_baseline` |
| `calculate_stage_2_friction_score` | `src/tennis_vision/friction.py` | Score model/runtime friction | Stage 2 flags | friction dict | Documents installation/runtime issues |
| `main` | `scripts/run_stage_2_yolo_cpu_baseline.py` | Stage 2 entrypoint | CLI args | annotated frames, reports | Search: `def main` |

## Inputs And Outputs

Reads:

- Local sample video.
- Small YOLO model file or model resolved by ultralytics.

Writes:

- `outputs/annotated/stage_2_yolo_cpu/*.jpg`
- `outputs/reports/stage_2_yolo_cpu_baseline_report.json`
- `outputs/reports/stage_2_yolo_cpu_baseline_report.md`
- `docs/lab-notebook/stage_2_yolo_cpu_baseline.md`

## Dependencies

- OpenCV
- ultralytics
- NumPy indirectly through model stack
- rich if available

## Product-Owner Interpretation

Stage 2 answers: "Can this machine run a local YOLO baseline on CPU?" It does not solve tennis-specific ball tracking.

## Known Limitations

- CPU inference may be slow.
- General YOLO classes are not expected to reliably detect a tennis ball in match footage.
- It should not process the full 4K video by default.

## Where To Inspect Code

- `src/tennis_vision/yolo_cpu.py`, search `def run_yolo_cpu_baseline`.
- `scripts/run_stage_2_yolo_cpu_baseline.py`, search `def main`.
