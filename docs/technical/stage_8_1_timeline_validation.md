# Stage 8.1 - Technical Functional Documentation

## Purpose

Stage 8.1 expands or reuses manual ball labels and validates whether the Stage 8 timeline has enough ball-position evidence to support tactical metrics.

This stage does not perform scoring, line calling, confirmed hit detection, or confirmed bounce detection. It is a validation gate before Stage 9.

## Main files

| Type | Path |
|---|---|
| Script | `scripts/run_stage_8_1_expand_labels.py` |
| Label expansion module | `src/tennis_vision/label_expansion.py` |
| Timeline validation module | `src/tennis_vision/timeline_validation.py` |
| Friction scoring | `src/tennis_vision/friction.py` |
| Lab notebook updater | `src/tennis_vision/lab_notebook.py` |

## Functional flow

1. Read existing manual labels from Stage 4.1.
2. Optionally open an OpenCV click-labeling workflow to collect more ball positions.
3. Merge existing and new labels by frame, preferring newer Stage 8.1 labels.
4. Analyze label coverage, including visible label count, frame range, average gap, and maximum gap.
5. Compare Stage 5.1 improved candidates against expanded labels.
6. Validate Stage 8 timeline events against nearest expanded labels.
7. Write expanded labels, candidate validation, timeline validation, and a validated timeline.
8. Generate lightweight visual previews and reports.
9. Update the lab notebook and experiment index automatically.

## Important functions

| Function | File | Purpose | Inputs | Outputs | Notes |
|---|---|---|---|---|---|
| `read_manual_labels` | `src/tennis_vision/label_expansion.py` | Load Stage 4.1 labels into Stage 8.1 schema | manual label CSV | label rows and warnings | Search hint: `def read_manual_labels` |
| `collect_interactive_labels` | `src/tennis_vision/label_expansion.py` | Reuse OpenCV click labeler for new labels | video, frame indices, output dir | new labels, warnings, errors | Search hint: `def collect_interactive_labels` |
| `merge_labels` | `src/tennis_vision/label_expansion.py` | Merge existing and new labels by frame | existing labels, new labels | merged labels | New Stage 8.1 labels win |
| `analyze_label_coverage` | `src/tennis_vision/label_expansion.py` | Compute label coverage metrics | labels, FPS | coverage dict | Search hint: `def analyze_label_coverage` |
| `read_candidates` | `src/tennis_vision/timeline_validation.py` | Load Stage 5.1 improved candidates | candidate CSV | candidate rows | Search hint: `def read_candidates` |
| `validate_candidates_against_labels` | `src/tennis_vision/timeline_validation.py` | Compare candidates to expanded labels | labels, candidates, tolerance | validation rows and summary | Uses 10/25/50/100/200 px thresholds |
| `read_timeline` | `src/tennis_vision/timeline_validation.py` | Load Stage 8 timeline | timeline CSV | event rows | Search hint: `def read_timeline` |
| `validate_timeline_events` | `src/tennis_vision/timeline_validation.py` | Attach label support status to timeline events | timeline rows, labels | validation rows, validated timeline, summary | Does not confirm event type |
| `calculate_stage_8_1_friction_score` | `src/tennis_vision/friction.py` | Score label/timeline validation friction | validation flags | friction dict | Search hint: `def calculate_stage_8_1_friction_score` |
| `main` | `scripts/run_stage_8_1_expand_labels.py` | Run Stage 8.1 end to end | CLI args | outputs, reports, notebook update | Search hint: `def main` |

## Inputs and outputs

Reads:

- `outputs/ball_tracking/stage_4_1_manual_labels/manual_ball_labels.csv`
- `outputs/ball_tracking/stage_5_1_candidate_improvement/improved_ball_candidates.csv`
- `outputs/ball_tracking/stage_6_trajectory_smoothing/smoothed_trajectory.csv`
- `outputs/timeline/stage_8_event_timeline/event_timeline.csv`
- `outputs/timeline/stage_8_event_timeline/rally_segments.csv`
- `outputs/timeline/stage_8_event_timeline/player_event_attribution.csv`
- `samples/video_01.mov`

Writes:

- `outputs/timeline/stage_8_1_timeline_validation/expanded_ball_labels.csv`
- `outputs/timeline/stage_8_1_timeline_validation/expanded_ball_labels.json`
- `outputs/timeline/stage_8_1_timeline_validation/label_coverage_report.csv`
- `outputs/timeline/stage_8_1_timeline_validation/expanded_candidate_validation.csv`
- `outputs/timeline/stage_8_1_timeline_validation/timeline_event_validation.csv`
- `outputs/timeline/stage_8_1_timeline_validation/validated_event_timeline.csv`
- `outputs/timeline/stage_8_1_timeline_validation/validated_event_timeline.json`
- `outputs/reports/stage_8_1_timeline_validation_report.json`
- `outputs/reports/stage_8_1_timeline_validation_report.md`

## Dependencies

- OpenCV
- NumPy
- rich

## Product-owner interpretation

Stage 8.1 is the quality gate before tactical metrics. If candidate distances remain small and enough timeline events are label-supported, the project can proceed. If label coverage is sparse, the right next step is more labeling, not tactical claims.

## Known limitations

- Non-interactive mode cannot create new labels.
- Label support validates ball position near an event frame, not whether a hit or bounce truly happened.
- Candidate validation is only as broad as the labeled frames.
- More labels are needed for strong rally-level confidence.

## Where to inspect code

- `scripts/run_stage_8_1_expand_labels.py`, search `def main`
- `src/tennis_vision/label_expansion.py`, search `def analyze_label_coverage`
- `src/tennis_vision/timeline_validation.py`, search `def validate_timeline_events`
