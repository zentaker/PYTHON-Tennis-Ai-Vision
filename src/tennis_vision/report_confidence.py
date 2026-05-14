"""Confidence scoring helpers for Stage 10 analytical reports."""

from __future__ import annotations

from typing import Any


def numeric_values(rows: list[dict[str, Any]], key: str) -> list[float]:
    """Return numeric values from a row field."""
    values: list[float] = []
    for row in rows:
        try:
            value = row.get(key)
            if value not in (None, ""):
                values.append(float(value))
        except (TypeError, ValueError):
            continue
    return values


def summarize_candidate_distance(candidate_validation_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize candidate distance from expanded label validation rows."""
    distances = numeric_values(candidate_validation_rows, "distance_px")
    if not distances:
        return {"average_candidate_distance": None, "median_candidate_distance": None, "matched_count": 0}
    sorted_distances = sorted(distances)
    mid = len(sorted_distances) // 2
    median = sorted_distances[mid] if len(sorted_distances) % 2 else (sorted_distances[mid - 1] + sorted_distances[mid]) / 2
    return {
        "average_candidate_distance": round(sum(distances) / len(distances), 3),
        "median_candidate_distance": round(median, 3),
        "matched_count": len(distances),
    }


def evaluate_report_confidence(
    *,
    label_count: int,
    projected_points_count: int,
    unknown_zone_count: int,
    candidate_validation_rows: list[dict[str, Any]],
    validated_events_count: int,
    supported_events_count: int,
    player_identity_count: int,
) -> dict[str, Any]:
    """Evaluate Stage 10 report confidence from upstream evidence quality."""
    reasons: list[str] = []
    limiting_factors: list[str] = []
    validation_steps: list[str] = []
    score = 0

    if label_count >= 10:
        score += 25
        reasons.append(f"{label_count} visible expanded ball labels are available.")
    else:
        limiting_factors.append("Fewer than 10 visible ball labels are available.")
        validation_steps.append("Collect more manual ball labels.")

    if label_count and projected_points_count == label_count and unknown_zone_count == 0:
        score += 25
        reasons.append("All visible labels have projected court coordinates and no unknown zones.")
    elif projected_points_count:
        score += 12
        limiting_factors.append("Some labels still lack confident zone assignment.")
        validation_steps.append("Review projection coverage and court zone bounds.")
    else:
        limiting_factors.append("No projected ball points are available.")
        validation_steps.append("Fix court projection before generating tactical reports.")

    distance_summary = summarize_candidate_distance(candidate_validation_rows)
    average_distance = distance_summary["average_candidate_distance"]
    if average_distance is not None and average_distance <= 10:
        score += 20
        reasons.append(f"Candidate validation distance is low on matched frames ({average_distance} px average).")
    elif average_distance is not None and average_distance <= 50:
        score += 10
        limiting_factors.append(f"Candidate validation distance is moderate ({average_distance} px average).")
        validation_steps.append("Validate more candidate frames.")
    else:
        limiting_factors.append("Candidate distance is missing or too high for strong confidence.")
        validation_steps.append("Rerun candidate validation with more labels.")

    if validated_events_count and supported_events_count == validated_events_count:
        score += 15
        reasons.append("All timeline events in the validated timeline are label-supported.")
    elif supported_events_count:
        score += 7
        limiting_factors.append("Only some timeline events are label-supported.")
        validation_steps.append("Add manual event validation.")
    else:
        limiting_factors.append("Timeline event support is missing.")
        validation_steps.append("Validate possible_* events before stronger reporting.")

    if player_identity_count >= 2:
        score += 10
        reasons.append("Two main player identities are available from Stage 7.1.")
    else:
        limiting_factors.append("Player identity context is incomplete.")
        validation_steps.append("Review player identity filtering.")

    if score >= 90 and label_count >= 20:
        level = "high"
    elif score >= 70:
        level = "medium-high"
    elif score >= 45:
        level = "medium"
    else:
        level = "low"

    return {
        "confidence_level": level,
        "confidence_score": min(score, 100),
        "confidence_reasons": reasons,
        "limiting_factors": limiting_factors or ["No major limiting factors detected for this prototype report."],
        "recommended_validation_steps": validation_steps or ["Proceed to Stage 11 while preserving uncertainty in report wording."],
        "candidate_distance_summary": distance_summary,
    }
