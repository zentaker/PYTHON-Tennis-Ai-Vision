"""Add a Stage 8.2 manual event window without opening the viewer."""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from tennis_vision.event_labeling import (  # noqa: E402
    merge_event_labels,
    read_event_labels,
    read_manual_event_windows,
    write_event_labels_csv,
    write_event_labels_json,
    write_manual_event_windows_csv,
    write_manual_event_windows_json,
)


ALLOWED_LABELS = {"bounce", "hit", "no_event", "uncertain"}
ALLOWED_CONFIDENCE = {"high", "medium", "low"}
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "timeline" / "stage_8_2_event_labels"
LABELS_CSV = OUTPUT_DIR / "manual_event_labels.csv"
LABELS_JSON = OUTPUT_DIR / "manual_event_labels.json"
WINDOWS_CSV = OUTPUT_DIR / "manual_event_windows.csv"
WINDOWS_JSON = OUTPUT_DIR / "manual_event_windows.json"
BACKUP_DIR = OUTPUT_DIR / "label_backups"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Add or list Stage 8.2 manual event windows.")
    parser.add_argument("--list", action="store_true", help="List existing manual event windows and exit.")
    parser.add_argument("--label", choices=sorted(ALLOWED_LABELS), help="Event label for the window.")
    parser.add_argument("--start-frame", type=int, help="First frame in the event window.")
    parser.add_argument("--end-frame", type=int, help="Last frame in the event window.")
    parser.add_argument("--confidence", choices=sorted(ALLOWED_CONFIDENCE), default="high")
    parser.add_argument("--player-id", default=None, help="Optional player id. Defaults to none for bounce/no_event and unknown for hit/uncertain.")
    parser.add_argument("--notes", default="", help="Plain-text note to attach to the window and frame labels.")
    parser.add_argument("--source", default="stage_8_2_manual_window_cli")
    parser.add_argument("--dry-run", action="store_true", help="Print planned changes without writing files.")
    return parser.parse_args()


def safe_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def default_player_id(label: str, player_id: str | None) -> str:
    if player_id:
        return player_id
    return "none" if label in {"bounce", "no_event"} else "unknown"


def normalize_window_label(label: str) -> str:
    return f"{label}_window"


def base_label_from_window(event_label: str) -> str:
    value = str(event_label or "")
    return value[:-7] if value.endswith("_window") else value


def window_id_for(label: str, start_frame: int, end_frame: int) -> str:
    return f"stage_8_2_window_cli_{label}_{start_frame}_{end_frame}"


def frame_indices_for(start_frame: int, end_frame: int) -> list[int]:
    start, end = min(start_frame, end_frame), max(start_frame, end_frame)
    return list(range(start, end + 1))


def read_existing_labels() -> list[dict[str, Any]]:
    if not LABELS_CSV.exists():
        return []
    labels, warnings = read_event_labels(LABELS_CSV)
    for warning in warnings:
        print(f"Warning: {warning}")
    return labels


def read_existing_windows() -> list[dict[str, Any]]:
    windows, warnings = read_manual_event_windows(WINDOWS_CSV)
    for warning in warnings:
        print(f"Warning: {warning}")
    return windows


def backup_existing_files(timestamp: str) -> dict[str, str]:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backups: dict[str, str] = {}
    if LABELS_CSV.exists():
        labels_backup = BACKUP_DIR / f"manual_event_labels_before_window_cli_{timestamp}.csv"
        shutil.copy2(LABELS_CSV, labels_backup)
        backups["manual_event_labels"] = str(labels_backup)
    if WINDOWS_CSV.exists():
        windows_backup = BACKUP_DIR / f"manual_event_windows_before_window_cli_{timestamp}.csv"
        shutil.copy2(WINDOWS_CSV, windows_backup)
        backups["manual_event_windows"] = str(windows_backup)
    return backups


