# Local Video Labeling Editor

This is a lightweight local timeline editor for manual video labels.

The layout is intentionally closer to a simple editing timeline:
- video preview above
- visual thumbnail strip below
- time ruler
- marker lane
- event-window lane
- vertical playhead
- zoom and horizontal timeline navigation
- label tools and confidence controls in the right panel

It is a static HTML/JavaScript tool:
- no server
- no build step
- no React/Vue
- no upload
- no automatic overlays by default

## Open The Editor

Open this file in a browser:

```text
tools/labeling_editor/index.html
```

Then choose a local video file with the Open video button.

## Basic Workflow

1. Open `index.html`.
2. Load `samples/video_01.mov` or another local video.
3. Set FPS. Default is 60.
4. Scrub, play, pause, and step through the video.
5. Use the timeline thumbnail strip to inspect the event region.
6. Add timecode labels with buttons or keyboard shortcuts.
7. Add draggable event ranges for bounce, hit, uncertain, or no_event.
8. Drag the center of a range to move it.
9. Drag the left or right edge to resize it.
10. Export JSON.
11. Convert JSON into pipeline CSV:

```powershell
python scripts\convert_timecode_labels.py --input path\to\exported_labels.json --output-dir outputs\timeline\stage_8_2_event_labels --fps 60
```

## Keyboard Controls

Navigation:
  Space = play/pause
  A = step backward one frame estimate
  D = step forward one frame estimate
  , = step backward one frame estimate
  . = step forward one frame estimate
  Shift+A = jump backward ten frame estimates
  Shift+D = jump forward ten frame estimates
  Home = start of clip
  End = end of clip

Timeline:
  Alt + mouse wheel = zoom timeline horizontally
  Ctrl + mouse wheel = pan timeline left/right
  Shift + mouse wheel = pan timeline left/right
  + or = = zoom in
  - = zoom out
  0 = fit clip
  click/drag timeline = scrub video

Ranges:
  B = add bounce range
  H = add hit range
  U = add uncertain range
  N = add no-event range
  Delete = delete selected range or legacy point label

## Range-Based Labeling

The primary workflow is now range-based.

Main range labels:

- bounce
- hit
- uncertain
- no_event

When you add a range, the editor creates a short block around the playhead.

Edit the range like a video clip:

- drag the center to move the event;
- drag the left edge to change the start;
- drag the right edge to change the end.

The contact estimate is derived from the center of the range by default:

```text
contact_estimate_time = range center
contact_frame_estimate = round(contact_estimate_time * fps)
```

Legacy point labels such as `pre_bounce`, `bounce_contact`, and `post_bounce`
remain available under Advanced legacy point labels, but they are no longer the
main workflow.

Export:
  S = export JSON

## Label Schema

The JSON export uses:

```json
{
  "schema": "tennis_ai_vision.video_labels.v1",
  "editor_version": "0.3.0",
  "video_name": "video_01.mov",
  "fps": 60,
  "duration_seconds": 12.345,
  "timeline_zoom_at_export": 4,
  "event_ranges": [],
  "labels": [],
  "windows": []
}
```

Each event range stores:
- range id
- label type
- start time seconds
- end time seconds
- center time seconds
- contact estimate time seconds
- start/end/contact frame estimates
- fps used
- confidence
- notes

Legacy point labels store:
- label id
- label type
- time seconds
- frame estimate
- fps used
- confidence
- notes

## Important Limitation

Browser video playback exposes time, not reliable decoded frame index.

The editor therefore creates timecode labels and frame estimates:

```text
frame_estimate = round(time_seconds * fps)
```

For future line calling, bounce_contact labels should still be reviewed with
uncertainty. A timecode label is not an official line call.
