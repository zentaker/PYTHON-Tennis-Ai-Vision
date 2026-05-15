# Manual Full-Rally Replay Report

VERDICT
  Final verdict: schema_generated
  Source video: samples/video_01.mov
  Manual annotation: C:\Users\MSI\Desktop\TennisAiVision\configs\manual_annotations\video_01_full_rally.json

SUMMARY
  Manual events: 16
  Hits: 8
  Bounces: 8
  Positions resolved: 16
  Positions unresolved: 0
  Projected positions: 16

SHOT TYPES
  - backhand_slice
  - backhand_topspin
  - forehand_flat
  - forehand_slice
  - forehand_topspin
  - forehand_topspin_adjusted
  - inside_out_forehand_topspin
  - serve_topspin

REPLAY OUTPUTS
  Top-view generated: False
  Side-view generated: False
  Curved side-view enabled: True
  Straight side-view segments used: 0
  Curve segments: 0
  Net clearance adjustments: 0

UNRESOLVED EVENTS
  None

WARNINGS
  None

ERRORS
  None

LIMITATIONS
  Product Owner provides event timing and shot type only.
  The system resolves ball positions automatically near those event times.
  Unresolved events are not rendered as known physical court points.
  Side-view curves are synthetic visual approximations, not measured 3D physics.
  Future line calling requires contact localization and uncertainty.

OUTPUTS
  - C:\Users\MSI\Desktop\TennisAiVision\outputs\replay\manual_full_rally\replay_schema.json
