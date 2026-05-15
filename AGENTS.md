# Agent Instructions

This repository is a local-first research project for tennis video analysis.

## Ground Rules

- Keep development local-first.
- Do not use cloud services in Stage 0.
- Do not add a frontend.
- Do not use Vue, Nuxt, React, Streamlit, FastAPI, Docker, AWS, RunPod, Modal, DigitalOcean, Colab, or other cloud runtimes.
- All scripts must be runnable from the terminal.
- All experiments must generate reports under `outputs/reports/`.
- Failures must be documented in reports and logs, not hidden.
- Use `pathlib` for filesystem work when possible.
- Keep dependencies minimal and stage-appropriate.
- Every stage must update the friction report or include friction scoring in its generated report.

## Operating model

- The user is the project administrator and tester.
- Codex is responsible for code implementation, report generation, documentation updates, and running the relevant stage scripts after implementation.
- Every stage must be self-documenting.
- Every stage script must automatically update `docs/lab-notebook/` after generating its JSON and Markdown reports.
- Codex must run the stage script after implementing or modifying a stage.
- Codex must verify that the lab notebook page and `experiment_index.md` were updated.
- Manual documentation commands are fallback/debug utilities only, not the normal workflow.
- Avoid unnecessary rewrites, duplicate prompts, redundant runs, dependency bloat, and cloud escalation.
- Prefer minimal high-signal iterations to reduce compute waste and project friction.
- Stage 2 validates local YOLO inference on CPU. It must stay small, avoid full-video processing by default, and document runtime friction honestly.
- Stage 3 must not attempt automatic court detection as the primary path. Manual calibration is the low-friction baseline. Automatic court detection can be explored later.
- Manual point selection should be supported by local tools. The user should not have to guess pixel coordinates from an image without a grid or selector.
- Stage 3 calibration uses the doubles court outer boundary. Do not confuse doubles boundary calibration with singles-line or service-box calibration; those can be derived or added in later layers.
- Stage 3 and Stage 3.1 must validate point order and reject crossed court polygons without silently auto-swapping user-selected points.
- Stage 4 is a probe, not a production tracker. Do not overclaim ball tracking accuracy. Record false positives, missed detections, and runtime friction honestly.
- When automatic detection produces many false positives, do not keep tuning blindly. Add a manual labeling or ground-truth step before optimizing the detector.
- When automatic candidates are noisy, compare against manual labels before tuning blindly. Do not overclaim tracking. Document candidate-to-label distance and projection quality.
- Before adding trajectory smoothing, validate candidate quality against manual labels. If nearest-candidate distances remain high, do not advance to event/rally logic; recommend model improvement instead.
- Trajectory smoothing must not be used to hide poor detections. If too few points exist, recommend collecting more manual labels instead of overclaiming event segmentation.
- Player-ball interactions must be labeled as hypotheses until validated. Do not infer confirmed hits from trajectory alone. Use player proximity and trajectory changes as supporting evidence, not proof.
- Player identity must be separated from court side. Near/far is a state, not a stable identity. If players switch sides, identity should persist based on track continuity and appearance cues when possible.
- Timeline and rally segmentation must preserve uncertainty. Use `possible_*` labels until validated, and do not transform hypotheses into confirmed tennis events without manual validation or stronger evidence.
- Before tactical metrics, timeline events must be validated against expanded ball labels. If label coverage is sparse, recommend collecting more labels rather than overclaiming timeline accuracy.
- When a stage has interactive data collection, the collected data must persist as the default source for later non-interactive validation. Do not make the user relabel data every run. Do not calculate friction from missing new labels if persisted labels already exist.
- Interactive user-generated data must never be overwritten by fallback data.
- Non-interactive validation must preserve richer datasets instead of downgrading them.
- Manual labeling stages must keep timestamped session backups so user work can be recovered.
- Tactical metrics must preserve uncertainty. Do not convert approximate zones, directions, or event hypotheses into confirmed coaching conclusions. Explain confidence and limitations clearly.
- Before generating coaching/report summaries, tactical metrics must have enough projected points and low unknown-zone rates. If many zones are unknown, fix projection coverage before creating narrative analysis.
- Analytical reports must preserve uncertainty. Do not turn possible_* events into confirmed events. Do not present tactical summaries as coaching truth. Use confidence levels and limitations.
- Packaging stages should not duplicate heavy artifacts blindly. Curate selected outputs, record missing artifacts, and preserve uncertainty/limitations.
- Before generating synthetic replay videos, create and validate a replay data schema. Rendering should consume structured data and preserve uncertainty. Do not use generative video as a substitute for reliable tracking data.
- Replay renderers must consume `replay_schema.json` and preserve uncertainty. Interpolated points must be marked as visual interpolation, not measured detections. Do not use generative AI until deterministic renderers work.
- Side-view replay currently uses synthetic height. Do not present synthetic height as measured 3D ball height. Preserve uncertainty in all visual labels and documentation.
- Synthetic side-view replay must visually ground bounce-like events near the court surface and distinguish interpolated visual points from event-anchored points. Do not present visually floating bounce points as acceptable output.
- Side-view event labels must be validated against player position and court depth. Do not render implausible in-court contact points as hits when the player remains near the baseline.
- When hit/bounce semantics are ambiguous, collect manual event labels before tuning visual renderers. Do not infer confirmed hits or bounces from trajectory heuristics alone.
- Video events like bounces may span a short frame window. Do not assume event labels are single-frame truths. Use event windows when manual labels cluster around the same action.
- Side-view replay must use validated event sources when available. Raw possible_hit events must not be rendered as physical contact markers unless validated by manual labels or stronger evidence.
- Manual labels should be used as active-learning signals when possible. If the user labels one event, the system should try to propose similar events instead of requiring every event to be manually labeled from scratch.
- Manual event labels must be treated as constraints. A candidate near a manually labeled hit must not be proposed as a bounce. Event propagation must respect tennis sequence.
- Manual labeling tools for temporal events must support correction and timeline review. Do not force one-way label-and-advance workflows for bounce/hit labeling.
- Manual labeling overlays should be optional and off by default when they may obscure the target being labeled.
- Manual labeling tools are model-training infrastructure. They must be fast, reversible, auditable, and visually clean. Do not show automated overlays by default if they can obscure the target being labeled.
- Manual event labeling should support event windows. Do not force frame-perfect labels when adjacent frames are visually duplicated or temporal event boundaries are ambiguous.
- Use sequential video decoding when random seeking creates duplicate or confusing frames.
- If near-duplicate frames exist, manual labeling should default to visual-group/window labeling. Do not force frame-perfect decisions when video content is visually duplicated.

