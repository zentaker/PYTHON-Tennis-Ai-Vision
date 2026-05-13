# Product Owner Guide

This guide is designed to be readable as plain text.
It avoids wide Markdown tables.

## What The System Does Today

- Checks whether the local Python environment is ready.
- Loads a local tennis MOV sample.
- Extracts frames and reads video metadata.
- Runs a small YOLO CPU baseline.
- Builds manual court calibration and homography.
- Generates and validates ball candidates.
- Supports manual ball labeling.
- Smooths a short ball trajectory.
- Detects and filters main tennis players.
- Builds a prototype event timeline.
- Validates timeline events against expanded ball labels.

## Current Pipeline

Stage 0:
  Environment and repo foundation.

Stage 1:
  Video loading and frame extraction.

Stage 2:
  YOLO CPU baseline.

Stage 3 and 3.1:
  Court calibration and point selection.

Stage 4 and 4.1:
  Ball candidate probe and manual ball labels.

Stage 5 and 5.1:
  Candidate filtering, projection, and improved candidate generation.

Stage 6:
  Trajectory smoothing and event hypotheses.

Stage 7 and 7.1:
  Player detection, filtering, and identity stabilization.

Stage 8 and 8.1:
  Timeline construction and validation against expanded labels.

## What Is Reliable

- Local video loading works for the MOV sample.
- Court calibration is valid after manual point selection.
- Improved HSV ball candidates match the current manual labels closely.
- Player filtering can isolate the two main players in the reviewed frames.
- Stage reports and lab notebook updates are generated automatically.

## What Is Experimental

- Ball tracking is not production-grade.
- Event types are hypotheses.
- Hit and bounce events are not confirmed.
- Rally segmentation is a prototype.
- Tactical metrics are not implemented yet.

## Where To Inspect Functions

Start with:

- docs/technical/function_inventory.md

Each function block includes:

- FUNCTION
- FILE
- LINE
- PURPOSE
- INPUTS
- OUTPUTS
- CALLED BY
- WHY PRODUCT OWNER CARES
- HOW TO FIND IT

## How To Read Line References

Example:

FILE:
  src/tennis_vision/event_timeline.py

LINE:
  154

How to inspect:

1. Open the file in VS Code or another editor.
2. Go to the listed line number.
3. Search for the listed function name if line numbers have shifted.

Line numbers are generated from source code by:

  scripts/update_function_inventory.py

## Documentation Layers

Lab notebook:
  docs/lab-notebook/

  Records execution results, verdicts, warnings, errors, friction,
  run history, and output paths.

Technical docs:
  docs/technical/

  Explain how the code works, which functions matter, what each stage
  reads and writes, and where to inspect implementation.

Friction docs:
  docs/friction/friction_casebook.md

  Explain problems that occurred, root causes, resolutions, and reusable
  rules for future agents.

## Common Confusions

Near/far player side is not identity:
  player_a and player_b should persist by identity cues when possible.
  near_side and far_side are temporary states.

possible_hit is not a confirmed hit:
  Event labels use possible_* until manually validated or supported by
  stronger evidence.

Low friction is not the same as product readiness:
  It means the local experiment ran with little operational friction.
  It does not mean the analysis is production-grade.

Generated media is local-only:
  Frames, overlays, videos, logs, models, and sample videos should not be
  committed to Git.
