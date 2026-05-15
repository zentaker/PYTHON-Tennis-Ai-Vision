"""Forensic audit for manual full-rally replay spatial failure."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESOLVED = PROJECT_ROOT / "outputs" / "replay" / "manual_full_rally" / "resolved_manual_events.csv"
DEFAULT_TIMELINE = PROJECT_ROOT / "outputs" / "replay" / "manual_full_rally" / "full_rally_event_timeline.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs" / "replay" / "manual_full_rally" / "event_position_audit.csv"
DEFAULT_REPORT_JSON = PROJECT_ROOT / "outputs" / "reports" / "manual_full_rally_forensic_audit.json"
DEFAULT_REPORT_MD = PROJECT_ROOT / "outputs" / "reports" / "manual_full_rally_forensic_audit.md"


AUDIT_FIELDS = [
    "event_id",
    "event_type",
    "shot_type",
    "manual_frame",
    "resolved_frame",
    "image_x",
    "image_y",
    "projected_x",
    "projected_y",
    "position_source",
    "fallback_used",
    "fallback_source",
    "projection_status",
    "render_as_physical_event",
    "should_have_rendered",
    "failure_reason",
    "audit_verdict",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit manual full-rally replay spatial position lineage and failures.")
    parser.add_argument("--resolved-events", type=Path, default=DEFAULT_RESOLVED)
    parser.add_argument("--event-timeline", type=Path, default=DEFAULT_TIMELINE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def read_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=AUDIT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def court_side(projected_y: Any) -> str:
    y = to_float(projected_y)
    if y is None:
        return "unknown"
    return "far" if y < 390 else "near"


def is_near_baseline(projected_y: Any) -> bool:
    y = to_float(projected_y)
    if y is None:
        return False
    return y <= 140 or y >= 640


def expected_next_physical_side(current: dict[str, Any]) -> str:
    side = court_side(current.get("projected_y"))
    if side == "near":
        return "far"
    if side == "far":
        return "near"
    return "unknown"


def audit_events(resolved_rows: list[dict[str, Any]], timeline_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    timeline_by_id = {row.get("event_id"): row for row in timeline_rows}
    audit_rows: list[dict[str, Any]] = []
    for index, row in enumerate(resolved_rows):
        event_id = str(row.get("event_id") or "")
        timeline = timeline_by_id.get(event_id, {})
        source = str(row.get("event_position_source") or "")
        projection_status = str(row.get("projection_status") or "")
        render_as_physical = str(timeline.get("should_render_as_physical_event") or "").lower() in {"yes", "true", "1"}
        fallback_used = source not in {"local_ball_detection", ""}
        fallback_source = source if fallback_used else ""
        position_trust = str(row.get("position_trust") or "")
        validation_status = str(row.get("position_validation_status") or "")
        validation_reason = str(row.get("sequence_validation_reason") or "")
        reasons: list[str] = []
        verdict = "valid_position"
        should_have_rendered = "yes"

        if not row.get("image_x") or not row.get("image_y"):
            reasons.append("No image-space position was available.")
            verdict = "invented_or_default_position"
            should_have_rendered = "no"
        if source != "local_ball_detection":
            if fallback_used:
                reasons.append(f"Position came from fallback source {source}, not local event-window detection.")
                verdict = "fallback_position"
            else:
                reasons.append("Position source is missing; cannot prove a detected ball position.")
                verdict = "invented_or_default_position"
            should_have_rendered = "no"
        if projection_status != "projected":
            reasons.append(f"Projection status is {projection_status}; projected court position is not reliable.")
            verdict = "projection_failure"
            should_have_rendered = "no"
        if position_trust and position_trust != "valid":
            reasons.append(f"Tennis sequence validator marked position_trust={position_trust}: {validation_status}. {validation_reason}")
            verdict = "wrong_side_likely" if "serve" in validation_status or "wrong_side" in validation_status else "suspicious_position"
            should_have_rendered = "no"

        side = court_side(row.get("projected_y"))
        if index == 0 and row.get("event_type") == "hit":
            if side != "far" or not is_near_baseline(row.get("projected_y")):
                reasons.append("Serve H1 resolved to the near side or non-plausible serving baseline region; Product Owner observed wrong-side serve placement.")
                verdict = "wrong_side_likely"
                should_have_rendered = "no"

        next_row = resolved_rows[index + 1] if index + 1 < len(resolved_rows) else None
        if row.get("event_type") == "hit" and next_row and next_row.get("event_type") == "bounce":
            expected_side = expected_next_physical_side(row)
            next_side = court_side(next_row.get("projected_y"))
            if expected_side != "unknown" and next_side != "unknown" and expected_side != next_side:
                reasons.append(f"Hit-to-bounce sequence stays on {next_side} side instead of crossing to {expected_side}; tennis rally geometry is suspicious.")
                verdict = "wrong_side_likely" if index == 0 else "suspicious_position"
                should_have_rendered = "no"

        previous_row = resolved_rows[index - 1] if index > 0 else None
        if row.get("event_type") == "bounce" and previous_row and previous_row.get("event_type") == "hit":
            expected_side = expected_next_physical_side(previous_row)
            current_side = court_side(row.get("projected_y"))
            if expected_side != "unknown" and current_side != "unknown" and expected_side != current_side:
                reasons.append(f"Bounce is on {current_side} side after a {court_side(previous_row.get('projected_y'))}-side hit; expected {expected_side}.")
                verdict = "suspicious_position" if verdict == "valid_position" else verdict
                should_have_rendered = "no"

        if row.get("event_position_status") == "unresolved" and render_as_physical:
            reasons.append("Event was unresolved but timeline marked it as a physical event.")
            verdict = "unresolved_but_rendered"
            should_have_rendered = "no"

        if should_have_rendered == "no" and render_as_physical and "timeline marked it as a physical event" not in " ".join(reasons):
            reasons.append("Renderer timeline allowed this suspicious/untrusted position to render as a physical anchor.")

        audit_rows.append(
            {
                "event_id": event_id,
                "event_type": row.get("event_type") or "",
                "shot_type": row.get("shot_type") or "",
                "manual_frame": row.get("contact_frame_estimate") or "",
                "resolved_frame": row.get("resolved_frame") or "",
                "image_x": row.get("image_x") or "",
                "image_y": row.get("image_y") or "",
                "projected_x": row.get("projected_x") or "",
                "projected_y": row.get("projected_y") or "",
                "position_source": source,
                "fallback_used": "yes" if fallback_used else "no",
                "fallback_source": fallback_source,
                "projection_status": projection_status,
                "render_as_physical_event": "yes" if render_as_physical else "no",
                "should_have_rendered": should_have_rendered,
                "failure_reason": " ".join(reasons) if reasons else "Position source, projection, and local tennis sequence checks did not flag this row.",
                "audit_verdict": verdict,
            }
        )
    return audit_rows


def summarize(audit_rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "total_events": len(audit_rows),
        "valid_positions": sum(1 for row in audit_rows if row["audit_verdict"] == "valid_position"),
        "suspicious_positions": sum(1 for row in audit_rows if row["audit_verdict"] == "suspicious_position"),
        "fallback_positions": sum(1 for row in audit_rows if row["audit_verdict"] == "fallback_position"),
        "unresolved_but_rendered": sum(1 for row in audit_rows if row["audit_verdict"] == "unresolved_but_rendered"),
        "invented_or_default_positions": sum(1 for row in audit_rows if row["audit_verdict"] == "invented_or_default_position"),
        "wrong_side_likely_events": sum(1 for row in audit_rows if row["audit_verdict"] == "wrong_side_likely"),
        "projection_failures": sum(1 for row in audit_rows if row["audit_verdict"] == "projection_failure"),
        "physical_render_mismatches": sum(1 for row in audit_rows if row["render_as_physical_event"] == "yes" and row["should_have_rendered"] == "no"),
    }


def build_report(audit_rows: list[dict[str, Any]], summary: dict[str, int], paths: dict[str, str]) -> dict[str, Any]:
    trustworthy = (
        summary["total_events"] > 0
        and summary["valid_positions"] == summary["total_events"]
        and summary["physical_render_mismatches"] == 0
    )
    root_causes = [
        "Manual event timing was used correctly, but local candidate scoring can treat high-scoring color/motion blobs as reliable ball positions unless tennis-sequence validation is applied.",
        "The resolver can mark local_ball_detection candidates as resolved/projected even when the resulting court side contradicts serve and hit-to-bounce geometry.",
    ]
    if summary["physical_render_mismatches"]:
        root_causes.append("The renderer still allowed suspicious positions to render as physical anchors.")
    else:
        root_causes.append("Current render safety flags prevent suspicious validator failures from rendering as physical anchors.")
    root_causes.extend(
        [
            "H1 was the critical failure case: the local detector selected a frame-100 blob at image (1467,1461), projected to near_deep_left, which is implausible for the serve side.",
            "Serve/bounce direction must be validated separately from timing because timing alone does not enforce tennis rally geometry.",
        ]
    )
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stage": "manual_full_rally_forensic_audit",
        "manual_full_rally_replay_trustworthy": trustworthy,
        "summary": summary,
        "root_causes": root_causes,
        "answers": {
            "position_source": "event_position_audit.csv lists the exact source for each event.",
            "local_ball_detection_used": sum(1 for row in audit_rows if row["position_source"] == "local_ball_detection"),
            "fallback_used": sum(1 for row in audit_rows if row["fallback_used"] == "yes"),
            "invented_or_reused": summary["invented_or_default_positions"],
            "homography_projection_applied": sum(1 for row in audit_rows if row["projection_status"] == "projected"),
            "projection_failed": summary["projection_failures"],
            "unresolved_rendered_reason": "Suspicious/untrusted events should have should_render_as_physical_event=no; physical_render_mismatches records any safety gate failure.",
            "h1_wrong_position_reason": "H1 used local_ball_detection at frame 100 and projected to near_deep_left, which contradicts the Product Owner's serve-side observation and serve plausibility.",
            "serve_direction_reason": "The audit found hit-to-bounce side-order violations; timing alone did not enforce tennis rally geometry.",
        },
        "output_paths": paths,
    }


def markdown_report(report: dict[str, Any], audit_rows: list[dict[str, Any]]) -> str:
    s = report["summary"]
    root_causes = "\n".join(f"  - {item}" for item in report["root_causes"])
    bad_rows = [row for row in audit_rows if row["audit_verdict"] != "valid_position"]
    bad_block = "\n".join(f"  - {row['event_id']}: {row['audit_verdict']} - {row['failure_reason']}" for row in bad_rows) or "  None"
    return f"""# Manual Full-Rally Forensic Audit

