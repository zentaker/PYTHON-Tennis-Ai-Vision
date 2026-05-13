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

Smooth the improved candidate trajectory and generate hypothesis-only event/rally segmentation markers.

Possible next paths:

- Stage 7: player tracking and ball-player interaction if trajectory smoothing is viable.
- Stage 6.1: expand manual labels if too few trajectory points exist.
- Stage 5.2: specialized ball model research if candidate quality collapses.

## Stage 7: Player Tracking And Ball-Player Interaction Probe

Detect players in sampled trajectory frames, create approximate player tracks, and associate ball positions with nearby players as hypothesis-only interaction windows.

## Stage 7.1: Court-Aware Player Filtering And Identity Stabilization

Filter irrelevant people detections, keep the main tennis players, and stabilize player identity using track continuity and appearance cues while keeping near/far side as a mutable state.

Possible next paths:

- Stage 8: shot/event timeline and rally segmentation prototype.
- Stage 7.2: manual player identity labeling helper if identity remains unreliable.
- Stage 7.3: improve player tracking if person detections or track IDs are unstable.

## Stage 8: Shot/Event Timeline And Rally Segmentation Prototype

Combine trajectory anchors, event hypotheses, player-ball interactions, and stabilized player identities into a first timeline and conservative rally segment prototype.

Possible next paths:

- Stage 9: tactical metrics and shot zone prototype if timeline evidence is strong enough.
- Stage 8.1: expand labels and timeline validation if the timeline is too sparse.
- Stage 8.2: manual event validation helper if event confidence is weak.

## Stage 8.1: Expanded Ball Labels And Timeline Validation

Current stage. Expand or reuse manual ball labels, validate improved candidates against those labels, and check whether Stage 8 timeline events have enough label support.

Possible next paths:

- Stage 9: tactical metrics and shot zones if label coverage and event support are strong enough.
- Stage 8.2: manual event labeling helper if event hypotheses need direct validation.
- Stage 8.1 repeat: collect more labels if coverage remains sparse.

## Stage 9: Tactical Metrics And Shot Zone Prototype

Planned. Use validated timeline, court projection, and player identities to start lightweight tactical metrics and shot-zone summaries without official scoring or line calling.

## Future Phase: Local MVP Pipeline

Connect local video loading, frame extraction, detection, calibration, tracking, and report generation into one terminal-driven pipeline.

## Future Phase: Synthetic Rally Replay

Generate simplified replay artifacts from validated ball trajectory, player states, and court projection. This should remain clearly separated from official broadcast-style analytics until the underlying detections are reliable.

## Future Phase: Analytical Video Generation

Create annotated analytical clips from local outputs, including trajectory overlays, event markers, player labels, and court-space summaries. This should use validated data and preserve uncertainty labels.

## Future Phase: Real-Time Court Vision

Explore whether the local pipeline can move from offline probes to near-real-time court understanding. This depends on stronger detector performance and careful runtime profiling.

## Future Phase: Multi-Angle Camera Support

Investigate calibration and event alignment across multiple camera angles. This is a later-stage capability after the single-camera pipeline is stable.

## Future Phase: Cloud Escalation Decision

Decide whether cloud resources are justified based on documented local friction, performance limits, and experiment results.
