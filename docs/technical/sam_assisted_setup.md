# SAM/SAM2-Assisted Setup

PURPOSE
  SAM/SAM2 is an optional experimental alternative for ball localization.
  It is not the primary recommended path for tennis ball tracking.

PRIMARY RECOMMENDATION
  TrackNet remains preferred because tennis ball localization is a temporal
  tracking problem. SAM/SAM2 may help only when prompted correctly and validated
  against tennis sequence rules.

WHAT SAM/SAM2 NEEDS
  - local Python dependency:
    - segment_anything, or
    - sam2
  - local weights:
    - models/sam/weights/sam.pt
    - models/sam/weights/sam.pth
    - models/sam2/weights/sam2.pt
    - models/sam2/weights/sam2.pth
  - trusted seed or point prompt near the ball;
  - mask-to-centroid conversion;
  - tennis-sequence validation before replay rendering.

CHECK COMMAND
  python scripts/check_sam_assisted_integration.py

PIPELINE COMMAND
  python scripts/run_sam_assisted_replay_pipeline.py

CURRENT EXPECTED BLOCKERS
  If segment_anything and sam2 are not installed, the check reports:
    dependency_missing

  If dependencies exist but weights are missing, the check reports:
    weights_missing

  If dependencies and weights exist but no seed prompt is available, the replay
  pipeline reports:
    blocked_seed_missing

IMPORTANT LIMITATIONS
  SAM/SAM2 should not be expected to solve fast tennis ball tracking alone.
  It is a segmentation/prompting tool, not automatically a temporal ball
  tracker.

  Do not download weights automatically.
  Do not use cloud.
  Do not fake SAM results.
  Do not treat SAM/SAM2 as better than TrackNet unless it resolves event
  positions correctly.