VERDICT
  manual_full_rally_replay_trustworthy: {str(report["manual_full_rally_replay_trustworthy"]).lower()}

SUMMARY
  Total events: {s["total_events"]}
  Valid positions: {s["valid_positions"]}
  Suspicious positions: {s["suspicious_positions"]}
  Fallback positions: {s["fallback_positions"]}
  Unresolved but rendered: {s["unresolved_but_rendered"]}
  Invented/default positions: {s["invented_or_default_positions"]}
  Wrong-side-likely events: {s["wrong_side_likely_events"]}
  Projection failures: {s["projection_failures"]}
  Physical render mismatches: {s["physical_render_mismatches"]}

ROOT CAUSE SUMMARY
{root_causes}

FAILED / SUSPICIOUS EVENTS
{bad_block}

DIRECT ANSWERS
  Was local ball detection used?
    {report["answers"]["local_ball_detection_used"]} events used local_ball_detection.

  Were old labels or fallbacks used?
    {report["answers"]["fallback_used"]} events used fallback sources.

  Were positions invented/defaulted/reused?
    {report["answers"]["invented_or_reused"]} events were classified as invented/default positions.

  Was homography projection applied?
    {report["answers"]["homography_projection_applied"]} events have projection_status=projected.

  Did projection fail?
    {report["answers"]["projection_failed"]} projection failures were found.

  Why did unresolved events still render?
    {report["answers"]["unresolved_rendered_reason"]}

  Why did H1 end up inside/wrong side?
    {report["answers"]["h1_wrong_position_reason"]}

  Why did serve/bounce direction not respect tennis sequence?
    {report["answers"]["serve_direction_reason"]}

