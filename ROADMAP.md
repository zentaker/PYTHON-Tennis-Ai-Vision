# Roadmap

## Stage 0: Environment And Repo Foundation

Create the repository structure, local environment checks, report helpers, cleanup script, and friction scoring.

## Stage 1: Video Loading And Frame Extraction

Load a local sample video, read metadata, extract frames into `outputs/frames/`, and generate JSON and Markdown reports.

## Stage 2: YOLO CPU Baseline

Current stage. Add a small local CPU object detection baseline after Stage 1 proves video loading and frame extraction work. Keep the run limited, save annotated frames, and document runtime friction.

## Stage 3: Court Calibration Probe

Experiment with local court line and geometry calibration from extracted frames. Stage 3 focuses on court calibration/court probing, not ball tracking yet.

## Stage 4: Ball Tracking Probe

Test local ball detection and tracking approaches on short sample clips.

## Stage 5: Friction Scoring System

Expand friction scoring to cover runtime performance, video quality, detection reliability, and manual intervention.

## Stage 6: Local MVP Pipeline

Connect local video loading, frame extraction, detection, calibration, tracking, and report generation into one terminal-driven pipeline.

## Stage 7: Cloud Escalation Decision

Decide whether cloud resources are justified based on documented local friction, performance limits, and experiment results.
