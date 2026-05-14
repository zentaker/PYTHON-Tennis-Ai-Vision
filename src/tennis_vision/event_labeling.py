"""Manual event labeling helpers for Stage 8.2."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any

import cv2
import numpy as np

from tennis_vision.ball_labeling import load_frame_at_index
from tennis_vision.ball_tracking_probe import resize_frame


EVENT_LABEL_FIELDS = [
    "frame_index",
    "timestamp_seconds",
    "event_label",
    "player_id",
    "x",
    "y",
    "source",
    "label_session",
    "confidence",
    "associated_ball_label_frame",
    "nearest_ball_x",
    "nearest_ball_y",
    "nearest_auto_event_type",
    "nearest_auto_event_frame",
    "frame_delta_to_auto_event",
    "notes",
]

COVERAGE_FIELDS = [
    "total_labeled_frames",
    "bounce_labels_count",
    "hit_labels_count",
    "no_event_count",
    "uncertain_count",
    "skipped_count",
    "frame_range",
    "average_gap",
    "max_gap",
]

COMPARISON_FIELDS = [
    "frame_index",
    "manual_event_label",
    "manual_confidence",
    "nearest_auto_event_type",
    "nearest_auto_event_frame",
    "frame_delta",
    "match_status",
    "comparison_reason",
]


def read_event_labels(path: Path, *, source: str = "stage_8_2_existing") -> tuple[list[dict[str, Any]], list[str]]:
    """Read Stage 8.2 manual event labels from CSV."""
    if not path.exists():
        return [], [f"Manual event labels CSV not found: {path}"]
    rows: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            frame = int_or_none(row.get("frame_index"))
            if frame is None:
                continue
            rows.append(
                {
                    "frame_index": frame,
                    "timestamp_seconds": float_or_none(row.get("timestamp_seconds")),
                    "event_label": row.get("event_label") or "uncertain",
                    "player_id": row.get("player_id") or "unknown",
                    "x": float_or_none(row.get("x")),
                    "y": float_or_none(row.get("y")),
                    "source": row.get("source") or source,
                    "label_session": row.get("label_session") or source,
                    "confidence": row.get("confidence") or "medium",
                    "associated_ball_label_frame": int_or_none(row.get("associated_ball_label_frame")),
                    "nearest_ball_x": float_or_none(row.get("nearest_ball_x")),
                    "nearest_ball_y": float_or_none(row.get("nearest_ball_y")),
                    "nearest_auto_event_type": row.get("nearest_auto_event_type") or "",
                    "nearest_auto_event_frame": int_or_none(row.get("nearest_auto_event_frame")),
                    "frame_delta_to_auto_event": int_or_none(row.get("frame_delta_to_auto_event")),
                    "notes": row.get("notes") or "",
                }
            )
    return rows, []


def latest_event_label_session_csv(session_dir: Path) -> Path | None:
    """Return the newest Stage 8.2 event label session CSV."""
    if not session_dir.exists():
        return None
    sessions = sorted(session_dir.glob("stage_8_2_event_labels_*.csv"), key=lambda path: path.stat().st_mtime)
    return sessions[-1] if sessions else None


def load_durable_event_labels(labels_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any], list[str]]:
    """Load durable event labels first, then latest session backup."""
    session_dir = labels_path.parent / "event_label_sessions"
    durable, durable_warnings = read_event_labels(labels_path, source="stage_8_2_existing")
    if durable:
        return durable, {"label_source_used": "manual_event_labels", "manual_event_labels_path": str(labels_path)}, []
    latest = latest_event_label_session_csv(session_dir)
    if latest:
        session_labels, session_warnings = read_event_labels(latest, source="stage_8_2_latest_session")
        if session_labels:
            return (
                session_labels,
                {
                    "label_source_used": "latest_event_label_session",
                    "manual_event_labels_path": str(labels_path),
                    "latest_session_path": str(latest),
                },
                session_warnings,
            )
    return (
        [],
        {"label_source_used": "missing", "manual_event_labels_path": str(labels_path), "latest_session_path": str(latest) if latest else "Not available"},
        durable_warnings if labels_path.exists() else [],
    )


def read_ball_labels(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Read visible expanded ball labels."""
    if not path.exists():
        return [], [f"Expanded ball labels not found: {path}"]
    rows: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            frame = int_or_none(row.get("frame_index"))
            visible = str(row.get("visible", "")).lower() in {"true", "1", "yes"}
            x = float_or_none(row.get("x"))
            y = float_or_none(row.get("y"))
            if frame is None or not visible or x is None or y is None:
                continue
            rows.append({"frame_index": frame, "x": x, "y": y, "visible": True})
    return rows, []


