# Tennis AI Vision

Tennis AI Vision is a local-first Python research project for building toward SwingVision-style tennis video analysis. The first milestone is not model accuracy or a product UI. It is proving that the local machine can support future experiments for video loading, frame extraction, CPU detection baselines, calibration probes, tracking probes, and local report generation.

## Current Stage

Stage 9.1: court zone tuning and projection coverage.

Stage 0 checks the local Python environment, required folders, required package imports, and whether `ffmpeg` is available from the terminal. Stage 1 loads a local sample video with OpenCV, reads metadata, extracts frames, and writes reports. Stage 2 runs a small local YOLO CPU baseline on sampled frames and saves annotated output. Stage 3 creates a manual court calibration reference frame and point overlay. Stage 3.1 helps read or select court point coordinates. Stage 4 probes simple local ball candidate detection. Stage 4.1 creates manual ball labels for ground truth. Stage 5 filters candidates and projects selected points into the calibrated court plane. Stage 5.1 improves candidate generation. Stage 6 smooths the trajectory. Stage 7 and 7.1 add player interaction and identity filtering. Stage 8 and 8.1 build and validate a hypothesis-only event timeline. Stage 9 creates first tactical metrics, and Stage 9.1 improves projection coverage so fewer validated ball labels become unknown zones.

## Documentation Map

Use these files when reviewing the project without reading source code first:

- `docs/lab-notebook/`
  - Stage run results.
  - Verdicts, friction, warnings, errors, outputs, and run history.

- `docs/technical/`
  - How the code works.
  - Main scripts, modules, function inventory, data flow, and file paths.

- `docs/friction/`
  - What went wrong, why it mattered, and what rule came from it.
  - Useful when an issue repeats or a future agent needs context.

- `ROADMAP.md`
  - Where the project is going next.
  - Current stage, planned stages, and long-term research directions.

Terminal output may use Rich tables because it is read directly in PowerShell.
Documentation files should remain plain-text friendly because they are often
opened as raw TXT or Markdown source.

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

## Stage 5 - Ball Candidate Filtering and Court Projection

Stage 4 generated many false positives. Stage 4.1 produced manual ball labels. Stage 5 compares automatic candidates to those labels, applies a first-pass filter, and projects selected candidates onto the calibrated court plane when Stage 3 homography is available.

Run:

```powershell
python scripts\run_stage_5_ball_candidate_filtering.py
```

Expected outputs:

- Candidate-to-label distances at `outputs/ball_tracking/stage_5_filtered_candidates/candidate_label_distances.csv`.
- Filtered candidates at `outputs/ball_tracking/stage_5_filtered_candidates/filtered_ball_candidates.csv`.
- Projected candidates at `outputs/ball_tracking/stage_5_filtered_candidates/projected_ball_candidates.csv`.
- Preview images under `outputs/ball_tracking/stage_5_filtered_candidates/`.
- JSON report at `outputs/reports/stage_5_ball_candidate_filtering_report.json`.
- Markdown report at `outputs/reports/stage_5_ball_candidate_filtering_report.md`.
- Automatic lab notebook update under `docs/lab-notebook/`.

## Stage 5.1 - Ball Candidate Generation Improvement

Stage 5 showed that the nearest automatic candidates were still too far from the manual ball labels. Stage 5.1 tests improved local computer vision strategies before moving to trajectory smoothing.

This stage uses the manual labels as ground truth and compares:

- HSV tennis-ball color thresholding.
- Motion-difference candidates.
- Hybrid scoring with color, motion, shape, and court-region signals.

Run:

```powershell
python scripts\run_stage_5_1_candidate_improvement.py
```

Expected outputs:

- Strategy comparison CSV at `outputs/ball_tracking/stage_5_1_candidate_improvement/strategy_comparison.csv`.
- Improved candidates CSV at `outputs/ball_tracking/stage_5_1_candidate_improvement/improved_ball_candidates.csv`.
- Projected improved candidates at `outputs/ball_tracking/stage_5_1_candidate_improvement/projected_improved_candidates.csv`.
- Review overlays and strategy preview under `outputs/ball_tracking/stage_5_1_candidate_improvement/`.
- JSON report at `outputs/reports/stage_5_1_candidate_improvement_report.json`.
- Markdown report at `outputs/reports/stage_5_1_candidate_improvement_report.md`.
- Automatic lab notebook update under `docs/lab-notebook/`.

