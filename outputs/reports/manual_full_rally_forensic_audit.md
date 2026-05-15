# Manual Full-Rally Forensic Audit

VERDICT
  manual_full_rally_replay_trustworthy: false

SUMMARY
  Total events: 16
  Valid positions: 6
  Suspicious positions: 6
  Fallback positions: 0
  Unresolved but rendered: 0
  Invented/default positions: 0
  Wrong-side-likely events: 4
  Projection failures: 0
  Physical render mismatches: 0

ROOT CAUSE SUMMARY
  - Manual event timing was used correctly, but local candidate scoring can treat high-scoring color/motion blobs as reliable ball positions unless tennis-sequence validation is applied.
  - The resolver can mark local_ball_detection candidates as resolved/projected even when the resulting court side contradicts serve and hit-to-bounce geometry.
  - Current render safety flags prevent suspicious validator failures from rendering as physical anchors.
  - H1 was the critical failure case: the local detector selected a frame-100 blob at image (1467,1461), projected to near_deep_left, which is implausible for the serve side.
  - Serve/bounce direction must be validated separately from timing because timing alone does not enforce tennis rally geometry.

FAILED / SUSPICIOUS EVENTS
  - manual_full_rally_001: wrong_side_likely - Tennis sequence validator marked position_trust=invalid: implausible_serve_position. Serve contact projected to near side; expected far serving side for this manual rally. Serve H1 resolved to the near side or non-plausible serving baseline region; Product Owner observed wrong-side serve placement. Hit-to-bounce sequence stays on near side instead of crossing to far; tennis rally geometry is suspicious.
  - manual_full_rally_002: suspicious_position - Tennis sequence validator marked position_trust=suspicious: impossible_hit_bounce_transition. Hit-to-bounce pair stays on near side; expected the ball to cross the net before the next bounce. Bounce is on near side after a near-side hit; expected far.
  - manual_full_rally_005: wrong_side_likely - Tennis sequence validator marked position_trust=suspicious: wrong_side_likely. Projected to near court side, but sequence expects far for this rally event.
  - manual_full_rally_006: wrong_side_likely - Tennis sequence validator marked position_trust=suspicious: wrong_side_likely. Bounce projected to far court side, but sequence expects near.
  - manual_full_rally_007: suspicious_position - Tennis sequence validator marked position_trust=suspicious: suspicious_transition. Hit-to-bounce pair stays on near side; expected the ball to cross the net before the next bounce. Hit-to-bounce sequence stays on near side instead of crossing to far; tennis rally geometry is suspicious.
  - manual_full_rally_008: wrong_side_likely - Tennis sequence validator marked position_trust=suspicious: wrong_side_likely. Bounce projected to near court side, but sequence expects far. Bounce is on near side after a near-side hit; expected far.
  - manual_full_rally_013: suspicious_position - Tennis sequence validator marked position_trust=suspicious: wrong_side_likely. Projected to near court side, but sequence expects far for this rally event. Hit-to-bounce sequence stays on near side instead of crossing to far; tennis rally geometry is suspicious.
  - manual_full_rally_014: suspicious_position - Tennis sequence validator marked position_trust=suspicious: impossible_hit_bounce_transition. Hit-to-bounce pair stays on near side; expected the ball to cross the net before the next bounce. Bounce is on near side after a near-side hit; expected far.
  - manual_full_rally_015: suspicious_position - Tennis sequence validator marked position_trust=suspicious: wrong_side_likely. Projected to far court side, but sequence expects near for this rally event. Hit-to-bounce sequence stays on far side instead of crossing to near; tennis rally geometry is suspicious.
  - manual_full_rally_016: suspicious_position - Tennis sequence validator marked position_trust=suspicious: impossible_hit_bounce_transition. Hit-to-bounce pair stays on far side; expected the ball to cross the net before the next bounce. Bounce is on far side after a far-side hit; expected near.

DIRECT ANSWERS
  Was local ball detection used?
    16 events used local_ball_detection.

  Were old labels or fallbacks used?
    0 events used fallback sources.

  Were positions invented/defaulted/reused?
    0 events were classified as invented/default positions.

  Was homography projection applied?
    16 events have projection_status=projected.

  Did projection fail?
    0 projection failures were found.

  Why did unresolved events still render?
    Suspicious/untrusted events should have should_render_as_physical_event=no; physical_render_mismatches records any safety gate failure.

  Why did H1 end up inside/wrong side?
    H1 used local_ball_detection at frame 100 and projected to near_deep_left, which contradicts the Product Owner's serve-side observation and serve plausibility.

  Why did serve/bounce direction not respect tennis sequence?
    The audit found hit-to-bounce side-order violations; timing alone did not enforce tennis rally geometry.

OUTPUTS
  Audit CSV: C:\Users\MSI\Desktop\TennisAiVision\outputs\replay\manual_full_rally\event_position_audit.csv
  Audit JSON: C:\Users\MSI\Desktop\TennisAiVision\outputs\reports\manual_full_rally_forensic_audit.json
  Audit Markdown: C:\Users\MSI\Desktop\TennisAiVision\outputs\reports\manual_full_rally_forensic_audit.md