def read_auto_events(paths: list[tuple[Path, str]]) -> tuple[list[dict[str, Any]], list[str]]:
    """Read automatic event hypotheses from Stage 6/7/8 CSVs."""
    warnings: list[str] = []
    events: list[dict[str, Any]] = []
    for path, source in paths:
        if not path.exists():
            warnings.append(f"Optional automatic event file not found: {path}")
            continue
        with path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                frame = int_or_none(row.get("frame_index"))
                if frame is None:
                    continue
                event_type = row.get("event_type") or row.get("interaction_type") or row.get("related_stage_6_event") or "unknown"
                events.append(
                    {
                        "frame_index": frame,
                        "event_type": event_type,
                        "event_source": source,
                        "player_id": row.get("player_id") or row.get("nearest_track_id") or "",
                        "x": float_or_none(row.get("ball_x") or row.get("x")),
                        "y": float_or_none(row.get("ball_y") or row.get("y")),
                        "confidence_like_score": float_or_none(row.get("confidence_like_score")),
                    }
                )
    return events, warnings


def nearest_ball_label(frame_index: int, ball_labels: list[dict[str, Any]], window: int) -> dict[str, Any] | None:
    """Find nearest visible ball label within a frame window."""
    eligible = [label for label in ball_labels if abs(int(label["frame_index"]) - frame_index) <= window]
    if not eligible:
        return None
    return min(eligible, key=lambda row: abs(int(row["frame_index"]) - frame_index))


def nearest_auto_event(frame_index: int, auto_events: list[dict[str, Any]], window: int) -> dict[str, Any] | None:
    """Find nearest automatic event hypothesis within a frame window."""
    eligible = [event for event in auto_events if abs(int(event["frame_index"]) - frame_index) <= window]
    if not eligible:
        return None
    return min(eligible, key=lambda row: (abs(int(row["frame_index"]) - frame_index), event_priority(row.get("event_type"))))


def build_event_label(
    *,
    frame_index: int,
    event_label: str,
    confidence: str,
    player_id: str,
    x: float | None,
    y: float | None,
    fps: float | None,
    source: str,
    label_session: str,
    ball_labels: list[dict[str, Any]],
    auto_events: list[dict[str, Any]],
    candidate_window: int,
    notes: str = "",
) -> dict[str, Any]:
    """Build one event label row with nearby ball and auto-event context."""
    nearest_ball = nearest_ball_label(frame_index, ball_labels, candidate_window)
    nearest_auto = nearest_auto_event(frame_index, auto_events, candidate_window)
    if x is None and nearest_ball:
        x = float_or_none(nearest_ball.get("x"))
    if y is None and nearest_ball:
        y = float_or_none(nearest_ball.get("y"))
    if player_id == "auto" and nearest_auto:
        player_id = infer_player_id(event_label, nearest_auto)
    elif player_id == "auto":
        player_id = "none" if event_label in {"bounce", "no_event", "skipped"} else "unknown"
    return {
        "frame_index": frame_index,
        "timestamp_seconds": round(frame_index / fps, 3) if fps else None,
        "event_label": event_label,
        "player_id": player_id,
        "x": round(float(x), 3) if x is not None else None,
        "y": round(float(y), 3) if y is not None else None,
        "source": source,
        "label_session": label_session,
        "confidence": confidence,
        "associated_ball_label_frame": nearest_ball.get("frame_index") if nearest_ball else None,
        "nearest_ball_x": nearest_ball.get("x") if nearest_ball else None,
        "nearest_ball_y": nearest_ball.get("y") if nearest_ball else None,
        "nearest_auto_event_type": nearest_auto.get("event_type") if nearest_auto else "",
        "nearest_auto_event_frame": nearest_auto.get("frame_index") if nearest_auto else None,
        "frame_delta_to_auto_event": abs(frame_index - int(nearest_auto["frame_index"])) if nearest_auto else None,
        "notes": notes,
    }


