# Tennis AI Vision Feasibility Summary

DECISION
  pause_until_tracknet_model_available

CONFIDENCE
  high

WHY
  Baseline failed, and TrackNet is the preferred next model family but is blocked by missing architecture or weights. SAM/SAM2 is optional and not the main path.

CURRENT STATUS
  Feasibility is not proven.
  Baseline localization failed.
  TrackNet status: blocked_weights_missing.
  SAM/SAM2 status: blocked_dependency_missing.

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
