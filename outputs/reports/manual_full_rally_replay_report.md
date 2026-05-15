# Manual Full-Rally Replay Report

VERDICT
  Final verdict: needs_better_ball_position_resolution
  Source video: samples/video_01.mov
  Manual annotation: C:\Users\MSI\Desktop\TennisAiVision\configs\manual_annotations\video_01_full_rally.json

SUMMARY
  Manual events: 16
  Hits: 8
  Bounces: 8
  Positions resolved: 16
  Positions unresolved: 0
  Projected positions: 16
  Sequence-valid positions: 6
  Suspicious positions: 9
  Invalid positions: 1
  Physical anchors rendered: 6
  Annotation events rendered: 16
  Replay trustworthy: False
  Trust reason: One or more resolved local detections failed tennis-sequence validation and were blocked from physical rendering.

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
  Top-view generated: True
  Side-view generated: True
  Curved side-view enabled: True
  Straight side-view segments used: 0
  Curve segments: 5
  Net clearance adjustments: 0

UNRESOLVED EVENTS
  None

WARNINGS
  - Suspicious positions blocked from physical rendering: manual_full_rally_002, manual_full_rally_005, manual_full_rally_006, manual_full_rally_007, manual_full_rally_008, manual_full_rally_013, manual_full_rally_014, manual_full_rally_015, manual_full_rally_016
  - Invalid positions blocked from physical rendering: manual_full_rally_001

ERRORS
  None

LIMITATIONS
  Product Owner provides event timing and shot type only.
  The system resolves ball positions automatically near those event times.
  Unresolved events are not rendered as known physical court points.
  Side-view curves are synthetic visual approximations, not measured 3D physics.
  Future line calling requires contact localization and uncertainty.

OUTPUTS
  - C:\Users\MSI\Desktop\TennisAiVision\outputs\replay\manual_full_rally\resolved_manual_events.csv
  - C:\Users\MSI\Desktop\TennisAiVision\outputs\replay\manual_full_rally\full_rally_event_timeline.csv
  - C:\Users\MSI\Desktop\TennisAiVision\outputs\replay\manual_full_rally\sequence_validation_audit.csv
  - C:\Users\MSI\Desktop\TennisAiVision\outputs\replay\manual_full_rally\replay_schema.json
  - C:\Users\MSI\Desktop\TennisAiVision\outputs\replay\manual_full_rally\top_view_replay.mp4
  - C:\Users\MSI\Desktop\TennisAiVision\outputs\replay\manual_full_rally\side_view_replay.mp4
  - C:\Users\MSI\Desktop\TennisAiVision\outputs\replay\manual_full_rally\side_view_curve_segments.csv
  - C:\Users\MSI\Desktop\TennisAiVision\outputs\reports\manual_full_rally_replay_report.json
  - C:\Users\MSI\Desktop\TennisAiVision\outputs\reports\manual_full_rally_replay_report.md
