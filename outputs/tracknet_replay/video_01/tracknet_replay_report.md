# TrackNet Replay Pipeline Report

VERDICT
  Final verdict: blocked_weights_missing
  Replay trustworthy: False

MODEL
  Model available: False
  Weights found: False
  Architecture available: False
  Architecture modules found: 0
  Architecture status: missing
  Weights status: missing
  Inference implementation status: waiting_for_weights
  Ready for inference: False
  Dependencies available: True
  Model weights path: None
  Weight type: missing

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
  Net clearance adjustments: 0

FAILURE REASON
  No local TrackNet/TrackNetV2/TrackNetV3/TrackNetV4 weights found. Place weights under models/tracknet/weights/ or pass --tracknet-weights.

WHY TRACKNET CANNOT RUN YET
  Architecture modules found: 0
  Weights found: False
  Ready for inference: False
  Next required artifact: TrackNet architecture plus matching pretrained weights.

EXPECTED WEIGHT LOCATIONS
  models/tracknet/weights/tracknet.pt
  models/tracknet/weights/tracknet.pth
  models/tracknet/weights/tracknetv2.pt
  models/tracknet/weights/tracknetv2.pth
  models/tracknet/weights/tracknetv3.pt
  models/tracknet/weights/tracknetv3.pth
  models/tracknet/weights/tracknetv4.pt
  models/tracknet/weights/tracknetv4.pth

NEXT CHECK COMMAND
  python scripts/check_tracknet_integration.py

RECOMMENDED NEXT STEP
  TrackNet cannot run yet because architecture modules found=0 and weights found=false. Next required artifact: TrackNet architecture plus matching pretrained weights. Place weights in models/tracknet/weights/ or pass --tracknet-weights, then rerun python scripts/check_tracknet_integration.py.

EXACT NEXT ACTION
  Add TrackNet architecture code and matching pretrained .pt/.pth weights under models/tracknet/weights/.

OUTPUTS
  Ball tracking: C:\Users\MSI\Desktop\TennisAiVision\outputs\tracknet_replay\video_01\ball_tracking_results.csv
  Projected positions: C:\Users\MSI\Desktop\TennisAiVision\outputs\tracknet_replay\video_01\projected_ball_positions.csv
  Event positions: C:\Users\MSI\Desktop\TennisAiVision\outputs\tracknet_replay\video_01\event_position_results.csv
  Replay schema: C:\Users\MSI\Desktop\TennisAiVision\outputs\tracknet_replay\video_01\replay_schema.json
