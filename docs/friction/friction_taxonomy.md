# Friction Taxonomy

This document is plain-text friendly.
It avoids wide Markdown tables.

PURPOSE:
  Friction is not only whether a script runs.
  In a computer-vision project, a stage can execute successfully while still
  creating product or semantic friction.

FRICTION TYPES

Execution friction:
  Measures whether the script runs.

  Examples:
    - inputs exist
    - outputs are written
    - no exceptions occur
    - reports are generated

Data/model friction:
  Measures whether the output is semantically useful.

  Examples:
    - detections are meaningful
    - event labels match tennis behavior
    - candidate proposals are plausible
    - model or heuristic output supports the project goal

Human-loop friction:
  Measures how much manual labeling, visual checking, or user intervention was
  required.

  Examples:
    - manual ball labels
    - manual bounce/hit labels
    - Product Owner frame review
    - repeated review queues

Product validation friction:
  Measures whether the visual or report output makes sense to the Product Owner.

  Examples:
    - replay looks like tennis
    - bounce markers are visually grounded
    - hit markers are not misleading
    - reports do not overclaim uncertain evidence

Downstream correction friction:
  Measures whether one stage creates extra repair stages, patches, or rework.

  Examples:
    - a renderer stage requires semantic patches
    - a validation gap creates a new manual labeling stage
    - a heuristic needs follow-up candidate propagation

Infrastructure friction:
  Measures cloud, Git, environment, dependency, or repository problems.

  Examples:
    - missing packages
    - ffmpeg warning
    - Git push failure
    - heavy artifacts
    - nested project folders

Documentation friction:
  Measures whether generated docs are readable and navigable.

  Examples:
    - wide Markdown tables in raw text
    - missing function file paths
    - missing line numbers
    - unclear Product Owner interpretation

REUSABLE RULE:
  Low execution friction does not mean low product friction.
  ML and computer-vision stages must report whether outputs are useful, not
  only whether files were generated.
