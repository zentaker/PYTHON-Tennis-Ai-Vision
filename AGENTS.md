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

## Repository hygiene rules

- Do not create a nested project folder inside the repository root.
- The repository root is the project root.
- Keep heavy artifacts local-only.
- Do not commit videos, model weights, generated frames, annotated outputs, logs, caches, virtual environments, or datasets.
- Commit source code, scripts, docs, requirements, lightweight reports, and lab notebook files.
- Before any Git commit, verify staged files with `git diff --cached --name-only`.
- Avoid `git add .` when heavy artifacts may be present.
- Prefer intentional staging.
- Repository structure problems count as development friction and must be documented.
- Codex must not commit heavy artifacts.
- Codex must verify staged files before every commit.
- Codex must keep the repository lightweight and pushable.
- Codex must treat Git push failure as operational friction and document it.

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
