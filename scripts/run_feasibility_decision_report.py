"""Generate the Tennis AI Vision feasibility decision report."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = PROJECT_ROOT / "outputs" / "reports"
FRICTION_SUMMARY_PATH = PROJECT_ROOT / "docs" / "friction" / "tennis_ai_vision_feasibility_summary.md"
DECISION_JSON_PATH = REPORT_DIR / "tennis_ai_vision_feasibility_decision.json"
DECISION_MD_PATH = REPORT_DIR / "tennis_ai_vision_feasibility_decision.md"


def read_json(path: Path) -> dict[str, Any]:
    """Read a JSON report, returning an empty dict when missing or invalid."""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def build_decision(project_root: Path) -> dict[str, Any]:
    """Build the final feasibility decision from existing stage reports."""
    reports = {
        "forensic": read_json(project_root / "outputs" / "reports" / "manual_full_rally_forensic_audit.json"),
        "benchmark": read_json(project_root / "outputs" / "reports" / "ball_tracking_model_benchmark_report.json"),
        "tracknet": read_first_json(
            [
                project_root / "outputs" / "reports" / "tracknet_replay_pipeline_report.json",
                project_root / "outputs" / "tracknet_replay" / "video_01" / "tracknet_replay_report.json",
            ]
        ),
        "sam": read_first_json(
            [
                project_root / "outputs" / "reports" / "sam_assisted_replay_pipeline_report.json",
                project_root / "outputs" / "sam_replay" / "video_01" / "sam_replay_report.json",
            ]
        ),
    }

    forensic = reports["forensic"]
    tracknet = reports["tracknet"]
    sam = reports["sam"]

    baseline = build_baseline_status(forensic)
    tracknet_status = build_tracknet_status(tracknet)
    sam_status = build_sam_status(sam)
    decision_payload = decide_project_path(baseline, tracknet_status, sam_status)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stage": "tennis_ai_vision_feasibility_decision",
        "summary_verdict": decision_payload,
        "model_path_results": {
            "baseline": baseline,
            "tracknet": tracknet_status,
            "sam_assisted": sam_status,
        },
        "project_decision": {
            "continue": decision_payload["decision"] in {"continue_with_tracknet", "continue_with_sam_assisted_experimental"},
            "pause": decision_payload["decision"] not in {"continue_with_tracknet", "continue_with_sam_assisted_experimental"},
            "required_next_asset": decision_payload["required_next_asset"],
        },
        "answers": {
            "baseline_worked": baseline["trustworthy"],
            "tracknet_run": tracknet_status["tracked_frames"] > 0,
            "sam_run": sam_status["tracked_frames"] > 0,
            "trustworthy_top_view_replay_exists": bool(tracknet_status["trustworthy"] and tracknet_status["replay_generated"]) or bool(sam_status["trustworthy"] and sam_status["replay_generated"]),
            "trustworthy_side_view_replay_exists": bool(tracknet_status["trustworthy"] and tracknet_status["replay_generated"]) or bool(sam_status["trustworthy"] and sam_status["replay_generated"]),
            "feasibility_proven": decision_payload["decision"] in {"continue_with_tracknet", "continue_with_sam_assisted_experimental"},
        },
        "what_worked": [
            "manual DaVinci annotation",
            "court/replay scaffolds",
            "model adapter scaffolds",
            "feasibility reporting",
        ],
        "what_failed": [
            "baseline local detector",
            "TrackNet real inference unavailable",
            "SAM/SAM2 real inference unavailable",
        ],
        "critical_blockers": list(dict.fromkeys(tracknet_status["missing"] + sam_status["missing"])),
        "recommended_next_step": "Get compatible TrackNet architecture and pretrained weights.",
        "next_action": {
            "primary": "Get compatible TrackNet architecture + weights.",
            "secondary": "Only test SAM/SAM2 if TrackNet remains unavailable.",
        },
        "do_not_continue": [
            "line calling",
            "coaching reports",
            "product UI",
            "second rally transfer",
        ],
        "friction_lessons": [
            "model availability must be checked before building downstream stages",
            "replay can render technically while being spatially invalid",
            "manual timing is useful but not enough without reliable ball localization",
            "YOLO/HSV baseline should not be used as the core bounce/localization model",
        ],
        "input_reports": {
            "manual_full_rally_forensic_audit": str(project_root / "outputs" / "reports" / "manual_full_rally_forensic_audit.json"),
            "ball_tracking_model_benchmark": str(project_root / "outputs" / "reports" / "ball_tracking_model_benchmark_report.json"),
            "tracknet_replay_pipeline": str(project_root / "outputs" / "reports" / "tracknet_replay_pipeline_report.json"),
            "tracknet_replay_local": str(project_root / "outputs" / "tracknet_replay" / "video_01" / "tracknet_replay_report.json"),
            "sam_assisted_replay_pipeline": str(project_root / "outputs" / "reports" / "sam_assisted_replay_pipeline_report.json"),
            "sam_assisted_replay_local": str(project_root / "outputs" / "sam_replay" / "video_01" / "sam_replay_report.json"),
        },
        "output_paths": {
            "decision_json": str(DECISION_JSON_PATH),
            "decision_md": str(DECISION_MD_PATH),
            "friction_summary": str(FRICTION_SUMMARY_PATH),
        },
    }


def read_first_json(paths: list[Path]) -> dict[str, Any]:
    """Read the first existing JSON report from a list."""
    for path in paths:
        payload = read_json(path)
        if payload:
            return payload
    return {}


def build_baseline_status(forensic: dict[str, Any]) -> dict[str, Any]:
    """Build baseline status block."""
    trustworthy = bool(forensic.get("manual_full_rally_replay_trustworthy"))
    return {
        "status": "passed" if trustworthy else "failed",
        "trustworthy": trustworthy,
        "reason": baseline_reason(forensic),
    }


def build_tracknet_status(tracknet: dict[str, Any]) -> dict[str, Any]:
    """Build TrackNet status block."""
    valid = int(tracknet.get("event_positions_valid") or 0)
    top = bool(tracknet.get("top_view_generated"))
    side = bool(tracknet.get("side_view_generated"))
    return {
        "status": str(tracknet.get("final_verdict") or "not_run"),
        "ready_for_inference": bool(tracknet.get("ready_for_inference")),
        "missing": tracknet_missing(tracknet),
        "replay_generated": bool(top or side),
        "top_view_generated": top,
        "side_view_generated": side,
        "trustworthy": bool(tracknet.get("replay_trustworthy")),
        "valid_positions": valid,
        "tracked_frames": int(tracknet.get("tracked_frames_count") or 0),
        "reason": str(tracknet.get("failure_reason") or "TrackNet did not produce a ready-for-review replay."),
    }


def build_sam_status(sam: dict[str, Any]) -> dict[str, Any]:
    """Build SAM/SAM2 status block."""
    valid = int(sam.get("event_positions_valid") or 0)
    top = bool(sam.get("top_view_generated"))
    side = bool(sam.get("side_view_generated"))
    return {
        "status": str(sam.get("final_verdict") or "not_run"),
        "ready_for_inference": bool(sam.get("ready_for_inference")),
        "missing": sam_missing(sam),
        "replay_generated": bool(top or side),
        "top_view_generated": top,
        "side_view_generated": side,
        "trustworthy": bool(sam.get("replay_trustworthy")),
        "valid_positions": valid,
        "tracked_frames": int(sam.get("tracked_frames_count") or 0),
        "reason": str(sam.get("failure_reason") or "SAM/SAM2 did not produce a ready-for-review replay."),
    }


def decide_project_path(
    baseline: dict[str, Any],
    tracknet: dict[str, Any],
    sam: dict[str, Any],
) -> dict[str, Any]:
    """Apply final feasibility decision logic."""
    baseline_failed = baseline["status"] == "failed"
    tracknet_missing_model = any("TrackNet architecture" in item or "TrackNet weights" in item for item in tracknet["missing"])
    tracknet_good = tracknet["ready_for_inference"] and tracknet["valid_positions"] >= 10 and tracknet["trustworthy"]
    sam_good = sam["ready_for_inference"] and sam["valid_positions"] >= 10 and sam["trustworthy"]
    tracknet_ran = tracknet["tracked_frames"] > 0
    sam_ran = sam["tracked_frames"] > 0

    if baseline_failed and tracknet_missing_model:
        return {
            "decision": "pause_until_tracknet_model_available",
            "confidence": "high",
            "required_next_asset": "compatible TrackNet architecture + pretrained weights",
            "reason": "Baseline failed, and TrackNet is the preferred next model family but is blocked by missing architecture or weights. SAM/SAM2 is optional and not the main path.",
        }
    if tracknet_good:
        return {
            "decision": "continue_with_tracknet",
            "confidence": "medium",
            "required_next_asset": "none",
            "reason": "TrackNet ran and produced enough valid, trustworthy event positions.",
        }
    if not tracknet["ready_for_inference"] and sam_good:
        return {
            "decision": "continue_with_sam_assisted_experimental",
            "confidence": "low",
            "required_next_asset": "SAM validation review",
            "reason": "TrackNet is unavailable, but SAM/SAM2 produced valid positions. Treat this as experimental.",
        }
    if not tracknet_ran and not sam_ran:
        return {
            "decision": "pause_model_integration",
            "confidence": "high",
            "required_next_asset": "compatible TrackNet architecture + pretrained weights",
            "reason": "All model alternatives are unavailable locally, so feasibility is not proven.",
        }
    return {
        "decision": "research_required_or_change_capture_strategy",
        "confidence": "medium",
        "required_next_asset": "model/capture research plan",
        "reason": "Available model paths ran but did not produce trustworthy ball localization.",
    }


def baseline_reason(forensic: dict[str, Any]) -> str:
    """Return the baseline verdict reason."""
    summary = forensic.get("summary") or {}
    if not forensic:
        return "Forensic audit report is missing, but baseline is considered failed by project decision context."
    return (
        "Manual full-rally replay was not trustworthy. "
        f"Valid positions: {summary.get('valid_positions', 0)}; "
        f"suspicious positions: {summary.get('suspicious_positions', 0)}; "
        f"wrong-side-likely events: {summary.get('wrong_side_likely_events', 0)}."
    )


def tracknet_missing(tracknet: dict[str, Any]) -> list[str]:
    """Return TrackNet missing requirements."""
    missing = []
    if not tracknet.get("architecture_available"):
        missing.append("TrackNet architecture missing")
    if not tracknet.get("weights_found"):
        missing.append("TrackNet weights missing")
    if not tracknet.get("ready_for_inference"):
        missing.append("TrackNet ready_for_inference false")
    return missing


def sam_missing(sam: dict[str, Any]) -> list[str]:
    """Return SAM/SAM2 missing requirements."""
    missing = []
    if not sam.get("dependencies_available"):
        missing.append("SAM/SAM2 dependencies missing")
    if not sam.get("weights_found"):
        missing.append("SAM/SAM2 weights missing")
    if not sam.get("ready_for_inference"):
        missing.append("SAM/SAM2 ready_for_inference false")
    return missing


def render_markdown(report: dict[str, Any]) -> str:
    """Render the plain-text-friendly decision report."""
    baseline = report["model_path_results"]["baseline"]
    tracknet = report["model_path_results"]["tracknet"]
    sam = report["model_path_results"]["sam_assisted"]
    verdict = report["summary_verdict"]
    project = report["project_decision"]
    return f"""# Tennis AI Vision Feasibility Decision Report