def build_window(
    *,
    label: str,
    start_frame: int,
    end_frame: int,
    confidence: str,
    source: str,
    notes: str,
    existing_windows: list[dict[str, Any]],
) -> tuple[dict[str, Any], bool]:
    frames = frame_indices_for(start_frame, end_frame)
    start, end = frames[0], frames[-1]
    event_label = normalize_window_label(label)
    existing = next(
        (
            window
            for window in existing_windows
            if int(window.get("start_frame", -1)) == start
            and int(window.get("end_frame", -1)) == end
            and base_label_from_window(str(window.get("event_label"))) == label
        ),
        None,
    )
    window_id = str(existing.get("window_id")) if existing else window_id_for(label, start, end)
    window = {
        "window_id": window_id,
        "start_frame": start,
        "end_frame": end,
        "center_frame": frames[len(frames) // 2],
        "event_label": event_label,
        "label_count": len(frames),
        "source": source,
        "confidence": confidence,
        "visual_group_id": "",
        "frame_indices": ",".join(str(frame) for frame in frames),
        "notes": notes or "Manual event window added by direct Stage 8.2 CLI.",
    }
    return window, existing is not None


def build_frame_labels(
    *,
    window: dict[str, Any],
    label: str,
    confidence: str,
    player_id: str,
    source: str,
    notes: str,
) -> list[dict[str, Any]]:
    frames = frame_indices_for(int(window["start_frame"]), int(window["end_frame"]))
    frame_notes = notes or "Frame-level compatibility label generated from manual event window."
    frame_notes = f"{frame_notes}; source_window_id={window['window_id']}; event_window_label=true"
    return [
        {
            "frame_index": frame,
            "timestamp_seconds": None,
            "event_label": label,
            "player_id": player_id,
            "x": None,
            "y": None,
            "source": source,
            "label_session": "stage_8_2_manual_window_cli",
            "confidence": confidence,
            "associated_ball_label_frame": None,
            "nearest_ball_x": None,
            "nearest_ball_y": None,
            "nearest_auto_event_type": "",
            "nearest_auto_event_frame": None,
            "frame_delta_to_auto_event": None,
            "source_window_id": window["window_id"],
            "event_window_label": True,
            "notes": frame_notes,
        }
        for frame in frames
    ]


def merge_windows(existing_windows: list[dict[str, Any]], window: dict[str, Any]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    replaced = False
    for existing in existing_windows:
        same_window = (
            int(existing.get("start_frame", -1)) == int(window["start_frame"])
            and int(existing.get("end_frame", -1)) == int(window["end_frame"])
            and base_label_from_window(str(existing.get("event_label"))) == base_label_from_window(str(window["event_label"]))
        )
        if same_window:
            merged.append(dict(window))
            replaced = True
        else:
            merged.append(dict(existing))
    if not replaced:
        merged.append(dict(window))
    return sorted(merged, key=lambda row: (int(row.get("start_frame", 0)), int(row.get("end_frame", 0)), str(row.get("event_label"))))


def list_windows() -> int:
    windows = read_existing_windows()
    if not windows:
        print("No Stage 8.2 manual event windows found.")
        return 0
    print("Stage 8.2 manual event windows")
    for window in windows:
        print(
            f"- {window.get('window_id')}: {window.get('event_label')} "
            f"{window.get('start_frame')}-{window.get('end_frame')} "
            f"confidence={window.get('confidence')} notes={window.get('notes') or ''}"
        )
    return 0


def validate_args(args: argparse.Namespace) -> None:
    if args.list:
        return
    missing = [name for name in ("label", "start_frame", "end_frame") if getattr(args, name) is None]
    if missing:
        raise SystemExit(f"Missing required argument(s): {', '.join('--' + item.replace('_', '-') for item in missing)}")


def main() -> int:
    args = parse_args()
    validate_args(args)
    if args.list:
        return list_windows()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    start, end = min(args.start_frame, args.end_frame), max(args.start_frame, args.end_frame)
    player_id = default_player_id(args.label, args.player_id)
    existing_windows = read_existing_windows()
    existing_labels = read_existing_labels()
    window, updated_existing = build_window(
        label=args.label,
        start_frame=start,
        end_frame=end,
        confidence=args.confidence,
        source=args.source,
        notes=args.notes,
        existing_windows=existing_windows,
    )
    frame_labels = build_frame_labels(
        window=window,
        label=args.label,
        confidence=args.confidence,
        player_id=player_id,
        source=args.source,
        notes=args.notes,
    )
    merged_windows = merge_windows(existing_windows, window)
    merged_labels = merge_event_labels(existing_labels, frame_labels)

    print("Stage 8.2 direct event-window label")
    print(f"  Action: {'update existing window' if updated_existing else 'add new window'}")
    print(f"  Label: {args.label}")
    print(f"  Window: {start}-{end}")
    print(f"  Frames: {len(frame_labels)}")
    print(f"  Player id: {player_id}")
    print(f"  Window id: {window['window_id']}")
    if args.dry_run:
        print("  Dry run: no files modified")
        return 0

    timestamp = safe_timestamp()
    backups = backup_existing_files(timestamp)
    write_manual_event_windows_csv(WINDOWS_CSV, merged_windows)
    write_manual_event_windows_json(WINDOWS_JSON, merged_windows)
    write_event_labels_csv(LABELS_CSV, merged_labels)
    write_event_labels_json(LABELS_JSON, merged_labels)
    print(f"  Wrote: {WINDOWS_CSV}")
    print(f"  Wrote: {LABELS_CSV}")
    if backups:
        print("  Backups:")
        for path in backups.values():
            print(f"    {path}")
    else:
        print("  Backups: no existing label files needed backup")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