def collect_event_labels_interactively(
    *,
    video_path: Path,
    frame_indices: list[int],
    output_dir: Path,
    resize_width: int,
    fps: float | None,
    ball_labels: list[dict[str, Any]],
    auto_events: list[dict[str, Any]],
    candidate_window: int,
    label_session: str,
) -> dict[str, Any]:
    """Let the user label bounce/hit/no-event/uncertain frames."""
    labels: list[dict[str, Any]] = []
    warnings: list[str] = []
    errors: list[str] = []
    overlay_dir = output_dir / "event_label_overlays"
    overlay_dir.mkdir(parents=True, exist_ok=True)
    window_name = "Stage 8.2 Manual Event Labeling"
    try:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    except cv2.error as exc:
        return {"labels": labels, "frames_shown": 0, "warnings": warnings, "errors": [f"OpenCV GUI unavailable: {exc}"]}

    frames_shown = 0
    quit_requested = False
    try:
        for frame_index in frame_indices:
            frame, frame_error = load_frame_at_index(video_path, frame_index)
            if frame_error or frame is None:
                errors.append(frame_error or f"Could not load frame {frame_index}.")
                continue
            original_h, original_w = frame.shape[:2]
            display, scale = resize_frame(frame, resize_width)
            selected_event = "uncertain"
            selected_confidence = "medium"
            selected_point: tuple[float, float] | None = None

            def on_mouse(event: int, x_value: int, y_value: int, _flags: int, _param: Any) -> None:
                nonlocal selected_point
                if event == cv2.EVENT_LBUTTONDOWN:
                    selected_point = (x_value / scale if scale else float(x_value), y_value / scale if scale else float(y_value))

            cv2.setMouseCallback(window_name, on_mouse)
            frames_shown += 1
            while True:
                shown = draw_event_label_overlay(
                    display.copy(),
                    frame_index=frame_index,
                    scale=scale,
                    event_label=selected_event,
                    selected_point=selected_point,
                    ball_label=nearest_ball_label(frame_index, ball_labels, candidate_window),
                    auto_event=nearest_auto_event(frame_index, auto_events, candidate_window),
                )
                cv2.setWindowTitle(window_name, f"Frame {frame_index} | b=bounce h=hit n=no_event u=uncertain s=save k=skip q=quit")
                cv2.imshow(window_name, shown)
                key = cv2.waitKey(30) & 0xFF
                if key == ord("b"):
                    selected_event = "bounce"
                    selected_confidence = "high"
                elif key == ord("h"):
                    selected_event = "hit"
                    selected_confidence = "high"
                elif key == ord("n"):
                    selected_event = "no_event"
                    selected_confidence = "high"
                elif key == ord("u"):
                    selected_event = "uncertain"
                    selected_confidence = "low"
                elif key in {ord("z"), 8}:
                    selected_point = None
                    selected_event = "uncertain"
                    selected_confidence = "medium"
                elif key in {ord("s"), ord("k"), ord("q")}:
                    label_name = "skipped" if key == ord("k") else selected_event
                    point_x, point_y = selected_point if selected_point else (None, None)
                    label = build_event_label(
                        frame_index=frame_index,
                        event_label=label_name,
                        confidence="low" if label_name in {"uncertain", "skipped"} else selected_confidence,
                        player_id="auto",
                        x=point_x,
                        y=point_y,
                        fps=fps,
                        source="stage_8_2_manual",
                        label_session=label_session,
                        ball_labels=ball_labels,
                        auto_events=auto_events,
                        candidate_window=candidate_window,
                        notes=f"original_width={original_w}; original_height={original_h}",
                    )
                    labels.append(label)
                    overlay_path = overlay_dir / f"event_label_frame_{frame_index:06d}.jpg"
                    write_event_overlay(video_path, label, ball_labels, auto_events, overlay_path, resize_width, candidate_window)
                    if key == ord("q"):
                        quit_requested = True
                    break
            if quit_requested:
                break
    finally:
        try:
            cv2.destroyWindow(window_name)
        except cv2.error:
            pass
    return {"labels": labels, "frames_shown": frames_shown, "warnings": warnings, "errors": errors}


