# Reusable ML Lessons

This file is plain-text friendly.
It records lessons that should carry across future stages.

LESSON: Preserve uncertainty in tactical metrics

WHAT IT MEANS:
  If a ball point cannot be projected onto the court, mark the zone as
  unknown. Then fix projection coverage before building narrative analysis.
  Do not invent tactical placement.

WHY IT MATTERS:
  Tactical outputs can look persuasive even when the underlying evidence is
  incomplete. The Product Owner needs to see where confidence is strong and
  where it is not.

RELATED STAGES:
  Stage 9
  Stage 9.1

---

LESSON: Use manual labels as active-learning signals

SOURCE FRICTION:
  F025 - Manual labels should become active candidates, not isolated corrections

RULE:
  When a user labels one ambiguous event, use that label to propose similar
  events for review. Do not force every future event to be discovered from
  scratch.

WHY IT MATTERS:
  Manual labeling is expensive. Candidate propagation keeps the Product Owner
  in control while reducing repeated review work.

RELATED STAGES:
  Stage 8.2
  Stage 8.3
  Stage 8.4

---

LESSON: Render from validated semantic layers

SOURCE FRICTION:
  F024 - Renderers should use validated event sources, not raw event hypotheses

RULE:
  Downstream visualizations should consume validated semantic layers before raw
  model hypotheses. Raw possible_hit events should not become physical contact
  markers unless manual labels or stronger validation support them.

WHY IT MATTERS:
  A renderer can make uncertain model guesses look more certain than they are.
  That is especially risky for side-view replay because contact markers carry
  strong tennis meaning.

RELATED STAGES:
  Stage 8.3
  Stage 14.3

---

LESSON: Project validated labels before zone analysis

WHAT IT MEANS:
  Manual labels are the strongest ball-position evidence in the current
  project. If labels exist in image coordinates, project them through the
  validated court homography before assigning tactical zones.

WHY IT MATTERS:
  Stage 9 had 12 labeled ball points but only 5 projected points, which
  created unknown zones. Stage 9.1 exists to close that coverage gap.

RELATED STAGES:
  Stage 8.1
  Stage 9
  Stage 9.1

---

LESSON: Validate before summarizing

WHAT IT MEANS:
  Tactical summaries should come after label validation, candidate validation,
  timeline validation, and player identity filtering.

WHY IT MATTERS:
  A clean report over weak detections is worse than an honest warning. The
  project should advance only when the evidence layer is visible.

RELATED STAGES:
  Stage 5.1
  Stage 8.1
  Stage 9

---

LESSON: Preserve uncertainty in narrative reports

WHAT IT MEANS:
  A readable report should not make weak evidence feel certain. Use cautious
  language, confidence levels, and limitations when translating model outputs
  into human-readable observations.

WHY IT MATTERS:
  Analytical and coaching-style reports are easier to trust at a glance, so
  they must clearly distinguish hypotheses from confirmed tennis facts.

RELATED STAGES:
  Stage 10
  Later reporting and packaging stages

---

LESSON: Package curated outputs only

WHAT IT MEANS:
  A deliverable package should contain the reports, selected visuals, selected
  CSVs, limitations, and provenance that make review easier. It should not
  blindly copy whole generated folders.

WHY IT MATTERS:
  Packaging is a handoff step. The package should be lightweight, readable,
  and honest about missing optional artifacts.

RELATED STAGES:
  Stage 11
  Later export stages

---

LESSON: Create replay data before replay rendering

WHAT IT MEANS:
  Synthetic replay work should start with a stable data contract, not video
  generation. The schema should list court geometry, players, ball keyframes,
  possible events, tactical context, confidence, camera presets, visual
  layers, and limitations.

WHY IT MATTERS:
  Rendering can make uncertain data feel real. A replay schema forces the
  pipeline to show what is known, what is inferred, and what is still missing
  before any animation or synthetic video is created.

RELATED STAGES:
  Stage 12
  Future replay renderer stages

---

LESSON: Label synthetic height as synthetic

WHAT IT MEANS:
  Side-view replay can use a height-like curve for readability, but the system
  must say that the value is synthetic when no measured 3D ball height exists.

WHY IT MATTERS:
  A side-view arc can look physically authoritative. Clear labels prevent a
  visual aid from being mistaken for measured 3D reconstruction.

RELATED STAGES:
  Stage 14
  Future replay renderer stages

---

LESSON: Synthetic renderers need visual semantics

WHAT IT MEANS:
  A renderer can produce valid frames while still communicating the wrong
  meaning. Bounce-like points should look grounded, hit-like points should sit
  in a plausible contact band, and interpolated points should look different
  from event anchors.

WHY IT MATTERS:
  Replay visuals are persuasive. If the visual language is wrong, the Product
  Owner may trust an artifact that is technically rendered but semantically
  confusing.

RELATED STAGES:
  Stage 14
  Stage 14.1
  Future replay renderer stages

---

LESSON: Validate event labels against actor position

WHAT IT MEANS:
  A raw event hypothesis should not automatically become a rendered tennis
  event. Hit labels need a conservative plausibility check against player
  position, court depth, and side-state context.

WHY IT MATTERS:
  A replay can look convincing even when an event marker is spatially
  implausible. Player-aware validation prevents the renderer from turning weak
  evidence into misleading contact labels.

RELATED STAGES:
  Stage 14.2
  Future event rendering stages

---

LESSON: Label ambiguous event semantics manually

WHAT IT MEANS:
  When a system cannot reliably tell hit, bounce, interaction cue, and
  uncertain trajectory moments apart, add manual labels before more renderer
  tuning.

WHY IT MATTERS:
  Visual polish can make weak event hypotheses look more trustworthy than they
  are. Manual event labels create the ground truth needed for honest event
  validation and reclassification.

RELATED STAGES:
  Stage 8.2
  Stage 8.3
  Stage 14 replay stages

---

LESSON: Represent short temporal actions as windows

WHAT IT MEANS:
  A bounce or contact moment may span several adjacent labeled frames. Those
  frames should often become one event window instead of multiple independent
  events.

WHY IT MATTERS:
  Windowed event validation keeps downstream timelines and replay renderers
  from exaggerating a single action into several separate actions.

RELATED STAGES:
  Stage 8.3
  Future event validation stages
