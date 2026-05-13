# Tennis AI Vision

Tennis AI Vision is a local-first Python research project for building toward SwingVision-style tennis video analysis. The first milestone is not model accuracy or a product UI. It is proving that the local machine can support future experiments for video loading, frame extraction, CPU detection baselines, calibration probes, tracking probes, and local report generation.

## Current Stage

Stage 4.1: manual ball labeling helper.

Stage 0 checks the local Python environment, required folders, required package imports, and whether `ffmpeg` is available from the terminal. Stage 1 loads a local sample video with OpenCV, reads metadata, extracts frames, and writes reports. Stage 2 runs a small local YOLO CPU baseline on sampled frames and saves annotated output. Stage 3 creates a manual court calibration reference frame and point overlay. Stage 3.1 helps read or select the court point pixel coordinates needed to rerun Stage 3 with homography. Stage 4 probes simple local ball candidate detection. Stage 4.1 creates manual ball labels for ground truth.

## Local Setup

From the repository root:

```powershell
cd C:\Users\MSI\Desktop\TennisAiVision
```

Create a virtual environment:

```powershell
python -m venv .venv
```

If Windows says `python` is not recognized, install Python 3.10 or newer from python.org, enable the option to add Python to PATH, then open a new terminal. If the Windows launcher is available, `py -m venv .venv` is also fine.

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install requirements:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run The Doctor Script

Run the Stage 0 environment check from the repository root:

```powershell
python scripts\doctor.py
```

The script prints a readable console summary and writes reports to:

```text
outputs/reports/environment_report.json
outputs/reports/environment_report.md
```

It also writes a timestamped log under:

```text
outputs/logs/
```

## Expected Outputs

After `scripts/doctor.py` runs, expect:

- Environment status in JSON.
- Environment status in Markdown.
- A timestamped log file.
- A friction score from 0 to 100.
- A final verdict:
  - `ready_for_stage_1`
  - `ready_with_warnings`
  - `blocked`

## Stage 1 - Video Loading And Frame Extraction

Place a short local tennis video here:

```text
samples/video_01.mov
```

The default sample can also be `samples/video_01.mp4`. Windows Explorer may display the MOV as `video_01` while the actual file extension is `.mov`.

Run the Stage 1 probe from the repository root:

```powershell
python scripts\run_stage_1_video_probe.py
```

Run with an explicit MOV path:

```powershell
python scripts\run_stage_1_video_probe.py --video samples\video_01.mov
```

Run with a custom interval and maximum frame count:

```powershell
python scripts\run_stage_1_video_probe.py --interval 15 --max-frames 40
```

Use a different local video path:

```powershell
python scripts\run_stage_1_video_probe.py --video samples\another_sample.mp4
```

Expected outputs:

- Extracted JPG frames in a timestamped folder under `outputs/frames/`.
- JSON report at `outputs/reports/stage_1_video_probe_report.json`.
- Markdown report at `outputs/reports/stage_1_video_probe_report.md`.
- Timestamped log file under `outputs/logs/`.
- Console summary with verdict, friction score, metadata, frames saved, and next step.

## Stage 2 - YOLO CPU Baseline

Stage 2 validates that a small YOLO model can run locally on CPU against a limited sample of video frames. It is intentionally small: it does not process the full 4K video by default, and it does not solve tennis ball tracking.

Codex normally runs this after implementation or stage changes:

```powershell
python scripts\run_stage_2_yolo_cpu_baseline.py
```

The user may validate manually if needed:

```powershell
python scripts\run_stage_2_yolo_cpu_baseline.py --max-frames 5 --interval 120 --resize-width 960
```

Expected outputs:

- Annotated JPG frames under `outputs/annotated/stage_2_yolo_cpu/`.
- JSON report at `outputs/reports/stage_2_yolo_cpu_baseline_report.json`.
- Markdown report at `outputs/reports/stage_2_yolo_cpu_baseline_report.md`.
- Timestamped log file under `outputs/logs/`.
- Automatic lab notebook update under `docs/lab-notebook/`.

CPU inference may be slow on 4K video, so Stage 2 resizes sampled frames before inference by default. Ball tracking and court reasoning are later stages.

## Stage 3 - Court Calibration Probe

Stage 3 creates a low-friction manual court calibration workflow. It loads one representative video frame, saves a reference image, reads court corner points from a JSON config, draws an overlay, and computes a homography only after real court point coordinates are available.

Stage 3 uses the doubles court outer boundary as the calibration baseline. Tennis courts include singles lines and doubles lines; singles-line and service-box geometry will be derived later from court geometry or selected in a future calibration layer.

The sample config lives at:

```text
configs/court_calibration_sample.json
```

The reference frame and overlay are generated under:

```text
outputs/calibration/stage_3_court_probe/
```

Run the probe:

```powershell
python scripts\run_stage_3_court_calibration_probe.py
```

Run with a specific frame:

```powershell
python scripts\run_stage_3_court_calibration_probe.py --frame-index 180
```

If the config still contains placeholder points like `[0, 0]`, the next task is to fill pixel coordinates from `calibration_reference_frame.jpg` and rerun Stage 3.

Corner meanings:

- `near_left_corner` = bottom-left doubles court corner.
- `near_right_corner` = bottom-right doubles court corner.
- `far_left_corner` = top-left doubles court corner.
- `far_right_corner` = top-right doubles court corner.

## Stage 3.1 - Court Point Selection Helper

Stage 3.1 exists because Stage 3 needs real pixel coordinates for the court corners. It generates a coordinate grid over the calibration reference frame and can optionally open a local OpenCV click selector.

