# Function Inventory

Search hints use the function definition text to find the implementation quickly.

| Area | File | Function/Class | Purpose | Inputs | Outputs | Called by | Notes |
|---|---|---|---|---|---|---|---|
| Stage 0 | `src/tennis_vision/environment.py` | `check_python_version` | Capture Python version and executable | current Python runtime | dict status | `run_environment_checks` | Search: `def check_python_version` |
| Stage 0 | `src/tennis_vision/environment.py` | `check_required_folders` | Validate project folders exist | project root | folder status dict | `run_environment_checks` | Checks samples and outputs paths |
| Stage 0 | `src/tennis_vision/environment.py` | `check_required_packages` | Validate imports for required packages | installed environment | package import status | `run_environment_checks` | Covers OpenCV, NumPy, pandas, pydantic, rich |
| Stage 0 | `src/tennis_vision/environment.py` | `check_ffmpeg` | Probe shell `ffmpeg` availability | shell PATH | availability dict | `run_environment_checks` | Warning, not blocker for current stages |
| Stage 0 | `src/tennis_vision/environment.py` | `run_environment_checks` | Run all environment checks | project root | combined checks dict | `scripts/doctor.py` | Main Stage 0 module entry |
| Reports | `src/tennis_vision/report.py` | `ensure_output_folders` | Create standard output folders | project root | folders on disk | all stage scripts | Does not create every stage-specific subfolder |
| Reports | `src/tennis_vision/report.py` | `write_json_report` | Write machine-readable report | path, dict | JSON file | all stage scripts | Uses sorted, indented JSON |
| Reports | `src/tennis_vision/report.py` | `write_markdown_report` | Write human-readable report | path, title, sections | Markdown file | all stage scripts | Section-based writer |
| Reports | `src/tennis_vision/report.py` | `write_timestamped_log` | Write timestamped log | project root, name, lines | `.log` file | all stage scripts | Logs are ignored by Git |
| Friction | `src/tennis_vision/friction.py` | `friction_band` | Map score to friction label | integer score | band string | all friction functions | 0-20 low, 21-50 medium, 51-80 high, 81+ blocking |
| Friction | `src/tennis_vision/friction.py` | `calculate_friction_score` | Score Stage 0 readiness | missing packages/folders, ffmpeg, errors | friction dict | `scripts/doctor.py` | Stage 0 |
| Friction | `src/tennis_vision/friction.py` | `calculate_stage_1_friction_score` | Score video loading friction | video/frame flags | friction dict | Stage 1 script | Stage 1 |
| Friction | `src/tennis_vision/friction.py` | `calculate_stage_2_friction_score` | Score YOLO CPU friction | model/video/runtime flags | friction dict | Stage 2 script | Stage 2 |
| Friction | `src/tennis_vision/friction.py` | `calculate_stage_3_friction_score` | Score court calibration friction | config/video/geometry flags | friction dict | Stage 3 script | Includes geometry invalidity |
| Friction | `src/tennis_vision/friction.py` | `calculate_stage_3_1_friction_score` | Score point selection friction | image/grid/point flags | friction dict | Stage 3.1 script | Grid-only is non-blocking |
| Friction | `src/tennis_vision/friction.py` | `calculate_stage_4_friction_score` | Score ball candidate probe friction | video/candidate/runtime flags | friction dict | Stage 4 script | Noisy candidates raise friction |
| Friction | `src/tennis_vision/friction.py` | `calculate_stage_4_1_friction_score` | Score manual labeling helper friction | video/frame/label/comparison flags | friction dict | Stage 4.1 script | No labels is warning, not blocker if frames load |
| Stage 0 script | `scripts/doctor.py` | `main` | Run doctor, reports, notebook update | CLI execution | reports, log, console summary | terminal | Search: `def main` |
| Stage 1 | `src/tennis_vision/video_io.py` | `validate_video_path` | Check video path exists | video path | validation dict | `read_video_metadata` | Search: `def validate_video_path` |
| Stage 1 | `src/tennis_vision/video_io.py` | `open_video` | Open OpenCV `VideoCapture` | video path | capture or error | video stages | Central video open helper |
| Stage 1 | `src/tennis_vision/video_io.py` | `read_video_metadata` | Read file size, FPS, frame count, resolution, codec | video path | metadata dict | Stage 1 script | Uses OpenCV |
| Stage 1 | `src/tennis_vision/frame_sampler.py` | `extract_frames` | Save sampled JPG frames | video path, output folder, interval, max frames | extraction stats | Stage 1 script | Writes ignored generated frames |
| Stage 1 script | `scripts/run_stage_1_video_probe.py` | `detect_default_video` | Auto-detect sample video | `samples/` folder | selected path metadata | `select_video_path` | Supports MOV/MP4/AVI/MKV/M4V |
| Stage 1 script | `scripts/run_stage_1_video_probe.py` | `main` | Run metadata extraction, frame sampling, reports | CLI args | Stage 1 reports, frames, notebook | terminal | Search: `def main` |
| Stage 2 | `src/tennis_vision/yolo_cpu.py` | `load_yolo_model` | Load small YOLO model | optional model name | model status dict | `run_yolo_cpu_baseline`, Stage 4 optional reference | Uses `ultralytics.YOLO` |
| Stage 2 | `src/tennis_vision/yolo_cpu.py` | `resize_frame` | Resize before inference | frame, width | resized frame | YOLO baseline | CPU cost control |
| Stage 2 | `src/tennis_vision/yolo_cpu.py` | `_collect_detections` | Convert YOLO boxes/classes to counts/confidences | YOLO result, class names | counts, confidence list | `run_yolo_cpu_baseline` | Search: `def _collect_detections` |
| Stage 2 | `src/tennis_vision/yolo_cpu.py` | `run_yolo_cpu_baseline` | Run limited CPU inference and save annotated frames | video, output folder, model, frame options | YOLO result dict | Stage 2 script | CPU-only, device=`cpu` |
| Stage 2 script | `scripts/run_stage_2_yolo_cpu_baseline.py` | `main` | Run Stage 2 reports and notebook update | CLI args | annotated frames, reports | terminal | Search: `def main` |
| Stage 3 | `src/tennis_vision/court_calibration.py` | `load_frame_at_index` | Load one calibration frame | video path, frame index | frame or error | calibration probe | OpenCV frame seek |
| Stage 3 | `src/tennis_vision/court_calibration.py` | `read_calibration_config` | Read manual point config | JSON path | config/errors/warnings | calibration probe | Uses `configs/court_calibration_sample.json` |
| Stage 3 | `src/tennis_vision/court_calibration.py` | `validate_points` | Validate corner coordinates and frame bounds | point dict, frame shape | validation dict | calibration probe | Calls geometry validation |
| Stage 3 | `src/tennis_vision/court_calibration.py` | `validate_corner_geometry` | Validate left/right order and polygon shape | usable corner points | geometry status | `validate_points` | Rejects inverted/crossed points |
| Stage 3 | `src/tennis_vision/court_calibration.py` | `quadrilateral_self_intersects` | Detect crossed court polygon | ordered four points | bool | `validate_corner_geometry` | Prevents X-shaped overlay |
| Stage 3 | `src/tennis_vision/court_calibration.py` | `compute_homography` | Compute court-to-mini-court transform | validated points | homography dict | calibration probe | Uses OpenCV `findHomography` |
| Stage 3 | `src/tennis_vision/court_calibration.py` | `draw_points_overlay` | Draw points and polygon on frame | frame, validation | overlay image | calibration probe | Labels doubles court corner meanings |
| Stage 3 | `src/tennis_vision/court_calibration.py` | `generate_mini_court_preview` | Warp frame into normalized court view | frame, homography | preview image or error | calibration probe | Only when homography succeeds |
| Stage 3 | `src/tennis_vision/court_calibration.py` | `run_court_calibration_probe` | Orchestrate frame load, validation, overlay, homography | config, output folder, overrides | calibration result dict | Stage 3 script | Main Stage 3 module entry |
| Stage 3 script | `scripts/run_stage_3_court_calibration_probe.py` | `main` | Run Stage 3 reports and notebook update | CLI args | calibration files, reports | terminal | Search: `def main` |
| Stage 3.1 | `src/tennis_vision/court_point_selector.py` | `generate_coordinate_grid` | Draw coordinate grid over reference frame | image path, output path, grid step | grid result | Stage 3.1 script | Makes manual coordinate reading easier |
| Stage 3.1 | `src/tennis_vision/court_point_selector.py` | `select_court_points_interactively` | OpenCV click selector for court corners | reference image, point names | selected points | Stage 3.1 script | Keys: `u`, `s`, `q` |
| Stage 3.1 | `src/tennis_vision/court_point_selector.py` | `update_calibration_config` | Write selected points to config | config path, points | update status | Stage 3.1 script | Does not auto-fix inverted points |
| Stage 3.1 | `src/tennis_vision/court_point_selector.py` | `validate_selected_points` | Validate selected points and geometry | point dict | point status | Stage 3.1 script | Uses court geometry validator |
| Stage 3.1 script | `scripts/run_stage_3_1_court_point_selector.py` | `main` | Generate grid, optionally select points, reports | CLI args | grid image, config update, reports | terminal | Search: `def main` |
| Stage 4 | `src/tennis_vision/ball_tracking_probe.py` | `resize_frame` | Resize video frame while preserving scale | frame, width | frame, scale | Stage 4 and 4.1 | Scale converts display/original coordinates |
| Stage 4 | `src/tennis_vision/ball_tracking_probe.py` | `detect_ball_candidates` | HSV + contour heuristic for ball-like blobs | frame, frame index | candidate list | Stage 4 probe | Yellow/green color threshold and circularity filter |
| Stage 4 | `src/tennis_vision/ball_tracking_probe.py` | `draw_candidates` | Draw candidate circles and scores | frame, candidates | overlay image | Stage 4 probe | Visual review artifact |
| Stage 4 | `src/tennis_vision/ball_tracking_probe.py` | `write_candidates_csv` | Save candidate positions | CSV path, candidates | CSV file | Stage 4 probe | Used by Stage 4.1 comparison |
| Stage 4 | `src/tennis_vision/ball_tracking_probe.py` | `save_trajectory_preview` | Draw rough line through best candidates | base frame, best candidates | preview path or none | Stage 4 probe | Exploratory only |
| Stage 4 | `src/tennis_vision/ball_tracking_probe.py` | `run_yolo_reference` | Optional YOLO reference on sampled frames | sampled frames, output folder, confidence | YOLO reference dict | Stage 4 probe when `--use-yolo` | Not default |
| Stage 4 | `src/tennis_vision/ball_tracking_probe.py` | `run_ball_tracking_probe` | Sample frames, detect candidates, save overlays/CSV | video, output folder, options | result dict | Stage 4 script | Main Stage 4 module entry |
| Stage 4 script | `scripts/run_stage_4_ball_tracking_probe.py` | `stage_3_spatial_status` | Check whether Stage 3 homography exists | Stage 3 report | spatial status dict | Stage 4 script | Marks image-space-only if missing |
| Stage 4 script | `scripts/run_stage_4_ball_tracking_probe.py` | `main` | Run Stage 4 probe, reports, notebook update | CLI args | candidates, reports | terminal | Search: `def main` |
| Stage 4.1 | `src/tennis_vision/ball_labeling.py` | `build_frame_indices` | Resolve frame list from CLI | frames string/start/interval/max | frame index list | Stage 4.1 script | Default list is small |
| Stage 4.1 | `src/tennis_vision/ball_labeling.py` | `load_frame_at_index` | Load selected frame | video path, frame index | frame or error | labeler | Uses OpenCV |
| Stage 4.1 | `src/tennis_vision/ball_labeling.py` | `label_frames_interactively` | OpenCV click labeling workflow | video, frame indices, output dir, resize width | labels and status | Stage 4.1 script | Keys: click, `u`, `s`, `n`, `q` |
| Stage 4.1 | `src/tennis_vision/ball_labeling.py` | `load_stage_4_display_frame` | Use Stage 4 overlay for display if available | overlay dir, frame index, fallback frame | display frame | labeler | Saves original-video coordinates |
| Stage 4.1 | `src/tennis_vision/ball_labeling.py` | `write_labels_csv` | Save manual labels to CSV | path, labels | CSV file | Stage 4.1 script | Ground truth output |
| Stage 4.1 | `src/tennis_vision/ball_labeling.py` | `write_labels_json` | Save manual labels to JSON | path, labels | JSON file | Stage 4.1 script | Ground truth output |
| Stage 4.1 | `src/tennis_vision/ball_labeling.py` | `compare_candidates_to_labels` | Find nearest Stage 4 candidate per manual label | labels, candidate CSV, output CSV | comparison summary and CSV | Stage 4.1 script | Thresholds: 10/25/50/100 px |
| Stage 4.1 script | `scripts/run_stage_4_1_ball_labeling_helper.py` | `load_frames_without_interaction` | Safe non-GUI verification path | video, frames, output dir | skipped labels/status | Stage 4.1 script | Used by `--no-interactive` |
| Stage 4.1 script | `scripts/run_stage_4_1_ball_labeling_helper.py` | `main` | Run labeler or non-interactive verification, reports, notebook update | CLI args | labels, comparison, reports | terminal | Search: `def main` |
| Lab notebook | `src/tennis_vision/lab_notebook.py` | `update_lab_notebook` | Update all known stage docs and index from reports | project root | Markdown pages | stage scripts, `scripts/update_lab_notebook.py` | Central notebook updater |
| Lab notebook | `src/tennis_vision/lab_notebook.py` | `build_experiment_index` | Build index table | stage summaries | Markdown text | `update_lab_notebook` | Writes `experiment_index.md` |
| Lab notebook | `src/tennis_vision/lab_notebook.py` | `build_stage_0_document` through `build_stage_4_1_document` | Convert stage reports into notebook pages | report dicts | body/history entries | `update_lab_notebook` | One builder per implemented stage |
| Lab notebook | `scripts/update_lab_notebook.py` | `main` | Manual fallback notebook update | CLI execution | notebook pages | terminal | Fallback/debug only |
