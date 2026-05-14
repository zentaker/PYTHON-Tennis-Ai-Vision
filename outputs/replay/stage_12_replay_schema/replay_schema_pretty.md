# Stage 12 Synthetic Rally Replay Data Schema

SCHEMA STATUS
  Verdict: ready_for_stage_13
  Schema version: 0.1.0
  Generated at: 2026-05-14T03:30:16+00:00
  Confidence level: medium-high
  Friction: 0 (low friction)

WHAT THIS IS
  This is a data contract for future deterministic replay renderers.
  It packages court, player, ball, event, tactical, confidence, and renderer hint data.

WHAT THIS IS NOT
  - not generated video
  - not photorealistic rendering
  - not official scoring
  - not line calling

REPLAY DATA INCLUDED
  Court model: available
  Players: 2
  Ball trajectory points: 61
  Projected points: 12
  Events: 5
  Rally segments: 1
  Tactical metrics: available
  Camera presets: 6
  Visual layers: 8

RENDERER-READY DATA
  A future renderer can consume normalized court keyframes, player identities,
  possible_* event markers, rally segments, tactical zones, and camera profile hints.

FIRST RECOMMENDED RENDERER
  2D tactical replay renderer.

FUTURE RENDERERS
  - side-view ball flight
  - baseline view
  - multi-camera analytical replay
  - synthetic stylized replay

LIMITATIONS
  - limited sample video
  - limited labels
  - possible_* events are hypotheses
  - player identity is clothing/track heuristic
  - no official line calling
  - no official scoring
  - no verified ball height
  - no real 3D reconstruction yet
  - no multi-angle camera support yet
  - no real-time support yet

NEXT STEP
  Proceed to Stage 13: 2D Tactical Replay Renderer.
