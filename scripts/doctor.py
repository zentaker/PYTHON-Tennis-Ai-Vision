"""Run Stage 0 local environment checks."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from tennis_vision.environment import run_environment_checks  # noqa: E402
from tennis_vision.friction import calculate_friction_score  # noqa: E402
from tennis_vision.report import (  # noqa: E402
    ensure_output_folders,
    utc_timestamp,
    write_json_report,
    write_markdown_report,
    write_timestamped_log,
)


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _bullet_list(items: list[str]) -> str:
    if not items:
        return "- None"
    return "\n".join(f"- {item}" for item in items)


def determine_verdict(checks: dict[str, Any], friction_score: int) -> str:
    """Determine the final Stage 0 verdict."""
    if checks["errors"] or friction_score >= 81:
        return "blocked"
    if checks["warnings"] or friction_score > 20:
        return "ready_with_warnings"
    return "ready_for_stage_1"


def build_markdown_sections(report: dict[str, Any]) -> list[tuple[str, str]]:
    """Build Markdown report sections."""
    package_lines = [
        f"- {name}: {'available' if details['available'] else 'missing'}"
        for name, details in report["packages"].items()
    ]
    folder_lines = [
        f"- {name}: {'exists' if details['exists'] else 'missing'}"
        for name, details in report["folders"].items()
    ]

    ffmpeg = report["ffmpeg"]
    ffmpeg_lines = [
        f"- Available: {_yes_no(ffmpeg['available'])}",
        f"- Path: {ffmpeg['path'] or 'not found'}",
        f"- Version: {ffmpeg['version'] or 'unknown'}",
    ]
    if ffmpeg["error"]:
        ffmpeg_lines.append(f"- Error: {ffmpeg['error']}")

    return [
        (
            "Summary",
            "\n".join(
                [
                    f"- Timestamp: {report['timestamp']}",
                    f"- Final verdict: {report['final_verdict']}",
                    f"- Friction score: {report['friction']['score']} ({report['friction']['band']})",
                ]
            ),
        ),
        (
            "System",
            "\n".join(
                [
                    f"- OS: {report['os']['platform']}",
                    f"- Python: {report['python']['version']}",
                    f"- Python executable: `{report['python']['executable']}`",
                    f"- Working directory: `{report['cwd']['path']}`",
                ]
            ),
        ),
        ("Package Import Status", "\n".join(package_lines)),
        ("Folder Status", "\n".join(folder_lines)),
        ("ffmpeg Status", "\n".join(ffmpeg_lines)),
        ("Errors", _bullet_list(report["errors"])),
        ("Warnings", _bullet_list(report["warnings"])),
        ("Recommended Fixes", _bullet_list(report["recommended_fixes"])),
    ]


def print_summary(report: dict[str, Any]) -> None:
    """Print a readable summary, using rich when available."""
    try:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title="Tennis AI Vision Stage 0 Doctor")
        table.add_column("Check")
        table.add_column("Result")
        table.add_row("Verdict", report["final_verdict"])
        table.add_row(
            "Friction",
            f"{report['friction']['score']} ({report['friction']['band']})",
        )
        table.add_row("Missing packages", str(len(report["missing_packages"])))
        table.add_row("Missing folders", str(len(report["missing_folders"])))
        table.add_row("ffmpeg", "available" if report["ffmpeg"]["available"] else "missing")
        table.add_row("Errors", str(len(report["errors"])))
        table.add_row("Warnings", str(len(report["warnings"])))
        console.print(table)
        if report["recommended_fixes"]:
            console.print("[bold]Recommended fixes:[/bold]")
            for fix in report["recommended_fixes"]:
                console.print(f"- {fix}")
    except ImportError:
        print("Tennis AI Vision Stage 0 Doctor")
        print(f"Verdict: {report['final_verdict']}")
        print(f"Friction: {report['friction']['score']} ({report['friction']['band']})")
        print(f"Missing packages: {len(report['missing_packages'])}")
        print(f"Missing folders: {len(report['missing_folders'])}")
        print(f"ffmpeg: {'available' if report['ffmpeg']['available'] else 'missing'}")
        print(f"Errors: {len(report['errors'])}")
        print(f"Warnings: {len(report['warnings'])}")
        if report["recommended_fixes"]:
            print("Recommended fixes:")
            for fix in report["recommended_fixes"]:
                print(f"- {fix}")


def update_lab_notebook_safely() -> None:
    """Best-effort lab notebook update that never fails the doctor."""
    try:
        from tennis_vision.lab_notebook import lab_notebook_paths, update_lab_notebook

        update_lab_notebook(PROJECT_ROOT)
        paths = lab_notebook_paths(PROJECT_ROOT, "stage_0")
        print(f"Lab notebook page: {paths['stage_page']}")
        print(f"Experiment index: {paths['experiment_index']}")
    except Exception as exc:
        print(f"Warning: lab notebook update failed: {exc}")


def main() -> int:
    ensure_output_folders(PROJECT_ROOT)
    checks = run_environment_checks(PROJECT_ROOT)
    manual_action_required = bool(checks["missing_packages"] or checks["missing_folders"])
    friction = calculate_friction_score(
        missing_packages=checks["missing_packages"],
        missing_folders=checks["missing_folders"],
        ffmpeg_missing=not checks["ffmpeg"]["available"],
        errors_count=len(checks["errors"]),
        manual_action_required=manual_action_required,
    )
    verdict = determine_verdict(checks, friction["score"])

    report = {
        "timestamp": utc_timestamp(),
        **checks,
        "friction": friction,
        "final_verdict": verdict,
    }

    json_path = PROJECT_ROOT / "outputs" / "reports" / "environment_report.json"
    markdown_path = PROJECT_ROOT / "outputs" / "reports" / "environment_report.md"
    write_json_report(json_path, report)
    write_markdown_report(
        markdown_path,
        "Tennis AI Vision Environment Report",
        build_markdown_sections(report),
    )
    log_path = write_timestamped_log(
        PROJECT_ROOT,
        "doctor",
        [
            f"timestamp={report['timestamp']}",
            f"verdict={verdict}",
            f"friction={friction['score']} ({friction['band']})",
            f"json_report={json_path}",
            f"markdown_report={markdown_path}",
        ],
    )
    report["log_path"] = str(log_path)

    print_summary(report)
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {markdown_path}")
    print(f"Log file: {log_path}")
    update_lab_notebook_safely()

    return 1 if verdict == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
