# Stage 0 - Technical Functional Documentation

## Purpose

Stage 0 verifies that the local Python environment and repository structure can support later video-analysis experiments.

## Main Files

- Script: `scripts/doctor.py`
- Modules: `src/tennis_vision/environment.py`, `src/tennis_vision/report.py`, `src/tennis_vision/friction.py`

## Functional Flow

1. `scripts/doctor.py` calls `run_environment_checks`.
2. Environment checks inspect Python, OS, current working directory, required folders, package imports, `ffmpeg`, `samples/`, and `outputs/reports/`.
3. The script computes Stage 0 friction.
4. It writes JSON, Markdown, and log outputs.
5. It updates `docs/lab-notebook/` automatically.
6. It prints a console summary.

## Important Functions

| Function | File | Purpose | Inputs | Outputs | Notes |
|---|---|---|---|---|---|
| `run_environment_checks` | `src/tennis_vision/environment.py` | Run all local checks | project root | checks dict | Search: `def run_environment_checks` |
| `check_required_packages` | `src/tennis_vision/environment.py` | Import required packages | none | package status | Search: `def check_required_packages` |
| `check_ffmpeg` | `src/tennis_vision/environment.py` | Probe shell `ffmpeg` | shell PATH | availability dict | Missing ffmpeg is warning |
| `calculate_friction_score` | `src/tennis_vision/friction.py` | Score Stage 0 readiness | missing packages/folders, errors | friction dict | Search: `def calculate_friction_score` |
| `write_json_report` | `src/tennis_vision/report.py` | Write report JSON | path, dict | JSON file | Shared helper |
| `main` | `scripts/doctor.py` | Stage 0 entrypoint | CLI execution | reports, log, console | Search: `def main` |

## Inputs And Outputs

Reads:

- Python runtime and imports.
- Repository folders.
- Shell command availability for `ffmpeg`.

Writes:

- `outputs/reports/environment_report.json`
- `outputs/reports/environment_report.md`
- `outputs/logs/doctor_*.log`
- `docs/lab-notebook/stage_0_environment.md`

## Dependencies

- Python standard library.
- OpenCV, NumPy, pandas, pydantic, rich are imported as checks.

## Product-Owner Interpretation

Stage 0 answers: "Can this local machine run the project foundation?" It does not process video.

## Known Limitations

- It only checks whether `ffmpeg` is available from the shell; it does not install or configure it.
- It does not validate GPU support.

## Where To Inspect Code

- `src/tennis_vision/environment.py`, search `def run_environment_checks`.
- `scripts/doctor.py`, search `def main`.