The decision is whether improved handcrafted candidates are close enough for Stage 6 smoothing or whether Stage 5.2 should research specialized ball models.

## Stage 6 - Trajectory Smoothing and Event Segmentation Probe

Stage 5.1 improved candidate quality enough to create a first local trajectory. Stage 6 builds that trajectory, applies lightweight moving-average smoothing, projects it into the calibrated court plane when possible, and creates simple event hypotheses.

Events are hypotheses only. Stage 6 does not implement scoring, official line calling, or production rally segmentation.

Run:

```powershell
python scripts\run_stage_6_trajectory_smoothing.py
```

Run with an explicit smoothing window:

```powershell
python scripts\run_stage_6_trajectory_smoothing.py --window-size 3
```

Expected outputs:

- Raw trajectory CSV at `outputs/ball_tracking/stage_6_trajectory_smoothing/raw_trajectory.csv`.
- Smoothed trajectory CSV at `outputs/ball_tracking/stage_6_trajectory_smoothing/smoothed_trajectory.csv`.
- Event hypotheses at `outputs/ball_tracking/stage_6_trajectory_smoothing/trajectory_events.csv`.
- Image and court trajectory previews under `outputs/ball_tracking/stage_6_trajectory_smoothing/`.
- JSON report at `outputs/reports/stage_6_trajectory_smoothing_report.json`.
- Markdown report at `outputs/reports/stage_6_trajectory_smoothing_report.md`.
- Automatic lab notebook update under `docs/lab-notebook/`.

If too few points exist, the next step is Stage 6.1 to expand manual labels. If candidate quality collapses, return to Stage 5.2 model research.

## Stage 7 - Player Tracking and Ball-Player Interaction Probe

Stage 6 generated trajectory and event hypotheses. Stage 7 adds local CPU player detection so player positions can help interpret possible ball-player interactions.

Player-ball interactions are hypotheses only. This stage does not confirm hits, scoring, line calls, or rally events.

Run:

```powershell
python scripts\run_stage_7_player_interaction_probe.py
```

Optional lighter run:

```powershell
python scripts\run_stage_7_player_interaction_probe.py --max-frames 10 --resize-width 960
```

Expected outputs:

- Player detections at `outputs/player_tracking/stage_7_player_interaction/player_detections.csv`.
- Approximate tracks at `outputs/player_tracking/stage_7_player_interaction/player_tracks.csv`.
- Ball-player distances at `outputs/player_tracking/stage_7_player_interaction/ball_player_distances.csv`.
- Interaction hypotheses at `outputs/player_tracking/stage_7_player_interaction/ball_player_interactions.csv`.
- Player and interaction overlays under `outputs/player_tracking/stage_7_player_interaction/`.
- JSON report at `outputs/reports/stage_7_player_interaction_probe_report.json`.
- Markdown report at `outputs/reports/stage_7_player_interaction_probe_report.md`.
- Automatic lab notebook update under `docs/lab-notebook/`.

## Stage 7.1 - Court-Aware Player Filtering and Identity Stabilization

Stage 7 detected too many people. Stage 7.1 filters irrelevant detections, keeps the likely main tennis players, and creates stable `player_a` / `player_b` identities.

Player identity is not permanently tied to near/far court side. Near/far is a side state that can change. Lightweight clothing/color appearance profiles help preserve identity when possible, but this is not robust biometric re-identification.

Run:

```powershell
python scripts\run_stage_7_1_player_filtering.py
```

Expected outputs:

