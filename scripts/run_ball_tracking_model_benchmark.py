"""Run rapid benchmark for tennis ball tracking model alternatives."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from tennis_vision.ball_tracking_benchmark import report_markdown, run_benchmark, write_json  # noqa: E402
from tennis_vision.baseline_quarantine import annotate_report_with_failed_baseline_warning, failed_baseline_block_message, print_failed_baseline_warning  # noqa: E402


DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "benchmarks" / "ball_tracking_model_benchmark"
DEFAULT_REPORT_JSON = PROJECT_ROOT / "outputs" / "reports" / "ball_tracking_model_benchmark_report.json"
DEFAULT_REPORT_MD = PROJECT_ROOT / "outputs" / "reports" / "ball_tracking_model_benchmark_report.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark ball tracking alternatives against manual full-rally event timing.")
    parser.add_argument("--annotation", type=Path, default=PROJECT_ROOT / "configs" / "manual_annotations" / "video_01_full_rally.json")
    parser.add_argument("--video", type=Path, default=PROJECT_ROOT / "samples" / "video_01.mov")
    parser.add_argument("--models", default="tracknet_candidate,sam_assisted_candidate")
    parser.add_argument("--include-baseline", action="store_true", help="Opt into baseline_current, which may use slower OpenCV frame access.")
    parser.add_argument("--skip-baseline", action="store_true", help="Remove baseline_current from the requested model list.")
    parser.add_argument("--allow-failed-baseline", action="store_true", help="Allow baseline_current benchmark for explicit research only.")
    parser.add_argument("--model-timeout-seconds", type=int, default=20)
    parser.add_argument("--search-padding", type=int, default=5)
    parser.add_argument("--resize-width", type=int, default=1280)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--generate-replay-for-best", action="store_true")
    return parser.parse_args()


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def print_summary(rows: list[dict[str, object]]) -> None:
    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(title="Ball Tracking Model Benchmark")
        for column in ("Model", "Available", "Events attempted", "Resolved", "Valid", "Suspicious", "Invalid", "Unresolved", "Verdict"):
            table.add_column(column, style="cyan" if column == "Model" else "white")
        for row in rows:
            table.add_row(
                str(row["model_name"]),
                str(row["available"]),
                str(row["events_attempted"]),
                str(row["resolved_count"]),
                str(row["valid_count"]),
                str(row["suspicious_count"]),
                str(row["invalid_count"]),
                str(row["unresolved_count"]),
                str(row["benchmark_verdict"]),
            )
        Console().print(table)
    except ImportError:
        print("Ball Tracking Model Benchmark")
        for row in rows:
            print(
                f"{row['model_name']}: available={row['available']} "
                f"resolved={row['resolved_count']} valid={row['valid_count']} "
                f"suspicious={row['suspicious_count']} invalid={row['invalid_count']} "
                f"unresolved={row['unresolved_count']} verdict={row['benchmark_verdict']}"
            )


def main() -> int:
    args = parse_args()
    if args.generate_replay_for_best:
        print("NOTE: --generate-replay-for-best is reserved for a later replay integration pass; benchmark only was run.")
    model_names = [item.strip() for item in args.models.split(",") if item.strip()]
    if args.include_baseline and "baseline_current" not in model_names:
        model_names.insert(0, "baseline_current")
    if args.skip_baseline:
        model_names = [name for name in model_names if name != "baseline_current"]
    if "baseline_current" in model_names and not args.allow_failed_baseline:
        print(failed_baseline_block_message())
        return 2
    if "baseline_current" in model_names:
        print_failed_baseline_warning()
    result = run_benchmark(
        project_root=PROJECT_ROOT,
        annotation_path=resolve(args.annotation),
        video_path=resolve(args.video),
        model_names=model_names,
        output_dir=resolve(args.output_dir),
        search_padding=args.search_padding,
        resize_width=args.resize_width,
        model_timeout_seconds=args.model_timeout_seconds,
    )
    report = result["report"]
    if "baseline_current" in model_names:
        annotate_report_with_failed_baseline_warning(report)
    write_json(DEFAULT_REPORT_JSON, report)
    DEFAULT_REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_REPORT_MD.write_text(report_markdown(report), encoding="utf-8")
    print_summary(result["summary_rows"])
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
