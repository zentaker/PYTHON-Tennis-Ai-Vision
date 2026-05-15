# Manual Full-Rally Replay

PURPOSE
  Uses the Product Owner's full-rally timing annotation as temporal ground
  truth, then resolves ball positions automatically from local video/candidate
  data and renders top-view and curved side-view replays.

IMPORTANT DATA CONTRACT
  The Product Owner labels when events happen.
  The system resolves where the ball is.
  The renderer shows only resolved physical positions as physical events.

SIDE-VIEW MODEL
  Side-view trajectories are synthetic Bezier curves influenced by shot_type.
  They are visual approximations, not measured 3D physics.

OUTPUTS
  outputs/replay/manual_full_rally/resolved_manual_events.csv
  outputs/replay/manual_full_rally/full_rally_event_timeline.csv
  outputs/replay/manual_full_rally/replay_schema.json
  outputs/replay/manual_full_rally/top_view_replay.mp4
  outputs/replay/manual_full_rally/side_view_replay.mp4
