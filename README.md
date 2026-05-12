# Tennis AI Vision

Tennis AI Vision is a local-first Python research project for building toward SwingVision-style tennis video analysis. The first milestone is not model accuracy or a product UI. It is proving that the local machine can support future experiments for video loading, frame extraction, CPU detection baselines, calibration probes, tracking probes, and local report generation.

## Current Stage

Stage 2: YOLO CPU baseline.

Stage 0 checks the local Python environment, required folders, required package imports, and whether `ffmpeg` is available from the terminal. Stage 1 loads a local sample video with OpenCV, reads metadata, extracts frames, and writes reports. Stage 2 runs a small local YOLO CPU baseline on sampled frames and saves annotated output.

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

## Cleaning Generated Outputs

To remove generated files while preserving the output folder structure:

```powershell
python scripts\clean_outputs.py
```

## Notes

`ffmpeg` is optional for the Stage 0 script to execute, but future video analysis stages will likely need it. If it is missing, install it locally and make sure the `ffmpeg` command is available in your terminal path.
