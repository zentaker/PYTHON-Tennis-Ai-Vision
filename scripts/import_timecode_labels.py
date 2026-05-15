"""Import DaVinci/manual timecode labels into Stage 8.2-compatible files."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

POINT_LABELS = {"bounce_contact", "hit", "pre_bounce", "post_bounce", "uncertain", "no_event"}
RANGE_LABELS = {"bounce_window", "hit_window", "uncertain_window", "no_event_window"}

POINT_LABEL_MAPPING = {
    "bounce_contact": "bounce",
    "hit": "hit",
    "pre_bounce": "pre_bounce",
    "post_bounce": "post_bounce",
    "uncertain": "uncertain",
    "no_event": "no_event",
}

WINDOW_BASE_LABELS = {
    "bounce_window": "bounce",
    "hit_window": "hit",
    "uncertain_window": "uncertain",
    "no_event_window": "no_event",
}

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import DaVinci/manual timecode labels into Stage 8.2 files.")
    parser.add_argument("--input", required=True, type=Path, help="CSV with label_type,timecode,time_seconds,start_timecode,end_timecode,confidence,notes.")
    parser.add_argument("--fps", required=True, type=float, help="FPS used to convert timecodes to frame estimates.")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs" / "timeline" / "stage_8_2_event_labels")
    parser.add_argument("--report-dir", type=Path, default=PROJECT_ROOT / "outputs" / "reports")
    parser.add_argument("--no-backup", action="store_true", help="Do not back up existing Stage 8.2 label files before overwriting.")
    return parser.parse_args()


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def normalize_confidence(value: Any) -> str:
    confidence = str(value or "medium").strip().lower()
    return confidence if confidence in {"high", "medium", "low"} else "medium"


def clean_cell(row: dict[str, Any], key: str) -> str:
    return str(row.get(key) or "").strip()


def parse_seconds(value: str) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_timecode(value: str, fps: float) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    direct_seconds = parse_seconds(text)
    if direct_seconds is not None:
        return direct_seconds

    if "." in text and text.count(":") == 2:
        hours_text, minutes_text, seconds_text = text.split(":")
        try:
            return int(hours_text) * 3600 + int(minutes_text) * 60 + float(seconds_text)
        except ValueError:
            return None

    parts = text.split(":")
    if len(parts) == 4:
        try:
            hours, minutes, seconds, frames = [int(part) for part in parts]
        except ValueError:
            return None
        return hours * 3600 + minutes * 60 + seconds + frames / fps

    if len(parts) == 3:
        try:
            hours, minutes, seconds = parts
            return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        except ValueError:
            return None
    return None


def row_time_seconds(row: dict[str, Any], fps: float, time_key: str, timecode_key: str) -> float | None:
    explicit_seconds = parse_seconds(clean_cell(row, time_key))
    if explicit_seconds is not None:
        return explicit_seconds
    return parse_timecode(clean_cell(row, timecode_key), fps)


def frame_index(seconds: float, fps: float) -> int:
    return int(round(seconds * fps))


def read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def backup_existing(output_dir: Path) -> dict[str, str]:
    backup_dir = output_dir / "label_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = utc_stamp()
    backups: dict[str, str] = {}
    for name in ["manual_event_labels.csv", "manual_event_labels.json", "manual_event_windows.csv", "manual_event_windows.json"]:
        path = output_dir / name
        if path.exists():
            backup = backup_dir / f"{path.stem}_before_timecode_import_{stamp}{path.suffix}"
            shutil.copy2(path, backup)
            backups[name] = str(backup)
    return backups


def make_label_row(
    *,
    frame: int,
    seconds: float,
    event_label: str,
    confidence: str,
    notes: str,
    session: str,
    source_window_id: str = "",
    event_window_label: bool = False,
) -> dict[str, Any]:
    return {
        "frame_index": frame,
        "timestamp_seconds": round(seconds, 3),
        "event_label": event_label,
        "player_id": "unknown" if event_label in {"hit", "uncertain"} else "none",
        "x": "",
        "y": "",
        "source": "davinci_timecode_import" if not event_window_label else "davinci_timecode_import_window",
        "label_session": session,
        "confidence": confidence,
        "associated_ball_label_frame": "",
        "nearest_ball_x": "",
        "nearest_ball_y": "",
        "nearest_auto_event_type": "",
        "nearest_auto_event_frame": "",
        "frame_delta_to_auto_event": "",
        "source_window_id": source_window_id,
        "event_window_label": "true" if event_window_label else "false",
        "contact_candidate_id": "",
        "notes": notes,
    }


def import_rows(rows: list[dict[str, Any]], fps: float, session: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str], list[str]]:
    labels: list[dict[str, Any]] = []
    windows: list[dict[str, Any]] = []
    warnings: list[str] = []
    errors: list[str] = []

    for row_number, row in enumerate(rows, start=2):
        label_type = clean_cell(row, "label_type").lower()
        confidence = normalize_confidence(clean_cell(row, "confidence"))
        notes = clean_cell(row, "notes")

        if label_type in POINT_LABELS:
            seconds = row_time_seconds(row, fps, "time_seconds", "timecode")
            if seconds is None:
                errors.append(f"Row {row_number}: point label {label_type} has no parseable time_seconds or timecode.")
                continue
            event_label = POINT_LABEL_MAPPING[label_type]
            labels.append(
                make_label_row(
                    frame=frame_index(seconds, fps),
                    seconds=seconds,
                    event_label=event_label,
                    confidence=confidence,
                    notes=notes,
                    session=session,
                )
            )
            continue

        if label_type in RANGE_LABELS:
            start_seconds = row_time_seconds(row, fps, "start_time_seconds", "start_timecode")
            end_seconds = row_time_seconds(row, fps, "end_time_seconds", "end_timecode")
            if start_seconds is None or end_seconds is None:
                errors.append(f"Row {row_number}: range label {label_type} needs start/end timecode or start/end seconds.")
                continue
            start, end = sorted((start_seconds, end_seconds))
            start_frame = frame_index(start, fps)
            end_frame = frame_index(end, fps)
            center = (start + end) / 2
            center_frame = frame_index(center, fps)
            frame_start, frame_end = sorted((start_frame, end_frame))
            frame_indices = list(range(frame_start, frame_end + 1))
            if not frame_indices:
                frame_indices = [center_frame]
            window_id = f"timecode_{label_type}_{frame_start}_{frame_end}_{len(windows) + 1:03d}"
            windows.append(
                {
                    "window_id": window_id,
                    "start_frame": frame_start,
                    "end_frame": frame_end,
                    "center_frame": center_frame,
                    "event_label": label_type,
                    "label_count": len(frame_indices),
                    "source": "davinci_timecode_import",
                    "confidence": confidence,
                    "visual_group_id": "",
                    "frame_indices": ",".join(str(frame) for frame in frame_indices),
                    "contact_frame": center_frame,
                    "notes": notes,
                }
            )
            base_label = WINDOW_BASE_LABELS[label_type]
            for frame in frame_indices:
                labels.append(
                    make_label_row(
                        frame=frame,
                        seconds=frame / fps,
                        event_label=base_label,
                        confidence=confidence,
                        notes=notes,
                        session=session,
                        source_window_id=window_id,
                        event_window_label=True,
                    )
                )
            continue

        warnings.append(f"Row {row_number}: unsupported label_type {label_type!r}; row skipped.")

    labels.sort(key=lambda item: (int(item["frame_index"]), str(item["event_label"])))
    windows.sort(key=lambda item: (int(item["start_frame"]), int(item["end_frame"]), str(item["event_label"])))
    return labels, windows, warnings, errors


def markdown_report(report: dict[str, Any]) -> str:
    return f"""# Stage LB1 Timecode Label Import Report