- Filtered detections at `outputs/player_tracking/stage_7_1_player_filtering/filtered_player_detections.csv`.
- Filtered tracks at `outputs/player_tracking/stage_7_1_player_filtering/filtered_player_tracks.csv`.
- Main player summary at `outputs/player_tracking/stage_7_1_player_filtering/main_players.csv`.
- Identity profiles at `outputs/player_tracking/stage_7_1_player_filtering/player_identity_profiles.json`.
- Player side states at `outputs/player_tracking/stage_7_1_player_filtering/player_side_states.csv`.
- JSON report at `outputs/reports/stage_7_1_player_filtering_report.json`.
- Markdown report at `outputs/reports/stage_7_1_player_filtering_report.md`.

## Stage 8 - Shot/Event Timeline and Rally Segmentation Prototype

Stage 8 combines the smoothed ball trajectory, Stage 6 event hypotheses, Stage 7 ball-player interaction hypotheses, and Stage 7.1 stabilized player identities into a first structured event timeline.

Events remain hypotheses. This stage does not perform official scoring, line calling, confirmed hit detection, confirmed bounce detection, or shot classification.

Run:

```powershell
python scripts\run_stage_8_event_timeline.py
```

Optional merge-window run:

```powershell
python scripts\run_stage_8_event_timeline.py --merge-window 5
```

Expected outputs:

- Event timeline at `outputs/timeline/stage_8_event_timeline/event_timeline.csv`.
- Event timeline JSON at `outputs/timeline/stage_8_event_timeline/event_timeline.json`.
- Rally segments at `outputs/timeline/stage_8_event_timeline/rally_segments.csv`.
- Player event attribution at `outputs/timeline/stage_8_event_timeline/player_event_attribution.csv`.
- Timeline previews under `outputs/timeline/stage_8_event_timeline/`.
- JSON report at `outputs/reports/stage_8_event_timeline_report.json`.
- Markdown report at `outputs/reports/stage_8_event_timeline_report.md`.

## Stage 8.1 - Expanded Ball Labels and Timeline Validation

Stage 8 created a prototype timeline from sparse data. Stage 8.1 expands or reuses manual ball labels, validates candidate quality against those labels, and checks whether timeline events are supported by labeled ball positions.

Interactive mode collects more labels and persists the merged label set to:

```text
outputs/timeline/stage_8_1_timeline_validation/expanded_ball_labels.csv
```

Each interactive labeling session also writes timestamped backups under:

```text
outputs/timeline/stage_8_1_timeline_validation/label_sessions/
```

Non-interactive mode validates with the persisted expanded labels by default. If the durable expanded file is missing, it looks for the latest session backup before falling back to the original Stage 4.1 labels. Non-interactive validation should not overwrite a richer expanded label dataset with fallback labels.

Correct workflow:

1. Run interactive label expansion:

```powershell
python scripts\run_stage_8_1_expand_labels.py --interactive --start-frame 90 --interval 15 --max-frames 12
```

2. Run non-interactive validation against the persisted expanded labels:

```powershell
python scripts\run_stage_8_1_expand_labels.py --no-interactive
```

Expected outputs:

- Expanded labels at `outputs/timeline/stage_8_1_timeline_validation/expanded_ball_labels.csv`.
- Candidate validation at `outputs/timeline/stage_8_1_timeline_validation/expanded_candidate_validation.csv`.
- Timeline validation at `outputs/timeline/stage_8_1_timeline_validation/timeline_event_validation.csv`.
- Validated timeline at `outputs/timeline/stage_8_1_timeline_validation/validated_event_timeline.csv`.
- JSON report at `outputs/reports/stage_8_1_timeline_validation_report.json`.
- Markdown report at `outputs/reports/stage_8_1_timeline_validation_report.md`.

## Stage 9 - Tactical Metrics and Shot Zone Prototype

Stage 9 converts validated trajectory and timeline data into first tactical metrics. It assigns approximate court zones, classifies ball depth, estimates simple shot direction, adds player-side context, and writes a rally tactical summary.

These outputs are approximate. Stage 9 does not perform official scoring, official line calling, confirmed shot classification, or coaching-grade tactical analysis.

Run:

```powershell
python scripts\run_stage_9_tactical_metrics.py
```

Expected outputs:

- Ball zone assignments at `outputs/tactical/stage_9_tactical_metrics/ball_zone_assignments.csv`.
- Shot direction estimates at `outputs/tactical/stage_9_tactical_metrics/shot_direction_estimates.csv`.
- Rally tactical summary at `outputs/tactical/stage_9_tactical_metrics/rally_tactical_summary.csv`.
- Tactical summary at `outputs/tactical/stage_9_tactical_metrics/tactical_summary.md`.
- Court zone and placement previews under `outputs/tactical/stage_9_tactical_metrics/`.
- JSON report at `outputs/reports/stage_9_tactical_metrics_report.json`.
- Markdown report at `outputs/reports/stage_9_tactical_metrics_report.md`.

## Stage 9.1 - Court Zone Tuning and Projection Coverage

Stage 9 produced too many unknown zones because only part of the expanded ball-label set had projected court coordinates. Stage 9.1 projects the expanded labels through the Stage 3 homography, reruns tuned zone assignment, and compares Stage 9 with Stage 9.1.

This is still a prototype. It does not perform official line calling, official scoring, or coaching-grade tactical analysis.

Run:

```powershell
python scripts\run_stage_9_1_projection_coverage.py
```

Expected outputs:

- Projected expanded labels at `outputs/tactical/stage_9_1_projection_coverage/projected_expanded_labels.csv`.
- Tuned zone assignments at `outputs/tactical/stage_9_1_projection_coverage/tuned_ball_zone_assignments.csv`.
- Before/after comparison at `outputs/tactical/stage_9_1_projection_coverage/stage_9_vs_9_1_zone_comparison.csv`.
- Projection and placement previews under `outputs/tactical/stage_9_1_projection_coverage/`.
- JSON report at `outputs/reports/stage_9_1_projection_coverage_report.json`.
- Markdown report at `outputs/reports/stage_9_1_projection_coverage_report.md`.

## Stage 10 - Analytical Report Generator and Coaching Summary Prototype

Stage 10 converts validated tactical metrics into a human-readable analytical report and cautious coaching-style summary. It is deterministic and local.

Stage 10 does not use external LLMs. It does not provide official coaching, scoring, line calling, or confirmed shot classification.

Run:

```powershell
python scripts\run_stage_10_analytical_report.py
```

Expected outputs:

- Analytical report at `outputs/reports_final/stage_10_analytical_report/analytical_report.md`.
- JSON summary at `outputs/reports_final/stage_10_analytical_report/analytical_report.json`.
- Coaching summary at `outputs/reports_final/stage_10_analytical_report/coaching_summary.md`.
- Confidence summary at `outputs/reports_final/stage_10_analytical_report/confidence_summary.json`.
- Key findings at `outputs/reports_final/stage_10_analytical_report/key_findings.md`.
- Visual reference index at `outputs/reports_final/stage_10_analytical_report/visual_references.md`.
- Pipeline report at `outputs/reports/stage_10_analytical_report_report.md`.

## Stage 11 - Annotated Highlight / Report Package Generator

Stage 11 packages the analysis outputs into a clean local deliverable. It does not create new analysis. It organizes reports, selected visuals, data files, source notes, limitations, and a manifest for future UI/reporting work.

Run:

```powershell
python scripts\run_stage_11_report_package.py
```

Expected outputs:

- Package README at `outputs/report_packages/stage_11_report_package/README.md`.
- Package manifest at `outputs/report_packages/stage_11_report_package/package_manifest.json`.
- Package index at `outputs/report_packages/stage_11_report_package/package_index.md`.
- Analysis files under `outputs/report_packages/stage_11_report_package/analysis/`.
- Selected data files under `outputs/report_packages/stage_11_report_package/data/`.
- Selected visuals under `outputs/report_packages/stage_11_report_package/visuals/`.
- Limitations and source notes under `outputs/report_packages/stage_11_report_package/notes/`.

## Stage 12 - Synthetic Rally Replay Data Schema

Stage 12 creates the data contract for future replay renderers. It does not generate video yet. It packages court, player, ball trajectory, event, tactical metric, confidence, camera preset, and visual-layer data into deterministic local schema files.

This is the bridge toward synthetic rally replay. It does not use generative AI, official scoring, or line calling.

