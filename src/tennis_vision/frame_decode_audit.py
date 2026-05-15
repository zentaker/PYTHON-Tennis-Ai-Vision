"""Frame decode audit helpers for the Stage 8.2R labeling workbench."""

from __future__ import annotations

import csv
import hashlib
import json
import time
from pathlib import Path
from typing import Any

import cv2
import numpy as np


FRAME_DECODE_AUDIT_FIELDS = [
    "requested_frame",
    "sequential_frame_loaded",
    "random_seek_frame_loaded",
    "timestamp_ms",
    "visual_hash",
    "diff_from_previous",
    "near_duplicate_of_previous",
    "visual_group_id",
    "visual_group_range",
    "decode_warning",
]


def compute_frame_signature(frame: np.ndarray, *, signature_width: int = 128) -> np.ndarray:
    """Return a small grayscale signature for visual diffing."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape[:2]
    safe_width = max(16, int(signature_width))
    safe_height = max(8, int(round((height / max(width, 1)) * safe_width)))
    small = cv2.resize(gray, (safe_width, safe_height), interpolation=cv2.INTER_AREA)
    return small.astype(np.float32) / 255.0


def visual_hash(signature: np.ndarray) -> str:
    """Return a compact deterministic hash for a frame signature."""
    digest = hashlib.sha1((signature * 255).astype(np.uint8).tobytes()).hexdigest()
    return digest[:16]


def frame_difference(previous: np.ndarray | None, current: np.ndarray) -> float | None:
    """Return mean absolute visual difference between two signatures."""
    if previous is None:
        return None
    return float(np.mean(np.abs(current - previous)))


def read_sequential_frames(
    video_path: Path,
    *,
    start_frame: int,
    end_frame: int,
    signature_width: int,
) -> tuple[list[dict[str, Any]], list[str], dict[str, float]]:
    """Decode a frame range sequentially."""
    start_time = time.perf_counter()
    signature_seconds = 0.0
    warnings: list[str] = []
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        return [], [f"Video could not be opened: {video_path}"], {"frame_loading_seconds": 0.0, "signature_compute_seconds": 0.0}
    rows: list[dict[str, Any]] = []
    try:
        capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        current = start_frame
        while current <= end_frame:
            ok, frame = capture.read()
            if not ok or frame is None:
                warnings.append(f"Sequential decode stopped before requested frame {current}.")
                break
            signature_start = time.perf_counter()
            signature = compute_frame_signature(frame, signature_width=signature_width)
            signature_seconds += time.perf_counter() - signature_start
            rows.append(
                {
                    "requested_frame": current,
                    "sequential_frame_loaded": True,
                    "timestamp_ms": round(float(capture.get(cv2.CAP_PROP_POS_MSEC) or 0.0), 3),
                    "decoded_frame_index": int(round(float(capture.get(cv2.CAP_PROP_POS_FRAMES) or current + 1) - 1)),
                    "signature": signature,
                    "visual_hash": visual_hash(signature),
                    "decode_warning": "",
                }
            )
            current += 1
    finally:
        capture.release()
    total_seconds = time.perf_counter() - start_time
    return rows, warnings, {
        "frame_loading_seconds": round(max(0.0, total_seconds - signature_seconds), 3),
        "signature_compute_seconds": round(signature_seconds, 3),
    }


def read_random_seek_signatures(
    video_path: Path,
    frame_indices: list[int],
    *,
    signature_width: int,
) -> tuple[dict[int, dict[str, Any]], list[str]]:
    """Read selected frames via random seek for comparison."""
    warnings: list[str] = []
    rows: dict[int, dict[str, Any]] = {}
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        return rows, [f"Video could not be opened for random seek: {video_path}"]
    try:
        for frame_index in frame_indices:
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ok, frame = capture.read()
            if not ok or frame is None:
                warnings.append(f"Random seek failed for frame {frame_index}.")
                continue
            signature = compute_frame_signature(frame, signature_width=signature_width)
            rows[frame_index] = {
                "random_seek_frame_loaded": True,
                "random_visual_hash": visual_hash(signature),
                "random_signature": signature,
            }
    finally:
        capture.release()
    return rows, warnings


def assign_visual_groups(rows: list[dict[str, Any]], *, duplicate_threshold: float) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Add diff and visual group fields to decode audit rows."""
    previous_signature: np.ndarray | None = None
    group_id = 0
    for row in rows:
        diff = frame_difference(previous_signature, row["signature"])
        is_duplicate = bool(diff is not None and diff <= duplicate_threshold)
        if previous_signature is None or not is_duplicate:
            group_id += 1
        row["diff_from_previous"] = round(diff, 6) if diff is not None else None
        row["near_duplicate_of_previous"] = is_duplicate
        row["visual_group_id"] = f"visual_group_{group_id:03d}"
        previous_signature = row["signature"]
    groups: dict[str, list[int]] = {}
    for row in rows:
        groups.setdefault(str(row["visual_group_id"]), []).append(int(row["requested_frame"]))
    for row in rows:
        frames = groups[str(row["visual_group_id"])]
        row["visual_group_range"] = f"{min(frames)}-{max(frames)}" if min(frames) != max(frames) else str(frames[0])
    multi_groups = [frames for frames in groups.values() if len(frames) > 1]
    largest = max((frames for frames in groups.values()), key=len, default=[])
    summary = {
        "total_frames_audited": len(rows),
        "near_duplicate_pairs": sum(1 for row in rows if row.get("near_duplicate_of_previous")),
        "visual_groups": len(groups),
        "largest_visual_group": f"{min(largest)}-{max(largest)}" if len(largest) > 1 else (str(largest[0]) if largest else ""),
        "groups_with_multiple_frames": len(multi_groups),
    }
    return rows, summary


