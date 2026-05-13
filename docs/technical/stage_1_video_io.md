# Stage 1 - Technical Functional Documentation

## Purpose

Stage 1 validates that the project can find a local sample video, open it with OpenCV, read metadata, and extract a limited set of frames.

## Main Files

- Script: `scripts/run_stage_1_video_probe.py`
- Modules: `src/tennis_vision/video_io.py`, `src/tennis_vision/frame_sampler.py`, `src/tennis_vision/friction.py`

## Functional Flow

1. The script selects a video from `--video` or auto-detects a supported file in `samples/`.
2. `read_video_metadata` opens the video and records FPS, resolution, duration, frame count, file size, and codec.
3. `extract_frames` samples frames at a configured interval and saves JPG files.
4. Stage 1 friction and verdict are computed.
5. JSON, Markdown, log, and lab notebook files are written.

## Important Functions

| Function | File | Purpose | Inputs | Outputs | Notes |
|---|---|---|---|---|---|
| `detect_default_video` | `scripts/run_stage_1_video_probe.py` | Find default video | `samples/` | selected path | Search: `def detect_default_video` |
| `open_video` | `src/tennis_vision/video_io.py` | Open OpenCV capture | video path | capture or error | Shared by later stages |
| `read_video_metadata` | `src/tennis_vision/video_io.py` | Read video metadata | video path | metadata dict | Search: `def read_video_metadata` |
| `extract_frames` | `src/tennis_vision/frame_sampler.py` | Save sampled JPG frames | video path, interval, max frames | extraction stats | Search: `def extract_frames` |
| `calculate_stage_1_friction_score` | `src/tennis_vision/friction.py` | Score video loading friction | Stage 1 flags | friction dict | Search hint matches function name |
| `main` | `scripts/run_stage_1_video_probe.py` | Stage 1 entrypoint | CLI args | frames, reports | Search: `def main` |

## Inputs And Outputs

Reads:

- `samples/video_01.mov`, `samples/video_01.mp4`, or another supported local video.

Writes:

- `outputs/frames/stage_1_*/frame_*.jpg`
- `outputs/reports/stage_1_video_probe_report.json`
- `outputs/reports/stage_1_video_probe_report.md`
- `docs/lab-notebook/stage_1_video_probe.md`

## Dependencies

- OpenCV
- pathlib
- rich if available for console output

## Product-Owner Interpretation

Stage 1 answers: "Can the local project read this tennis video and extract frames?"

## Known Limitations

- It does not detect players, courts, or balls.
- MOV decoding depends on local OpenCV build support.

## Where To Inspect Code

- `src/tennis_vision/video_io.py`, search `def read_video_metadata`.
- `src/tennis_vision/frame_sampler.py`, search `def extract_frames`.
- `scripts/run_stage_1_video_probe.py`, search `def main`.
