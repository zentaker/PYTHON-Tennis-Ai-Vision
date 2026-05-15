"""Stage 8.2R event labeling workbench helpers."""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Any

import cv2

from tennis_vision.ball_labeling import load_frame_at_index
from tennis_vision.ball_tracking_probe import resize_frame
from tennis_vision.event_contact_labels import (
    audit_label_integrity,
    build_contact_candidate,
    build_event_window,
    export_compatibility,
    load_contact_candidates,
    load_event_windows,
    save_contact_candidates,
    save_event_windows,
    write_integrity_report,
)


def frame_indices(start_frame: int, end_frame: int) -> list[int]:
    start, end = min(int(start_frame), int(end_frame)), max(int(start_frame), int(end_frame))
    return list(range(start, end + 1))


def cache_dir_for(output_dir: Path, start_frame: int, end_frame: int, resize_width: int) -> Path:
    return output_dir / "frame_cache" / f"frames_{start_frame}_{end_frame}_w{resize_width}"


def cache_metadata_path(cache_dir: Path) -> Path:
    return cache_dir / "cache_metadata.json"


def clear_cache(output_dir: Path) -> None:
    cache_root = output_dir / "frame_cache"
    if cache_root.exists():
        shutil.rmtree(cache_root)


def cache_is_valid(cache_dir: Path, *, start_frame: int, end_frame: int, resize_width: int, video_path: Path) -> bool:
    meta_path = cache_metadata_path(cache_dir)
    if not meta_path.exists():
        return False
    try:
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    if metadata.get("start_frame") != start_frame or metadata.get("end_frame") != end_frame:
        return False
    if metadata.get("resize_width") != resize_width or metadata.get("video_path") != str(video_path):
        return False
    expected = frame_indices(start_frame, end_frame)
    return all((cache_dir / f"frame_{frame:06d}.jpg").exists() for frame in expected)


def build_frame_cache(
    video_path: Path,
    output_dir: Path,
    *,
    start_frame: int,
    end_frame: int,
    resize_width: int = 1280,
    force: bool = False,
) -> tuple[dict[str, Any], list[str]]:
    """Build or reuse a clean resized frame cache."""
    start_time = time.perf_counter()
    warnings: list[str] = []
    cache_dir = cache_dir_for(output_dir, start_frame, end_frame, resize_width)
    if force and cache_dir.exists():
        shutil.rmtree(cache_dir)
    if cache_is_valid(cache_dir, start_frame=start_frame, end_frame=end_frame, resize_width=resize_width, video_path=video_path):
        metadata = json.loads(cache_metadata_path(cache_dir).read_text(encoding="utf-8"))
        metadata["cache_status"] = "reused"
        metadata["cache_build_seconds"] = 0
        return metadata, warnings
    cache_dir.mkdir(parents=True, exist_ok=True)
    frames_written = 0
    metadata_frames: list[dict[str, Any]] = []
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        warnings.append(f"Video could not be opened for cache build: {video_path}")
    else:
        try:
            capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            for frame_index in frame_indices(start_frame, end_frame):
                ok, frame = capture.read()
                if not ok or frame is None:
                    warnings.append(f"Sequential cache decode stopped before frame {frame_index}.")
                    break
                display, _scale = resize_frame(frame, resize_width)
                output_path = cache_dir / f"frame_{frame_index:06d}.jpg"
                if cv2.imwrite(str(output_path), display):
                    frames_written += 1
                    metadata_frames.append(
                        {
                            "frame_index": frame_index,
                            "cache_path": str(output_path),
                            "timestamp_ms": round(float(capture.get(cv2.CAP_PROP_POS_MSEC) or 0.0), 3),
                        }
                    )
        finally:
            capture.release()
    metadata = {
        "cache_status": "built",
        "video_path": str(video_path),
        "start_frame": start_frame,
        "end_frame": end_frame,
        "resize_width": resize_width,
        "frames_requested": len(frame_indices(start_frame, end_frame)),
        "frames_cached": frames_written,
        "cache_dir": str(cache_dir),
        "cache_build_seconds": round(time.perf_counter() - start_time, 3),
        "frames": metadata_frames,
    }
    cache_metadata_path(cache_dir).write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metadata, warnings


def load_decode_groups(audit_json: Path) -> dict[int, dict[str, Any]]:
    if not audit_json.exists():
        return {}
    payload = json.loads(audit_json.read_text(encoding="utf-8"))
    return {int(row["requested_frame"]): row for row in payload.get("frames", [])}