def run_frame_decode_audit(
    video_path: Path,
    *,
    start_frame: int,
    end_frame: int,
    duplicate_threshold: float = 0.0006,
    signature_width: int = 128,
    random_seek_compare: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[str]]:
    """Audit a frame range for decode consistency and visual duplicates."""
    start_time = time.perf_counter()
    warnings: list[str] = []
    rows, sequential_warnings, decode_timing = read_sequential_frames(video_path, start_frame=start_frame, end_frame=end_frame, signature_width=signature_width)
    warnings.extend(sequential_warnings)
    random_seek_seconds = 0.0
    if random_seek_compare and rows:
        random_start = time.perf_counter()
        random_rows, random_warnings = read_random_seek_signatures(video_path, [int(row["requested_frame"]) for row in rows], signature_width=signature_width)
        random_seek_seconds = time.perf_counter() - random_start
        warnings.extend(random_warnings)
        for row in rows:
            random_row = random_rows.get(int(row["requested_frame"]))
            row["random_seek_frame_loaded"] = bool(random_row)
            if random_row and random_row.get("random_visual_hash") != row.get("visual_hash"):
                row["decode_warning"] = "random_seek_hash_differs_from_sequential"
        suspected_seek_artifacts = sum(1 for row in rows if row.get("decode_warning"))
    else:
        for row in rows:
            row["random_seek_frame_loaded"] = False
        suspected_seek_artifacts = 0
    grouping_start = time.perf_counter()
    rows, summary = assign_visual_groups(rows, duplicate_threshold=duplicate_threshold)
    grouping_seconds = time.perf_counter() - grouping_start
    suspected_true_duplicates = sum(1 for row in rows if row.get("near_duplicate_of_previous") and not row.get("decode_warning"))
    summary.update(
        {
            "audit_seconds": round(time.perf_counter() - start_time, 3),
            "frame_loading_seconds": decode_timing.get("frame_loading_seconds", 0.0),
            "signature_compute_seconds": decode_timing.get("signature_compute_seconds", 0.0),
            "grouping_seconds": round(grouping_seconds, 3),
            "random_seek_seconds": round(random_seek_seconds, 3),
            "suspected_true_duplicates": suspected_true_duplicates,
            "suspected_seek_artifacts": suspected_seek_artifacts,
            "duplicate_threshold": duplicate_threshold,
            "signature_width": signature_width,
            "recommendation": "Use visual-group event windows for duplicated frames." if summary.get("near_duplicate_pairs") else "Raw frame navigation is acceptable for this range.",
        }
    )
    public_rows = []
    for row in rows:
        public_rows.append({field: row.get(field) for field in FRAME_DECODE_AUDIT_FIELDS})
    return public_rows, summary, warnings


def write_decode_audit_outputs(output_dir: Path, rows: list[dict[str, Any]], summary: dict[str, Any]) -> dict[str, str]:
    """Write decode audit CSV, JSON, and Markdown files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "frame_decode_audit.csv"
    json_path = output_dir / "frame_decode_audit.json"
    md_path = output_dir / "frame_decode_audit.md"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FRAME_DECODE_AUDIT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    json_path.write_text(json.dumps({"summary": summary, "frames": rows}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_lines = [
        "# Stage 8.2R Frame Decode Audit",
        "",
        "SUMMARY",
        f"  Total frames audited: {summary.get('total_frames_audited')}",
        f"  Near-duplicate pairs: {summary.get('near_duplicate_pairs')}",
        f"  Visual groups: {summary.get('visual_groups')}",
        f"  Largest visual group: {summary.get('largest_visual_group') or 'Not available'}",
        f"  Suspected true duplicates: {summary.get('suspected_true_duplicates')}",
        f"  Suspected seek artifacts: {summary.get('suspected_seek_artifacts')}",
        f"  Audit seconds: {summary.get('audit_seconds')}",
        f"  Frame loading seconds: {summary.get('frame_loading_seconds')}",
        f"  Signature compute seconds: {summary.get('signature_compute_seconds')}",
        f"  Grouping seconds: {summary.get('grouping_seconds')}",
        f"  Random seek seconds: {summary.get('random_seek_seconds')}",
        "",
        "RECOMMENDATION",
        f"  {summary.get('recommendation')}",
    ]
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return {"csv": str(csv_path), "json": str(json_path), "markdown": str(md_path)}
