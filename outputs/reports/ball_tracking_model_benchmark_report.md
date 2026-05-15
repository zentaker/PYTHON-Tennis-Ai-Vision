# Ball Tracking Model Benchmark Report

WHY THIS EXISTS
  Current YOLO/HSV/local detector failed spatial replay feasibility.
  Manual timing was correct, but local ball position resolution produced
  tennis-sequence-invalid court anchors.

MODELS TESTED
  tracknet_candidate
  sam_assisted_candidate

RESULT SUMMARY
  Model: tracknet_candidate
    available: no
    resolved: 0
    valid: 0
    suspicious: 0
    invalid: 0
    unresolved: 16
    verdict: unavailable
  Model: sam_assisted_candidate
    available: no
    resolved: 0
    valid: 0
    suspicious: 0
    invalid: 0
    unresolved: 16
    verdict: unavailable

INTERPRETATION
  Alternative model families were not available locally, so this run mainly confirms the baseline failure and integration gap.

TRACKNET PATH
  Worth continuing: True
  Reason: No local TrackNet/TrackNetV2/TrackNetV3/TrackNetV4 weights found. Place weights under models/tracknet/weights/ or pass --tracknet-weights.

SAM PATH
  Worth continuing now: False
  Reason: No local segment_anything or sam2 Python dependency is installed.

BEST MODEL
  none

WARNINGS
  None

ERRORS
  None

RECOMMENDED NEXT STEP
  Acquire or integrate a local TrackNet-style pretrained temporal heatmap tracker before continuing replay/product pipeline work.
