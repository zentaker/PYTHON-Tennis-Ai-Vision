# Roadmap

## Stage 0: Environment And Repo Foundation

Create the repository structure, local environment checks, report helpers, cleanup script, and friction scoring.

## Stage 1: Video Loading And Frame Extraction

Load a local sample video, read metadata, extract frames into `outputs/frames/`, and generate JSON and Markdown reports.

## Stage 2: YOLO CPU Baseline

Add a small local CPU object detection baseline after Stage 1 proves video loading and frame extraction work. Keep the run limited, save annotated frames, and document runtime friction.

## Stage 3: Court Calibration Probe

Generate a manual court calibration reference frame, point overlay, optional homography, and normalized mini-court preview. Stage 3 focuses on court calibration/court probing, not ball tracking yet.
The calibration baseline is the doubles court outer boundary; singles-line and service-box geometry are later calibration layers.

## Stage 3.1: Court Point Selection Helper

Generate a coordinate grid and provide a local OpenCV click selector so the user can fill court point coordinates without a frontend.
The helper validates left/right ordering and crossed polygons so inverted corner selections are documented instead of silently accepted.

## Stage 3 Rerun: Homography Check

After Stage 3.1 saves valid points, rerun Stage 3 to compute and validate the court homography.

## Stage 4: Ball Tracking Probe

Generate automatic ball candidates on short sample clips only after court calibration has a stable reference. This is a probe, not production-quality tracking.

## Stage 4.1: Manual Ball Labeling Helper

Manually label true ball positions to create a small ground-truth set for validating noisy automatic candidates.

## Stage 5: Ball Candidate Filtering And Court Projection

Filter candidates using court calibration and manual labels, then project candidate coordinates into the calibrated court plane.

## Stage 5.1: Ball Candidate Generation Improvement

Current stage. Improve local handcrafted candidate generation and compare HSV, motion, court-region, and hybrid strategies against manual labels.

Decision branch:

- If improved candidates are close enough, proceed to Stage 6.
- If candidates remain too far from manual labels, proceed to Stage 5.2 specialized ball model research.

## Stage 5.2: Specialized Ball Model Research

If handcrafted candidate generation remains weak, research and benchmark specialized tennis-ball candidate generation before smoothing.

## Stage 6: Trajectory Smoothing And Event/Rally Segmentation Probe

Current stage. Smooth the improved candidate trajectory and generate hypothesis-only event/rally segmentation markers.

Possible next paths:

- Stage 7: player tracking and ball-player interaction if trajectory smoothing is viable.
- Stage 6.1: expand manual labels if too few trajectory points exist.
- Stage 5.2: specialized ball model research if candidate quality collapses.

## Stage 6.x: Local MVP Pipeline

Connect local video loading, frame extraction, detection, calibration, tracking, and report generation into one terminal-driven pipeline.

## Stage 7: Cloud Escalation Decision

Decide whether cloud resources are justified based on documented local friction, performance limits, and experiment results.
