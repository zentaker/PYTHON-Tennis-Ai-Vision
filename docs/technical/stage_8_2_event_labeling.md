# Stage 8.2 - Manual Bounce / Hit Event Labeling Helper

This document is designed to be readable as plain text.
It avoids wide Markdown tables.

STAGE PURPOSE:
  Create manual ground truth for tennis event semantics.

  Earlier stages have ball labels, player identities, and automatic event
  hypotheses. They do not yet have human labels for true bounce, true hit,
  no_event, or uncertain frames. Stage 8.2 fills that gap.

MAIN SCRIPT:
  scripts/run_stage_8_2_event_labeling_helper.py

MAIN MODULE:
  - src/tennis_vision/event_labeling.py

READS:
  - samples/video_01.mov
  - outputs/timeline/stage_8_1_timeline_validation/expanded_ball_labels.csv
  - outputs/timeline/stage_8_event_timeline/event_timeline.csv
  - outputs/ball_tracking/stage_6_trajectory_smoothing/trajectory_events.csv
  - outputs/player_tracking/stage_7_player_interaction/ball_player_interactions.csv

WRITES:
  - outputs/timeline/stage_8_2_event_labels/manual_event_labels.csv
  - outputs/timeline/stage_8_2_event_labels/manual_event_labels.json
  - outputs/timeline/stage_8_2_event_labels/event_label_comparison.csv
  - outputs/timeline/stage_8_2_event_labels/event_label_coverage.csv
  - outputs/timeline/stage_8_2_event_labels/event_label_overlays/
  - outputs/reports/stage_8_2_event_labeling_report.json
  - outputs/reports/stage_8_2_event_labeling_report.md

FUNCTIONAL FLOW:
  1. Load the sample video.
  2. Load any existing durable manual event labels.
  3. Load expanded ball labels from Stage 8.1.
  4. Load automatic event hypotheses from Stage 8, Stage 6, and Stage 7.
  5. In interactive mode, show selected frames in OpenCV.
  6. In timeline viewer mode, load the selected frame window and let the
     user move backward and forward before deciding labels.
  7. Let the user label frames as:
     - bounce
     - hit
     - no_event
     - uncertain
     - skipped
  8. Save durable labels and timestamped session backups.
  9. Compare manual labels to nearby automatic hypotheses.
  10. Save coverage, overlays, reports, lab notebook, and technical docs.

INTERACTIVE MODES:
  Linear mode:
    The original OpenCV workflow shows one frame, accepts a label, saves or
    skips it, then advances. It remains available for quick one-pass labeling.

  Timeline viewer mode:
    Enable with:
      python scripts/run_stage_8_2_event_labeling_helper.py --interactive --timeline-viewer --start-frame 190 --interval 1 --max-frames 90

    The viewer loads a sorted, deduplicated frame window. The user can inspect
    motion first, move backward and forward, update labels in memory, delete
    previous labels, and save all changes without being forced through a
    one-way label-and-advance flow.

    By default, timeline viewer mode lazy-loads frames on demand and caches
    recently viewed resized frames. This makes large windows open faster than
    loading every selected frame before the viewer appears.

    When interval is 1, timeline viewer mode uses sequential video decoding by
    default unless --random-seek is passed. Sequential decoding helps avoid
    confusing results from random seeking in compressed MOV files.

    Timeline viewer mode also collapses near-duplicate visual groups by default.
    In collapsed mode, d/a moves between visual groups instead of forcing the
    user to inspect every near-identical raw frame. Use --expand-duplicates to
    return to raw-frame navigation.

  Review-only mode:
    Enable with:
      python scripts/run_stage_8_2_event_labeling_helper.py --interactive --timeline-viewer --review-only --start-frame 198 --interval 1 --max-frames 90

    Review-only mode lets the Product Owner scan a frame window without saving
    labels. It is useful when the approximate bounce/hit frame is still being
    found.

TIMELINE VIEWER CONTROLS:
  Navigation:
    a / left arrow:
      previous frame

    d / right arrow:
      next frame

    A / page up:
      jump backward 10 frames

    D / page down:
      jump forward 10 frames

    home / end:
      first or last loaded frame when supported by OpenCV.

    g / G:
      jump to the first or last frame of the current visual group.

    [ / ]:
      jump to the previous or next visual group.

  Labeling:
    b:
      label current frame as bounce

    h:
      label current frame as hit

    n:
      label current frame as no_event

    u:
      label current frame as uncertain

    x:
      delete the current frame label

    w:
      start or end a manual event window selection.

    W:
      select the current visual duplicate group as an event window. Then press
      b, h, n, or u to apply a window label.

    c:
      clear clicked event point

  Point:
    left click:
      set or update an event point for the current frame.

    Event point markers are hidden by default. Press p to show or hide the
    small point marker. Points belong only to the current frame label and are
    not carried across navigation.

  Overlays:
    o:
      toggle overlays

    p:
      toggle the event point marker

    m:
      toggle the nearest ball marker overlay

    l:
      toggle label text

  Save:
    s:
      save current session labels and keep viewing

    q:
      save current session labels and quit