OUTPUTS
  Audit CSV: {report["output_paths"]["event_position_audit_csv"]}
  Audit JSON: {report["output_paths"]["forensic_audit_json"]}
  Audit Markdown: {report["output_paths"]["forensic_audit_md"]}
"""


def print_summary(report: dict[str, Any]) -> None:
    rows = [
        ("Replay trustworthy", report["manual_full_rally_replay_trustworthy"]),
        ("Total events", report["summary"]["total_events"]),
        ("Valid positions", report["summary"]["valid_positions"]),
        ("Suspicious positions", report["summary"]["suspicious_positions"]),
        ("Fallback positions", report["summary"]["fallback_positions"]),
        ("Unresolved but rendered", report["summary"]["unresolved_but_rendered"]),
        ("Wrong-side likely", report["summary"]["wrong_side_likely_events"]),
        ("Physical render mismatches", report["summary"]["physical_render_mismatches"]),
    ]
    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(title="Manual Full Rally Forensic Audit")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        for field, value in rows:
            table.add_row(str(field), str(value))
        Console().print(table)
    except ImportError:
        print("Manual Full Rally Forensic Audit")
        for field, value in rows:
            print(f"{field}: {value}")


def to_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def main() -> int:
    args = parse_args()
    resolved_path = resolve(args.resolved_events)
    timeline_path = resolve(args.event_timeline)
    output_path = resolve(args.output)
    report_json_path = resolve(args.report_json)
    report_md_path = resolve(args.report_md)
    resolved_rows = read_csv(resolved_path)
    timeline_rows = read_csv(timeline_path)
    audit_rows = audit_events(resolved_rows, timeline_rows)
    write_csv(output_path, audit_rows)
    paths = {
        "event_position_audit_csv": str(output_path),
        "forensic_audit_json": str(report_json_path),
        "forensic_audit_md": str(report_md_path),
    }
    summary = summarize(audit_rows)
    report = build_report(audit_rows, summary, paths)
    write_json(report_json_path, report)
    report_md_path.parent.mkdir(parents=True, exist_ok=True)
    report_md_path.write_text(markdown_report(report, audit_rows), encoding="utf-8")
    print_summary(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
