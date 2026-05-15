"""SAM/SAM2-assisted replay feasibility pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tennis_vision.manual_event_position_resolver import load_manual_full_rally_annotation, normalize_manual_events
from tennis_vision.model_adapters import sam_assisted_adapter
from tennis_vision.tennis_sequence_validator import validate_manual_event_sequence
from tennis_vision.tracknet_replay_pipeline import (
    BALL_TRACKING_FIELDS,
    PROJECTED_FIELDS,
    build_replay_schema,
    event_search_range,
    flatten_event_row,
    maybe_render_replays,
    normalize_tracking_rows,
    project_tracking_rows,
    write_csv,
    write_json,
    _float,
)
from tennis_vision.court_projection import load_stage_3_calibration


EVENT_POSITION_FIELDS = [
    "event_id",
    "sequence_index",
    "event_type",
    "shot_type",
    "manual_start_frame",
    "manual_end_frame",
    "manual_contact_frame",
    "resolved_frame",
    "image_x",
    "image_y",
    "projected_x",
    "projected_y",
    "court_zone",
    "depth",
    "lateral_lane",
    "sam_confidence",
    "position_status",
    "position_trust",
    "validation_status",
    "validation_reason",
    "should_render_as_physical_event",
    "should_render_as_annotation",
]


def run_sam_assisted_replay_pipeline(
    *,
    project_root: Path,
    video_path: Path,
    annotation_path: Path,
    output_dir: Path,
    fps: int = 60,
    rally_padding: int = 15,
    event_search_padding: int = 5,
    sam_weights: Path | None = None,
    generate_replays: bool = True,
) -> dict[str, Any]:
    """Run SAM-assisted replay feasibility or write a blocked report."""
    del rally_padding
    output_dir.mkdir(parents=True, exist_ok=True)
    annotation = load_manual_full_rally_annotation(annotation_path)
    events = normalize_manual_events(annotation)
    hits = [event for event in events if event["event_type"] == "hit"]
    bounces = [event for event in events if event["event_type"] == "bounce"]

    availability = sam_assisted_adapter.check_availability(project_root, weights_path=sam_weights)
    seed_rows = load_seed_rows(project_root)
    tracking_result = track_events_with_sam(
        project_root=project_root,
        video_path=video_path,
        events=events,
        availability=availability,
        weights_path=sam_weights,
        seed_rows=seed_rows,
        event_search_padding=event_search_padding,
        fps=fps,
    )
    tracked_rows = normalize_tracking_rows(tracking_result.get("tracked_frames", []), fps=fps)
    write_csv(output_dir / "ball_tracking_results.csv", tracked_rows, BALL_TRACKING_FIELDS)

    calibration = load_stage_3_calibration(project_root / "outputs" / "reports" / "stage_3_court_calibration_probe_report.json")
    projected_rows = project_tracking_rows(tracked_rows, calibration)
    write_csv(output_dir / "projected_ball_positions.csv", projected_rows, PROJECTED_FIELDS)

    event_rows = resolve_events_from_sam(
        events=events,
        projected_rows=projected_rows,
        event_search_padding=event_search_padding,
        blocked_status=str(tracking_result.get("status") or availability.get("status") or ""),
        blocked_reason=str(tracking_result.get("reason") or availability.get("reason") or ""),
    )
    write_csv(output_dir / "event_position_results.csv", event_rows, EVENT_POSITION_FIELDS)

    schema = build_replay_schema(
        annotation=annotation,
        annotation_path=annotation_path,
        video_path=video_path,
        output_dir=output_dir,
        availability={**availability, "status": availability.get("status", ""), "weights_path": availability.get("weights_path", "")},
        tracked_rows=tracked_rows,
        projected_rows=projected_rows,
        event_rows=event_rows,
    )
    schema["metadata"]["pipeline"] = "sam_assisted_replay_pipeline"
    schema["metadata"]["model_source"] = "SAM/SAM2-assisted segmentation candidate"
    schema["metadata"]["model_status"] = availability.get("status", "")
    write_json(output_dir / "replay_schema.json", schema)
    (output_dir / "replay_schema_pretty.md").write_text(sam_schema_markdown(schema), encoding="utf-8")

    render_results = maybe_render_replays(event_rows, output_dir=output_dir, fps=12, enabled=generate_replays)
    report = build_report(
        availability=availability,
        tracking_result=tracking_result,
        video_path=video_path,
        annotation_path=annotation_path,
        events=events,
        hits=hits,
        bounces=bounces,
        tracked_rows=tracked_rows,
        projected_rows=projected_rows,
        event_rows=event_rows,
        output_dir=output_dir,
        render_results=render_results,
    )
    write_json(output_dir / "sam_replay_report.json", report)
    (output_dir / "sam_replay_report.md").write_text(report_markdown(report), encoding="utf-8")
    return report


def load_seed_rows(project_root: Path) -> list[dict[str, Any]]:
    """Load trusted ball seed rows when previous validated labels exist."""
    import csv

    candidates = [
        project_root / "outputs" / "timeline" / "stage_8_1_timeline_validation" / "expanded_ball_labels.csv",
        project_root / "outputs" / "tactical" / "stage_9_1_projection_coverage" / "projected_expanded_labels.csv",
    ]
    rows: list[dict[str, Any]] = []
    for path in candidates:
        if not path.exists():
            continue
        with path.open("r", newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                frame = row.get("frame_index") or row.get("frame")
                x = row.get("x") or row.get("ball_x") or row.get("image_x")
                y = row.get("y") or row.get("ball_y") or row.get("image_y")
                if frame not in (None, "") and x not in (None, "") and y not in (None, ""):
                    rows.append({"frame_index": frame, "x": x, "y": y, "source": str(path)})
    return rows


def track_events_with_sam(
    *,
    project_root: Path,
    video_path: Path,
    events: list[dict[str, Any]],
    availability: dict[str, Any],
    weights_path: Path | None,
    seed_rows: list[dict[str, Any]],
    event_search_padding: int,
    fps: int,
) -> dict[str, Any]:
    """Track local event windows with SAM if model and seeds are ready."""
    if not availability.get("available"):
        return {
            "status": availability.get("status"),
            "tracked_frames": [],
            "reason": availability.get("reason"),
            "seed_available": bool(seed_rows),
            "availability": availability,
        }
    if not seed_rows:
        return {
            "status": "seed_missing",
            "tracked_frames": [],
            "reason": "SAM/SAM2 requires a trusted ball seed point; no seed labels were found near manual event windows.",
            "seed_available": False,
            "availability": availability,
        }
    try:
        selected_weights = weights_path if weights_path else Path(str(availability["weights_path"]))
        model_context = sam_assisted_adapter.load_model(selected_weights, project_root)
    except Exception as exc:  # pragma: no cover - depends on local SAM assets
        return {
            "status": "model_load_failed",
            "tracked_frames": [],
            "reason": f"SAM model load failed: {type(exc).__name__}: {exc}",
            "seed_available": bool(seed_rows),
            "availability": availability,
        }

    tracked_by_frame: dict[int, dict[str, Any]] = {}
    seed_missing = 0
    for event in events:
        search_start, search_end = event_search_range(event, event_search_padding)
        prompt = sam_assisted_adapter.initialize_prompt(event, {"seed_rows": seed_rows, "seed_tolerance": event_search_padding})
        if not prompt.get("seed_available"):
            seed_missing += 1
            continue
        result = sam_assisted_adapter.track_clip(
            video_path=video_path,
            event=event,
            search_start_frame=search_start,
            search_end_frame=search_end,
            model_context=model_context,
            prompt=prompt,
            fps=fps,
        )
        for row in result.get("tracked_frames", []):
            tracked_by_frame[int(row["frame_index"])] = row
    rows = [tracked_by_frame[key] for key in sorted(tracked_by_frame)]
    return {
        "status": "resolved" if rows else "seed_missing" if seed_missing else "unresolved",
        "tracked_frames": rows,
        "reason": "SAM-assisted event tracking completed." if rows else "No SAM-assisted event clips produced ball masks.",
        "seed_available": bool(seed_rows),
        "events_without_seed": seed_missing,
        "availability": availability,
    }


def resolve_events_from_sam(
    *,
    events: list[dict[str, Any]],
    projected_rows: list[dict[str, Any]],
    event_search_padding: int,
    blocked_status: str,
    blocked_reason: str,
) -> list[dict[str, Any]]:
    """Resolve manual event positions from SAM-assisted trajectory rows."""
    by_frame = {int(row["frame_index"]): row for row in projected_rows if row.get("frame_index") not in (None, "")}
    raw_events: list[dict[str, Any]] = []
    for event in events:
        search_start, search_end = event_search_range(event, event_search_padding)
        candidates = [row for frame, row in by_frame.items() if search_start <= frame <= search_end]
        best = max(candidates, key=lambda row: (_float(row.get("confidence")) or 0.0, -abs(int(row["frame_index"]) - int(event["contact_frame_estimate"]))), default=None)
        if not best:
            raw_events.append(unresolved_event_row(event, blocked_status=blocked_status, blocked_reason=blocked_reason))
            continue
        raw_events.append(
            {
                **event,
                "manual_start_frame": event["start_frame"],
                "manual_end_frame": event["end_frame"],
                "manual_contact_frame": event["contact_frame_estimate"],
                "resolved_frame": best["frame_index"],
                "image_x": best.get("ball_x", ""),
                "image_y": best.get("ball_y", ""),
                "projected_x": best.get("projected_x", ""),
                "projected_y": best.get("projected_y", ""),
                "court_zone": best.get("court_zone", "unknown"),
                "depth": best.get("depth", "unknown"),
                "lateral_lane": best.get("lateral_lane", "unknown"),
                "sam_confidence": best.get("confidence", ""),
                "tracknet_confidence": best.get("confidence", ""),
                "event_position_status": "resolved",
                "event_position_source": "sam_assisted",
                "event_position_confidence": confidence_from_value(best.get("confidence")),
                "projection_status": best.get("projection_status", ""),
                "position_status": "resolved",
            }
        )
    validated = validate_manual_event_sequence(raw_events)
    rows = [flatten_event_row(row) for row in validated]
    for row in rows:
        row["sam_confidence"] = row.pop("tracknet_confidence", "")
    return rows


def unresolved_event_row(event: dict[str, Any], *, blocked_status: str, blocked_reason: str) -> dict[str, Any]:
    """Create an unresolved SAM event row."""
    reason = blocked_reason or "No SAM-assisted trajectory point was available near this manual event."
    return {
        **event,
        "manual_start_frame": event["start_frame"],
        "manual_end_frame": event["end_frame"],
        "manual_contact_frame": event["contact_frame_estimate"],
        "resolved_frame": "",
        "image_x": "",
        "image_y": "",
        "projected_x": "",
        "projected_y": "",
        "court_zone": "unknown",
        "depth": "unknown",
        "lateral_lane": "unknown",
        "sam_confidence": "",
        "tracknet_confidence": "",
        "event_position_status": "unresolved",
        "event_position_source": "sam_assisted",
        "event_position_confidence": "low",
        "projection_status": "not_attempted",
        "position_status": blocked_status or "unresolved",
        "position_notes": reason,
    }


def build_report(
    *,
    availability: dict[str, Any],
    tracking_result: dict[str, Any],
    video_path: Path,
    annotation_path: Path,
    events: list[dict[str, Any]],
    hits: list[dict[str, Any]],
    bounces: list[dict[str, Any]],
    tracked_rows: list[dict[str, Any]],
    projected_rows: list[dict[str, Any]],
    event_rows: list[dict[str, Any]],
    output_dir: Path,
    render_results: dict[str, Any],
) -> dict[str, Any]:
    """Build SAM-assisted replay pipeline report."""
    valid = [row for row in event_rows if row["position_trust"] == "valid"]
    suspicious = [row for row in event_rows if row["position_trust"] == "suspicious"]
    invalid = [row for row in event_rows if row["position_trust"] == "invalid"]
    unresolved = [row for row in event_rows if row["position_trust"] == "unresolved"]
    projected_count = sum(1 for row in projected_rows if row.get("projection_status") == "projected")
    top_view_generated = bool(render_results.get("top_view_generated")) and (output_dir / "top_view_replay.mp4").exists()
    side_view_generated = bool(render_results.get("side_view_generated")) and (output_dir / "side_view_replay.mp4").exists()
    verdict, failure_reason = classify_verdict(availability, tracking_result, event_rows, top_view_generated, side_view_generated)
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stage": "sam_assisted_replay_pipeline",
        "model_available": bool(availability.get("available")),
        "weights_found": bool(availability.get("weights_found")),
        "dependencies_available": bool(availability.get("dependencies_available")),
        "segment_anything_available": bool(availability.get("segment_anything_available")),
        "sam2_available": bool(availability.get("sam2_available")),
        "seed_available": bool(tracking_result.get("seed_available")),
        "model_name": "sam_assisted",
        "model_weights_path": availability.get("weights_path", ""),
        "architecture_available": bool(availability.get("architecture_available")),
        "ready_for_inference": bool(availability.get("ready_for_inference")),
        "video_path": str(video_path),
        "manual_annotation_source": str(annotation_path),
        "manual_events_count": len(events),
        "hits_count": len(hits),
        "bounces_count": len(bounces),
        "tracked_frames_count": len(tracked_rows),
        "event_positions_resolved": sum(1 for row in event_rows if row["position_status"] == "resolved"),
        "event_positions_valid": len(valid),
        "event_positions_suspicious": len(suspicious),
        "event_positions_invalid": len(invalid),
        "event_positions_unresolved": len(unresolved),
        "projected_positions_count": projected_count,
        "top_view_generated": top_view_generated,
        "side_view_generated": side_view_generated,
        "curve_segments_count": int(render_results.get("curve_segments_count") or 0),
        "net_clearance_adjustments": int(render_results.get("net_clearance_adjustments") or 0),
        "replay_trustworthy": verdict == "ready_for_review",
        "failure_reason": failure_reason or render_results.get("reason", ""),
        "recommended_next_step": recommended_next_step(verdict, availability, tracking_result),
        "final_verdict": verdict,
        "sam_status": tracking_result.get("status", availability.get("status", "")),
        "warnings": ["SAM/SAM2 is experimental for tennis ball localization and requires validation against sequence rules."],
        "errors": [] if verdict.startswith("blocked") else [],
        "output_folder": str(output_dir),
        "output_paths": {
            "ball_tracking_results": str(output_dir / "ball_tracking_results.csv"),
            "projected_ball_positions": str(output_dir / "projected_ball_positions.csv"),
            "event_position_results": str(output_dir / "event_position_results.csv"),
            "replay_schema": str(output_dir / "replay_schema.json"),
            "top_view_replay": str(output_dir / "top_view_replay.mp4"),
            "side_view_replay": str(output_dir / "side_view_replay.mp4"),
            "report_json": str(output_dir / "sam_replay_report.json"),
            "report_md": str(output_dir / "sam_replay_report.md"),
        },
    }


def classify_verdict(
    availability: dict[str, Any],
    tracking_result: dict[str, Any],
    event_rows: list[dict[str, Any]],
    top: bool,
    side: bool,
) -> tuple[str, str]:
    """Classify SAM-assisted pipeline result."""
    status = availability.get("status")
    track_status = tracking_result.get("status")
    if status == "dependency_missing":
        return "blocked_dependency_missing", availability.get("reason", "SAM/SAM2 dependency is missing.")
    if status == "weights_missing":
        return "blocked_weights_missing", availability.get("reason", "SAM/SAM2 weights are missing.")
    if track_status == "seed_missing":
        return "blocked_seed_missing", tracking_result.get("reason", "SAM/SAM2 requires a seed point.")
    if status in {"architecture_missing", "inference_not_implemented", "model_load_failed"}:
        return "needs_better_sam_integration", availability.get("reason", "SAM/SAM2 inference is not ready.")
    valid = sum(1 for row in event_rows if row["position_trust"] == "valid")
    unresolved = sum(1 for row in event_rows if row["position_trust"] == "unresolved")
    if valid >= 10 and top and side:
        return "ready_for_review", ""
    if unresolved >= len(event_rows) / 2:
        return "needs_better_sam_integration", "SAM-assisted tracking did not resolve enough event positions."
    if top or side:
        return "ready_with_warnings", "Replay generated with validation warnings."
    return "failed", "Replay would require fake anchors, so it was not generated."


def recommended_next_step(verdict: str, availability: dict[str, Any], tracking_result: dict[str, Any]) -> str:
    """Return recommended next step."""
    if verdict == "blocked_dependency_missing":
        return "Install local segment_anything or sam2 dependencies, then rerun scripts/check_sam_assisted_integration.py."
    if verdict == "blocked_weights_missing":
        return "Place SAM/SAM2 weights in models/sam/weights/ or models/sam2/weights/, or pass --sam-weights."
    if verdict == "blocked_seed_missing":
        return "Provide trusted ball seed labels near manual event windows before using SAM-assisted tracking."
    if verdict == "needs_better_sam_integration":
        return availability.get("reason") or tracking_result.get("reason") or "Wire a concrete SAM/SAM2 predictor path."
    return "Review SAM-assisted replay outputs and compare them against TrackNet."


def report_markdown(report: dict[str, Any]) -> str:
    """Render plain-text-friendly SAM report Markdown."""
    return f"""# SAM-Assisted Replay Pipeline Report

