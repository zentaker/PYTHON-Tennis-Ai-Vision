"""Event reclassification helpers for Stage 8.3."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def reclassify_auto_event(
    auto_event: dict[str, Any],
    *,
    validation_status: str,
    nearest_manual_label: str,
    manual_hit_count: int,
) -> dict[str, Any]:
    """Reclassify one automatic event using manual event validation."""
    auto_type = str(auto_event.get("auto_event_type") or "auto_unknown")
    confidence_before = float(auto_event.get("confidence_before") or 0.5)
    if auto_type == "auto_possible_hit" and validation_status == "contradicted_by_bounce_window":
        return build_reclassification("possible_bounce_candidate", "bounce_validated", confidence_before, -0.2, "Manual bounce window contradicts automatic hit.", True, True)
    if auto_type == "auto_possible_hit" and validation_status == "contradicted_by_no_event":
        return build_reclassification("rejected_event", "rejected_event", confidence_before, -0.45, "Manual no_event contradicts automatic hit.", False, False)
    if auto_type == "auto_possible_hit" and validation_status == "validated_by_manual_label" and nearest_manual_label == "hit":
        return build_reclassification("validated_possible_hit", "hit_validated", confidence_before, 0.2, "Manual hit label supports automatic hit.", True, True)
    if auto_type == "auto_possible_hit" and manual_hit_count == 0:
        return build_reclassification("possible_hit_unvalidated", "hit_unvalidated", confidence_before, -0.25, "No hit events are confirmed because no manual hit labels were provided.", False, True)
    if auto_type == "auto_possible_bounce" and validation_status == "validated_by_manual_label":
        return build_reclassification("validated_possible_bounce", "bounce_validated", confidence_before, 0.2, "Manual bounce window supports automatic bounce.", True, True)
    if auto_type == "auto_ball_near_player":
        return build_reclassification("ball_near_player", "interaction_cue", confidence_before, -0.05, "Player interaction cue retained; not treated as a hit.", False, True)
    if validation_status == "near_uncertain_label":
        return build_reclassification("uncertain_event", "uncertain_event", confidence_before, -0.15, "Nearby manual label is uncertain.", False, True)
    if validation_status == "outside_manual_coverage":
        return build_reclassification(auto_type.replace("auto_", ""), "trajectory_annotation", confidence_before, -0.1, "Outside manual coverage; kept as unvalidated hypothesis.", False, True)
    if auto_type in {"auto_direction_change", "auto_speed_spike", "auto_speed_drop"}:
        return build_reclassification(auto_type.replace("auto_", ""), "trajectory_annotation", confidence_before, -0.05, "Trajectory annotation retained as non-physical event.", False, True)
    return build_reclassification("uncertain_event", "uncertain_event", confidence_before, -0.2, "Automatic event remains unvalidated.", False, True)


def build_reclassification(
    event_type: str,
    render_role: str,
    confidence_before: float,
    adjustment: float,
    reason: str,
    physical: bool,
    annotation: bool,
) -> dict[str, Any]:
    """Build a reclassification result dictionary."""
    confidence_after = max(0.0, min(1.0, confidence_before + adjustment))
    return {
        "reclassified_event_type": event_type,
        "render_role": render_role,
        "confidence_after": round(confidence_after, 3),
        "confidence_adjustment": round(adjustment, 3),
        "reason": reason,
        "should_render_as_physical_event": "yes" if physical else "no",
        "should_render_as_annotation": "yes" if annotation else "no",
    }


def calculate_event_confidence_adjustment(validation_status: str) -> float:
    """Return a simple confidence adjustment for validation status."""
    return {
        "validated_by_manual_label": 0.2,
        "contradicted_by_no_event": -0.45,
        "contradicted_by_bounce_window": -0.2,
        "contradicted_by_hit_window": -0.2,
        "near_uncertain_label": -0.15,
        "outside_manual_coverage": -0.1,
        "no_manual_label_nearby": -0.1,
    }.get(validation_status, 0.0)


def build_validated_event_timeline(validation_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build validated event timeline rows from event validation results."""
    timeline: list[dict[str, Any]] = []
    for index, row in enumerate(validation_results, start=1):
        timeline.append(
            {
                "event_id": f"v_evt_{index:03d}",
                "frame_index": row.get("auto_frame_index"),
                "original_event_type": row.get("auto_event_type"),
                "validated_event_type": row.get("reclassified_event_type"),
                "render_role": row.get("render_role"),
                "player_id": row.get("player_id") or "",
                "validation_status": row.get("validation_status"),
                "confidence_like_score": row.get("confidence_before"),
                "confidence_adjusted": row.get("confidence_after"),
                "reason": row.get("reason"),
                "source": row.get("auto_event_source"),
                "manual_support": row.get("nearest_manual_label") or "",
                "should_render_as_physical_event": row.get("should_render_as_physical_event"),
                "should_render_as_annotation": row.get("should_render_as_annotation"),
            }
        )
    return timeline