OVERLAY DEFAULT:
  The automatic ball marker overlay is off by default in timeline viewer mode.
  This prevents wrong or distracting ball circles from covering the ball while
  the Product Owner is doing manual event review.

  Event point markers are also off by default so crosses do not obscure the
  ball. Label text remains on by default so frame number, window position,
  current label, point status, and unsaved-change status are always visible.

NO_EVENT POINT SEMANTICS:
  A no_event label normally should not have x/y event coordinates. The timeline
  viewer clears no_event points unless --preserve-no-event-points is passed.
  This prevents stale clicked points from making no_event frames look like
  physical bounce/hit events.

LABEL INTEGRITY AUDIT:
  Audit existing labels:
    python scripts/run_stage_8_2_event_labeling_helper.py --audit-labels

  Fix safe integrity issues:
    python scripts/run_stage_8_2_event_labeling_helper.py --audit-labels --fix-labels

  The audit writes:
    outputs/timeline/stage_8_2_event_labels/event_label_integrity_report.json
    outputs/timeline/stage_8_2_event_labels/event_label_integrity_report.md

  The fix command creates a backup before changing labels:
    outputs/timeline/stage_8_2_event_labels/label_backups/

  Current audit checks:
    - no_event labels with x/y points
    - repeated identical x/y points across consecutive frames
    - duplicate labels for the same frame
    - labels outside a selected frame range
    - bounce/hit labels without points

FRAME DUPLICATE AUDIT:
  Audit selected frames for near-duplicate visual content:
    python scripts/run_stage_8_2_event_labeling_helper.py --audit-frames --start-frame 198 --interval 1 --max-frames 90

  Fast audit:
    python scripts/run_stage_8_2_event_labeling_helper.py --audit-frames --audit-fast --start-frame 198 --interval 1 --max-frames 90

  Fast audit uses downscaled grayscale signatures and skips UI, overlay
  generation, and lab notebook refresh. It is intended to feel like a lightweight
  data-quality check, not a heavy model run.

  The audit writes:
    outputs/timeline/stage_8_2_event_labels/frame_duplicate_audit.csv
    outputs/timeline/stage_8_2_event_labels/frame_duplicate_audit.md

  Each frame row includes:
    - requested frame index
    - decoded frame index when OpenCV reports it
    - timestamp_ms when available
    - visual diff from previous selected frame
    - near-duplicate flag
    - visual group id
    - visual group range

  OpenCV decoded position can be unreliable for some encoded files. The audit
  records it when available, but visual grouping is based on decoded pixels.

COLLAPSED VISUAL GROUP LABELING:
  Default:
    --collapse-duplicates

  In collapsed mode, a visual group such as 204-205 appears once as:
    Frame group 204-205
    group size 2
    representative frame 204

  Pressing b/h/n/u in collapsed mode writes an event window for the current
  visual group, even when the group has only one representative frame:
    bounce_window
    hit_window
    no_event_window
    uncertain_window

  This means visual groups are the navigation and labeling unit. The viewer no
  longer merely displays visual grouping metadata while asking the user to make
  frame-perfect decisions.

  Expanded raw-frame mode:
    --expand-duplicates

EVENT WINDOW LABELS:
  Frame-perfect labels are not always appropriate when several adjacent frames
  look identical or when an event spans more than one frame.

  Stage 8.2 can now save manual event windows:
    outputs/timeline/stage_8_2_event_labels/manual_event_windows.csv
    outputs/timeline/stage_8_2_event_labels/manual_event_windows.json

  Supported window labels:
    - bounce_window
    - hit_window
    - no_event_window
    - uncertain_window

  For compatibility, the viewer can also write frame-level labels for frames in
  a window. Those labels include source_window_id and event_window_label.

