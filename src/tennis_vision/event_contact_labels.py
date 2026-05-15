"""Event window and contact-candidate label storage for Stage 8.2R."""

from __future__ import annotations

import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EVENT_WINDOW_FIELDS = [
    "window_id",
    "event_label",
    "start_frame",
    "end_frame",
    "center_frame",
    "representative_frame",
    "frame_indices",
    "visual_group_id",
    "confidence",
    "source",
    "notes",
    "created_at",
    "updated_at",
]

CONTACT_CANDIDATE_FIELDS = [
    "contact_id",
    "related_window_id",
    "event_type",
    "contact_frame",
    "contact_x",
    "contact_y",
    "visual_group_id",
    "contact_precision",
    "uncertainty_frames",
    "uncertainty_reason",
    "line_call_candidate",
    "line_call_candidate_reason",
    "notes",
    "created_at",
    "updated_at",
]

COMPAT_LABEL_FIELDS = [
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
    "contact_candidate_id",
    "notes",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def safe_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def read_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_json(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_event_windows(output_dir: Path) -> list[dict[str, Any]]:
    return read_csv(output_dir / "event_windows.csv")


def load_contact_candidates(output_dir: Path) -> list[dict[str, Any]]:
    return read_csv(output_dir / "contact_candidates.csv")


def save_event_windows(output_dir: Path, windows: list[dict[str, Any]]) -> dict[str, str]:
    csv_path = write_csv(output_dir / "event_windows.csv", windows, EVENT_WINDOW_FIELDS)
    json_path = write_json(output_dir / "event_windows.json", windows)
    return {"csv": str(csv_path), "json": str(json_path)}


def save_contact_candidates(output_dir: Path, contacts: list[dict[str, Any]]) -> dict[str, str]:
    csv_path = write_csv(output_dir / "contact_candidates.csv", contacts, CONTACT_CANDIDATE_FIELDS)
    json_path = write_json(output_dir / "contact_candidates.json", contacts)
    return {"csv": str(csv_path), "json": str(json_path)}


def frame_list(start_frame: int, end_frame: int) -> list[int]:
    start, end = min(int(start_frame), int(end_frame)), max(int(start_frame), int(end_frame))
    return list(range(start, end + 1))


def build_event_window(
    *,
    event_label: str,
    start_frame: int,
    end_frame: int,
    representative_frame: int,
    visual_group_id: str,
    confidence: str = "high",
    notes: str = "",
    existing_window_id: str | None = None,
) -> dict[str, Any]:
    frames = frame_list(start_frame, end_frame)
    now = utc_now()
    label = event_label if event_label.endswith("_window") else f"{event_label}_window"
    return {
        "window_id": existing_window_id or f"stage_8_2r_window_{label}_{frames[0]}_{frames[-1]}",
        "event_label": label,
        "start_frame": frames[0],
        "end_frame": frames[-1],
        "center_frame": frames[len(frames) // 2],
        "representative_frame": representative_frame,
        "frame_indices": ",".join(str(frame) for frame in frames),
        "visual_group_id": visual_group_id,
        "confidence": confidence,
        "source": "stage_8_2r_workbench",
        "notes": notes,
        "created_at": now,
        "updated_at": now,
    }


def build_contact_candidate(
    *,
    related_window_id: str,
    event_type: str,
    contact_frame: int,
    contact_x: float | None,
    contact_y: float | None,
    visual_group_id: str,
    visual_group_size: int,
    notes: str = "",
) -> dict[str, Any]:
    now = utc_now()
    ambiguous_group = visual_group_size > 1
    has_point = contact_x is not None and contact_y is not None
    precision = "estimated_within_window" if ambiguous_group else "exact_frame"
    if not has_point:
        precision = "ambiguous"
    uncertainty_frames = max(1, visual_group_size)
    line_ready = bool(has_point and not ambiguous_group and event_type == "bounce")
    return {
        "contact_id": f"stage_8_2r_contact_{event_type}_{contact_frame}",
        "related_window_id": related_window_id,
        "event_type": event_type,
        "contact_frame": contact_frame,
        "contact_x": contact_x,
        "contact_y": contact_y,
        "visual_group_id": visual_group_id,
        "contact_precision": precision,
        "uncertainty_frames": uncertainty_frames,
        "uncertainty_reason": "visual group contains duplicated frames" if ambiguous_group else "single-frame visual group",
        "line_call_candidate": "true" if line_ready else "false",
        "line_call_candidate_reason": "exact bounce frame with point" if line_ready else "contact point or frame precision is insufficient",
        "notes": notes,
        "created_at": now,
        "updated_at": now,
    }


def audit_label_integrity(windows: list[dict[str, Any]], contacts: list[dict[str, Any]]) -> dict[str, Any]:
    """Audit workbench labels for training-data integrity."""
    issues: list[str] = []
    contacts_by_window: dict[str, list[dict[str, Any]]] = {}
    for contact in contacts:
        contacts_by_window.setdefault(str(contact.get("related_window_id")), []).append(contact)
    bounce_without_contact = 0
    windows_without_contact = 0
    no_event_with_contact = 0
    for window in windows:
        window_id = str(window.get("window_id"))
        label = str(window.get("event_label") or "")
        related = contacts_by_window.get(window_id, [])
        if not related:
            windows_without_contact += 1
            if label == "bounce_window":
                bounce_without_contact += 1
        if label == "no_event_window" and related:
            no_event_with_contact += 1
    window_ids = {str(window.get("window_id")) for window in windows}
    contacts_outside_window = sum(1 for contact in contacts if str(contact.get("related_window_id")) not in window_ids)
    ambiguous_contacts = sum(1 for contact in contacts if str(contact.get("contact_precision")) == "ambiguous")
    line_call_candidates = sum(1 for contact in contacts if str(contact.get("line_call_candidate")).lower() == "true")
    overlaps = 0
    sorted_windows = sorted(windows, key=lambda row: (int(row.get("start_frame") or 0), int(row.get("end_frame") or 0)))
    for left, right in zip(sorted_windows, sorted_windows[1:]):
        if int(left.get("end_frame") or 0) >= int(right.get("start_frame") or 0):
            overlaps += 1
    if bounce_without_contact:
        issues.append(f"{bounce_without_contact} bounce window(s) have no contact candidate.")
    if contacts_outside_window:
        issues.append(f"{contacts_outside_window} contact candidate(s) reference missing windows.")
    if no_event_with_contact:
        issues.append(f"{no_event_with_contact} no_event window(s) have contact candidates.")
    if overlaps:
        issues.append(f"{overlaps} overlapping event window pair(s) found.")
    if ambiguous_contacts:
        issues.append(f"{ambiguous_contacts} contact candidate(s) are ambiguous.")
    issue_count = bounce_without_contact + contacts_outside_window + no_event_with_contact + overlaps + ambiguous_contacts
    return {
        "event_windows_count": len(windows),
        "contact_candidates_count": len(contacts),
        "bounce_windows_without_contact_candidate": bounce_without_contact,
        "event_windows_without_contact_candidate": windows_without_contact,
        "contact_candidates_outside_window": contacts_outside_window,
        "no_event_windows_with_contact_candidate": no_event_with_contact,
        "overlapping_event_windows": overlaps,
        "ambiguous_contacts": ambiguous_contacts,
        "line_call_candidates": line_call_candidates,
        "integrity_issues_count": issue_count,
        "issues": issues,
    }


def write_integrity_report(output_dir: Path, audit: dict[str, Any]) -> dict[str, str]:
    json_path = output_dir / "label_integrity_report.json"
    md_path = output_dir / "label_integrity_report.md"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Stage 8.2R Label Integrity Report",
        "",
        "SUMMARY",
        f"  Event windows: {audit.get('event_windows_count')}",
        f"  Contact candidates: {audit.get('contact_candidates_count')}",
        f"  Integrity issues: {audit.get('integrity_issues_count')}",
        f"  Line-call candidates: {audit.get('line_call_candidates')}",
        "",
        "ISSUES",
    ]
    issues = audit.get("issues") or []
    lines.extend([f"- {item}" for item in issues] if issues else ["  No integrity issues found."])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def backup_compat_files(old_dir: Path) -> dict[str, str]:
    backup_dir = old_dir / "label_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = safe_timestamp()
    backups: dict[str, str] = {}
    for name in ("manual_event_windows.csv", "manual_event_labels.csv"):
        path = old_dir / name
        if path.exists():
            target = backup_dir / f"{path.stem}_before_8_2r_export_{stamp}.csv"
            shutil.copy2(path, target)
            backups[name] = str(target)
    return backups


def export_compatibility(old_dir: Path, windows: list[dict[str, Any]], contacts: list[dict[str, Any]]) -> dict[str, Any]:
    """Export workbench labels to legacy Stage 8.2 paths."""
    old_dir.mkdir(parents=True, exist_ok=True)
    backups = backup_compat_files(old_dir)
    contact_by_window = {str(contact.get("related_window_id")): contact for contact in contacts}
    compat_windows: list[dict[str, Any]] = []
    compat_labels: list[dict[str, Any]] = []
    for window in windows:
        frames = [int(item) for item in str(window.get("frame_indices") or "").split(",") if item.strip()]
        if not frames:
            frames = frame_list(int(window["start_frame"]), int(window["end_frame"]))
        compat_windows.append(
            {
                "window_id": window["window_id"],
                "start_frame": window["start_frame"],
                "end_frame": window["end_frame"],
                "center_frame": window["center_frame"],
                "event_label": window["event_label"],
                "label_count": len(frames),
                "source": "stage_8_2r_workbench",
                "confidence": window["confidence"],
                "visual_group_id": window.get("visual_group_id", ""),
                "frame_indices": ",".join(str(frame) for frame in frames),
                "notes": window.get("notes", ""),
            }
        )
        base_label = str(window["event_label"]).replace("_window", "")
        contact = contact_by_window.get(str(window["window_id"]), {})
        for frame in frames:
            compat_labels.append(
                {
                    "frame_index": frame,
                    "timestamp_seconds": "",
                    "event_label": base_label,
                    "player_id": "none" if base_label in {"bounce", "no_event"} else "unknown",
                    "x": "",
                    "y": "",
                    "source": "stage_8_2r_workbench",
                    "label_session": "stage_8_2r_workbench",
                    "confidence": window.get("confidence", "medium"),
                    "associated_ball_label_frame": "",
                    "nearest_ball_x": "",
                    "nearest_ball_y": "",
                    "nearest_auto_event_type": "",
                    "nearest_auto_event_frame": "",
                    "frame_delta_to_auto_event": "",
                    "source_window_id": window["window_id"],
                    "event_window_label": "true",
                    "contact_candidate_id": contact.get("contact_id", ""),
                    "notes": window.get("notes", ""),
                }
            )
    write_csv(old_dir / "manual_event_windows.csv", compat_windows, ["window_id", "start_frame", "end_frame", "center_frame", "event_label", "label_count", "source", "confidence", "visual_group_id", "frame_indices", "notes"])
    write_json(old_dir / "manual_event_windows.json", compat_windows)
    write_csv(old_dir / "manual_event_labels.csv", compat_labels, COMPAT_LABEL_FIELDS)
    write_json(old_dir / "manual_event_labels.json", compat_labels)
    return {
        "status": "exported",
        "windows_exported": len(compat_windows),
        "frame_labels_exported": len(compat_labels),
        "backups": backups,
    }
