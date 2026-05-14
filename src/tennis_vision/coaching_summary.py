"""Rule-based coaching-style summaries for Stage 10."""

from __future__ import annotations

from pathlib import Path
from typing import Any


CAUTION = "This is a prototype observation from limited labeled frames, not official coaching advice."


def most_common_distribution_value(distribution: dict[str, int]) -> tuple[str, int]:
    """Return the most common distribution value."""
    if not distribution:
        return "unknown", 0
    return sorted(distribution.items(), key=lambda item: (-item[1], item[0]))[0]


def build_coaching_observations(summary: dict[str, Any], confidence: dict[str, Any]) -> list[dict[str, Any]]:
    """Build cautious, deterministic coaching-style observations."""
    observations: list[dict[str, Any]] = []
    depth, depth_count = most_common_distribution_value(summary.get("depth_distribution", {}))
    lane, lane_count = most_common_distribution_value(summary.get("lateral_distribution", {}))
    direction, direction_count = most_common_distribution_value(summary.get("direction_distribution", {}))

    if depth != "unknown":
        observations.append(
            {
                "title": "Placement depth pattern",
                "what_it_suggests": f"In this sample, ball placements appear {depth}-oriented ({depth_count} points).",
                "confidence": confidence["confidence_level"],
                "limitation": CAUTION,
            }
        )
    else:
        observations.append(
            {
                "title": "Placement depth pattern",
                "what_it_suggests": "Depth placement could not be summarized reliably from the available data.",
                "confidence": "low",
                "limitation": "More projected labels are needed before making depth observations.",
            }
        )

    if lane != "unknown":
        observations.append(
            {
                "title": "Lateral placement pattern",
                "what_it_suggests": f"The current sample appears {lane}-oriented laterally ({lane_count} points).",
                "confidence": confidence["confidence_level"],
                "limitation": CAUTION,
            }
        )

    observations.append(
        {
            "title": "Shot direction pattern",
            "what_it_suggests": (
                f"Direction estimates are mostly {direction} ({direction_count} estimates)."
                if direction != "unknown"
                else "Shot direction estimates are limited and should be interpreted cautiously."
            ),
            "confidence": "medium" if summary.get("direction_estimates_count", 0) >= 4 else "low",
            "limitation": "Direction estimates are hypothesis-based and depend on sparse projected ball points.",
        }
    )

    if summary.get("supported_events_count", 0):
        observations.append(
            {
                "title": "Event support",
                "what_it_suggests": f"{summary['supported_events_count']} timeline events are supported by expanded ball labels.",
                "confidence": confidence["confidence_level"],
                "limitation": "possible_* events are still not confirmed hits, bounces, or tactical events.",
            }
        )
    return observations


def build_key_findings(summary: dict[str, Any], confidence: dict[str, Any]) -> list[str]:
    """Build short report findings."""
    findings = [
        f"The report analyzed {summary['label_count']} visible ball labels.",
        f"{summary['projected_points_count']} labels have projected court coordinates.",
        f"Unknown tactical zones: {summary['unknown_zone_count']}.",
        f"Confidence level: {confidence['confidence_level']}.",
    ]
    dominant_zone, count = most_common_distribution_value(summary.get("zone_distribution", {}))
    if dominant_zone != "unknown":
        findings.append(f"Most frequent prototype zone: {dominant_zone} ({count} points).")
    if summary.get("rally_segments_count"):
        findings.append(f"Rally segments summarized: {summary['rally_segments_count']}.")
    return findings


def write_coaching_summary(path: Path, observations: list[dict[str, Any]], confidence: dict[str, Any]) -> Path:
    """Write the coaching-style summary in plain-text-friendly Markdown."""
    lines = [
        "# Stage 10 Coaching-Style Summary",
        "",
        "IMPORTANT:",
        "  This is not official coaching advice.",
        "  It is a deterministic prototype summary from limited validated data.",
        "",
        f"CONFIDENCE LEVEL: {confidence['confidence_level']}",
        "",
        "OBSERVATIONS:",
    ]
    for index, observation in enumerate(observations, start=1):
        lines.extend(
            [
                "",
                f"Observation {index}: {observation['title']}",
                "  What it suggests:",
                f"    {observation['what_it_suggests']}",
                "  Confidence:",
                f"    {observation['confidence']}",
                "  Limitation:",
                f"    {observation['limitation']}",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def write_key_findings(path: Path, findings: list[str]) -> Path:
    """Write short key findings."""
    lines = ["# Stage 10 Key Findings", ""]
    for finding in findings:
        lines.append(f"- {finding}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path
