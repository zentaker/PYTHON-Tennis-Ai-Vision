"""Manual event labeling helpers for Stage 8.2."""

from __future__ import annotations

import csv
import json
import math
import time
from collections import OrderedDict
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
    "source_window_id",
    "event_window_label",
    "notes",
]

EVENT_WINDOW_FIELDS = [
    "window_id",
    "start_frame",
    "end_frame",
    "center_frame",
    "event_label",
    "label_count",
    "source",
    "confidence",
    "visual_group_id",
    "frame_indices",
    "notes",
]

FRAME_DUPLICATE_AUDIT_FIELDS = [
    "frame_index",
    "previous_frame_index",
    "decoded_frame_index",
    "timestamp_ms",
    "visual_diff_from_previous",
    "is_near_duplicate_of_previous",
    "visual_group_id",
    "visual_group_range",
    "representative_frame_index",
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


def dedupe_sorted_frame_indices(frame_indices: list[int]) -> tuple[list[int], int]:
    """Return sorted unique frame indices and the number of duplicates removed."""
    sorted_frames = sorted(int(frame) for frame in frame_indices)
    unique_frames: list[int] = []
    seen: set[int] = set()
    duplicates = 0
    for frame in sorted_frames:
        if frame in seen:
            duplicates += 1
            continue
        seen.add(frame)
        unique_frames.append(frame)
    return unique_frames, duplicates


def print_timeline_viewer_controls() -> None:
    """Print timeline viewer controls for the Product Owner."""
    print(
        "\n".join(
            [
                "",
                "EVENT LABELING TIMELINE VIEWER",
                "",
                "Navigation:",
                "  a / left arrow  = previous group in collapsed mode, previous frame in expanded mode",
                "  d / right arrow = next group in collapsed mode, next frame in expanded mode",
                "  page keys or A/D = jump 10 frames if supported",
                "  g / G = first / last frame in current visual group",
                "  [ / ] = previous / next visual group",
                "",
                "Labels:",
                "  b = bounce_window in collapsed mode, bounce frame in expanded mode",
                "  h = hit_window in collapsed mode, hit frame in expanded mode",
                "  n = no_event_window in collapsed mode, no_event frame in expanded mode",
                "  u = uncertain_window in collapsed mode, uncertain frame in expanded mode",
                "  x = delete current group/window label in collapsed mode",
                "  w = start/end manual event window selection",
                "  W = select current visual group as event window",
                "",
                "Point:",
                "  left click = set event point",
                "",
                "Overlays:",
                "  o = toggle all overlays",
                "  p = toggle event point marker",
                "  l = toggle label text",
                "  m = toggle automatic ball marker overlay",
                "",
                "Save:",
                "  s = save labels",
                "  q = save and quit",
                "",
                "Default:",
                "  automatic ball marker overlay is OFF.",
                "  collapse-duplicates mode labels visual groups as event windows.",
                "",
            ]
        )
    )


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
                    "source_window_id": row.get("source_window_id") or "",
                    "event_window_label": str(row.get("event_window_label") or "").lower() in {"true", "1", "yes"},
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


def read_manual_event_windows(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Read Stage 8.2 manually created event windows."""
    if not path.exists():
        return [], []
    rows: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            start = int_or_none(row.get("start_frame"))
            end = int_or_none(row.get("end_frame"))
            if start is None or end is None:
                continue
            frames_text = row.get("frame_indices") or ""
            rows.append(
                {
                    "window_id": row.get("window_id") or f"manual_window_{len(rows) + 1:03d}",
                    "start_frame": start,
                    "end_frame": end,
                    "center_frame": int_or_none(row.get("center_frame")) or int(round((start + end) / 2)),
                    "event_label": row.get("event_label") or "uncertain_window",
                    "label_count": int_or_none(row.get("label_count")) or len([item for item in frames_text.split(",") if item.strip()]) or (end - start + 1),
                    "source": row.get("source") or "stage_8_2_manual_window",
                    "confidence": row.get("confidence") or "medium",
                    "visual_group_id": row.get("visual_group_id") or "",
                    "frame_indices": frames_text,
                    "notes": row.get("notes") or "",
                }
            )
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


def compute_frame_signature(frame: np.ndarray, *, signature_width: int = 160) -> np.ndarray:
    """Compute a lightweight grayscale visual signature for a frame."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape[:2]
    safe_width = max(16, int(signature_width))
    safe_height = max(8, int(round((height / max(width, 1)) * safe_width)))
    small = cv2.resize(gray, (safe_width, safe_height), interpolation=cv2.INTER_AREA)
    return small.astype(np.float32) / 255.0


def compute_frame_difference(previous_signature: np.ndarray | None, signature: np.ndarray) -> float | None:
    """Compute mean absolute signature difference from the previous frame."""
    if previous_signature is None:
        return None
    return float(np.mean(np.abs(signature - previous_signature)))


def load_frame_payloads_sequential(
    video_path: Path,
    frame_indices: list[int],
    *,
    resize_width: int,
    signature_width: int = 160,
    keep_display: bool = True,
) -> tuple[dict[int, dict[str, Any]], list[str]]:
    """Load selected frames by reading sequentially through the requested range."""
    warnings: list[str] = []
    payloads: dict[int, dict[str, Any]] = {}
    if not frame_indices:
        return payloads, warnings
    requested = set(int(frame) for frame in frame_indices)
    min_frame, max_frame = min(requested), max(requested)
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        return payloads, [f"Video could not be opened for sequential read: {video_path}"]
    try:
        capture.set(cv2.CAP_PROP_POS_FRAMES, min_frame)
        current = min_frame
        while current <= max_frame:
            ok, frame = capture.read()
            if not ok or frame is None:
                warnings.append(f"Sequential read stopped before frame {current}.")
                break
            decoded_position = capture.get(cv2.CAP_PROP_POS_FRAMES)
            timestamp_ms = capture.get(cv2.CAP_PROP_POS_MSEC)
            if current in requested:
                display, scale = resize_frame(frame, resize_width) if keep_display else (None, 1.0)
                original_h, original_w = frame.shape[:2]
                signature_start = time.perf_counter()
                signature = compute_frame_signature(frame, signature_width=signature_width)
                signature_seconds = time.perf_counter() - signature_start
                payloads[current] = {
                    "frame_index": current,
                    "decoded_frame_index": int(round(decoded_position - 1)) if decoded_position and decoded_position >= 1 else None,
                    "timestamp_ms": round(float(timestamp_ms), 3) if timestamp_ms is not None else None,
                    "display": display,
                    "scale": scale,
                    "original_width": original_w,
                    "original_height": original_h,
                    "signature": signature,
                    "signature_compute_seconds": signature_seconds,
                }
            current += 1
    finally:
        capture.release()
    missing = sorted(requested - set(payloads))
    if missing:
        warnings.append(f"Sequential read missed {len(missing)} requested frame(s): {missing[:10]}")
    return payloads, warnings


def load_frame_payload_random(
    video_path: Path,
    frame_index: int,
    *,
    resize_width: int,
    signature_width: int = 160,
    keep_display: bool = True,
) -> tuple[dict[str, Any] | None, str | None]:
    """Load one selected frame by direct seeking."""
    frame, frame_error = load_frame_at_index(video_path, frame_index)
    if frame_error or frame is None:
        return None, frame_error or f"Could not load frame {frame_index}."
    display, scale = resize_frame(frame, resize_width) if keep_display else (None, 1.0)
    original_h, original_w = frame.shape[:2]
    signature_start = time.perf_counter()
    signature = compute_frame_signature(frame, signature_width=signature_width)
    signature_seconds = time.perf_counter() - signature_start
    return {
        "frame_index": frame_index,
        "decoded_frame_index": None,
        "timestamp_ms": None,
        "display": display,
        "scale": scale,
        "original_width": original_w,
        "original_height": original_h,
        "signature": signature,
        "signature_compute_seconds": signature_seconds,
    }, None


def build_visual_frame_groups(payloads_by_frame: dict[int, dict[str, Any]], frame_indices: list[int], *, duplicate_threshold: float) -> tuple[list[dict[str, Any]], dict[int, dict[str, Any]]]:
    """Build per-frame visual difference rows and visual group metadata."""
    rows: list[dict[str, Any]] = []
    previous_signature: np.ndarray | None = None
    previous_frame: int | None = None
    group_id = 0
    for frame_index in frame_indices:
        payload = payloads_by_frame.get(frame_index)
        if payload is None:
            continue
        diff = compute_frame_difference(previous_signature, payload["signature"])
        is_duplicate = bool(diff is not None and diff <= duplicate_threshold)
        if previous_signature is None or not is_duplicate:
            group_id += 1
        rows.append(
            {
                "frame_index": frame_index,
                "previous_frame_index": previous_frame,
                "decoded_frame_index": payload.get("decoded_frame_index"),
                "timestamp_ms": payload.get("timestamp_ms"),
                "visual_diff_from_previous": round(diff, 6) if diff is not None else None,
                "is_near_duplicate_of_previous": is_duplicate,
                "visual_group_id": f"visual_group_{group_id:03d}",
                "visual_group_range": "",
            }
        )
        previous_signature = payload["signature"]
        previous_frame = frame_index
    groups_by_id: dict[str, list[int]] = {}
    for row in rows:
        groups_by_id.setdefault(str(row["visual_group_id"]), []).append(int(row["frame_index"]))
    group_meta: dict[int, dict[str, Any]] = {}
    for row in rows:
        frames = groups_by_id[str(row["visual_group_id"])]
        representative = frames[len(frames) // 2]
        group_range = f"{min(frames)}-{max(frames)}" if min(frames) != max(frames) else str(frames[0])
        row["visual_group_range"] = group_range
        row["representative_frame_index"] = representative
        group_meta[int(row["frame_index"])] = {
            "visual_group_id": row["visual_group_id"],
            "start_frame": min(frames),
            "end_frame": max(frames),
            "representative_frame_index": representative,
            "frame_indices": frames,
            "visual_group_range": group_range,
            "visual_diff_from_previous": row["visual_diff_from_previous"],
            "is_near_duplicate_of_previous": row["is_near_duplicate_of_previous"],
        }
    return rows, group_meta


def analyze_frame_duplicates(
    *,
    video_path: Path,
    frame_indices: list[int],
    resize_width: int,
    duplicate_threshold: float,
    sequential_read: bool,
    signature_width: int = 160,
    keep_display: bool = True,
) -> tuple[list[dict[str, Any]], dict[int, dict[str, Any]], dict[int, dict[str, Any]], list[str], dict[str, Any]]:
    """Load selected frames and analyze near-duplicate visual groups."""
    warnings: list[str] = []
    unique_frames, _duplicates_removed = dedupe_sorted_frame_indices(frame_indices)
    load_start = time.perf_counter()
    if sequential_read:
        payloads, seq_warnings = load_frame_payloads_sequential(
            video_path,
            unique_frames,
            resize_width=resize_width,
            signature_width=signature_width,
            keep_display=keep_display,
        )
        warnings.extend(seq_warnings)
    else:
        payloads = {}
        for frame_index in unique_frames:
            payload, error = load_frame_payload_random(
                video_path,
                frame_index,
                resize_width=resize_width,
                signature_width=signature_width,
                keep_display=keep_display,
            )
            if payload:
                payloads[frame_index] = payload
            elif error:
                warnings.append(error)
    frame_loading_seconds = time.perf_counter() - load_start
    grouping_start = time.perf_counter()
    rows, group_meta = build_visual_frame_groups(payloads, unique_frames, duplicate_threshold=duplicate_threshold)
    grouping_seconds = time.perf_counter() - grouping_start
    profile = {
        "frame_loading_seconds": round(frame_loading_seconds, 3),
        "signature_compute_seconds": round(sum(float(payload.get("signature_compute_seconds") or 0) for payload in payloads.values()), 3),
        "grouping_seconds": round(grouping_seconds, 3),
    }
    return rows, group_meta, payloads, warnings, profile


def write_frame_duplicate_audit(
    output_dir: Path,
    rows: list[dict[str, Any]],
    *,
    duplicate_threshold: float,
    sequential_read: bool,
    signature_width: int,
    audit_runtime_seconds: float,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write frame duplicate audit CSV/Markdown and return summary."""
    csv_path = output_dir / "frame_duplicate_audit.csv"
    json_path = output_dir / "frame_duplicate_audit.json"
    md_path = output_dir / "frame_duplicate_audit.md"
    near_duplicate_pairs = sum(1 for row in rows if row.get("is_near_duplicate_of_previous"))
    groups: dict[str, list[int]] = {}
    for row in rows:
        groups.setdefault(str(row.get("visual_group_id")), []).append(int(row["frame_index"]))
    multi_groups = {group_id: frames for group_id, frames in groups.items() if len(frames) > 1}
    largest = max((frames for frames in groups.values()), key=len, default=[])
    summary = {
        "total_frames": len(rows),
        "unique_visual_groups": len(groups),
        "near_duplicate_pairs_count": near_duplicate_pairs,
        "visual_groups_with_more_than_one_frame": len(multi_groups),
        "largest_duplicate_group": f"{min(largest)}-{max(largest)}" if len(largest) > 1 else (str(largest[0]) if largest else ""),
        "largest_visual_group": f"{min(largest)}-{max(largest)}" if len(largest) > 1 else (str(largest[0]) if largest else ""),
        "duplicate_threshold": duplicate_threshold,
        "signature_width": signature_width,
        "audit_runtime_seconds": round(audit_runtime_seconds, 3),
        "frame_loading_seconds": (profile or {}).get("frame_loading_seconds", 0),
        "signature_compute_seconds": (profile or {}).get("signature_compute_seconds", 0),
        "grouping_seconds": (profile or {}).get("grouping_seconds", 0),
        "report_write_seconds": 0,
        "sequential_read_used": sequential_read,
        "collapse_duplicates_recommended": near_duplicate_pairs > 0,
        "csv_path": str(csv_path),
        "json_path": str(json_path),
        "markdown_path": str(md_path),
    }

    def audit_markdown() -> list[str]:
        return [
            "# Stage 8.2 Frame Duplicate Audit",
            "",
            "SUMMARY",
            f"  Total frames: {summary['total_frames']}",
            f"  Unique visual groups: {summary['unique_visual_groups']}",
            f"  Near-duplicate pairs: {summary['near_duplicate_pairs_count']}",
            f"  Visual groups with more than one frame: {summary['visual_groups_with_more_than_one_frame']}",
            f"  Largest duplicate group: {summary['largest_duplicate_group'] or 'Not available'}",
            f"  Audit runtime seconds: {summary['audit_runtime_seconds']}",
            f"  Frame loading seconds: {summary['frame_loading_seconds']}",
            f"  Signature compute seconds: {summary['signature_compute_seconds']}",
            f"  Grouping seconds: {summary['grouping_seconds']}",
            f"  Report write seconds: {summary['report_write_seconds']}",
            f"  Signature width: {signature_width}",
            f"  Duplicate threshold: {duplicate_threshold}",
            f"  Sequential read used: {sequential_read}",
            f"  Collapse duplicates recommended: {summary['collapse_duplicates_recommended']}",
            "",
            "RECOMMENDED LABELING APPROACH",
            "  If a bounce or hit spans visually duplicated frames, label it as an event window instead of guessing one exact frame.",
            "  In collapsed timeline viewer mode, press b/h/n/u to label the current visual group as a window.",
        ]

    write_start = time.perf_counter()
    write_csv(csv_path, rows, FRAME_DUPLICATE_AUDIT_FIELDS)
    json_path.write_text(json.dumps({"summary": summary, "frames": rows}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text("\n".join(audit_markdown()) + "\n", encoding="utf-8")
    summary["report_write_seconds"] = round(time.perf_counter() - write_start, 3)
    json_path.write_text(json.dumps({"summary": summary, "frames": rows}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text("\n".join(audit_markdown()) + "\n", encoding="utf-8")
    return summary


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


def collect_event_labels_timeline_viewer(
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
    existing_labels: list[dict[str, Any]],
    show_ball_overlay: bool = False,
    preload: bool = False,
    review_only: bool = False,
    preserve_no_event_points: bool = False,
    cache_size: int = 12,
    duplicate_threshold: float = 0.0006,
    sequential_read: bool = False,
    signature_width: int = 160,
    collapse_duplicates: bool = True,
) -> dict[str, Any]:
    """Let the user review selected frames as an editable timeline."""
    unique_frames, duplicates_removed = dedupe_sorted_frame_indices(frame_indices)
    labels_csv = output_dir / "manual_event_labels.csv"
    labels_json = output_dir / "manual_event_labels.json"
    session_dir = output_dir / "event_label_sessions"
    warnings: list[str] = []
    errors: list[str] = []
    if not unique_frames:
        return {
            "labels": [],
            "deleted_frames": [],
            "frames_shown": 0,
            "frames_loaded": 0,
            "duplicate_frames_removed": duplicates_removed,
            "labels_created": 0,
            "labels_updated": 0,
            "labels_deleted": 0,
            "overlays_default_off": True,
            "ball_overlay_enabled": show_ball_overlay,
            "warnings": warnings,
            "errors": ["No frames were selected for timeline viewer."],
        }

    print_timeline_viewer_controls()
    window_name = "Stage 8.2 Event Labeling Timeline Viewer"
    try:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    except cv2.error as exc:
        return {
            "labels": [],
            "deleted_frames": [],
            "frames_shown": 0,
            "frames_loaded": 0,
            "duplicate_frames_removed": duplicates_removed,
            "labels_created": 0,
            "labels_updated": 0,
            "labels_deleted": 0,
            "overlays_default_off": True,
            "ball_overlay_enabled": show_ball_overlay,
            "warnings": warnings,
            "errors": [f"OpenCV GUI unavailable: {exc}"],
        }

    visual_rows, visual_group_meta, analyzed_payloads, analysis_warnings, _analysis_profile = analyze_frame_duplicates(
        video_path=video_path,
        frame_indices=unique_frames,
        resize_width=resize_width,
        duplicate_threshold=duplicate_threshold,
        sequential_read=sequential_read,
        signature_width=signature_width,
        keep_display=True,
    )
    warnings.extend(analysis_warnings)
    all_frame_indices = [int(row["frame_index"]) for row in visual_rows] or unique_frames
    if collapse_duplicates:
        display_frame_indices: list[int] = []
        seen_groups: set[str] = set()
        for row in visual_rows:
            group_id = str(row["visual_group_id"])
            if group_id in seen_groups:
                continue
            seen_groups.add(group_id)
            group_meta = visual_group_meta[int(row["frame_index"])]
            display_frame_indices.append(int(group_meta.get("representative_frame_index") or group_meta["frame_indices"][0]))
        frames = [{"frame_index": frame_index} for frame_index in display_frame_indices]
    else:
        frames = [{"frame_index": row["frame_index"]} for row in visual_rows] or [{"frame_index": frame_index} for frame_index in unique_frames]
    frame_cache: OrderedDict[int, dict[str, Any]] = OrderedDict()
    for frame_index, payload in analyzed_payloads.items():
        payload = dict(payload)
        payload.pop("signature", None)
        frame_cache[int(frame_index)] = payload
    frames_loaded_count = len(frame_cache)

    def load_payload(index: int) -> dict[str, Any] | None:
        nonlocal frames_loaded_count
        frame_index = int(frames[index]["frame_index"])
        if frame_index in frame_cache:
            payload = frame_cache.pop(frame_index)
            frame_cache[frame_index] = payload
            return payload
        frame, frame_error = load_frame_at_index(video_path, frame_index)
        if frame_error or frame is None:
            message = frame_error or f"Could not load frame {frame_index}."
            if message not in errors:
                errors.append(message)
            return None
        display, scale = resize_frame(frame, resize_width)
        original_h, original_w = frame.shape[:2]
        payload = {
            "frame_index": frame_index,
            "display": display,
            "scale": scale,
            "original_width": original_w,
            "original_height": original_h,
        }
        frame_cache[frame_index] = payload
        frames_loaded_count += 1
        while len(frame_cache) > max(1, cache_size):
            frame_cache.popitem(last=False)
        return payload

    if preload and not analyzed_payloads:
        for preload_index in range(len(frames)):
            load_payload(preload_index)
        if not frame_cache:
            try:
                cv2.destroyWindow(window_name)
            except cv2.error:
                pass
            return {
                "labels": [],
                "deleted_frames": [],
                "frames_shown": 0,
                "frames_loaded": frames_loaded_count,
                "duplicate_frames_removed": duplicates_removed,
                "labels_created": 0,
                "labels_updated": 0,
                "labels_deleted": 0,
                "overlays_default_off": True,
                "point_marker_enabled": False,
                "ball_overlay_enabled": show_ball_overlay,
                "warnings": warnings,
                "errors": errors or ["No selected frames could be loaded."],
            }

    selected_frames = set(all_frame_indices)
    existing_by_frame = {int(label["frame_index"]): dict(label) for label in existing_labels if int(label["frame_index"]) in selected_frames}
    if not preserve_no_event_points:
        for label in existing_by_frame.values():
            if str(label.get("event_label")) == "no_event" and (label.get("x") not in (None, "") or label.get("y") not in (None, "")):
                label["x"] = None
                label["y"] = None
                label["notes"] = append_note(label.get("notes"), "no_event_point_hidden_in_timeline_viewer")
    working_by_frame = {frame: dict(label) for frame, label in existing_by_frame.items()}
    pending_points: dict[int, tuple[float, float]] = {
        frame: (float(label["x"]), float(label["y"]))
        for frame, label in existing_by_frame.items()
        if label.get("x") not in (None, "")
        and label.get("y") not in (None, "")
        and (preserve_no_event_points or str(label.get("event_label")) != "no_event")
    }
    changed_frames: set[int] = set()
    deleted_frames: set[int] = set()
    save_snapshots: list[dict[str, Path]] = []
    existing_windows, window_warnings = read_manual_event_windows(output_dir / "manual_event_windows.csv")
    warnings.extend(window_warnings)
    session_windows: list[dict[str, Any]] = []
    deleted_window_ids: set[str] = set()
    pending_window_start: int | None = None
    pending_window_range: tuple[int, int] | None = None
    current_index = 0
    overlays_enabled = True
    ball_overlay_enabled = show_ball_overlay
    point_marker_enabled = False
    label_text_enabled = True
    unsaved_changes = False
    save_status = "Unsaved changes: no"
    save_status_until = 0.0

    def current_visual_group() -> dict[str, Any]:
        return visual_group_meta.get(current_frame_index(), {"visual_group_id": "", "start_frame": current_frame_index(), "end_frame": current_frame_index(), "frame_indices": [current_frame_index()], "visual_group_range": str(current_frame_index), "visual_diff_from_previous": None, "is_near_duplicate_of_previous": False})

    def current_frame_index() -> int:
        return int(frames[current_index]["frame_index"])

    def current_point() -> tuple[float, float] | None:
        label = working_by_frame.get(current_frame_index())
        if not label or str(label.get("event_label")) == "no_event":
            return None
        return pending_points.get(current_frame_index())

    def current_display_label(frame_index: int) -> dict[str, Any] | None:
        label = working_by_frame.get(frame_index)
        if collapse_duplicates:
            group = current_visual_group()
            start = int(group.get("start_frame", frame_index))
            end = int(group.get("end_frame", frame_index))
            visual_group_id = str(group.get("visual_group_id") or "")
            matching_window = next(
                (
                    window
                    for window in reversed(session_windows)
                    if (
                        int(window.get("start_frame", -1)) == start
                        and int(window.get("end_frame", -1)) == end
                    )
                    or (visual_group_id and str(window.get("visual_group_id") or "") == visual_group_id)
                ),
                None,
            )
            if matching_window is None:
                matching_window = next(
                    (
                        window
                        for window in reversed(existing_windows)
                        if str(window.get("window_id")) not in deleted_window_ids
                        and (
                            int(window.get("start_frame", -1)) == start
                            and int(window.get("end_frame", -1)) == end
                            or (visual_group_id and str(window.get("visual_group_id") or "") == visual_group_id)
                        )
                    ),
                    None,
                )
            if matching_window is not None:
                return {
                    "event_label": matching_window.get("event_label") or "uncertain_window",
                    "confidence": matching_window.get("confidence") or "medium",
                }
        if label and label.get("event_window_label"):
            display = dict(label)
            display["event_label"] = f"{display.get('event_label')}_window"
            return display
        return label

    def session_changed_labels() -> list[dict[str, Any]]:
        return [working_by_frame[frame] for frame in sorted(changed_frames) if frame in working_by_frame and frame not in deleted_frames]

    def save_progress() -> None:
        nonlocal unsaved_changes, save_status, save_status_until
        session_labels = session_changed_labels()
        if review_only:
            save_status = "Review-only mode: labels not saved"
            save_status_until = time.monotonic() + 2.0
            print("Review-only mode: labels not saved.")
            return
        merged = merge_event_labels(existing_labels, session_labels, deleted_frames=sorted(deleted_frames))
        write_event_labels_csv(labels_csv, merged)
        write_event_labels_json(labels_json, merged)
        retained_existing_windows = [window for window in existing_windows if str(window.get("window_id")) not in deleted_window_ids]
        merged_windows = merge_event_windows(retained_existing_windows, session_windows)
        write_manual_event_windows_csv(output_dir / "manual_event_windows.csv", merged_windows)
        write_manual_event_windows_json(output_dir / "manual_event_windows.json", merged_windows)
        if session_labels:
            backup_paths = write_event_label_session_backup(session_dir, label_session, session_labels)
            save_snapshots.append(backup_paths)
        unsaved_changes = False
        save_status = "Saved session changes"
        save_status_until = time.monotonic() + 2.0
        print("Saved current label state. Unsaved changes: 0")

    def on_mouse(event: int, x_value: int, y_value: int, _flags: int, _param: Any) -> None:
        if event != cv2.EVENT_LBUTTONDOWN:
            return
        payload = load_payload(current_index)
        if payload is None:
            return
        scale = float(payload["scale"] or 1.0)
        frame = current_frame_index()
        pending_points[frame] = (x_value / scale, y_value / scale)
        if frame in working_by_frame:
            label = dict(working_by_frame[frame])
            if str(label.get("event_label")) == "no_event" and not preserve_no_event_points:
                pending_points.pop(frame, None)
                return
            label["x"] = round(pending_points[frame][0], 3)
            label["y"] = round(pending_points[frame][1], 3)
            label["notes"] = append_note(label.get("notes"), "event_point_updated_in_timeline_viewer")
            working_by_frame[frame] = label
            changed_frames.add(frame)
            deleted_frames.discard(frame)
            nonlocal_set_unsaved()

    def nonlocal_set_unsaved() -> None:
        nonlocal unsaved_changes, save_status
        unsaved_changes = True
        save_status = "Unsaved changes: yes"

    def apply_window_label(start_frame: int, end_frame: int, event_label: str, visual_group_id: str = "") -> None:
        nonlocal pending_window_range, pending_window_start
        start, end = min(start_frame, end_frame), max(start_frame, end_frame)
        frames_in_window = [frame for frame in all_frame_indices if start <= frame <= end]
        if not frames_in_window:
            frames_in_window = list(range(start, end + 1))
        for existing in existing_windows:
            if int(existing.get("start_frame", -1)) == start and int(existing.get("end_frame", -1)) == end:
                deleted_window_ids.add(str(existing.get("window_id")))
            elif visual_group_id and str(existing.get("visual_group_id") or "") == visual_group_id:
                deleted_window_ids.add(str(existing.get("window_id")))
        session_windows[:] = [
            window
            for window in session_windows
            if not (
                int(window.get("start_frame", -1)) == start
                and int(window.get("end_frame", -1)) == end
                or (visual_group_id and str(window.get("visual_group_id") or "") == visual_group_id)
            )
        ]
        window_id = f"stage_8_2_window_{label_session}_{len(existing_windows) + len(session_windows) + 1:03d}"
        confidence = "low" if event_label == "uncertain" else "high"
        window = {
            "window_id": window_id,
            "start_frame": start,
            "end_frame": end,
            "center_frame": int(round(mean(frames_in_window))),
            "event_label": f"{event_label}_window",
            "label_count": len(frames_in_window),
            "source": "stage_8_2_manual_window",
            "confidence": confidence,
            "visual_group_id": visual_group_id,
            "frame_indices": ",".join(str(frame) for frame in frames_in_window),
            "notes": "Manual event window created in Stage 8.2 timeline viewer.",
        }
        session_windows.append(window)
        for frame in frames_in_window:
            label = build_event_label(
                frame_index=frame,
                event_label=event_label,
                confidence=confidence,
                player_id="auto",
                x=None,
                y=None,
                fps=fps,
                source="stage_8_2_manual",
                label_session=label_session,
                ball_labels=ball_labels,
                auto_events=auto_events,
                candidate_window=candidate_window,
                notes=f"event_window_label=true; source_window_id={window_id}",
            )
            label["source_window_id"] = window_id
            label["event_window_label"] = True
            working_by_frame[frame] = label
            changed_frames.add(frame)
            deleted_frames.discard(frame)
        pending_window_range = None
        pending_window_start = None
        nonlocal_set_unsaved()

    def delete_current_group_label(frame_index: int) -> None:
        group = current_visual_group()
        if collapse_duplicates:
            start = int(group.get("start_frame", frame_index))
            end = int(group.get("end_frame", frame_index))
            frames_in_group = [frame for frame in all_frame_indices if start <= frame <= end] or [frame_index]
            visual_group_id = str(group.get("visual_group_id") or "")
            for existing in existing_windows:
                if int(existing.get("start_frame", -1)) == start and int(existing.get("end_frame", -1)) == end:
                    deleted_window_ids.add(str(existing.get("window_id")))
                elif visual_group_id and str(existing.get("visual_group_id") or "") == visual_group_id:
                    deleted_window_ids.add(str(existing.get("window_id")))
            session_windows[:] = [
                window
                for window in session_windows
                if not (
                    int(window.get("start_frame", -1)) == start
                    and int(window.get("end_frame", -1)) == end
                    or (visual_group_id and str(window.get("visual_group_id") or "") == visual_group_id)
                )
            ]
        else:
            frames_in_group = [frame_index]
        for frame in frames_in_group:
            working_by_frame.pop(frame, None)
            pending_points.pop(frame, None)
            changed_frames.discard(frame)
            if frame in existing_by_frame:
                deleted_frames.add(frame)
        nonlocal_set_unsaved()

    cv2.setMouseCallback(window_name, on_mouse)
    frames_shown = 0
    try:
        while True:
            payload = load_payload(current_index)
            if payload is None:
                key = cv2.waitKeyEx(0)
                if key in {ord("q"), 27}:
                    save_progress()
                    break
                current_index = min(len(frames) - 1, current_index + 1)
                continue
            frame_index = int(payload["frame_index"])
            label = current_display_label(frame_index)
            shown = draw_timeline_viewer_overlay(
                payload["display"].copy(),
                frame_index=frame_index,
                position=current_index + 1,
                total=len(frames),
                scale=float(payload["scale"]),
                label=label,
                selected_point=current_point(),
                show_point_marker=overlays_enabled and point_marker_enabled,
                ball_label=nearest_ball_label(frame_index, ball_labels, candidate_window) if overlays_enabled and ball_overlay_enabled else None,
                auto_event=nearest_auto_event(frame_index, auto_events, candidate_window) if overlays_enabled else None,
                overlays_enabled=overlays_enabled,
                label_text_enabled=label_text_enabled,
                unsaved_changes=unsaved_changes,
                save_status=save_status if time.monotonic() < save_status_until else "",
                fps=fps,
                visual_group=current_visual_group(),
                event_windows_count=len(existing_windows) + len(session_windows),
                collapsed_mode=collapse_duplicates,
            )
            if collapse_duplicates:
                group = current_visual_group()
                cv2.setWindowTitle(window_name, f"Frame group {group.get('visual_group_range')} ({current_index + 1}/{len(frames)})")
            else:
                cv2.setWindowTitle(window_name, f"Frame {frame_index} ({current_index + 1}/{len(frames)})")
            cv2.imshow(window_name, shown)
            frames_shown += 1
            key = cv2.waitKeyEx(0)
            if key in {ord("d"), 83, 2555904}:
                current_index = min(len(frames) - 1, current_index + 1)
            elif key in {ord("a"), 81, 2424832}:
                current_index = max(0, current_index - 1)
            elif key in {ord("D"), 2228224}:
                current_index = min(len(frames) - 1, current_index + 10)
            elif key in {ord("A"), 2162688}:
                current_index = max(0, current_index - 10)
            elif key in {2359296}:
                current_index = 0
            elif key in {2293760}:
                current_index = len(frames) - 1
            elif key == ord("g"):
                start = int(current_visual_group().get("start_frame", frame_index))
                current_index = next((idx for idx, row in enumerate(frames) if int(row["frame_index"]) == start), current_index)
            elif key == ord("G"):
                end = int(current_visual_group().get("end_frame", frame_index))
                current_index = next((idx for idx, row in enumerate(frames) if int(row["frame_index"]) == end), current_index)
            elif key == ord("]"):
                group_id = current_visual_group().get("visual_group_id")
                current_index = next((idx for idx, row in enumerate(frames) if idx > current_index and visual_group_meta.get(int(row["frame_index"]), {}).get("visual_group_id") != group_id), current_index)
            elif key == ord("["):
                group_id = current_visual_group().get("visual_group_id")
                for idx in range(current_index - 1, -1, -1):
                    if visual_group_meta.get(int(frames[idx]["frame_index"]), {}).get("visual_group_id") != group_id:
                        current_index = idx
                        break
            elif key == ord("W"):
                group = current_visual_group()
                pending_window_range = (int(group.get("start_frame", frame_index)), int(group.get("end_frame", frame_index)))
                save_status = f"Window selected {pending_window_range[0]}-{pending_window_range[1]}; press b/h/n/u"
                save_status_until = time.monotonic() + 4.0
            elif key == ord("w"):
                if pending_window_start is None:
                    pending_window_start = frame_index
                    save_status = f"Window start set {frame_index}; move and press w again"
                    save_status_until = time.monotonic() + 4.0
                else:
                    pending_window_range = (pending_window_start, frame_index)
                    save_status = f"Window selected {min(pending_window_range)}-{max(pending_window_range)}; press b/h/n/u"
                    save_status_until = time.monotonic() + 4.0
            elif key in {ord("b"), ord("h"), ord("n"), ord("u")}:
                event_label = {ord("b"): "bounce", ord("h"): "hit", ord("n"): "no_event", ord("u"): "uncertain"}[key]
                group = current_visual_group()
                if pending_window_range is not None:
                    apply_window_label(pending_window_range[0], pending_window_range[1], event_label, str(group.get("visual_group_id") or ""))
                    continue
                if collapse_duplicates:
                    apply_window_label(int(group["start_frame"]), int(group["end_frame"]), event_label, str(group.get("visual_group_id") or ""))
                    continue
                confidence = "low" if event_label == "uncertain" else "high"
                point = pending_points.get(frame_index)
                if event_label == "no_event" and not preserve_no_event_points:
                    point = None
                    pending_points.pop(frame_index, None)
                label = build_event_label(
                    frame_index=frame_index,
                    event_label=event_label,
                    confidence=confidence,
                    player_id="auto",
                    x=point[0] if point else None,
                    y=point[1] if point else None,
                    fps=fps,
                    source="stage_8_2_manual",
                    label_session=label_session,
                    ball_labels=ball_labels,
                    auto_events=auto_events,
                    candidate_window=candidate_window,
                    notes=f"timeline_viewer=true; original_width={payload['original_width']}; original_height={payload['original_height']}",
                )
                working_by_frame[frame_index] = label
                changed_frames.add(frame_index)
                deleted_frames.discard(frame_index)
                nonlocal_set_unsaved()
            elif key == ord("x"):
                delete_current_group_label(frame_index)
            elif key == ord("c"):
                pending_points.pop(frame_index, None)
                if frame_index in working_by_frame:
                    label = dict(working_by_frame[frame_index])
                    label["x"] = None
                    label["y"] = None
                    label["notes"] = append_note(label.get("notes"), "event_point_cleared_in_timeline_viewer")
                    working_by_frame[frame_index] = label
                    changed_frames.add(frame_index)
                    nonlocal_set_unsaved()
            elif key == ord("o"):
                overlays_enabled = not overlays_enabled
            elif key == ord("p"):
                point_marker_enabled = not point_marker_enabled
            elif key == ord("m"):
                ball_overlay_enabled = not ball_overlay_enabled
            elif key == ord("l"):
                label_text_enabled = not label_text_enabled
            elif key == ord("?"):
                print_timeline_viewer_controls()
            elif key == ord("s"):
                save_progress()
            elif key in {ord("q"), 27}:
                save_progress()
                break
    finally:
        try:
            cv2.destroyWindow(window_name)
        except cv2.error:
            pass

    changed_labels = session_changed_labels()
    initial_existing = set(existing_by_frame)
    labels_created = sum(1 for label in changed_labels if int(label["frame_index"]) not in initial_existing)
    labels_updated = sum(1 for label in changed_labels if int(label["frame_index"]) in initial_existing)
    session_backup_path = ""
    if save_snapshots:
        session_backup_path = str(save_snapshots[-1].get("csv", ""))
    return {
        "labels": changed_labels,
        "deleted_frames": sorted(deleted_frames),
        "event_windows": session_windows,
        "event_windows_created": len(session_windows),
        "event_windows_updated": 0,
        "frames_shown": frames_shown,
        "frames_loaded": frames_loaded_count,
        "duplicate_frames_removed": duplicates_removed,
        "near_duplicate_pairs": sum(1 for row in visual_rows if row.get("is_near_duplicate_of_previous")),
        "visual_groups_count": len({row.get("visual_group_id") for row in visual_rows}),
        "frame_duplicate_analysis_enabled": True,
        "sequential_read_used": sequential_read,
        "collapse_duplicates": collapse_duplicates,
        "display_items_count": len(frames),
        "labels_created": labels_created,
        "labels_updated": labels_updated,
        "labels_deleted": len(deleted_frames),
        "overlays_default_off": True,
        "point_marker_enabled": point_marker_enabled,
        "ball_overlay_enabled": ball_overlay_enabled,
        "review_only": review_only,
        "preload": preload,
        "session_backup_path": session_backup_path,
        "warnings": warnings,
        "errors": errors,
    }


def merge_event_labels(
    existing_labels: list[dict[str, Any]],
    new_labels: list[dict[str, Any]],
    *,
    deleted_frames: list[int] | None = None,
) -> list[dict[str, Any]]:
    """Merge event labels by frame, preferring newest Stage 8.2 labels."""
    deleted = {int(frame) for frame in (deleted_frames or [])}
    by_frame: dict[int, dict[str, Any]] = {}
    for label in existing_labels:
        frame = int(label["frame_index"])
        if frame not in deleted:
            by_frame[frame] = dict(label)
    for label in new_labels:
        frame = int(label["frame_index"])
        if frame in deleted:
            continue
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


def write_manual_event_windows_csv(path: Path, windows: list[dict[str, Any]]) -> Path:
    """Write Stage 8.2 manual event windows to CSV."""
    return write_csv(path, windows, EVENT_WINDOW_FIELDS)


def write_manual_event_windows_json(path: Path, windows: list[dict[str, Any]]) -> Path:
    """Write Stage 8.2 manual event windows to JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(windows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def merge_event_windows(existing_windows: list[dict[str, Any]], new_windows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge event windows by window id."""
    by_id = {str(window.get("window_id")): dict(window) for window in existing_windows}
    for window in new_windows:
        by_id[str(window.get("window_id"))] = dict(window)
    return [by_id[key] for key in sorted(by_id)]


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


def draw_timeline_viewer_overlay(
    frame: np.ndarray,
    *,
    frame_index: int,
    position: int,
    total: int,
    scale: float,
    label: dict[str, Any] | None,
    selected_point: tuple[float, float] | None,
    show_point_marker: bool,
    ball_label: dict[str, Any] | None,
    auto_event: dict[str, Any] | None,
    overlays_enabled: bool,
    label_text_enabled: bool,
    unsaved_changes: bool,
    save_status: str,
    fps: float | None,
    visual_group: dict[str, Any],
    event_windows_count: int,
    collapsed_mode: bool = False,
) -> np.ndarray:
    """Draw unobtrusive timeline viewer context on a frame."""
    event_label = str(label.get("event_label")) if label else "unlabeled"
    color = event_label_color(event_label)
    height, width = frame.shape[:2]
    if label_text_enabled:
        cv2.rectangle(frame, (0, 0), (width, 42), (0, 0, 0), -1)
        cv2.rectangle(frame, (0, max(0, height - 42)), (width, height), (0, 0, 0), -1)
        group_range = visual_group.get("visual_group_range") or str(frame_index)
        group_frames = visual_group.get("frame_indices") or [frame_index]
        group_size = len(group_frames)
        if collapsed_mode:
            label_text = f"Frame group {group_range} | group {position}/{total} | size {group_size} | representative frame: {frame_index} | label: {event_label}"
            if group_size > 1:
                label_text += " | label as window"
        elif group_size > 1:
            label_text = f"Frame group {group_range} | group {position}/{total} | size {group_size} | representative frame: {frame_index} | label: {event_label}"
        else:
            label_text = f"Frame {frame_index} | {position}/{total} | label: {event_label}"
        if fps:
            label_text += f" | t={frame_index / fps:.2f}s"
        diff = visual_group.get("visual_diff_from_previous")
        diff_text = "n/a" if diff in (None, "") else f"{float(diff):.3f}"
        label_text += f" | diff prev: {diff_text}"
        if str(group_range) != str(frame_index):
            label_text += f" | visual group: {group_range}"
        point_status = "point hidden" if selected_point and not show_point_marker else ("point set for this frame" if selected_point else "no point")
        label_text += f" | {point_status} | windows: {event_windows_count} | unsaved: {'yes' if unsaved_changes else 'no'}"
        cv2.putText(frame, label_text, (18, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.62, color, 2, cv2.LINE_AA)
        if save_status:
            controls = save_status
        elif collapsed_mode:
            controls = "a/d prev/next group | b bounce_window | h hit_window | n no_event_window | u uncertain_window | x delete window | s save | q save+quit"
            if group_size > 1:
                controls = "Near-duplicate group. Label this as a window. " + controls
        elif group_size > 1:
            controls = "Near-duplicate group. W selects group window | a/d prev/next frame | q save+quit"
        else:
            controls = "a/d prev/next | b bounce | h hit | n no_event | u uncertain | x delete | s save | q save+quit"
        cv2.putText(frame, controls, (18, height - 14), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (235, 235, 235), 1, cv2.LINE_AA)
    if selected_point and show_point_marker:
        px = int(round(selected_point[0] * scale))
        py = int(round(selected_point[1] * scale))
        cv2.drawMarker(frame, (px, py), color, cv2.MARKER_TILTED_CROSS, 12, 1, cv2.LINE_AA)
    if overlays_enabled and ball_label:
        bx = int(round(float(ball_label["x"]) * scale))
        by = int(round(float(ball_label["y"]) * scale))
        cv2.circle(frame, (bx, by), 8, (0, 210, 255), 1)
    if overlays_enabled and auto_event and label_text_enabled:
        text = f"auto: {auto_event.get('event_type')} f{auto_event.get('frame_index')}"
        cv2.putText(frame, text, (18, 64), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (210, 210, 210), 1, cv2.LINE_AA)
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


def append_note(existing: Any, note: str) -> str:
    """Append a note to the semicolon-separated notes field."""
    text = str(existing or "").strip()
    return "; ".join(item for item in [text, note] if item)


def audit_event_labels(
    labels: list[dict[str, Any]],
    *,
    selected_frames: list[int] | None = None,
) -> dict[str, Any]:
    """Audit manual event labels for stale points and duplicate frame rows."""
    warnings: list[str] = []
    frame_counts: dict[int, int] = {}
    for label in labels:
        frame = int(label["frame_index"])
        frame_counts[frame] = frame_counts.get(frame, 0) + 1

    selected_set = {int(frame) for frame in selected_frames or []}
    suspicious_no_event_points = []
    labels_without_point = []
    labels_outside_selected = []
    point_rows: list[tuple[int, str, tuple[float, float]]] = []
    for label in labels:
        frame = int(label["frame_index"])
        event_label = str(label.get("event_label") or "")
        has_point = label.get("x") not in (None, "") and label.get("y") not in (None, "")
        if event_label == "no_event" and has_point:
            suspicious_no_event_points.append(frame)
        if event_label in {"bounce", "hit"} and not has_point:
            labels_without_point.append(frame)
        if selected_set and frame not in selected_set:
            labels_outside_selected.append(frame)
        if has_point:
            point_rows.append((frame, event_label, (round(float(label["x"]), 2), round(float(label["y"]), 2))))

    repeated_sequences: list[dict[str, Any]] = []
    sorted_points = sorted(point_rows, key=lambda item: item[0])
    sequence_start: int | None = None
    previous_frame: int | None = None
    previous_point: tuple[float, float] | None = None
    sequence_frames: list[int] = []
    for frame, _event_label, point in sorted_points:
        if previous_frame is not None and previous_point == point and frame - previous_frame <= 1:
            if sequence_start is None:
                sequence_start = previous_frame
                sequence_frames = [previous_frame]
            sequence_frames.append(frame)
        else:
            if sequence_start is not None and len(sequence_frames) > 1:
                repeated_sequences.append({"start_frame": sequence_start, "end_frame": sequence_frames[-1], "point": previous_point, "frames": sequence_frames})
            sequence_start = None
            sequence_frames = []
        previous_frame = frame
        previous_point = point
    if sequence_start is not None and len(sequence_frames) > 1:
        repeated_sequences.append({"start_frame": sequence_start, "end_frame": sequence_frames[-1], "point": previous_point, "frames": sequence_frames})

    duplicate_frames = sorted(frame for frame, count in frame_counts.items() if count > 1)
    if suspicious_no_event_points:
        warnings.append("Some no_event labels still have x/y event points.")
    if repeated_sequences:
        warnings.append("Some consecutive labels reuse identical event points.")
    if duplicate_frames:
        warnings.append("Duplicate frame labels were found.")
    if labels_without_point:
        warnings.append("Some bounce/hit labels do not have event points.")

    return {
        "labels_count": len(labels),
        "suspicious_no_event_points_count": len(suspicious_no_event_points),
        "suspicious_no_event_point_frames": suspicious_no_event_points,
        "repeated_point_sequences_count": len(repeated_sequences),
        "repeated_point_sequences": repeated_sequences,
        "duplicate_frame_labels_count": len(duplicate_frames),
        "duplicate_frame_label_frames": duplicate_frames,
        "labels_outside_selected_frame_range_count": len(labels_outside_selected),
        "labels_outside_selected_frame_range": labels_outside_selected,
        "labels_without_point_count": len(labels_without_point),
        "labels_without_point_frames": labels_without_point,
        "no_event_labels_with_event_point_count": len(suspicious_no_event_points),
        "cleaned_no_event_points_count": 0,
        "warnings": warnings,
        "recommended_fixes": build_integrity_recommendations(
            suspicious_no_event_points=suspicious_no_event_points,
            repeated_sequences=repeated_sequences,
            duplicate_frames=duplicate_frames,
            labels_without_point=labels_without_point,
        ),
    }


def clean_event_labels_for_integrity(
    labels: list[dict[str, Any]],
    *,
    preserve_no_event_points: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Clean duplicate rows and no_event points while preserving newest labels."""
    by_frame: dict[int, dict[str, Any]] = {}
    duplicate_frame_labels_count = 0
    cleaned_no_event_points_count = 0
    for label in labels:
        frame = int(label["frame_index"])
        if frame in by_frame:
            duplicate_frame_labels_count += 1
        row = dict(label)
        if str(row.get("event_label")) == "no_event" and not preserve_no_event_points and (row.get("x") not in (None, "") or row.get("y") not in (None, "")):
            row["x"] = None
            row["y"] = None
            row["notes"] = append_note(row.get("notes"), "no_event_point_cleared_by_integrity_fix")
            cleaned_no_event_points_count += 1
        by_frame[frame] = row
    return [by_frame[frame] for frame in sorted(by_frame)], {
        "duplicate_frame_labels_removed": duplicate_frame_labels_count,
        "cleaned_no_event_points_count": cleaned_no_event_points_count,
    }


def write_event_label_integrity_reports(output_dir: Path, audit: dict[str, Any]) -> dict[str, Path]:
    """Write JSON and Markdown label integrity reports."""
    json_path = output_dir / "event_label_integrity_report.json"
    md_path = output_dir / "event_label_integrity_report.md"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Stage 8.2 Event Label Integrity Report",
        "",
        "SUMMARY",
        f"  Labels audited: {audit.get('labels_count')}",
        f"  no_event labels with points: {audit.get('suspicious_no_event_points_count')}",
        f"  Repeated point sequences: {audit.get('repeated_point_sequences_count')}",
        f"  Duplicate frame labels: {audit.get('duplicate_frame_labels_count')}",
        f"  Bounce/hit labels without point: {audit.get('labels_without_point_count')}",
        f"  Cleaned no_event points: {audit.get('cleaned_no_event_points_count')}",
        "",
        "WARNINGS",
    ]
    lines.extend([f"  - {item}" for item in audit.get("warnings", [])] or ["  No warnings."])
    lines.extend(["", "RECOMMENDED FIXES"])
    lines.extend([f"  - {item}" for item in audit.get("recommended_fixes", [])] or ["  No fixes recommended."])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": json_path, "markdown": md_path}


def build_integrity_recommendations(
    *,
    suspicious_no_event_points: list[int],
    repeated_sequences: list[dict[str, Any]],
    duplicate_frames: list[int],
    labels_without_point: list[int],
) -> list[str]:
    """Build plain-language recommendations from audit findings."""
    recommendations: list[str] = []
    if suspicious_no_event_points:
        recommendations.append("Run --audit-labels --fix-labels to clear points from no_event labels.")
    if duplicate_frames:
        recommendations.append("Run --audit-labels --fix-labels to preserve newest labels for duplicate frames.")
    if repeated_sequences:
        recommendations.append("Review repeated point sequences; they may indicate stale point carryover.")
    if labels_without_point:
        recommendations.append("Review bounce/hit labels without points when precise event location matters.")
    return recommendations


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