DIRECT EVENT-WINDOW CLI:
  SCRIPT:
    scripts/add_stage_8_2_event_window.py

  PURPOSE:
    Adds or updates a manual event window without opening the OpenCV viewer.
    This is the recommended fallback when duplicated frames make the visual
    viewer high-friction.

  EXAMPLES:
    python scripts/add_stage_8_2_event_window.py --label bounce --start-frame 229 --end-frame 231 --confidence high --notes "second bounce window"

    python scripts/add_stage_8_2_event_window.py --label hit --start-frame 257 --end-frame 259 --confidence high --notes "player hit window"

    python scripts/add_stage_8_2_event_window.py --list

  BEHAVIOR:
    - writes manual_event_windows.csv
    - writes manual_event_windows.json
    - updates compatible frame-level labels in manual_event_labels.csv/json
    - marks those frame rows with source_window_id and event_window_label
    - creates timestamped CSV backups before modifying existing label files
    - updates the existing window instead of duplicating it when the same
      label/start/end already exists

  WHY PRODUCT OWNER CARES:
    Bounce and hit events can span several near-identical frames. A direct
    event-window command lets the user record the correct temporal event range
    without fighting the interactive viewer.

STAGE 8.3 COMPATIBILITY:
  Stage 8.3 reads:
    outputs/timeline/stage_8_2_event_labels/manual_event_windows.csv

  When user-created windows are available, Stage 8.3 treats them as preferred
  manual event-window evidence before falling back to regrouping frame labels.

SEQUENTIAL READ VS RANDOM SEEK:
  Sequential read:
    Reads forward through the selected range from one video capture. This is
    preferred for dense frame windows such as interval=1.

  Random seek:
    Seeks each frame independently. It can be useful for sparse frame lists, but
    some encoded videos may return visually confusing repeated frames.

  CLI:
    --sequential-read
    --random-seek

RECOMMENDED LABELING WORKFLOW:
  1. Load a short frame window around the likely event.
  2. Scan forward and backward before labeling.
  3. Find the exact bounce or hit frame, or label a short window if the event
     spans several frames.
  4. Use x to delete or revise labels if a better frame appears.
  5. Save at the end, then rerun Stage 8.3 validation.

RECOMMENDED COMMANDS:
  Post-hit bounce search:
    python scripts/run_stage_8_2_event_labeling_helper.py --interactive --timeline-viewer --start-frame 198 --interval 1 --max-frames 90

  Review only:
    python scripts/run_stage_8_2_event_labeling_helper.py --interactive --timeline-viewer --review-only --start-frame 198 --interval 1 --max-frames 90

  Audit duplicate frames:
    python scripts/run_stage_8_2_event_labeling_helper.py --audit-frames --start-frame 198 --interval 1 --max-frames 90

  Fast duplicate audit:
    python scripts/run_stage_8_2_event_labeling_helper.py --audit-frames --audit-fast --start-frame 198 --interval 1 --max-frames 90

  Timeline viewer with sequential read:
    python scripts/run_stage_8_2_event_labeling_helper.py --interactive --timeline-viewer --sequential-read --start-frame 198 --interval 1 --max-frames 90

  Collapsed group timeline viewer:
    python scripts/run_stage_8_2_event_labeling_helper.py --interactive --timeline-viewer --collapse-duplicates --start-frame 198 --interval 1 --max-frames 90

  Expanded raw-frame mode:
    python scripts/run_stage_8_2_event_labeling_helper.py --interactive --timeline-viewer --expand-duplicates --start-frame 198 --interval 1 --max-frames 90

  Narrow region:
    python scripts/run_stage_8_2_event_labeling_helper.py --interactive --timeline-viewer --frames 193,194,195,196,197

  Manual review list:
    python scripts/run_stage_8_2_event_labeling_helper.py --interactive --timeline-viewer --frames 210,211,212,213,214

IMPORTANT FUNCTIONS:
  See docs/technical/function_inventory.md for FILE and LINE references.
  Search that file for: Stage 8.2

PRODUCT OWNER INTERPRETATION:
  Stage 8.2 is the point where the project stops trying to infer ambiguous
  hit/bounce semantics from heuristics alone. The user can create event ground
  truth, then Stage 8.3 can use it to validate or reclassify automatic event
  hypotheses.

CURRENT LIMITATIONS:
  - Non-interactive mode only validates existing labels.
  - It does not train a model.
  - It does not implement scoring or line calling.
  - Hit/bounce labels depend on human review of selected frames.
  - Timeline viewer mode still uses OpenCV desktop windows, not a browser UI.

WHERE TO INSPECT CODE:
  Start with:
  - src/tennis_vision/event_labeling.py

  Then inspect:
  - scripts/run_stage_8_2_event_labeling_helper.py

  Use the Function Inventory for exact line numbers.
