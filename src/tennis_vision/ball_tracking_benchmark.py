"""Benchmark ball tracking model alternatives against manual rally timings."""

from __future__ import annotations

import csv
import importlib
import json
import multiprocessing as mp
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from tennis_vision.court_projection import load_stage_3_calibration
from tennis_vision.manual_event_position_resolver import (
    load_manual_full_rally_annotation,
    normalize_manual_events,
    project_event_position_to_court,
)
from tennis_vision.tennis_sequence_validator import validate_manual_event_sequence


ADAPTERS = {
    "baseline_current": "tennis_vision.model_adapters.baseline_ball_adapter",
    "tracknet_candidate": "tennis_vision.model_adapters.tracknet_adapter",
    "sam_assisted_candidate": "tennis_vision.model_adapters.sam_assisted_adapter",
}

EVENT_RESULT_FIELDS = [
    "model_name",
    "event_id",
    "event_type",
    "shot_type",
    "manual_frame",
    "search_start_frame",
    "search_end_frame",
    "resolved_frame",
    "image_x",
    "image_y",
    "projected_x",
    "projected_y",
    "court_zone",
    "depth",
    "lateral_lane",
    "raw_score",
    "confidence",
    "position_status",
    "position_trust",
    "validation_status",
    "validation_reason",
    "debug_reason",
]

MODEL_SUMMARY_FIELDS = [
    "model_name",
    "available",
    "events_attempted",
    "resolved_count",
    "valid_count",
    "suspicious_count",
    "invalid_count",
    "unresolved_count",
    "wrong_side_likely_count",
    "average_confidence",
    "benchmark_verdict",
]


def build_event_search_window(event: dict[str, Any], *, search_padding: int = 5) -> list[int]:
    """Build benchmark search frames from the manual event timing."""
    start = int(event["start_frame"])
    end = int(event["end_frame"])
    if start == end:
        start -= search_padding
        end += search_padding
    else:
        range_padding = max(1, search_padding - 2)
        start -= range_padding
        end += range_padding
    return list(range(max(0, start), max(start, end) + 1))


def run_benchmark(
    *,
    project_root: Path,
    annotation_path: Path,
    video_path: Path,
    model_names: list[str],
    output_dir: Path,
    search_padding: int = 5,
    resize_width: int = 1280,
    model_timeout_seconds: int = 20,
) -> dict[str, Any]:
    """Run all requested model adapters on manual full-rally events."""
    annotation = load_manual_full_rally_annotation(annotation_path)
    events = normalize_manual_events(annotation)
    calibration = load_stage_3_calibration(project_root / "outputs" / "reports" / "stage_3_court_calibration_probe_report.json")
    search_windows = {event["event_id"]: build_event_search_window(event, search_padding=search_padding) for event in events}
    output_dir.mkdir(parents=True, exist_ok=True)

    all_event_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    availability: dict[str, Any] = {}
    warnings: list[str] = []
    errors: list[str] = []

    for model_name in model_names:
        print(f"Checking model: {model_name}", flush=True)
        adapter_path = ADAPTERS.get(model_name)
        if not adapter_path:
            warnings.append(f"Unknown model adapter requested: {model_name}")
            continue
        adapter = importlib.import_module(adapter_path)
        available = adapter.check_availability(project_root)
        availability[model_name] = available

    for model_name in model_names:
        adapter_path = ADAPTERS.get(model_name)
        if not adapter_path:
            continue
        available = availability.get(model_name, {})
        if not available.get("available"):
            event_rows = build_status_rows(
                model_name=model_name,
                events=events,
                search_windows=search_windows,
                position_status=str(available.get("status") or "model_unavailable"),
                debug_reason=str(available.get("reason") or "Model unavailable."),
            )
        else:
            event_rows, model_errors = run_model_with_timeout(
                adapter_path=adapter_path,
                model_name=model_name,
                project_root=project_root,
                video_path=video_path,
                events=events,
                search_windows=search_windows,
                calibration=calibration,
                resize_width=resize_width,
                timeout_seconds=model_timeout_seconds,
            )
            errors.extend(model_errors)
        all_event_rows.extend(event_rows)
        summary_rows.append(summarize_model(model_name, event_rows, available))

    write_csv(output_dir / "model_event_results.csv", all_event_rows, EVENT_RESULT_FIELDS)
    write_csv(output_dir / "model_summary.csv", summary_rows, MODEL_SUMMARY_FIELDS)
    best_model = choose_best_model(summary_rows)
    report = build_report(
        annotation_path=annotation_path,
        video_path=video_path,
        model_names=model_names,
        availability=availability,
        summary_rows=summary_rows,
        best_model=best_model,
        warnings=warnings,
        errors=errors,
        output_dir=output_dir,
    )
    return {
        "report": report,
        "event_rows": all_event_rows,
        "summary_rows": summary_rows,
        "events": events,
    }


