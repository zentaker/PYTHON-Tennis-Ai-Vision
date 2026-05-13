# Technical Documentation

This folder explains how Tennis AI Vision works at the code and pipeline level.

It is different from `docs/lab-notebook/`:

- `docs/lab-notebook/` records execution results: verdicts, friction scores, inputs, outputs, warnings, errors, and run history.
- `docs/technical/` records functional architecture: scripts, modules, important functions, data flow, file paths, dependencies, and implementation limits.

The Product Owner should be able to understand what each stage does without reading Python source directly.

Every future stage must update both documentation layers:

- Lab notebook: what happened when the stage ran.
- Technical docs: what the code does and how the stage is wired.

Start here:

- `pipeline_map.md` for the stage-by-stage system map.
- `function_inventory.md` for important scripts, modules, functions, inputs, outputs, and search hints.
- Stage-specific files for functional detail.
