"""Guardrails for the failed YOLO/HSV/local baseline replay path."""

from __future__ import annotations

from pathlib import Path


FEASIBILITY_REPORT = "outputs/reports/tennis_ai_vision_feasibility_decision.md"
BASELINE_TRUST_STATUS = "failed"
BASELINE_USAGE_WARNING = True

FAILED_BASELINE_WARNING = """WARNING:
The YOLO/HSV/local baseline ball localization path failed the feasibility test and should not be used for trusted replay, tactical depth, or line calling.
Use TrackNet/SAM paths or explicit research mode instead.
"""


def print_failed_baseline_warning() -> None:
    """Print the failed-baseline warning."""
    print(FAILED_BASELINE_WARNING)


def failed_baseline_block_message() -> str:
    """Return the standard blocked-run message."""
    return (
        FAILED_BASELINE_WARNING
        + "\nThis command is blocked by default because it can generate misleading replay outputs.\n"
        + "Pass --allow-failed-baseline only for explicit research or historical comparison.\n"
        + f"Review the feasibility report: {FEASIBILITY_REPORT}\n"
    )


def is_old_replay_schema(path: Path) -> bool:
    """Return whether a replay schema path belongs to the old baseline pipeline."""
    normalized = str(path).replace("\\", "/").lower()
    return (
        "outputs/replay/stage_12_replay_schema/replay_schema.json" in normalized
        or "outputs/replay/manual_full_rally/replay_schema.json" in normalized
    )


def annotate_report_with_failed_baseline_warning(report: dict) -> dict:
    """Add failed-baseline trust metadata to a report."""
    report["baseline_trust_status"] = BASELINE_TRUST_STATUS
    report["baseline_usage_warning"] = BASELINE_USAGE_WARNING
    return report