def run_model_with_timeout(
    *,
    adapter_path: str,
    model_name: str,
    project_root: Path,
    video_path: Path,
    events: list[dict[str, Any]],
    search_windows: dict[str, list[int]],
    calibration: dict[str, Any],
    resize_width: int,
    timeout_seconds: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Run one available adapter in a separate process with a hard timeout."""
    queue: mp.Queue = mp.Queue()
    process = mp.Process(
        target=_run_model_worker,
        kwargs={
            "adapter_path": adapter_path,
            "model_name": model_name,
            "project_root": str(project_root),
            "video_path": str(video_path),
            "events": events,
            "search_windows": search_windows,
            "calibration": calibration,
            "resize_width": resize_width,
            "queue": queue,
        },
    )
    process.start()
    process.join(max(1, int(timeout_seconds)))
    if process.is_alive():
        process.terminate()
        process.join(5)
        reason = f"{model_name} timeout after {timeout_seconds}s; baseline timeout / OpenCV random seek too slow."
        return (
            build_status_rows(
                model_name=model_name,
                events=events,
                search_windows=search_windows,
                position_status="error",
                debug_reason=reason,
            ),
            [reason],
        )
    if queue.empty():
        reason = f"{model_name} worker exited without returning results."
        return (
            build_status_rows(
                model_name=model_name,
                events=events,
                search_windows=search_windows,
                position_status="error",
                debug_reason=reason,
            ),
            [reason],
        )
    payload = queue.get()
    if payload.get("status") != "ok":
        reason = str(payload.get("error") or f"{model_name} failed.")
        return (
            build_status_rows(
                model_name=model_name,
                events=events,
                search_windows=search_windows,
                position_status="error",
                debug_reason=reason,
            ),
            [reason],
        )
    return payload.get("event_rows", []), payload.get("errors", [])


def _run_model_worker(
    *,
    adapter_path: str,
    model_name: str,
    project_root: str,
    video_path: str,
    events: list[dict[str, Any]],
    search_windows: dict[str, list[int]],
    calibration: dict[str, Any],
    resize_width: int,
    queue: mp.Queue,
) -> None:
    """Worker process for one model adapter."""
    try:
        adapter = importlib.import_module(adapter_path)
        context = adapter.prepare_context(
            project_root=Path(project_root),
            video_path=Path(video_path),
            events=events,
            search_windows=search_windows,
            calibration=calibration,
            resize_width=resize_width,
        )
        raw_rows = [
            adapter.resolve_event_position(Path(video_path), event, search_windows[event["event_id"]], context)
            for event in events
        ]
        projected = [project_adapter_result(row, events[index], calibration) for index, row in enumerate(raw_rows)]
        validated = validate_manual_event_sequence(projected)
        event_rows = [flatten_validated_result(row) for row in validated]
        queue.put({"status": "ok", "model_name": model_name, "event_rows": event_rows, "errors": context.get("errors", [])})
    except Exception as exc:  # pragma: no cover - defensive worker boundary
        queue.put({"status": "error", "model_name": model_name, "error": f"{type(exc).__name__}: {exc}"})


def build_status_rows(
    *,
    model_name: str,
    events: list[dict[str, Any]],
    search_windows: dict[str, list[int]],
    position_status: str,
    debug_reason: str,
) -> list[dict[str, Any]]:
    """Build per-event rows for unavailable, timed out, or failed adapters."""
    rows: list[dict[str, Any]] = []
    for event in events:
        window = search_windows.get(event["event_id"], [])
        rows.append(
            {
                "model_name": model_name,
                "event_id": event["event_id"],
                "event_type": event["event_type"],
                "shot_type": event.get("shot_type", ""),
                "manual_frame": event["contact_frame_estimate"],
                "search_start_frame": min(window) if window else "",
                "search_end_frame": max(window) if window else "",
                "resolved_frame": "",
                "image_x": "",
                "image_y": "",
                "projected_x": "",
                "projected_y": "",
                "court_zone": "unknown",
                "depth": "unknown",
                "lateral_lane": "unknown",
                "raw_score": "",
                "confidence": "low",
                "position_status": position_status,
                "position_trust": "unresolved",
                "validation_status": position_status,
                "validation_reason": debug_reason,
                "debug_reason": debug_reason,
            }
        )
    return rows


def project_adapter_result(row: dict[str, Any], event: dict[str, Any], calibration: dict[str, Any]) -> dict[str, Any]:
    """Project adapter image-space results and normalize fields for validation."""
    status = str(row.get("position_status") or "")
    base = {
        **event,
        "model_name": row.get("model_name", ""),
        "manual_frame": row.get("manual_frame", event["contact_frame_estimate"]),
        "search_start_frame": row.get("search_start_frame", ""),
        "search_end_frame": row.get("search_end_frame", ""),
        "resolved_frame": row.get("resolved_frame", ""),
        "image_x": row.get("image_x", ""),
        "image_y": row.get("image_y", ""),
        "projected_x": "",
        "projected_y": "",
        "court_zone": "unknown",
        "depth": "unknown",
        "lateral_lane": "unknown",
        "raw_score": row.get("raw_score", ""),
        "confidence": row.get("confidence", "low"),
        "event_position_status": "resolved" if status == "resolved" else "unresolved",
        "event_position_source": row.get("model_name", ""),
        "event_position_confidence": row.get("confidence", "low"),
        "detection_score": row.get("raw_score", ""),
        "projection_status": "not_attempted",
        "position_status": status,
        "debug_reason": row.get("debug_reason", ""),
    }
    if status != "resolved":
        base["projection_status"] = "not_attempted"
        return base
    return project_event_position_to_court(base, calibration)


def flatten_validated_result(row: dict[str, Any]) -> dict[str, Any]:
    """Flatten validation output to benchmark CSV fields."""
    position_status = row.get("position_status") or ("resolved" if row.get("event_position_status") == "resolved" else "unresolved")
    return {
        "model_name": row.get("model_name", ""),
        "event_id": row.get("event_id", ""),
        "event_type": row.get("event_type", ""),
        "shot_type": row.get("shot_type", ""),
        "manual_frame": row.get("manual_frame", row.get("contact_frame_estimate", "")),
        "search_start_frame": row.get("search_start_frame", ""),
        "search_end_frame": row.get("search_end_frame", ""),
        "resolved_frame": row.get("resolved_frame", ""),
        "image_x": row.get("image_x", ""),
        "image_y": row.get("image_y", ""),
        "projected_x": row.get("projected_x", ""),
        "projected_y": row.get("projected_y", ""),
        "court_zone": row.get("court_zone", "unknown"),
        "depth": row.get("depth", "unknown"),
        "lateral_lane": row.get("lateral_lane", "unknown"),
        "raw_score": row.get("raw_score", ""),
        "confidence": row.get("confidence", "low"),
        "position_status": position_status,
        "position_trust": row.get("position_trust", "unresolved"),
        "validation_status": row.get("position_validation_status", ""),
        "validation_reason": row.get("sequence_validation_reason", ""),
        "debug_reason": row.get("debug_reason", ""),
    }


def summarize_model(model_name: str, rows: list[dict[str, Any]], availability: dict[str, Any]) -> dict[str, Any]:
    """Summarize one adapter result set."""
    resolved = [row for row in rows if row["position_status"] == "resolved"]
    valid = [row for row in rows if row["position_trust"] == "valid"]
    suspicious = [row for row in rows if row["position_trust"] == "suspicious"]
    invalid = [row for row in rows if row["position_trust"] == "invalid"]
    unresolved = [row for row in rows if row["position_trust"] == "unresolved"]
    wrong_side = [row for row in rows if "wrong_side" in str(row["validation_status"])]
    score = average_confidence(rows)
    verdict = classify_model_verdict(availability, rows, valid, suspicious, invalid, unresolved)
    return {
        "model_name": model_name,
        "available": "yes" if availability.get("available") else "no",
        "events_attempted": len(rows),
        "resolved_count": len(resolved),
        "valid_count": len(valid),
        "suspicious_count": len(suspicious),
        "invalid_count": len(invalid),
        "unresolved_count": len(unresolved),
        "wrong_side_likely_count": len(wrong_side),
        "average_confidence": round(score, 3) if score is not None else "",
        "benchmark_verdict": verdict,
    }


def classify_model_verdict(
    availability: dict[str, Any],
    rows: list[dict[str, Any]],
    valid: list[dict[str, Any]],
    suspicious: list[dict[str, Any]],
    invalid: list[dict[str, Any]],
    unresolved: list[dict[str, Any]],
) -> str:
    """Classify benchmark verdict for one model."""
    if not availability.get("available"):
        return "unavailable"
    if any(row.get("position_status") == "error" for row in rows):
        return "failed"
    if not rows or len(unresolved) == len(rows):
        return "inconclusive"
    if len(valid) >= 8 and len(valid) > len(suspicious) + len(invalid):
        return "promising"
    if len(valid) <= len(suspicious) + len(invalid):
        return "failed"
    return "inconclusive"


def choose_best_model(summary_rows: list[dict[str, Any]]) -> str:
    """Choose the best promising model, if any."""
    promising = [row for row in summary_rows if row["benchmark_verdict"] == "promising"]
    if not promising:
        return "none"
    best = max(promising, key=lambda row: (int(row["valid_count"]), int(row["resolved_count"])))
    return str(best["model_name"])


def average_confidence(rows: list[dict[str, Any]]) -> float | None:
    """Convert coarse confidence labels to a simple average."""
    weights = {"high": 1.0, "medium": 0.66, "low": 0.33}
    values = [weights.get(str(row.get("confidence") or "").lower()) for row in rows if row.get("position_status") == "resolved"]
    values = [value for value in values if value is not None]
    return mean(values) if values else None


def build_report(
    *,
    annotation_path: Path,
    video_path: Path,
    model_names: list[str],
    availability: dict[str, Any],
    summary_rows: list[dict[str, Any]],
    best_model: str,
    warnings: list[str],
    errors: list[str],
    output_dir: Path,
) -> dict[str, Any]:
    """Build machine-readable benchmark report."""
    tracknet = availability.get("tracknet_candidate", {})
    sam = availability.get("sam_assisted_candidate", {})
    all_unavailable_or_failed = all(row["benchmark_verdict"] in {"failed", "unavailable", "inconclusive"} for row in summary_rows)
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stage": "ball_tracking_model_benchmark",
        "annotation_path": str(annotation_path),
        "video_path": str(video_path),
        "models_tested": model_names,
        "model_availability": availability,
        "model_summaries": summary_rows,
        "best_model": best_model,
        "tracknet_path_worth_continuing": bool(not tracknet.get("available")),
        "tracknet_reason": tracknet.get("reason", "TrackNet-style temporal heatmaps remain the preferred direction for small fast tennis-ball tracking."),
        "sam_path_worth_continuing": bool(sam.get("available")),
        "sam_reason": sam.get("reason", "SAM is unavailable or unwired locally; it is not an immediate replacement for temporal tennis-ball tracking."),
        "all_models_failed_or_unavailable": all_unavailable_or_failed,
        "interpretation": interpret_results(summary_rows, availability),
        "recommended_next_step": recommend_next_step(summary_rows, availability, best_model),
        "warnings": warnings,
        "errors": errors,
        "output_paths": {
            "model_event_results_csv": str(output_dir / "model_event_results.csv"),
            "model_summary_csv": str(output_dir / "model_summary.csv"),
            "report_json": str(output_dir.parents[1] / "reports" / "ball_tracking_model_benchmark_report.json"),
            "report_md": str(output_dir.parents[1] / "reports" / "ball_tracking_model_benchmark_report.md"),
        },
    }


def interpret_results(summary_rows: list[dict[str, Any]], availability: dict[str, Any]) -> str:
    """Explain what the benchmark says about detector/model risk."""
    baseline = next((row for row in summary_rows if row["model_name"] == "baseline_current"), None)
    if baseline and baseline["benchmark_verdict"] == "failed":
        return "The current local HSV/motion candidate detector remains the bottleneck: it resolves positions, but too many fail tennis-sequence plausibility."
    if all(not item.get("available") for name, item in availability.items() if name != "baseline_current"):
        return "Alternative model families were not available locally, so this run mainly confirms the baseline failure and integration gap."
    return "Benchmark results are inconclusive; inspect per-event rows before choosing a replacement tracker."


def recommend_next_step(summary_rows: list[dict[str, Any]], availability: dict[str, Any], best_model: str) -> str:
    """Recommend next action from benchmark results."""
    if best_model != "none":
        return f"Continue with {best_model} and wire it into event position resolution."
    tracknet = availability.get("tracknet_candidate", {})
    if not tracknet.get("available"):
        return "Acquire or integrate a local TrackNet-style pretrained temporal heatmap tracker before continuing replay/product pipeline work."
    return "Pause downstream replay work and research capture/model strategy for reliable tennis-ball localization."


def report_markdown(report: dict[str, Any]) -> str:
    """Render a plain-text-friendly Markdown report."""
    summary_blocks = []
    for row in report["model_summaries"]:
        summary_blocks.append(
            f"""  Model: {row['model_name']}
    available: {row['available']}
    resolved: {row['resolved_count']}
    valid: {row['valid_count']}
    suspicious: {row['suspicious_count']}
    invalid: {row['invalid_count']}
    unresolved: {row['unresolved_count']}
    verdict: {row['benchmark_verdict']}"""
        )
    warnings = "\n".join(f"  - {item}" for item in report["warnings"]) or "  None"
    errors = "\n".join(f"  - {item}" for item in report["errors"]) or "  None"
    return f"""# Ball Tracking Model Benchmark Report

WHY THIS EXISTS
  Current YOLO/HSV/local detector failed spatial replay feasibility.
  Manual timing was correct, but local ball position resolution produced
  tennis-sequence-invalid court anchors.

MODELS TESTED
{chr(10).join(f"  {item}" for item in report["models_tested"])}

RESULT SUMMARY
{chr(10).join(summary_blocks)}

INTERPRETATION
  {report["interpretation"]}

TRACKNET PATH
  Worth continuing: {report["tracknet_path_worth_continuing"]}
  Reason: {report["tracknet_reason"]}

SAM PATH
  Worth continuing now: {report["sam_path_worth_continuing"]}
  Reason: {report["sam_reason"]}

BEST MODEL
  {report["best_model"]}

WARNINGS
{warnings}

ERRORS
{errors}

RECOMMENDED NEXT STEP
  {report["recommended_next_step"]}
"""


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    """Write CSV rows with stable fields."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    """Write JSON with stable formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
