# SAM-Assisted Replay Pipeline Report

VERDICT
  Final verdict: blocked_dependency_missing
  Replay trustworthy: False

MODEL
  Model available: False
  Dependencies available: False
  segment_anything available: False
  sam2 available: False
  Weights found: False
  Seed/prompt available: True
  Ready for inference: False
  Model weights path: None

SUMMARY
  Manual events: 16
  Hits: 8
  Bounces: 8
  Tracked frames: 0
  Projected positions: 0
  Valid event positions: 0
  Suspicious event positions: 0
  Invalid event positions: 0
  Unresolved event positions: 16

REPLAY OUTPUTS
  Top-view generated: False
  Side-view generated: False
  Curve segments: 0

IMPORTANT LIMITATION
  SAM/SAM2 is experimental for tennis ball localization.
  It is not equivalent to TrackNet unless it resolves event positions correctly.
  No fake ball positions or fallback YOLO/HSV anchors are used here.

FAILURE REASON
  No local segment_anything or sam2 Python dependency is installed.

RECOMMENDED NEXT STEP
  Install local segment_anything or sam2 dependencies, then rerun scripts/check_sam_assisted_integration.py.

OUTPUTS
  Ball tracking: C:\Users\MSI\Desktop\TennisAiVision\outputs\sam_replay\video_01\ball_tracking_results.csv
  Projected positions: C:\Users\MSI\Desktop\TennisAiVision\outputs\sam_replay\video_01\projected_ball_positions.csv
  Event positions: C:\Users\MSI\Desktop\TennisAiVision\outputs\sam_replay\video_01\event_position_results.csv
  Replay schema: C:\Users\MSI\Desktop\TennisAiVision\outputs\sam_replay\video_01\replay_schema.json
