# Tennis AI Vision Feasibility Decision Report

SUMMARY VERDICT
  Decision: pause_until_tracknet_model_available
  Confidence: high
  Reason:
    Baseline failed, and TrackNet is the preferred next model family but is blocked by missing architecture or weights. SAM/SAM2 is optional and not the main path.

PATH STATUS

Baseline:
  Status: failed
  Trustworthy: False
  Reason:
    Manual full-rally replay was not trustworthy. Valid positions: 6; suspicious positions: 6; wrong-side-likely events: 4.

TrackNet:
  Status: blocked_weights_missing
  Ready for inference: False
  Missing:
    - TrackNet architecture missing
    - TrackNet weights missing
    - TrackNet ready_for_inference false
  Replay generated: False
  Trustworthy: False
  Reason:
    No local TrackNet/TrackNetV2/TrackNetV3/TrackNetV4 weights found. Place weights under models/tracknet/weights/ or pass --tracknet-weights.

SAM/SAM2:
  Status: blocked_dependency_missing
  Ready for inference: False
  Missing:
    - SAM/SAM2 dependencies missing
    - SAM/SAM2 weights missing
    - SAM/SAM2 ready_for_inference false
  Replay generated: False
  Trustworthy: False
  Reason:
    No local segment_anything or sam2 Python dependency is installed.

PROJECT DECISION
  Continue: False
  Pause: True
  Required next asset: compatible TrackNet architecture + pretrained weights

WHAT WORKED
  - manual DaVinci annotation
  - court/replay scaffolds
  - model adapter scaffolds
  - feasibility reporting

WHAT FAILED
  - baseline local detector
  - TrackNet real inference unavailable
  - SAM/SAM2 real inference unavailable

CRITICAL BLOCKERS
  - TrackNet architecture missing
  - TrackNet weights missing
  - TrackNet ready_for_inference false
  - SAM/SAM2 dependencies missing
  - SAM/SAM2 weights missing
  - SAM/SAM2 ready_for_inference false

NEXT ACTION
  Primary:
    Get compatible TrackNet architecture + weights.

  Secondary:
    Only test SAM/SAM2 if TrackNet remains unavailable.

DO NOT CONTINUE YET
  - line calling
  - coaching reports
  - product UI
  - second rally transfer
  until a temporal ball tracker runs and resolves event positions.

FRICTION LESSONS
  - model availability must be checked before building downstream stages
  - replay can render technically while being spatially invalid
  - manual timing is useful but not enough without reliable ball localization
  - YOLO/HSV baseline should not be used as the core bounce/localization model