def merge_event_labels(existing_labels: list[dict[str, Any]], new_labels: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge event labels by frame, preferring newest Stage 8.2 labels."""
    by_frame: dict[int, dict[str, Any]] = {}
    for label in existing_labels:
        by_frame[int(label["frame_index"])] = dict(label)
    for label in new_labels:
        frame = int(label["frame_index"])
        previous = by_frame.get(frame)
        updated = dict(label)
        if previous:
            prior = f"previous_label={previous.get('event_label')} source={previous.get('source')}"
            updated["notes"] = "; ".join(item for item in [updated.get("notes"), prior] if item)
        by_frame[frame] = updated
    return [by_frame[key] for key in sorted(by_frame)]


def compare_manual_events_to_auto_events(
    labels: list[dict[str, Any]],
    auto_events: list[dict[str, Any]],
    *,
    candidate_window: int,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Compare manual event labels against automatic event hypotheses."""
    rows: list[dict[str, Any]] = []
    summary = {"comparison_count": 0, "exact_matches": 0, "compatible_matches": 0, "mismatches": 0, "no_auto_event_nearby": 0}
    for label in labels:
        event_label = str(label.get("event_label") or "uncertain")
        if event_label == "skipped":
            continue
        nearest = nearest_auto_event(int(label["frame_index"]), auto_events, candidate_window)
        status, reason = classify_match(event_label, str(label.get("confidence") or "medium"), nearest)
        row = {
            "frame_index": label.get("frame_index"),
            "manual_event_label": event_label,
            "manual_confidence": label.get("confidence"),
            "nearest_auto_event_type": nearest.get("event_type") if nearest else "",
            "nearest_auto_event_frame": nearest.get("frame_index") if nearest else None,
            "frame_delta": abs(int(label["frame_index"]) - int(nearest["frame_index"])) if nearest else None,
            "match_status": status,
            "comparison_reason": reason,
        }
        rows.append(row)
        summary["comparison_count"] += 1
        if status == "exact_match":
            summary["exact_matches"] += 1
        elif status == "compatible_match":
            summary["compatible_matches"] += 1
        elif status == "mismatch":
            summary["mismatches"] += 1
        elif status == "no_auto_event_nearby":
            summary["no_auto_event_nearby"] += 1
    return rows, summary


def analyze_event_label_coverage(labels: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize event label coverage."""
    frames = sorted(int(label["frame_index"]) for label in labels if str(label.get("event_label")) != "skipped")
    gaps = [current - previous for previous, current in zip(frames, frames[1:])]
    return {
        "total_labeled_frames": len(frames),
        "bounce_labels_count": count_label(labels, "bounce"),
        "hit_labels_count": count_label(labels, "hit"),
        "no_event_count": count_label(labels, "no_event"),
        "uncertain_count": count_label(labels, "uncertain"),
        "skipped_count": count_label(labels, "skipped"),
        "frame_range": f"{frames[0]} to {frames[-1]}" if frames else "Not available",
        "average_gap": round(mean(gaps), 3) if gaps else None,
        "max_gap": max(gaps) if gaps else None,
    }


def write_event_labels_csv(path: Path, labels: list[dict[str, Any]]) -> Path:
    """Write manual event labels to CSV."""
    return write_csv(path, labels, EVENT_LABEL_FIELDS)


def write_event_labels_json(path: Path, labels: list[dict[str, Any]]) -> Path:
    """Write manual event labels to JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(labels, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_event_label_session_backup(session_dir: Path, timestamp: str, labels: list[dict[str, Any]]) -> dict[str, Path]:
    """Write timestamped session backup for interactive event labels."""
    safe = timestamp.replace(":", "").replace("+", "Z")
    csv_path = session_dir / f"stage_8_2_event_labels_{safe}.csv"
    json_path = session_dir / f"stage_8_2_event_labels_{safe}.json"
    write_event_labels_csv(csv_path, labels)
    write_event_labels_json(json_path, labels)
    return {"csv": csv_path, "json": json_path}


def write_event_comparison_csv(path: Path, rows: list[dict[str, Any]]) -> Path:
    """Write manual-vs-automatic event comparison CSV."""
    return write_csv(path, rows, COMPARISON_FIELDS)


def write_event_coverage_csv(path: Path, coverage: dict[str, Any]) -> Path:
    """Write one-row event label coverage CSV."""
    return write_csv(path, [coverage], COVERAGE_FIELDS)


def write_event_overlays(
    *,
    video_path: Path,
    labels: list[dict[str, Any]],
    ball_labels: list[dict[str, Any]],
    auto_events: list[dict[str, Any]],
    overlay_dir: Path,
    resize_width: int,
    candidate_window: int,
) -> tuple[int, list[str]]:
    """Write overlay images for labeled frames."""
    warnings: list[str] = []
    written = 0
    for label in labels:
        path = overlay_dir / f"event_label_frame_{int(label['frame_index']):06d}.jpg"
        ok = write_event_overlay(video_path, label, ball_labels, auto_events, path, resize_width, candidate_window)
        if ok:
            written += 1
        else:
            warnings.append(f"Could not write event label overlay for frame {label['frame_index']}.")
    return written, warnings


def write_event_overlay(
    video_path: Path,
    label: dict[str, Any],
    ball_labels: list[dict[str, Any]],
    auto_events: list[dict[str, Any]],
    output_path: Path,
    resize_width: int,
    candidate_window: int,
) -> bool:
    """Write one event label overlay image."""
    frame_index = int(label["frame_index"])
    frame, error = load_frame_at_index(video_path, frame_index)
    if error or frame is None:
        return False
    display, scale = resize_frame(frame, resize_width)
    overlay = draw_event_label_overlay(
        display,
        frame_index=frame_index,
        scale=scale,
        event_label=str(label.get("event_label") or "uncertain"),
        selected_point=(float(label["x"]), float(label["y"])) if label.get("x") is not None and label.get("y") is not None else None,
        ball_label=nearest_ball_label(frame_index, ball_labels, candidate_window),
        auto_event=nearest_auto_event(frame_index, auto_events, candidate_window),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return bool(cv2.imwrite(str(output_path), overlay))


def draw_event_label_overlay(
    frame: np.ndarray,
    *,
    frame_index: int,
    scale: float,
    event_label: str,
    selected_point: tuple[float, float] | None,
    ball_label: dict[str, Any] | None,
    auto_event: dict[str, Any] | None,
) -> np.ndarray:
    """Draw event label context on a frame."""
    color = event_label_color(event_label)
    cv2.putText(frame, f"Frame {frame_index} | label: {event_label}", (24, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 4, cv2.LINE_AA)
    cv2.putText(frame, f"Frame {frame_index} | label: {event_label}", (24, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2, cv2.LINE_AA)
    cv2.putText(frame, "b=bounce h=hit n=no_event u=uncertain s=save k=skip q=quit click=event point", (24, 78), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)
    if ball_label:
        bx = int(round(float(ball_label["x"]) * scale))
        by = int(round(float(ball_label["y"]) * scale))
        cv2.circle(frame, (bx, by), 14, (0, 255, 255), 2)
        cv2.putText(frame, f"ball label f{ball_label['frame_index']}", (bx + 16, by - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)
    if selected_point:
        px = int(round(selected_point[0] * scale))
        py = int(round(selected_point[1] * scale))
        cv2.drawMarker(frame, (px, py), color, cv2.MARKER_TILTED_CROSS, 26, 3, cv2.LINE_AA)
    if auto_event:
        text = f"nearest auto: {auto_event.get('event_type')} f{auto_event.get('frame_index')}"
        cv2.putText(frame, text, (24, 112), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (230, 230, 230), 2, cv2.LINE_AA)
    return frame


def classify_match(event_label: str, confidence: str, auto_event: dict[str, Any] | None) -> tuple[str, str]:
    """Classify one manual label against nearest automatic event."""
    if event_label == "uncertain":
        return "manual_uncertain", "Manual label is uncertain, so it is not a hard mismatch."
    if auto_event is None:
        if event_label == "no_event":
            return "manual_no_event", "Manual no_event label has no nearby automatic event."
        return "no_auto_event_nearby", "No automatic event was near the manual label frame."
    auto_type = str(auto_event.get("event_type") or "").lower()
    if event_label == "no_event":
        if confidence == "low":
            return "manual_no_event", "Low-confidence no_event label is not treated as a hard mismatch."
        if "hit" in auto_type or "bounce" in auto_type:
            return "mismatch", "Manual no_event conflicts with a nearby hit/bounce hypothesis."
        return "manual_no_event", "Manual no_event does not conflict with a strong nearby hit/bounce hypothesis."
    if event_label == "hit":
        if auto_type == "hit":
            return "exact_match", "Manual hit exactly matches automatic hit label."
        if "hit" in auto_type or "ball_near_player" in auto_type or "near_player" in auto_type:
            return "compatible_match", "Manual hit is compatible with nearby possible hit or player interaction cue."
    if event_label == "bounce":
        if auto_type == "bounce":
            return "exact_match", "Manual bounce exactly matches automatic bounce label."
        if "bounce" in auto_type:
            return "compatible_match", "Manual bounce is compatible with nearby possible bounce hypothesis."
    return "mismatch", "Manual event label does not match the nearest automatic hypothesis."


def event_priority(event_type: Any) -> int:
    """Prioritize strong event hypotheses when frames tie."""
    text = str(event_type or "").lower()
    if "hit" in text or "bounce" in text:
        return 0
    if "near_player" in text:
        return 1
    return 2


def count_label(labels: list[dict[str, Any]], label_name: str) -> int:
    """Count a specific manual event label."""
    return sum(1 for label in labels if str(label.get("event_label")) == label_name)


def infer_player_id(event_label: str, auto_event: dict[str, Any]) -> str:
    """Infer player id when interactive labeling does not select one."""
    if event_label in {"bounce", "no_event", "skipped"}:
        return "none"
    player = str(auto_event.get("player_id") or "")
    if player in {"player_a", "player_b"}:
        return player
    return "unknown"


def event_label_color(event_label: str) -> tuple[int, int, int]:
    """Return BGR color for manual event labels."""
    return {
        "bounce": (80, 220, 120),
        "hit": (60, 120, 255),
        "no_event": (190, 190, 190),
        "uncertain": (80, 220, 255),
        "skipped": (120, 120, 120),
    }.get(event_label, (255, 255, 255))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> Path:
    """Write rows to CSV with stable fields."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    return path


def float_or_none(value: Any) -> float | None:
    """Convert value to float when possible."""
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def int_or_none(value: Any) -> int | None:
    """Convert value to int when possible."""
    try:
        if value in (None, ""):
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None
