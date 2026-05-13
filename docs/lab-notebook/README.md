# Lab Notebook

This folder is the persistent project lab notebook for Tennis AI Vision.

The notebook records technical friction, inputs, outputs, decisions, warnings, errors, and validation results for each stage. This matters because the project is not only building a local tennis video analysis pipeline; it is also learning where the local workflow succeeds, where it struggles, and what should happen next.

The notebook is plain-text friendly. Stage summaries use short field blocks instead of wide Markdown tables so they can be read in VS Code, Notepad, terminal previews, or raw GitHub view.

The normal workflow is automatic:

1. Codex implements or modifies a stage.
2. Codex runs the relevant stage script.
3. The stage script generates JSON and Markdown reports.
4. The stage script updates `docs/lab-notebook/` automatically.
5. Codex verifies the stage page and `experiment_index.md`.

The manual update command exists only as a fallback/debug utility, not as the normal user workflow:

```powershell
python scripts\update_lab_notebook.py
```

Stage scripts update the notebook automatically after they write their normal reports. If notebook generation fails, the stage script should continue and print a warning. Stage pages keep a run history so previous entries are preserved.

Future stages must call the lab notebook updater automatically at the end of their stage script. They should write JSON reports under `outputs/reports/`, include verdict and friction fields, then add a builder in `src/tennis_vision/lab_notebook.py` so the result appears in this notebook and the experiment index.
