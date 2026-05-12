# Git Hygiene

Tennis AI Vision is a local-first research project. The repository root should be the base `TennisAiVision` folder, not a nested project folder inside it. Keep the repository lightweight so it can be pushed to GitHub without carrying local media, model caches, or generated artifacts.

This repository previously hit Git push friction because heavy artifacts entered local Git history. Git attempted to upload hundreds of MiB and GitHub returned an HTTP 408 during push. That kind of failure is project friction and should be documented, then fixed by creating clean lightweight history rather than retrying the same oversized push.

## Local-only files

Future agents must not create nested project roots inside the existing repository. Project files such as `src/`, `scripts/`, `docs/`, `samples/`, and `outputs/` belong directly under the repository root.

Sample videos are local-only and should not be committed. Keep files such as `samples/video_01.mov` on your machine, but leave them out of Git.

Generated frames and annotated outputs are also local-only. They are reproducible from the stage scripts and can become very large.

YOLO model files such as `yolo11n.pt` are reproducible local artifacts. They may be downloaded again by `ultralytics`, so they should not be committed.

Virtual environments, caches, logs, datasets, generated frames, annotations, model weights, and local videos must remain local-only.

## Trackable evidence

Reports and lab notebook files are okay to commit because they are lightweight evidence of experiments:

- `outputs/reports/*.json`
- `outputs/reports/*.md`
- `docs/lab-notebook/`

The normal user workflow is intentionally simple after Git hygiene has been verified:

```powershell
git status
git add .
git status
git commit -m "your message"
git push
```

Before committing, verify the staged file list:

```powershell
git diff --cached --name-only
```

`git add .` should be safe because `.gitignore` excludes heavy/generated/local artifacts. If a heavy file appears in `git diff --cached --name-only`, the agent must fix `.gitignore` or remove the file from Git tracking before the user commits.

The user should not need long manual staging commands for normal commits. Prefer the simple workflow above once repository hygiene is confirmed.

## Untracking files already added to Git

`.gitignore` prevents new matching files from being added, but it does not remove files that are already tracked. To stop tracking a file while keeping it on disk, use `git rm --cached`.

Examples:

```powershell
git rm -r --cached samples
git rm -r --cached outputs/frames
git rm -r --cached outputs/annotated
git rm -r --cached outputs/logs
git rm -r --cached runs
git rm --cached *.pt
```

Safer version when some paths may not exist:

```powershell
git rm -r --cached --ignore-unmatch samples outputs/frames outputs/annotated outputs/logs runs
git rm --cached --ignore-unmatch *.pt *.pth *.onnx
```

After untracking, add the hygiene files and inspect the result:

```powershell
git add .
git status
git diff --cached --name-only
```
