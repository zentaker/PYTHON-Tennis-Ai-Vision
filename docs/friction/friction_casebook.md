# Friction Casebook

This casebook is designed to be readable as plain text.
It uses case blocks instead of wide tables.

---

CASE F001 - AWS/cloud friction

AREA:
  Cloud / infrastructure

WHAT HAPPENED:
  Early project direction considered cloud escalation, but the project scope
  required local-first research.

ROOT CAUSE:
  Cloud tools can distract from validating whether the local pipeline works.

IMPACT:
  Risk of cost, complexity, and dependency sprawl.

RESOLUTION:
  Keep stages local-first and document any future cloud decision as a later
  escalation, not a default.

REUSABLE RULE:
  Do not use cloud services unless a documented local friction case justifies it.

RELATED STAGES:
  Stage 0 and all later stages.

---

CASE F002 - Missing Python packages

AREA:
  Local environment

WHAT HAPPENED:
  The doctor script checks required imports before stage work.

ROOT CAUSE:
  New dependencies can break local reproducibility.

IMPACT:
  Scripts may fail before producing reports.

RESOLUTION:
  Keep requirements minimal and document missing packages in reports.

REUSABLE RULE:
  Add dependencies only when a stage needs them.

RELATED STAGES:
  Stage 0.

---

CASE F003 - ffmpeg warning

AREA:
  Video tooling

WHAT HAPPENED:
  ffmpeg was missing from the shell, but OpenCV still read the MOV sample.

ROOT CAUSE:
  ffmpeg is useful but not required for every OpenCV read path.

IMPACT:
  Warning only; not a blocker for validated stages.

RESOLUTION:
  Keep ffmpeg documented as optional until a stage requires it.

REUSABLE RULE:
  Treat ffmpeg as warning unless it blocks video reading.

RELATED STAGES:
  Stage 0, Stage 1.

---

CASE F004 - MOV input handling

AREA:
  Video input

WHAT HAPPENED:
  The sample video was `samples/video_01.mov`, while Stage 1 initially assumed MP4.

ROOT CAUSE:
  File extension assumptions were too narrow.

IMPACT:
  The default stage command could miss the actual sample.

RESOLUTION:
  Add default video detection for MOV, MP4, AVI, MKV, and M4V.

REUSABLE RULE:
  Detect supported local video files instead of hard-coding MP4.

RELATED STAGES:
  Stage 1 and later video stages.

---

CASE F005 - Git push failure due to heavy artifacts

AREA:
  Repository hygiene

WHAT HAPPENED:
  Git tried to upload a pack around 787 MiB and push failed.

ROOT CAUSE:
  Heavy artifacts entered Git tracking/history.

IMPACT:
  GitHub push became unreliable.

RESOLUTION:
  Strengthen `.gitignore`, keep generated media local-only, and document safe
  Git hygiene rules.

REUSABLE RULE:
  Use `git add .` only after artifact ignore rules are verified.

RELATED STAGES:
  Repository maintenance.

---

CASE F006 - Nested project folder

AREA:
  Repository structure

WHAT HAPPENED:
  The project appeared inside an extra nested folder.

ROOT CAUSE:
  Project scaffolding did not align with repository root.

IMPACT:
  Git paths and staging became confusing.

RESOLUTION:
  Normalize the repository root as the project root.

REUSABLE RULE:
  Do not create nested project roots inside an existing repository.

RELATED STAGES:
  Repository maintenance.

---

CASE F007 - Court point order inversion

AREA:
  Court calibration

WHAT HAPPENED:
  Far court corners were selected in inverted order and produced a crossed polygon.

ROOT CAUSE:
  Homography code accepted geometrically suspicious point ordering.

IMPACT:
  Court calibration could look valid while being wrong.

RESOLUTION:
  Validate point order and self-intersection before accepting homography.

REUSABLE RULE:
  Do not silently auto-fix geometry; warn and require reselection.

RELATED STAGES:
  Stage 3, Stage 3.1.

---

CASE F008 - Ball candidate false positives

AREA:
  Ball detection

WHAT HAPPENED:
  Simple color/blob heuristics detected signs, lights, audience, and artifacts.

ROOT CAUSE:
  Tennis-ball color alone is not discriminative enough in the sample video.

IMPACT:
  Automatic candidates were far from the real ball.

RESOLUTION:
  Add manual labels and evaluate candidate distance before tuning further.

REUSABLE RULE:
  When detection is noisy, create ground truth before optimizing.

RELATED STAGES:
  Stage 4, Stage 4.1, Stage 5.

---

CASE F009 - Manual label persistence bug

AREA:
  Timeline validation

WHAT HAPPENED:
  Stage 8.1 interactive labels were not used by later non-interactive runs.

ROOT CAUSE:
  Non-interactive mode fell back to original Stage 4.1 labels instead of
  persisted Stage 8.1 expanded labels.

IMPACT:
  Friction jumped and validation regressed after a successful interactive run.

RESOLUTION:
  Make `expanded_ball_labels.csv` the durable default label source.

REUSABLE RULE:
  Interactive data collection must persist as the default source for later
  validation.

RELATED STAGES:
  Stage 8.1.

---

CASE F010 - Documentation black-box risk

AREA:
  Documentation

WHAT HAPPENED:
  Agent-created code ran, but the Product Owner could not easily see what
  functions did without reading source.

ROOT CAUSE:
  Lab notebook documented results, not functional architecture.

IMPACT:
  Product ownership and review became harder.

RESOLUTION:
  Add technical docs, function inventory, and plain-text documentation rules.

REUSABLE RULE:
  Do not let agent-created code become a black box.

RELATED STAGES:
  All stages.

---

CASE F011 - Player detection noise

AREA:
  Player tracking

WHAT HAPPENED:
  YOLO detected the main players plus audience, line judges, ball kids, and
  background people.

ROOT CAUSE:
  Generic person detection sees all people, not only active tennis players.

IMPACT:
  Player tracks were noisy and identities were unstable.

RESOLUTION:
  Add court-aware filtering and lightweight clothing-color identity profiles.

REUSABLE RULE:
  Separate player identity from court side. Near/far is a state.

RELATED STAGES:
  Stage 7, Stage 7.1.

---

CASE F012 - Sparse trajectory labels

AREA:
  Timeline validation

WHAT HAPPENED:
  Stage 8 worked structurally but initially had only five high-confidence ball
  points.

ROOT CAUSE:
  Manual labels covered too small a frame range.

IMPACT:
  Timeline and rally segmentation were too sparse for tactical metrics.

RESOLUTION:
  Add Stage 8.1 expanded labels and timeline validation.

REUSABLE RULE:
  Validate timeline events against expanded labels before tactical metrics.

RELATED STAGES:
  Stage 8, Stage 8.1.