Run:

```powershell
python scripts\run_stage_12_replay_schema.py
```

Expected outputs:

- Full replay schema at `outputs/replay/stage_12_replay_schema/replay_schema.json`.
- Plain-text schema summary at `outputs/replay/stage_12_replay_schema/replay_schema_pretty.md`.
- Replay keyframes at `outputs/replay/stage_12_replay_schema/replay_keyframes.csv`.
- Replay events at `outputs/replay/stage_12_replay_schema/replay_events.csv`.
- Replay players at `outputs/replay/stage_12_replay_schema/replay_players.json`.
- Camera presets at `outputs/replay/stage_12_replay_schema/replay_camera_presets.json`.
- Replay manifest at `outputs/replay/stage_12_replay_schema/replay_manifest.json`.

## Stage 13 - 2D Tactical Replay Renderer

Stage 13 renders a deterministic 2D tactical replay from `replay_schema.json`. It shows the court, ball trajectory, player markers, possible event markers, and a timeline strip.

It does not generate photorealistic video. It does not use generative AI. MP4 export is attempted only when local OpenCV codec support allows it.

Run:

```powershell
python scripts\run_stage_13_2d_tactical_replay.py
```

Optional commands:

```powershell
python scripts\run_stage_13_2d_tactical_replay.py --no-video
python scripts\run_stage_13_2d_tactical_replay.py --fps 12 --interpolation-steps 5
```

Expected outputs:

- Replay frames under `outputs/replay/stage_13_2d_tactical_replay/frames/`.
- Renderer manifest at `outputs/replay/stage_13_2d_tactical_replay/renderer_manifest.json`.
- Replay summary at `outputs/replay/stage_13_2d_tactical_replay/replay_summary.md`.
- Contact sheet at `outputs/replay/stage_13_2d_tactical_replay/tactical_replay_contact_sheet.jpg`.
- Final frame at `outputs/replay/stage_13_2d_tactical_replay/tactical_replay_final_frame.jpg`.
- Optional MP4 at `outputs/replay/stage_13_2d_tactical_replay/tactical_replay.mp4`.

## Stage 14 - Side-View Ball Flight Renderer

Stage 14 renders a deterministic side-view visualization from `replay_schema.json`. It shows court depth, the net, an estimated ball arc, possible event markers, and a timeline strip.

The side-view height is synthetic and estimated. It is not true measured 3D ball height. Stage 14 does not use generative AI and does not create a photorealistic replay.

Run:

```powershell
python scripts\run_stage_14_side_view_replay.py
```

Optional commands:

```powershell
python scripts\run_stage_14_side_view_replay.py --no-video
python scripts\run_stage_14_side_view_replay.py --fps 12 --interpolation-steps 8
```

Expected outputs:

- Side-view frames under `outputs/replay/stage_14_side_view_replay/frames/`.
- Side-view manifest at `outputs/replay/stage_14_side_view_replay/side_view_manifest.json`.
- Side-view summary at `outputs/replay/stage_14_side_view_replay/side_view_summary.md`.
- Contact sheet at `outputs/replay/stage_14_side_view_replay/side_view_contact_sheet.jpg`.
- Final frame at `outputs/replay/stage_14_side_view_replay/side_view_final_frame.jpg`.
- Arc preview at `outputs/replay/stage_14_side_view_replay/side_view_arc_preview.jpg`.
- Optional MP4 at `outputs/replay/stage_14_side_view_replay/side_view_replay.mp4`.

## Stage 14.1 - Side-View Height Semantics Patch

Stage 14.1 improves side-view replay readability. It grounds bounce-like events near the court surface, keeps hit heights in a plausible estimated contact band, and distinguishes interpolated visual points from event-anchored points.

It still does not represent measured 3D height.

Run:

```powershell
python scripts\run_stage_14_side_view_replay.py
```

Expected patch output:

- Semantic debug image at `outputs/replay/stage_14_side_view_replay/side_view_semantic_debug.jpg`.
- Patch report at `outputs/reports/stage_14_1_side_view_patch_report.md`.

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