SUMMARY VERDICT
  Decision: {verdict["decision"]}
  Confidence: {verdict["confidence"]}
  Reason:
    {verdict["reason"]}

PATH STATUS

Baseline:
  Status: {baseline["status"]}
  Trustworthy: {baseline["trustworthy"]}
  Reason:
    {baseline["reason"]}

TrackNet:
  Status: {tracknet["status"]}
  Ready for inference: {tracknet["ready_for_inference"]}
  Missing:
{render_list(tracknet["missing"], indent="    - ")}
  Replay generated: {tracknet["replay_generated"]}
  Trustworthy: {tracknet["trustworthy"]}
  Reason:
    {tracknet["reason"]}

SAM/SAM2:
  Status: {sam["status"]}
  Ready for inference: {sam["ready_for_inference"]}
  Missing:
{render_list(sam["missing"], indent="    - ")}
  Replay generated: {sam["replay_generated"]}
  Trustworthy: {sam["trustworthy"]}
  Reason:
    {sam["reason"]}

PROJECT DECISION
  Continue: {project["continue"]}
  Pause: {project["pause"]}
  Required next asset: {project["required_next_asset"]}

WHAT WORKED
{render_list(report["what_worked"])}

WHAT FAILED
{render_list(report["what_failed"])}

CRITICAL BLOCKERS
{render_list(report["critical_blockers"])}