VERDICT
  Final verdict: {report["final_verdict"]}
  Replay trustworthy: {report["replay_trustworthy"]}

MODEL
  Model available: {report["model_available"]}
  Dependencies available: {report["dependencies_available"]}
  segment_anything available: {report["segment_anything_available"]}
  sam2 available: {report["sam2_available"]}
  Weights found: {report["weights_found"]}
  Seed/prompt available: {report["seed_available"]}
  Ready for inference: {report["ready_for_inference"]}
  Model weights path: {report["model_weights_path"] or "None"}

SUMMARY
  Manual events: {report["manual_events_count"]}
  Hits: {report["hits_count"]}
  Bounces: {report["bounces_count"]}
  Tracked frames: {report["tracked_frames_count"]}
  Projected positions: {report["projected_positions_count"]}
  Valid event positions: {report["event_positions_valid"]}
  Suspicious event positions: {report["event_positions_suspicious"]}
  Invalid event positions: {report["event_positions_invalid"]}
  Unresolved event positions: {report["event_positions_unresolved"]}

REPLAY OUTPUTS
  Top-view generated: {report["top_view_generated"]}
  Side-view generated: {report["side_view_generated"]}
  Curve segments: {report["curve_segments_count"]}

IMPORTANT LIMITATION
  SAM/SAM2 is experimental for tennis ball localization.
  It is not equivalent to TrackNet unless it resolves event positions correctly.
  No fake ball positions or fallback YOLO/HSV anchors are used here.