VERDICT
  Final verdict: {report["final_verdict"]}
  Friction: {report["friction_score"]}

IMPORT SUMMARY
  Input rows: {report["input_rows"]}
  Manual event labels: {report["manual_event_labels_count"]}
  Manual event windows: {report["manual_event_windows_count"]}
  FPS: {report["fps"]}

OUTPUTS
  Manual event labels CSV: {report["output_paths"]["manual_event_labels_csv"]}
  Manual event labels JSON: {report["output_paths"]["manual_event_labels_json"]}
  Manual event windows CSV: {report["output_paths"]["manual_event_windows_csv"]}
  Manual event windows JSON: {report["output_paths"]["manual_event_windows_json"]}

WARNINGS
{chr(10).join(f"  - {item}" for item in report["warnings"]) if report["warnings"] else "  None"}

ERRORS
{chr(10).join(f"  - {item}" for item in report["errors"]) if report["errors"] else "  None"}

PRODUCT OWNER NOTE
  Stage LB1 treats DaVinci Resolve or manual timecode notes as the trusted
  visual labeling interface. The importer converts those time labels into
  Stage 8.2-compatible frame estimates without opening video or processing
  frames.
"""


def build_report(
    *,
    input_path: Path,
    output_dir: Path,
    fps: float,
    input_rows: int,
    labels: list[dict[str, Any]],
    windows: list[dict[str, Any]],
    warnings: list[str],
    errors: list[str],
    backups: dict[str, str],
) -> dict[str, Any]:
    friction_score = len(warnings) * 3 + len(errors) * 10
    if not labels and not windows:
        friction_score += 20
    final_verdict = "blocked" if errors and not labels and not windows else "ready_with_warnings" if warnings or errors else "ready_for_stage_8_3"
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stage": "Stage LB1 - Timecode Label Import",
        "input_path": str(input_path),
        "fps": fps,
        "input_rows": input_rows,
        "manual_event_labels_count": len(labels),
        "manual_event_windows_count": len(windows),
        "backups": backups,
        "warnings": warnings,
        "errors": errors,
        "friction_score": friction_score,
        "final_verdict": final_verdict,
        "recommended_next_step": "Run Stage 8.3 event validation after importing trusted timecode labels.",
        "output_paths": {
            "manual_event_labels_csv": str(output_dir / "manual_event_labels.csv"),
            "manual_event_labels_json": str(output_dir / "manual_event_labels.json"),
            "manual_event_windows_csv": str(output_dir / "manual_event_windows.csv"),
            "manual_event_windows_json": str(output_dir / "manual_event_windows.json"),
        },
    }


def main() -> int:
    args = parse_args()
    input_path = resolve(args.input)
    output_dir = resolve(args.output_dir)
    report_dir = resolve(args.report_dir)

    if args.fps <= 0:
        raise SystemExit("--fps must be greater than zero.")
    if not input_path.exists():
        raise SystemExit(f"Input CSV not found: {input_path}")

    rows = read_csv(input_path)
    session = f"timecode_import_{utc_stamp()}"
    backups = {} if args.no_backup else backup_existing(output_dir)
    labels, windows, warnings, errors = import_rows(rows, args.fps, session)

    write_csv(output_dir / "manual_event_labels.csv", labels, LABEL_FIELDS)
    write_json(output_dir / "manual_event_labels.json", labels)
    write_csv(output_dir / "manual_event_windows.csv", windows, WINDOW_FIELDS)
    write_json(output_dir / "manual_event_windows.json", windows)

    report = build_report(
        input_path=input_path,
        output_dir=output_dir,
        fps=args.fps,
        input_rows=len(rows),
        labels=labels,
        windows=windows,
        warnings=warnings,
        errors=errors,
        backups=backups,
    )
    report_dir.mkdir(parents=True, exist_ok=True)
    write_json(report_dir / "stage_lb1_timecode_label_import_report.json", report)
    (report_dir / "stage_lb1_timecode_label_import_report.md").write_text(markdown_report(report), encoding="utf-8")

    print("Stage LB1 timecode labels imported.")
    print(f"Verdict: {report['final_verdict']}")
    print(f"Manual event labels: {len(labels)}")
    print(f"Manual event windows: {len(windows)}")
    print(f"Report: {report_dir / 'stage_lb1_timecode_label_import_report.md'}")
    return 1 if report["final_verdict"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