def summarize_reclassification(validation_results: list[dict[str, Any]], manual_summary: dict[str, int]) -> dict[str, Any]:
    """Summarize event validation and reclassification outputs."""
    validated_bounce = sum(1 for row in validation_results if row.get("render_role") == "bounce_validated")
    validated_hit = sum(1 for row in validation_results if row.get("render_role") == "hit_validated")
    downgraded_hit = sum(
        1
        for row in validation_results
        if row.get("auto_event_type") == "auto_possible_hit" and row.get("render_role") in {"hit_unvalidated", "uncertain_event", "rejected_event", "bounce_validated"}
    )
    rejected = sum(1 for row in validation_results if row.get("render_role") == "rejected_event")
    outside = sum(1 for row in validation_results if row.get("validation_status") == "outside_manual_coverage")
    unvalidated = sum(1 for row in validation_results if row.get("validation_status") in {"no_manual_label_nearby", "near_uncertain_label", "outside_manual_coverage"})
    recommendation = "Proceed to Stage 14.3 using validated events."
    if manual_summary.get("manual_hit_count", 0) == 0:
        recommendation = "Proceed cautiously: no hit events are confirmed because no manual hit labels were provided."
    return {
        **manual_summary,
        "auto_events_count": len(validation_results),
        "validated_bounce_count": validated_bounce,
        "validated_hit_count": validated_hit,
        "downgraded_hit_count": downgraded_hit,
        "rejected_event_count": rejected,
        "unvalidated_event_count": unvalidated,
        "outside_coverage_count": outside,
        "recommendation": recommendation,
    }


def write_event_validation_results_csv(path: Path, rows: list[dict[str, Any]]) -> Path:
    """Write event validation result CSV."""
    return write_csv(
        path,
        rows,
        [
            "auto_event_id",
            "auto_event_source",
            "auto_frame_index",
            "auto_event_type",
            "nearest_manual_label",
            "nearest_manual_frame_or_window",
            "frame_delta",
            "validation_status",
            "reclassified_event_type",
            "confidence_before",
            "confidence_after",
            "reason",
        ],
    )


def write_validated_event_timeline_csv(path: Path, rows: list[dict[str, Any]]) -> Path:
    """Write validated event timeline CSV."""
    return write_csv(
        path,
        rows,
        [
            "event_id",
            "frame_index",
            "original_event_type",
            "validated_event_type",
            "render_role",
            "player_id",
            "validation_status",
            "confidence_like_score",
            "confidence_adjusted",
            "reason",
            "source",
            "manual_support",
            "should_render_as_physical_event",
            "should_render_as_annotation",
        ],
    )


def write_event_validation_summary_json(path: Path, summary: dict[str, Any]) -> Path:
    """Write event validation summary JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> Path:
    """Write rows to CSV with stable fields."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    return path