FAILURE REASON
  {report["failure_reason"] or "None"}

RECOMMENDED NEXT STEP
  {report["recommended_next_step"]}

OUTPUTS
  Ball tracking: {report["output_paths"]["ball_tracking_results"]}
  Projected positions: {report["output_paths"]["projected_ball_positions"]}
  Event positions: {report["output_paths"]["event_position_results"]}
  Replay schema: {report["output_paths"]["replay_schema"]}
"""


def sam_schema_markdown(schema: dict[str, Any]) -> str:
    """Render SAM replay schema summary Markdown."""
    return f"""# SAM-Assisted Replay Schema

Pipeline:
  {schema["metadata"]["pipeline"]}

Model status:
  {schema["metadata"]["model_status"]}

Tracked frames:
  {schema["ball_tracking_results"]["tracked_frames_count"]}

Event positions:
  {len(schema["event_positions"])}

Limitations:
  - SAM/SAM2 requires a prompt or seed point.
  - Manual annotation supplies event timing only.
  - Validated physical anchors are required before replay rendering.
  - Side-view height is synthetic, not measured 3D.
"""


def confidence_from_value(value: Any) -> str:
    """Convert numeric confidence into a coarse label."""
    score = _float(value)
    if score is None:
        return "low"
    if score >= 0.75:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"
