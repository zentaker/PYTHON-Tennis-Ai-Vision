"""Run the integrated TrackNet replay pipeline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from tennis_vision.tracknet_replay_pipeline import report_markdown, run_tracknet_replay_pipeline, write_json  # noqa: E402


DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "tracknet_replay" / "video_01"
REPORT_DIR = PROJECT_ROOT / "outputs" / "reports"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run TrackNet-based tennis replay pipeline.")
    parser.add_argument("--video", type=Path, default=PROJECT_ROOT / "samples" / "video_01.mov")
    parser.add_argument("--annotation", type=Path, default=PROJECT_ROOT / "configs" / "manual_annotations" / "video_01_full_rally.json")
    parser.add_argument("--tracknet-weights", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fps", type=int, default=60)
    parser.add_argument("--rally-padding", type=int, default=15)
    parser.add_argument("--event-search-padding", type=int, default=5)
    parser.add_argument("--generate-replays", dest="generate_replays", action="store_true", default=True)
    parser.add_argument("--no-replays", dest="generate_replays", action="store_false")
    return parser.parse_args()


def resolve(path: Path | None) -> Path | None:
    if path is None:
        return None
    return path if path.is_absolute() else PROJECT_ROOT / path


def print_summary(report: dict[str, object]) -> None:
    rows = [
        ("Verdict", report["final_verdict"]),
        ("Model available", report["model_available"]),
        ("Weights found", report["weights_found"]),
        ("Architecture available", report["architecture_available"]),
        ("Architecture modules found", report.get("architecture_modules_found", 0)),
        ("Weights status", report.get("weights_status", "missing")),
        ("Inference status", report.get("inference_implementation_status", "not_ready")),
        ("Dependencies", report["dependencies_available"]),
        ("Manual events", report["manual_events_count"]),
        ("Tracked frames", report["tracked_frames_count"]),
        ("Valid positions", report["event_positions_valid"]),
        ("Suspicious positions", report["event_positions_suspicious"]),
        ("Invalid positions", report["event_positions_invalid"]),
        ("Unresolved positions", report["event_positions_unresolved"]),
        ("Top-view replay", report["top_view_generated"]),
        ("Side-view replay", report["side_view_generated"]),
        ("Replay trustworthy", report["replay_trustworthy"]),
        ("Output folder", report["output_folder"]),
        ("Recommended next step", report["recommended_next_step"]),
    ]
    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(title="TrackNet Replay Pipeline")
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")
        for field, value in rows:
            table.add_row(str(field), str(value))
        Console().print(table)
    except ImportError:
        print("TrackNet Replay Pipeline")
        for field, value in rows:
            print(f"{field}: {value}")


def main() -> int:
    args = parse_args()
    output_dir = resolve(args.output_dir)
    report = run_tracknet_replay_pipeline(
        project_root=PROJECT_ROOT,
        video_path=resolve(args.video),
        annotation_path=resolve(args.annotation),
        output_dir=output_dir,
        fps=args.fps,
        rally_padding=args.rally_padding,
        event_search_padding=args.event_search_padding,
        tracknet_weights=resolve(args.tracknet_weights),
        generate_replays=args.generate_replays,
    )
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(REPORT_DIR / "tracknet_replay_pipeline_report.json", report)
    (REPORT_DIR / "tracknet_replay_pipeline_report.md").write_text(report_markdown(report), encoding="utf-8")
    print_summary(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
