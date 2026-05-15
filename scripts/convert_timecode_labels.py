"""Convert local labeling editor JSON exports to Stage 8.2-compatible files."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

LABEL_FIELDS = [
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

WINDOW_FIELDS = [
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
    "contact_frame",
    "notes",
]

LABEL_MAPPING = {
    "bounce_contact": "bounce",
    "hit": "hit",
    "no_event": "no_event",
    "uncertain": "uncertain",
    "pre_bounce": "pre_bounce",
    "post_bounce": "post_bounce",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert local video-labeling editor JSON to Stage 8.2 CSV/JSON files.")
    parser.add_argument("--input", required=True, type=Path, help="Path to exported labeling-editor JSON.")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs" / "timeline" / "stage_8_2_event_labels")
    parser.add_argument("--fps", type=float, default=None, help="Override FPS used for frame estimates.")
    parser.add_argument("--no-backup", action="store_true", help="Do not back up existing Stage 8.2 label files before writing.")
    return parser.parse_args()


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def backup_existing(output_dir: Path) -> dict[str, str]:
    backup_dir = output_dir / "label_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = utc_stamp()
    backups: dict[str, str] = {}
    for name in ["manual_event_labels.csv", "manual_event_labels.json", "manual_event_windows.csv", "manual_event_windows.json"]:
        path = output_dir / name
        if path.exists():
            backup = backup_dir / f"{path.stem}_before_timecode_convert_{stamp}{path.suffix}"
            shutil.copy2(path, backup)
            backups[name] = str(backup)
    return backups


def frame_for_label(label: dict[str, Any], fps: float) -> int:
    if label.get("frame_estimate") not in (None, ""):
        return int(round(float(label["frame_estimate"])))
    return int(round(float(label.get("time_seconds") or 0) * fps))


def normalize_confidence(value: Any) -> str:
    normalized = str(value or "medium").strip().lower()
    return normalized if normalized in {"high", "medium", "low"} else "medium"


def build_manual_label_rows(labels: list[dict[str, Any]], fps: float, session: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label in labels:
        label_type = str(label.get("label_type") or "").strip()
        mapped = LABEL_MAPPING.get(label_type)
        if not mapped:
            continue
        frame = frame_for_label(label, fps)
        rows.append(
            {
                "frame_index": frame,
                "timestamp_seconds": round(float(label.get("time_seconds") or frame / fps), 3),
                "event_label": mapped,
                "player_id": "unknown" if mapped in {"hit", "uncertain"} else "none",
                "x": "",
                "y": "",
                "source": "local_labeling_editor",
                "label_session": session,
                "confidence": normalize_confidence(label.get("confidence")),
                "associated_ball_label_frame": "",
                "nearest_ball_x": "",
                "nearest_ball_y": "",
                "nearest_auto_event_type": "",
                "nearest_auto_event_frame": "",
                "frame_delta_to_auto_event": "",
                "source_window_id": "",
                "event_window_label": "false",
                "contact_candidate_id": str(label.get("label_id") or ""),
                "notes": str(label.get("notes") or ""),
            }
        )
    rows.sort(key=lambda row: int(row["frame_index"]))
    return rows


def build_bounce_windows(labels: list[dict[str, Any]], fps: float) -> list[dict[str, Any]]:
    sorted_labels = sorted(labels, key=lambda row: float(row.get("time_seconds") or 0))
    pre_labels = [row for row in sorted_labels if row.get("label_type") == "pre_bounce"]
    contact_labels = [row for row in sorted_labels if row.get("label_type") == "bounce_contact"]
    post_labels = [row for row in sorted_labels if row.get("label_type") == "post_bounce"]
    windows: list[dict[str, Any]] = []
    used_pre: set[str] = set()
    used_post: set[str] = set()
    for contact in contact_labels:
        contact_frame = frame_for_label(contact, fps)
        pre = max((row for row in pre_labels if str(row.get("label_id")) not in used_pre and frame_for_label(row, fps) <= contact_frame), key=lambda row: frame_for_label(row, fps), default=None)
        post = min((row for row in post_labels if str(row.get("label_id")) not in used_post and frame_for_label(row, fps) >= contact_frame), key=lambda row: frame_for_label(row, fps), default=None)
        if not pre or not post:
            continue
        pre_frame = frame_for_label(pre, fps)
        post_frame = frame_for_label(post, fps)
        if post_frame < pre_frame:
            continue
        used_pre.add(str(pre.get("label_id")))
        used_post.add(str(post.get("label_id")))
        frames = list(range(pre_frame, post_frame + 1))
        window_id = f"local_editor_bounce_window_{pre_frame}_{contact_frame}_{post_frame}"
        windows.append(
            {
                "window_id": window_id,
                "start_frame": pre_frame,
                "end_frame": post_frame,
                "center_frame": contact_frame,
                "event_label": "bounce_window",
                "label_count": len(frames),
                "source": "local_labeling_editor",
                "confidence": normalize_confidence(contact.get("confidence")),
                "visual_group_id": "",
                "frame_indices": ",".join(str(frame) for frame in frames),
                "contact_frame": contact_frame,
                "notes": str(contact.get("notes") or "created from pre_bounce/bounce_contact/post_bounce triplet"),
            }
        )
    return windows


def build_exported_windows(windows: list[dict[str, Any]], fps: float) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in windows:
        raw_type = str(item.get("label_type") or "").strip()
        base_type = raw_type.replace("_window", "")
        if base_type not in {"bounce", "hit", "uncertain", "no_event"}:
            continue
        label_type = f"{base_type}_window"
        start = float(item.get("start_time_seconds") or 0)
        end = float(item.get("end_time_seconds") or start)
        start_frame = int(round(float(item.get("start_frame_estimate") if item.get("start_frame_estimate") not in (None, "") else start * fps)))
        end_frame = int(round(float(item.get("end_frame_estimate") if item.get("end_frame_estimate") not in (None, "") else end * fps)))
        center_source = item.get("contact_frame_estimate") if item.get("contact_frame_estimate") not in (None, "") else item.get("center_frame_estimate")
        center_frame = int(round(float(center_source if center_source not in (None, "") else ((start + end) / 2) * fps)))
        frame_start, frame_end = min(start_frame, end_frame), max(start_frame, end_frame)
        frames = list(range(frame_start, frame_end + 1))
        rows.append(
            {
                "window_id": str(item.get("window_id") or f"local_editor_{label_type}_{frame_start}_{frame_end}"),
                "start_frame": frame_start,
                "end_frame": frame_end,
                "center_frame": center_frame,
                "event_label": label_type,
                "label_count": len(frames),
                "source": "local_labeling_editor_range",
                "confidence": normalize_confidence(item.get("confidence")),
                "visual_group_id": "",
                "frame_indices": ",".join(str(frame) for frame in frames),
                "contact_frame": center_frame,
                "notes": str(item.get("notes") or ""),
            }
        )
    return rows


def add_window_compat_rows(label_rows: list[dict[str, Any]], windows: list[dict[str, Any]], fps: float, session: str) -> None:
    existing_by_frame_type = {(int(row["frame_index"]), str(row["event_label"])): row for row in label_rows}
    for window in windows:
        frames = [int(frame) for frame in str(window["frame_indices"]).split(",") if frame.strip()]
        base_label = str(window.get("event_label") or "").replace("_window", "")
        if base_label not in {"bounce", "hit", "uncertain", "no_event"}:
            base_label = "uncertain"
        for frame in frames:
            key = (frame, base_label)
            row = existing_by_frame_type.get(key)
            if row is None:
                row = {
                    "frame_index": frame,
                    "timestamp_seconds": round(frame / fps, 3),
                    "event_label": base_label,
                    "player_id": "unknown" if base_label in {"hit", "uncertain"} else "none",
                    "x": "",
                    "y": "",
                    "source": "local_labeling_editor_range",
                    "label_session": session,
                    "confidence": window.get("confidence", "medium"),
                    "associated_ball_label_frame": "",
                    "nearest_ball_x": "",
                    "nearest_ball_y": "",
                    "nearest_auto_event_type": "",
                    "nearest_auto_event_frame": "",
                    "frame_delta_to_auto_event": "",
                    "source_window_id": window["window_id"],
                    "event_window_label": "true",
                    "contact_candidate_id": "",
                    "notes": window.get("notes", ""),
                }
                label_rows.append(row)
                existing_by_frame_type[key] = row
            else:
                row["source_window_id"] = window["window_id"]
                row["event_window_label"] = "true"
                row["source"] = "local_labeling_editor_range"


def main() -> int:
    args = parse_args()
    input_path = resolve(args.input)
    output_dir = resolve(args.output_dir)
    payload = read_json(input_path)
    if payload.get("schema") != "tennis_ai_vision.video_labels.v1":
        raise SystemExit(f"Unsupported schema: {payload.get('schema')}")
    fps = float(args.fps if args.fps is not None else payload.get("fps") or 60)
    labels = list(payload.get("labels") or [])
    exported_windows = list(payload.get("event_ranges") or payload.get("windows") or [])
    session = f"local_labeling_editor_{utc_stamp()}"
    backups = {} if args.no_backup else backup_existing(output_dir)
    label_rows = build_manual_label_rows(labels, fps, session)
    windows = build_exported_windows(exported_windows, fps) + build_bounce_windows(labels, fps)
    add_window_compat_rows(label_rows, windows, fps, session)
    label_rows.sort(key=lambda row: (int(row["frame_index"]), str(row["event_label"])))
    write_csv(output_dir / "manual_event_labels.csv", label_rows, LABEL_FIELDS)
    write_json(output_dir / "manual_event_labels.json", label_rows)
    write_csv(output_dir / "manual_event_windows.csv", windows, WINDOW_FIELDS)
    write_json(output_dir / "manual_event_windows.json", windows)
    print("Converted local labeling editor export.")
    print(f"Labels written: {len(label_rows)}")
    print(f"Bounce windows written: {len(windows)}")
    print(f"Output dir: {output_dir}")
    if backups:
        print(f"Backups created: {len(backups)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
