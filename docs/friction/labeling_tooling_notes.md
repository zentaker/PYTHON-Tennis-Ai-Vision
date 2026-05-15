# Labeling Tooling Notes

## Why This Exists

Manual annotation is training infrastructure.

If the labeling tool is slow, confusing, or visually cluttered, the project can
create bad ground truth. Bad ground truth then affects event validation, replay
rendering, model training, and future line-calling.

## OpenCV Frame Viewer Friction

The OpenCV frame viewer caused high human-loop friction:

- It was frame-based rather than timeline-based.
- Adjacent frames could appear duplicated or nearly duplicated.
- The user had to guess between visually similar frames.
- Automatic overlays and markers could obscure the ball.
- It was awkward to scrub before and after an event.

## Timeline-Based Labeling Rule

Video event labeling should behave like video review.

Useful controls include:

- play/pause
- timeline scrubber
- time display
- frame estimate display
- keyboard stepping
- quick label shortcuts
- import/export labels

## Reusable Rule

For video ML workflows, annotation UX should match the medium:

  use timeline-based tools for temporal events.

Frame stepping can still be useful for debugging, but it should not be the only
labeling path for bounce/hit events.
