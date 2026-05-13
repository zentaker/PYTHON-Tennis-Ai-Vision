# Pipeline Map

## Stage Table

| Stage | Purpose | Main script | Main modules | Reads | Writes | Status |
|---|---|---|---|---|---|---|
| Stage 0 | Validate local environment and repo foundation | `scripts/doctor.py` | `src/tennis_vision/environment.py`, `report.py`, `friction.py` | repo folders, Python imports, shell `ffmpeg` | `outputs/reports/environment_report.*`, logs, lab notebook | Implemented |
| Stage 1 | Load video, read metadata, extract sample frames | `scripts/run_stage_1_video_probe.py` | `video_io.py`, `frame_sampler.py`, `friction.py` | `samples/video_01.mov` or supported sample video | `outputs/frames/`, `outputs/reports/stage_1_video_probe_report.*` | Implemented |
| Stage 2 | Validate local YOLO CPU inference on sampled frames | `scripts/run_stage_2_yolo_cpu_baseline.py` | `yolo_cpu.py`, `video_io.py`, `friction.py` | sample video, local/downloaded YOLO small model | `outputs/annotated/stage_2_yolo_cpu/`, Stage 2 reports | Implemented |
| Stage 3 | Generate manual court calibration reference and homography | `scripts/run_stage_3_court_calibration_probe.py` | `court_calibration.py`, `friction.py` | `configs/court_calibration_sample.json`, sample video | `outputs/calibration/stage_3_court_probe/`, Stage 3 reports | Implemented |
| Stage 3.1 | Help user select court corner coordinates | `scripts/run_stage_3_1_court_point_selector.py` | `court_point_selector.py`, `court_calibration.py` | Stage 3 reference frame, calibration config | grid image, updated config, Stage 3.1 reports | Implemented |
| Stage 4 | Generate exploratory automatic ball candidates | `scripts/run_stage_4_ball_tracking_probe.py` | `ball_tracking_probe.py`, `friction.py` | sample video, Stage 3 report | `outputs/ball_tracking/stage_4_ball_probe/`, Stage 4 reports | Implemented |
| Stage 4.1 | Manually label true ball positions for ground truth | `scripts/run_stage_4_1_ball_labeling_helper.py` | `ball_labeling.py`, `ball_tracking_probe.py`, `friction.py` | sample video, Stage 4 candidate CSV if present | `outputs/ball_tracking/stage_4_1_manual_labels/`, Stage 4.1 reports | Implemented |
| Stage 5 | Filter candidates and project into court plane | `scripts/run_stage_5_ball_candidate_filtering.py` | `ball_candidate_filtering.py`, `court_projection.py` | Stage 4 candidates, Stage 4.1 labels, Stage 3 homography | `outputs/ball_tracking/stage_5_filtered_candidates/`, Stage 5 reports | Implemented |
| Stage 5.1 | Improve candidate generation and compare strategies against labels | `scripts/run_stage_5_1_candidate_improvement.py` | `ball_candidate_improvement.py`, `court_projection.py` | sample video, Stage 4.1 labels, Stage 3 homography, Stage 5 baseline | `outputs/ball_tracking/stage_5_1_candidate_improvement/`, Stage 5.1 reports | Implemented |
| Stage 5.2 | Research specialized ball model if handcrafted candidates remain weak | Not implemented | Planned | Stage 5.1 report and strategy comparison | Planned | Planned |
| Stage 6 | Smooth trajectory and probe event/rally segmentation hypotheses | `scripts/run_stage_6_trajectory_smoothing.py` | `trajectory_smoothing.py`, `event_segmentation.py` | Stage 5.1 improved/projected candidates, manual labels | `outputs/ball_tracking/stage_6_trajectory_smoothing/`, Stage 6 reports | Implemented |

## Flow

```text
Stage 0 Environment Doctor
  -> Stage 1 Video Probe
  -> Stage 2 YOLO CPU Baseline
  -> Stage 3 Court Calibration
  -> Stage 3.1 Court Point Selection
  -> Stage 3 Rerun Homography Check
  -> Stage 4 Ball Tracking Probe
  -> Stage 4.1 Manual Ball Labeling
  -> Stage 5 Candidate Filtering and Court Projection
  -> Stage 5.1 Candidate Generation Improvement
  -> Stage 6 Trajectory Smoothing and Event/Rally Segmentation
  -> Stage 7 Player Tracking and Ball-Player Interaction
```

## Architecture Notes

- The project is local-first and console-only.
- Stage scripts are the user-facing entrypoints.
- Modules under `src/tennis_vision/` hold reusable logic.
- Reports under `outputs/reports/` are lightweight evidence and may be committed.
- Heavy media outputs, videos, model weights, logs, and generated images remain local-only.
- The lab notebook is updated automatically by stage scripts.
- Technical docs must be updated whenever a stage adds or changes meaningful functionality.
