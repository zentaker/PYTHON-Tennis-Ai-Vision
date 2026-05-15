# Local Video Labeling Editor

PURPOSE
  The local video labeling editor is a lightweight browser-based tool for
  manual timecode labels.

  It replaces the idea that a small OpenCV frame viewer should become a full
  video annotation environment.

CURRENT RECOMMENDED LABELING UI
  DaVinci Resolve or manual timecode notes are currently recommended for
  trusted bounce/hit visual review.

  The browser editor remains useful for lightweight local experiments, but the
  pipeline now includes Stage LB1 so the Product Owner can use a real video
  editor and import timecode labels directly.

STAGE LB1 TIMECODE IMPORT
  Script:
    scripts/import_timecode_labels.py

  Purpose:
    Converts DaVinci/manual timecode CSV rows into Stage 8.2-compatible
    manual_event_labels.csv, manual_event_labels.json,
    manual_event_windows.csv, and manual_event_windows.json.

  Command:
    python scripts/import_timecode_labels.py --input labels.csv --fps 60 --output-dir outputs/timeline/stage_8_2_event_labels

  Input CSV columns:
    label_type,timecode,time_seconds,start_timecode,end_timecode,confidence,notes

  Point labels:
    bounce_contact
    hit
    pre_bounce
    post_bounce
    uncertain
    no_event

  Range labels:
    bounce_window
    hit_window
    uncertain_window
    no_event_window

  Time parsing:
    If time_seconds is provided, it is preferred.
    Otherwise, timecode can be HH:MM:SS:FF, HH:MM:SS.mmm, or decimal seconds.
    Range labels use start/end timecode or start/end seconds.

WHY THE OPENCV VIEWER WAS NOT ENOUGH
  The OpenCV viewer was frame-oriented. Tennis events are temporal. The Product
  Owner needs to watch before and after an event, scrub smoothly, and add labels
  at the moment that makes visual sense.

  Adjacent decoded frames can also look identical or nearly identical. Forcing
  exact frame choices in that situation creates bad ground truth.

WHY TIMECODE LABELING HELPS
  Browser video playback is natural for scrubbing, pausing, stepping, and
  replaying short moments. The editor stores labels by time_seconds, then
  computes frame_estimate from the configured FPS:

  frame_estimate = round(time_seconds * fps)

  This makes the editor usable like a lightweight video editor while still
  producing pipeline-compatible labels.

WHY DAVINCI-STYLE TIMELINE CONTROLS WERE NEEDED
  A simple player with one scrubber still did not provide enough temporal
  context for precise sports-event labeling.

  The updated editor adds:
    visual thumbnail strip
    timeline ruler
    colored marker lane
    event-window lane
    vertical playhead
    timeline zoom status
    Alt + mouse wheel timeline zoom
    Ctrl + mouse wheel horizontal timeline navigation

  This better matches how Product Owners inspect short video events in
  editing tools such as DaVinci Resolve.

FILES
  Editor:
    tools/labeling_editor/index.html
    tools/labeling_editor/labeling_editor.js
    tools/labeling_editor/labeling_editor.css

  Converter:
    scripts/convert_timecode_labels.py

  Labeling output folder:
    outputs/labeling/

PRIMARY LABEL TYPES
  The editor now uses range labels as the primary workflow:

  - bounce
  - hit
  - uncertain
  - no_event

  The user adds a short event range at the playhead and edits it by dragging
  the block or resizing its edges.

LEGACY POINT LABELS
  The editor can still import and render old point labels:

  - pre_bounce
  - bounce_contact
  - post_bounce
  - hit
  - no_event
  - uncertain

  These are no longer the main UX.

EVENT RANGES
  The editor exports event_ranges as the primary annotation data.

  Event ranges support:
    bounce
    hit
    uncertain
    no_event

  Event ranges include:
    range_id
    label_type
    start_time_seconds
    end_time_seconds
    center_time_seconds
    contact_estimate_time_seconds
    start_frame_estimate
    end_frame_estimate
    contact_frame_estimate
    fps_used
    confidence
    notes

  The contact estimate defaults to the center of the range. Future stages can
  refine it if more precise contact localization is needed.

