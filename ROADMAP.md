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

Implemented. Improve local handcrafted candidate generation and compare HSV, motion, court-region, and hybrid strategies against manual labels.

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

Implemented. Expand or reuse manual ball labels, validate improved candidates against those labels, and check whether Stage 8 timeline events have enough label support.

Possible next paths:

- Stage 9: tactical metrics and shot zones if label coverage and event support are strong enough.
- Stage 8.2: manual event labeling helper if event hypotheses need direct validation.
- Stage 8.1 repeat: collect more labels if coverage remains sparse.

## Stage 9: Tactical Metrics And Shot Zone Prototype

Implemented. Use validated timeline, court projection, and player identities to start lightweight tactical metrics and shot-zone summaries without official scoring or line calling.

Possible next paths:

- Stage 10: analytical report generator and coaching summary prototype.
- Stage 9.1: court zone tuning if unknown zones or zone boundaries need refinement.
- Stage 8.2: manual event labeling if event confidence is weak.

## Stage 9.1: Court Zone Tuning And Projection Coverage

Implemented. Project expanded labels through the Stage 3 homography, tune court zone assignment, compare Stage 9 vs Stage 9.1, and reduce unknown tactical zones before narrative reporting.

Possible next paths:

- Stage 10: analytical report generator and coaching summary prototype.
- Stage 9.2: projection review if unknown zones or out-of-bounds projections remain high.
- Stage 8.2: manual event validation if event confidence is weak.

## Stage 10: Analytical Report Generator And Coaching Summary Prototype

Implemented. Turn validated metrics, timeline evidence, and visual references into a plain-language analysis report and cautious coaching-style summary while preserving uncertainty.

Possible next paths:

- Stage 11: annotated highlight/report package generator.
- Stage 10.1: report wording and confidence tuning.
- Stage 8.2: manual event validation if event confidence is weak.
- Stage 12 later: synthetic rally replay data schema.

## Stage 11: Annotated Highlight / Report Package Generator

Implemented. Package the most useful reports, data files, selected visuals, limitations, and source notes into a clean local deliverable.

Possible next paths:

- Stage 12: Synthetic Rally Replay Data Schema.
- Stage 11.1: Package polish and PDF/HTML export.
- Stage 10.1: Report wording and confidence tuning.

## Stage 12: Synthetic Rally Replay Data Schema

Implemented. Define and generate a structured replay data contract from court calibration, players, ball trajectory, events, tactical metrics, confidence data, and renderer hints.

Stage 12 does not generate replay video. It prepares deterministic data for future renderers while preserving uncertainty.

Possible next paths:

- Stage 13: 2D Tactical Replay Renderer.
- Stage 14: Side-View Ball Flight Renderer.
- Stage 15: Multi-Camera Analytical Replay.
- Stage 16: Stylistic Replay Layer.

## Stage 13: 2D Tactical Replay Renderer

Implemented. Render the first deterministic mini-court replay from Stage 12 replay_schema.json, including court, ball trail, player markers, possible event markers, timeline strip, exported frames, and optional MP4.

Possible next paths:

- Stage 14: Side-View Ball Flight Renderer.
- Stage 13.1: Replay visual polish.
- Stage 13.2: HTML/interactive replay viewer later.
- Stage 15: Multi-Camera Analytical Replay.

## Stage 14: Side-View Ball Flight Renderer

Implemented. Render a deterministic side-view replay with court depth, net, estimated ball arc, event markers, and optional MP4 while clearly labeling height as synthetic.

Possible next paths:

- Stage 15: Multi-Camera Analytical Replay.
- Stage 14.1: Side-view visual polish.
- Stage 13.1: 2D replay visual polish.
- Stage 16: Stylistic Replay Layer later.

## Stage 14.1: Side-View Height Semantics Patch

Implemented. Improve side-view replay readability by grounding bounce-like events, keeping hit-like events in a plausible synthetic contact band, and clearly marking interpolated visual points.

Possible next paths:

- Stage 15: Multi-Camera Analytical Replay.
- Stage 14.2: Further side-view polish if needed.
- Stage 13.1: Top-view replay polish if needed.

## Stage 14.2: Side-View Event Disambiguation Patch

Current stage. Validate side-view hit labels against player position and court depth, downgrade implausible hit labels, and separate bounce, hit, interaction, uncertainty, and interpolation render roles.

Possible next paths:

- Stage 15: Multi-Camera Analytical Replay.
- Stage 14.3: Further side-view tuning if needed.
- Stage 13.1: Top-view replay polish if needed.

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
