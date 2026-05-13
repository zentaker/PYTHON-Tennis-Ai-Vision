# Stage 8 Shot/Event Timeline and Rally Segmentation Prototype Report

## Verdict

- Final verdict: ready_with_warnings
- Friction score: 15
- Friction level: low friction

## Inputs

- Stage 6 smoothed trajectory: `C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_6_trajectory_smoothing\smoothed_trajectory.csv`
- Stage 6 trajectory events: `C:\Users\MSI\Desktop\TennisAiVision\outputs\ball_tracking\stage_6_trajectory_smoothing\trajectory_events.csv`
- Stage 7 interactions: `C:\Users\MSI\Desktop\TennisAiVision\outputs\player_tracking\stage_7_player_interaction\ball_player_interactions.csv`
- Stage 7.1 main players: `C:\Users\MSI\Desktop\TennisAiVision\outputs\player_tracking\stage_7_1_player_filtering\main_players.csv`
- Stage 7.1 refined distances: `C:\Users\MSI\Desktop\TennisAiVision\outputs\player_tracking\stage_7_1_player_filtering\refined_ball_player_distances.csv`
- Stage 7.1 side states: `C:\Users\MSI\Desktop\TennisAiVision\outputs\player_tracking\stage_7_1_player_filtering\player_side_states.csv`

## Timeline summary

| Metric | Value |
|---|---:|
| trajectory points | 5 |
| source events | 18 |
| merged timeline events | 5 |
| rally segments | 1 |
| player-attributed events | 5 |
| merge window | 5 |

## Events by type

| Event type | Count |
|---|---:|
| ball_near_player | 2 |
| possible_hit | 3 |

## Rally segments

| Rally ID | Start frame | End frame | Events | Possible hits | Possible bounces | Confidence |
|---|---:|---:|---:|---:|---:|---:|
| rally_001 | 120 | 180 | 5 | 3 | 0 | 0.79 |

## Player attribution

Events are attributed to `player_a` / `player_b` when Stage 7.1 identity evidence exists near the event frame. Near/far side remains a side state, not permanent identity.

## Visual outputs

- Timeline preview: `C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_event_timeline\timeline_preview.jpg`
- Court timeline preview: `C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_event_timeline\court_timeline_preview.jpg`
- Timeline summary markdown: `C:\Users\MSI\Desktop\TennisAiVision\outputs\timeline\stage_8_event_timeline\timeline_summary.md`

## Product Owner interpretation

Stage 8 creates a first structured timeline by merging ball trajectory anchors, Stage 6 event hypotheses, Stage 7 ball-player hypotheses, and Stage 7.1 stabilized player identities. The result is useful as a prototype evidence map, but it is not official scoring, line calling, or confirmed shot classification. The current timeline is sparse, so more labels are needed before treating rally segmentation as meaningful.

## Warnings

- Only a small number of high-confidence trajectory anchors are available; timeline segmentation is preliminary.

## Errors

No errors.

## Next step

Proceed to Stage 8.1: expand labels and timeline validation before tactical metrics.