NEXT ACTION
  Primary:
    {report["next_action"]["primary"]}

  Secondary:
    {report["next_action"]["secondary"]}

DO NOT CONTINUE YET
{render_list(report["do_not_continue"])}
  until a temporal ball tracker runs and resolves event positions.

FRICTION LESSONS
{render_list(report["friction_lessons"])}
"""


def render_friction_summary(report: dict[str, Any]) -> str:
    """Render the friction-facing summary."""
    verdict = report["summary_verdict"]
    return f"""# Tennis AI Vision Feasibility Summary

DECISION
  {verdict["decision"]}

CONFIDENCE
  {verdict["confidence"]}

WHY
  {verdict["reason"]}

CURRENT STATUS
  Feasibility is not proven.
  Baseline localization failed.
  TrackNet status: {report["model_path_results"]["tracknet"]["status"]}.
  SAM/SAM2 status: {report["model_path_results"]["sam_assisted"]["status"]}.

NEXT ACTION
  Primary:
    {report["next_action"]["primary"]}

  Secondary:
    {report["next_action"]["secondary"]}

DO NOT CONTINUE YET
{render_list(report["do_not_continue"])}
  until a temporal ball tracker runs and resolves event positions.

FRICTION LESSONS
{render_list(report["friction_lessons"])}
"""


def render_list(items: list[str], indent: str = "  - ") -> str:
    """Render a simple bullet list."""
    if not items:
        return f"{indent}None"
    return "\n".join(f"{indent}{item}" for item in items)


def write_outputs(report: dict[str, Any]) -> None:
    """Write JSON, Markdown, and friction summary outputs."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    FRICTION_SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    DECISION_JSON_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    DECISION_MD_PATH.write_text(render_markdown(report), encoding="utf-8")
    FRICTION_SUMMARY_PATH.write_text(render_friction_summary(report), encoding="utf-8")


def print_summary(report: dict[str, Any]) -> None:
    """Print the feasibility decision table."""
    rows = [
        ("Decision", report["summary_verdict"]["decision"]),
        ("Baseline", report["model_path_results"]["baseline"]["status"]),
        ("TrackNet", report["model_path_results"]["tracknet"]["status"]),
        ("SAM/SAM2", report["model_path_results"]["sam_assisted"]["status"]),
        ("Replay trustworthy", report["answers"]["feasibility_proven"]),
        ("Next asset needed", report["project_decision"]["required_next_asset"]),
        ("Report path", report["output_paths"]["decision_md"]),
    ]
    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(title="Feasibility Decision")
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")
        for field, value in rows:
            table.add_row(str(field), str(value))
        Console().print(table)
    except ImportError:
        print("Feasibility Decision")
        for field, value in rows:
            print(f"{field}: {value}")


def main() -> int:
    """CLI entrypoint."""
    report = build_decision(PROJECT_ROOT)
    write_outputs(report)
    print_summary(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
