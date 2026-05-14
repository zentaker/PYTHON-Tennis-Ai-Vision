# Stage 14 Side-View Ball Flight Summary

WHAT WAS RENDERED
  - side-view court
  - net
  - estimated ball arc
  - ball trajectory
  - possible event markers
  - timeline strip

INPUT DATA
  Replay schema: C:\Users\MSI\Desktop\TennisAiVision\outputs\replay\stage_12_replay_schema\replay_schema.json
  Schema version: 0.1.0
  Keyframes: 12
  Events: 5

HEIGHT MODEL
  True height available:
    false

  Height type:
    synthetic / estimated

  Explanation:
    The project currently has 2D projected court data, not measured 3D ball height.
    The side-view height is a visual approximation.

SEMANTIC HEIGHT PATCH
  Bounces are now visually grounded near the court surface.
  Hits use a plausible estimated contact-height band.
  Interpolated points remain synthetic visual points.
  The renderer still does not use measured 3D height.

EVENT DISAMBIGUATION PATCH
  Hit labels are now filtered by player-aware plausibility.
  Implausible hit labels downgraded: 3
  Bounce events remain grounded.
  Player interaction cues are visually separated from hit and bounce labels.
  Synthetic height is still estimated, not measured.

OUTPUTS
  Frames: C:\Users\MSI\Desktop\TennisAiVision\outputs\replay\stage_14_side_view_replay\frames
  Video: C:\Users\MSI\Desktop\TennisAiVision\outputs\replay\stage_14_side_view_replay\side_view_replay.mp4
  Contact sheet: C:\Users\MSI\Desktop\TennisAiVision\outputs\replay\stage_14_side_view_replay\side_view_contact_sheet.jpg
  Final frame: C:\Users\MSI\Desktop\TennisAiVision\outputs\replay\stage_14_side_view_replay\side_view_final_frame.jpg
  Arc preview: C:\Users\MSI\Desktop\TennisAiVision\outputs\replay\stage_14_side_view_replay\side_view_arc_preview.jpg
  Manifest: C:\Users\MSI\Desktop\TennisAiVision\outputs\replay\stage_14_side_view_replay\side_view_manifest.json

LIMITATIONS
  - no true 3D reconstruction
  - no measured ball height
  - possible_* events are hypotheses
  - side-view is analytical visualization only
  - not a broadcast reconstruction

NEXT STEP
  Stage 15: Multi-Camera Analytical Replay or Stage 14.1 Side-View Visual Polish.