Generate only the coordinate grid:

```powershell
python scripts\run_stage_3_1_court_point_selector.py --no-interactive
```

Run the interactive selector:

```powershell
python scripts\run_stage_3_1_court_point_selector.py --interactive
```

In the interactive selector, click the four points in order:

```text
1. near_left_corner = bottom-left doubles court corner
2. near_right_corner = bottom-right doubles court corner
3. far_left_corner = top-left doubles court corner
4. far_right_corner = top-right doubles court corner
```

Use `u` to undo, `s` to save, and `q` to quit without saving. Saved points update:

```text
configs/court_calibration_sample.json
```

After points are saved, rerun Stage 3:

```powershell
python scripts\run_stage_3_court_calibration_probe.py
```

Expected outputs:

- Grid image at `outputs/calibration/stage_3_court_probe/calibration_reference_grid.jpg`.
- JSON report at `outputs/reports/stage_3_1_court_point_selector_report.json`.
- Markdown report at `outputs/reports/stage_3_1_court_point_selector_report.md`.
- Automatic lab notebook update under `docs/lab-notebook/`.

## Stage 4 - Ball Tracking Probe

Stage 4 is an exploratory local ball candidate detector. It does not solve production ball tracking. It samples a small number of frames, runs simple OpenCV HSV color and blob heuristics, saves candidate overlays, and documents false-positive or missed-detection friction.

YOLO is optional and off by default. The default run avoids full-video processing.

Run the probe:

```powershell
python scripts\run_stage_4_ball_tracking_probe.py
```

Optional lighter run:

```powershell
python scripts\run_stage_4_ball_tracking_probe.py --max-frames 10 --interval 30 --resize-width 960
```

Optional YOLO reference pass:

```powershell
python scripts\run_stage_4_ball_tracking_probe.py --use-yolo --max-frames 5
```

Expected outputs:

- Candidate overlays under `outputs/ball_tracking/stage_4_ball_probe/ball_candidates_overlay/`.
- Candidate CSV at `outputs/ball_tracking/stage_4_ball_probe/ball_candidates.csv`.
- Optional trajectory preview at `outputs/ball_tracking/stage_4_ball_probe/trajectory_preview.jpg`.
- JSON report at `outputs/reports/stage_4_ball_tracking_probe_report.json`.
- Markdown report at `outputs/reports/stage_4_ball_tracking_probe_report.md`.
- Automatic lab notebook update under `docs/lab-notebook/`.

## Stage 4.1 - Manual Ball Labeling Helper

Stage 4 generated too many false positives for this video. The simple heuristic often selected scoreboard, audience, signage, lights, or court artifacts instead of the real tennis ball.

Stage 4.1 lets the user manually click the real ball on selected frames. These labels become ground truth for Stage 5 filtering and court projection. This helper is still not production ball tracking.

Run with explicit frames:

```powershell
python scripts\run_stage_4_1_ball_labeling_helper.py --frames 120,150,180
```

Run with a generated frame list:

```powershell
python scripts\run_stage_4_1_ball_labeling_helper.py --start-frame 90 --interval 30 --max-frames 8
```

Controls:

- Left click: select the real tennis ball.
- `u`: undo current frame selection.
- `s`: save current frame label and continue.
- `n`: skip current frame.
- `q`: quit and save progress.

Expected outputs:

- Manual labels CSV at `outputs/ball_tracking/stage_4_1_manual_labels/manual_ball_labels.csv`.
- Manual labels JSON at `outputs/ball_tracking/stage_4_1_manual_labels/manual_ball_labels.json`.
- Label overlays under `outputs/ball_tracking/stage_4_1_manual_labels/label_overlays/`.
- Candidate comparison CSV at `outputs/ball_tracking/stage_4_1_manual_labels/candidate_label_comparison.csv` when Stage 4 candidates exist.
- JSON report at `outputs/reports/stage_4_1_ball_labeling_helper_report.json`.
- Markdown report at `outputs/reports/stage_4_1_ball_labeling_helper_report.md`.
- Automatic lab notebook update under `docs/lab-notebook/`.

## Lab Notebook

The lab notebook turns generated reports into persistent project documentation. It records each stage's inputs, outputs, verdict, friction score, warnings, errors, interpretation, and next step.

Notebook files are saved under:

```text
docs/lab-notebook/
```

Normal workflow:

1. Codex implements or modifies a stage.
2. Codex runs the relevant stage script.
3. The stage script generates reports.
4. The stage script updates `docs/lab-notebook/` automatically.
5. The user may optionally inspect the docs, but does not need to run documentation commands.

The manual update command is optional fallback/debug tooling only:

```powershell
python scripts\update_lab_notebook.py
```

Stage pages keep a run history so previous entries are preserved. Future stages should write JSON reports under `outputs/reports/`, update the notebook automatically at the end of their stage script, and add a notebook builder so the stage appears in the lab notebook and experiment index.

## Documentation Layers

This project now has two documentation layers:

- `docs/lab-notebook/` records execution results and friction history from stage runs.
- `docs/technical/` explains functional code behavior, important functions, scripts, data flow, file paths, and pipeline architecture.

Codex must maintain both layers when implementing or modifying stages.

## Cleaning Generated Outputs

To remove generated files while preserving the output folder structure:

```powershell
python scripts\clean_outputs.py
```

## Notes

`ffmpeg` is optional for the Stage 0 script to execute, but future video analysis stages will likely need it. If it is missing, install it locally and make sure the `ffmpeg` command is available in your terminal path.