def representative_groups(audit_json: Path) -> list[dict[str, Any]]:
    groups_by_id: dict[str, list[dict[str, Any]]] = {}
    for row in load_decode_groups(audit_json).values():
        groups_by_id.setdefault(str(row.get("visual_group_id")), []).append(row)
    groups: list[dict[str, Any]] = []
    for group_id, rows in groups_by_id.items():
        frames = [int(row["requested_frame"]) for row in rows]
        representative = frames[len(frames) // 2]
        groups.append(
            {
                "visual_group_id": group_id,
                "start_frame": min(frames),
                "end_frame": max(frames),
                "representative_frame": representative,
                "frame_indices": frames,
                "visual_group_range": f"{min(frames)}-{max(frames)}" if min(frames) != max(frames) else str(frames[0]),
                "group_size": len(frames),
            }
        )
    return sorted(groups, key=lambda row: int(row["start_frame"]))


def save_session_outputs(
    output_dir: Path,
    windows: list[dict[str, Any]],
    contacts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Save workbench labels and audit integrity."""
    start_time = time.perf_counter()
    window_paths = save_event_windows(output_dir, windows)
    contact_paths = save_contact_candidates(output_dir, contacts)
    audit = audit_label_integrity(windows, contacts)
    integrity_paths = write_integrity_report(output_dir, audit)
    return {
        "save_seconds": round(time.perf_counter() - start_time, 3),
        "window_paths": window_paths,
        "contact_paths": contact_paths,
        "integrity": audit,
        "integrity_paths": integrity_paths,
    }


def run_label_integrity_audit(output_dir: Path) -> tuple[dict[str, Any], dict[str, str]]:
    """Audit existing workbench labels."""
    windows = load_event_windows(output_dir)
    contacts = load_contact_candidates(output_dir)
    audit = audit_label_integrity(windows, contacts)
    paths = write_integrity_report(output_dir, audit)
    return audit, paths


def export_legacy_compatibility(output_dir: Path, old_stage_8_2_dir: Path) -> dict[str, Any]:
    """Export Stage 8.2R labels for Stage 8.3 compatibility."""
    windows = load_event_windows(output_dir)
    contacts = load_contact_candidates(output_dir)
    if not windows:
        return {"status": "not_run_no_windows", "windows_exported": 0, "frame_labels_exported": 0, "backups": {}}
    return export_compatibility(old_stage_8_2_dir, windows, contacts)


def run_review_or_label_viewer(
    *,
    output_dir: Path,
    cache_metadata: dict[str, Any],
    audit_json: Path,
    review_only: bool,
) -> dict[str, Any]:
    """Open a minimal clean-frame workbench viewer.

    The non-interactive pipeline does not depend on this function. It exists as
    the local OpenCV workbench entry point for Product Owner review.
    """
    groups = representative_groups(audit_json)
    if not groups:
        return {"viewer_started": False, "viewer_start_seconds": 0, "warnings": ["No visual groups available. Run --audit-decode first."], "errors": []}
    start_time = time.perf_counter()
    cache_dir = Path(str(cache_metadata.get("cache_dir")))
    window_name = "Stage 8.2R Event Labeling Workbench"
    warnings: list[str] = []
    errors: list[str] = []
    windows = load_event_windows(output_dir)
    contacts = load_contact_candidates(output_dir)
    unsaved_changes = False
    save_seconds = 0.0
    click_state: dict[str, Any] = {"point": None}
    try:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    except cv2.error as exc:
        return {"viewer_started": False, "viewer_start_seconds": round(time.perf_counter() - start_time, 3), "warnings": warnings, "errors": [f"OpenCV GUI unavailable: {exc}"]}

    def on_mouse(event: int, x: int, y: int, _flags: int, _param: Any) -> None:
        if event == cv2.EVENT_LBUTTONDOWN:
            click_state["point"] = (x, y)
        elif event == cv2.EVENT_RBUTTONDOWN:
            click_state["point"] = None

    cv2.setMouseCallback(window_name, on_mouse)

    def window_for_group(group: dict[str, Any]) -> dict[str, Any] | None:
        group_id = str(group.get("visual_group_id"))
        for window in windows:
            if str(window.get("visual_group_id")) == group_id:
                return window
        return None

    def delete_group_label(group: dict[str, Any]) -> None:
        group_id = str(group.get("visual_group_id"))
        related_ids = {str(window.get("window_id")) for window in windows if str(window.get("visual_group_id")) == group_id}
        windows[:] = [window for window in windows if str(window.get("visual_group_id")) != group_id]
        contacts[:] = [contact for contact in contacts if str(contact.get("related_window_id")) not in related_ids]

    def upsert_group_window(event_label: str, group: dict[str, Any]) -> dict[str, Any]:
        existing = window_for_group(group)
        existing_id = str(existing.get("window_id")) if existing else None
        if existing:
            windows.remove(existing)
        window = build_event_window(
            event_label=event_label,
            start_frame=int(group["start_frame"]),
            end_frame=int(group["end_frame"]),
            representative_frame=int(group["representative_frame"]),
            visual_group_id=str(group["visual_group_id"]),
            confidence="high",
            notes="created in Stage 8.2R OpenCV workbench",
            existing_window_id=existing_id,
        )
        windows.append(window)
        return window

    index = 0
    try:
        while True:
            group = groups[index]
            frame_path = cache_dir / f"frame_{int(group['representative_frame']):06d}.jpg"
            frame = cv2.imread(str(frame_path))
            if frame is None:
                errors.append(f"Cached frame missing: {frame_path}")
                break
            cv2.rectangle(frame, (0, 0), (frame.shape[1], 70), (0, 0, 0), -1)
            current_window = window_for_group(group)
            current_label = str(current_window.get("event_label")) if current_window else "unlabeled"
            click_text = "point set" if click_state.get("point") else "no point"
            label = "review only" if review_only else "b/h/n/u label group | c contact candidate"
            cv2.putText(frame, f"Frame group {group['visual_group_range']} | group {index + 1}/{len(groups)} | size {group['group_size']} | rep {group['representative_frame']} | label {current_label}", (18, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2)
            cv2.putText(frame, f"a/d groups | {label} | x delete | s save | q save+quit | unsaved {'yes' if unsaved_changes else 'no'} | {click_text}", (18, 56), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (220, 220, 220), 1)
            cv2.imshow(window_name, frame)
            key = cv2.waitKeyEx(0)
            if key in {ord("d"), 83, 2555904}:
                index = min(len(groups) - 1, index + 1)
                click_state["point"] = None
            elif key in {ord("a"), 81, 2424832}:
                index = max(0, index - 1)
                click_state["point"] = None
            elif key in {ord("]")}:
                index = min(len(groups) - 1, index + 10)
                click_state["point"] = None
            elif key in {ord("[")}:
                index = max(0, index - 10)
                click_state["point"] = None
            elif not review_only and key in {ord("b"), ord("h"), ord("n"), ord("u")}:
                event_label = {ord("b"): "bounce", ord("h"): "hit", ord("n"): "no_event", ord("u"): "uncertain"}[key]
                upsert_group_window(event_label, group)
                unsaved_changes = True
            elif not review_only and key == ord("c"):
                window = window_for_group(group) or upsert_group_window("uncertain", group)
                point = click_state.get("point")
                contact = create_contact_for_group(window, group, x=point[0] if point else None, y=point[1] if point else None, notes="created in Stage 8.2R OpenCV workbench")
                contacts[:] = [item for item in contacts if str(item.get("contact_id")) != str(contact.get("contact_id"))]
                contacts.append(contact)
                unsaved_changes = True
            elif not review_only and key == ord("x"):
                delete_group_label(group)
                unsaved_changes = True
            elif not review_only and key == ord("s"):
                saved = save_session_outputs(output_dir, windows, contacts)
                save_seconds = float(saved.get("save_seconds") or 0)
                unsaved_changes = False
            elif key in {ord("q"), 27}:
                if unsaved_changes and not review_only:
                    saved = save_session_outputs(output_dir, windows, contacts)
                    save_seconds = float(saved.get("save_seconds") or 0)
                    unsaved_changes = False
                break
            elif key == ord("?"):
                print("Stage 8.2R controls: a/d visual groups, j/k raw frames, b/h/n/u event windows, c contact candidate, s save, q save+quit")
    finally:
        try:
            cv2.destroyWindow(window_name)
        except cv2.error:
            pass
    return {"viewer_started": True, "viewer_start_seconds": round(time.perf_counter() - start_time, 3), "save_seconds": save_seconds, "warnings": warnings, "errors": errors}


def create_window_from_group(event_label: str, group: dict[str, Any], *, confidence: str = "high", notes: str = "") -> dict[str, Any]:
    """Create an event-window row from a visual group."""
    return build_event_window(
        event_label=event_label,
        start_frame=int(group["start_frame"]),
        end_frame=int(group["end_frame"]),
        representative_frame=int(group["representative_frame"]),
        visual_group_id=str(group["visual_group_id"]),
        confidence=confidence,
        notes=notes,
    )


def create_contact_for_group(window: dict[str, Any], group: dict[str, Any], *, x: float | None = None, y: float | None = None, notes: str = "") -> dict[str, Any]:
    """Create a contact candidate tied to an event window and visual group."""
    return build_contact_candidate(
        related_window_id=str(window["window_id"]),
        event_type=str(window["event_label"]).replace("_window", ""),
        contact_frame=int(group["representative_frame"]),
        contact_x=x,
        contact_y=y,
        visual_group_id=str(group["visual_group_id"]),
        visual_group_size=int(group["group_size"]),
        notes=notes,
    )