## Repository hygiene rules

- Do not create a nested project folder inside the repository root.
- The repository root is the project root.
- Keep heavy artifacts local-only.
- Do not commit videos, model weights, generated frames, annotated outputs, logs, caches, virtual environments, or datasets.
- Commit source code, scripts, docs, requirements, lightweight reports, and lab notebook files.
- Before any Git commit, verify staged files with `git diff --cached --name-only`.
- Normal user workflow should be `git add .` after Git hygiene is verified.
- The user should not need long manual staging commands for normal commits.
- If a heavy file appears in `git diff --cached --name-only`, Codex must fix `.gitignore` or remove it from Git tracking before commit.
- Repository structure problems count as development friction and must be documented.
- Codex must not commit heavy artifacts.
- Codex must verify staged files before every commit.
- Codex must keep the repository lightweight and pushable.
- Codex must treat Git push failure as operational friction and document it.

## Technical documentation rules

- Every future stage must update `docs/technical/` in addition to `docs/lab-notebook/`.
- Lab notebook documents run outputs, verdicts, warnings, errors, friction, and run history.
- Technical docs document code behavior, functions, scripts, data flow, model/package calls, and file paths.
- The Product Owner should be able to understand the stage without reading code.
- Important functions must be listed with file path and search hint.
- Do not let agent-created code become a black box.
- If a function calls a model, external package, or important algorithm, document where and how.
- If a stage adds a new script or module, update `docs/technical/function_inventory.md` and `docs/technical/pipeline_map.md`.

## Plain-text documentation rules

- Plain-text documentation rules apply to documentation files, not console output.
- Documentation must be readable without a Markdown renderer.
- Avoid wide Markdown tables in Product Owner-facing documentation.
- Future generated documentation must not rely on wide Markdown tables.
- Use vertical blocks for functions, friction cases, and stage technical descriptions.
- Product Owner must be able to read docs in VS Code, Notepad, terminal, or raw GitHub view.
- Console summaries should use Rich tables when available because the user reads them directly in PowerShell.
- Markdown/docs should avoid wide tables because the user often opens them as raw TXT.
- Function references must include file path and line number when possible.
- If line numbers are generated, use a script rather than inventing them.
- Prefer short sections, bullets, and blocks over dense tables.
- Do not make Product Owner inspect source code just to understand the pipeline.

## Stage 0 Scope

Stage 0 is only for repository foundation and local environment checks.

Allowed work:

- Environment checks.
- Folder validation.
- Package import validation.
- `ffmpeg` availability checks.
- JSON, Markdown, and log report generation.
- Local cleanup of generated output files.

Not allowed yet:

- YOLO or `ultralytics`.
- Video processing pipelines beyond environment probing.
- Web APIs.
- Frontend UI.
- Cloud execution.

## Reporting Standard

Every script that performs a check or experiment should write:

- A machine-readable report when practical.
- A human-readable Markdown report when practical.
- Clear warnings, errors, recommended fixes, and friction score.

If something fails, record the failure and provide the next local action.

## Friction scoring rules

- Do not treat successful script execution as full success.
- Always distinguish execution success from semantic/product success.
- If a stage produces a visual output, product validation is required.
- If the user must manually inspect or correct model output, record human-loop friction.
- If a stage creates new patch stages, record downstream correction friction.
- ML/CV systems must measure whether outputs are useful, not only whether files were generated.
- Visual grouping must change the UX, not just appear as metadata.
- Manual event labeling should default to event windows when adjacent frames are near-duplicates.
- If a labeling tool detects visual groups, navigation and b/h/n/u labeling should operate on those groups by default.
- If interactive labeling UX becomes high-friction, provide a direct CLI fallback.
- Do not force frame-perfect labels for duplicated frames.
- Event-window labels are valid ground truth for temporal sports events.
- Do not use bounce windows directly for line calling. Use localized bounce contact points with uncertainty.
- Event labeling is training infrastructure. If a viewer becomes slow, confusing,
  or visually ambiguous, rebuild the labeling workflow instead of repeatedly
  patching around bad ground-truth collection.
- Stage 8.2R separates decode audit, visual grouping, event windows, contact
  candidates, uncertainty, and integrity audit. Preserve that separation in
  future labeling work.
- A bounce or hit window is temporal evidence. A precise contact candidate is
  spatial evidence. Do not collapse those concepts into one label.
- If frame-based labeling remains high-friction, use the local video labeling
  editor before adding more OpenCV viewer patches. Timeline-based annotation is
  the preferred abstraction for temporal video events.
- Timecode labels are frame estimates. Preserve FPS and uncertainty when
  converting them into pipeline labels.
