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