WHY RANGE-BASED LABELS REPLACED POINT PHASES
  The previous workflow exposed pre_bounce, bounce_contact, and post_bounce as
  separate point labels. That was too complex for practical annotation when the
  event visually spanned repeated or near-duplicate frames.

  The new workflow asks the user for the simpler human action:
    draw/resize the event range.

  Technical details such as center/contact estimate are derived internally.

MARKER SEMANTICS
  The editor distinguishes instant labels from duration labels.

  Point labels:
    pre_bounce
    bounce_contact
    post_bounce
    hit
    no_event
    uncertain

  Point labels render as fixed-width markers on the timeline. They use a thin
  vertical line and a small diamond so they remain precise even when zoomed in.

  Window labels:
    bounce_window
    hit_window
    no_event_window
    uncertain_window

  Window labels render as translucent horizontal range blocks from start time
  to end time.

  Product rule:
    bounce_contact is a point label, not a range.

  Future line-calling work should rely on bounce_contact or a contact candidate
  with uncertainty, not only on broad bounce_window labels.

BOUNCE SEMANTICS
  A single physical bounce can span multiple video frames.

  Correct representation:
    pre_bounce:
      point label before contact

    bounce_window:
      window label covering the full contact duration

    bounce_contact:
      one representative point label inside the bounce_window

    post_bounce:
      point label after contact

  Do not represent one physical bounce as multiple nearby bounce_contact point
  labels. The editor warns when multiple bounce_contact labels are detected in
  a very short interval.

EXPORT FORMAT
  The editor exports JSON:

  schema:
    tennis_ai_vision.video_labels.v1

  label fields:
    label_id
    label_type
    time_seconds
    frame_estimate
    fps_used
    confidence
    notes

  event_range fields:
    range_id
    label_type
    start_time_seconds
    end_time_seconds
    center_time_seconds
    contact_estimate_time_seconds
    start_frame_estimate
    end_frame_estimate
    contact_frame_estimate
    fps_used
    confidence
    notes

  window fields:
    window_id
    label_type
    start_time_seconds
    end_time_seconds
    center_time_seconds
    start_frame_estimate
    end_frame_estimate
    center_frame_estimate
    fps_used
    confidence
    notes

CONVERSION TO STAGE 8.2
  Run:

    python scripts/convert_timecode_labels.py --input outputs/labeling/video_01_labels.json --output-dir outputs/timeline/stage_8_2_event_labels --fps 60

  The converter writes:
    outputs/timeline/stage_8_2_event_labels/manual_event_labels.csv
    outputs/timeline/stage_8_2_event_labels/manual_event_labels.json
    outputs/timeline/stage_8_2_event_labels/manual_event_windows.csv
    outputs/timeline/stage_8_2_event_labels/manual_event_windows.json

  Mapping:
    bounce_contact -> bounce
    hit -> hit
    no_event -> no_event
    uncertain -> uncertain
    pre_bounce and post_bounce are retained as phase labels

  If pre_bounce, bounce_contact, and post_bounce labels bracket the same bounce,
  the converter creates a bounce_window with contact_frame equal to the
  bounce_contact frame estimate.

  Exported windows are also converted to manual_event_windows.csv and compatible
  frame-level labels.

LIMITATIONS
  Browser video playback exposes time, not a guaranteed decoded frame index.
  Frame estimates depend on the FPS value entered by the user.
  Thumbnail generation uses browser seeking and may be approximate.
  This is not official line calling.
  Future line calling still needs contact uncertainty and validation.

FRICTION RULE
  For video ML workflows, annotation UX should match the medium. Temporal
  events should be labeled with timeline tools, not only frame-stepping tools.
