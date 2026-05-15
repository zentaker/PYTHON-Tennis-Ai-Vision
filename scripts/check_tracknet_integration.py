"""Check local TrackNet integration readiness."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from tennis_vision.model_adapters.tracknet_adapter import describe_missing_requirements  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check local TrackNet weights, dependencies, and inference readiness.")
    parser.add_argument("--weights", type=Path, default=None)
    return parser.parse_args()


def resolve(path: Path | None) -> Path | None:
    if path is None:
        return None
    return path if path.is_absolute() else PROJECT_ROOT / path


def print_summary(result: dict[str, object]) -> None:
    availability = result["availability"]
    rows = [
        ("PyTorch available", "torch" not in availability.get("missing_dependencies", []) and availability.get("status") != "dependency_missing"),
        ("OpenCV available", "cv2" not in availability.get("missing_dependencies", [])),
        ("Registry loaded", availability.get("registry_loaded")),
        ("Variants checked", ", ".join(item.get("variant", "") for item in availability.get("variants_checked", [])) or "None"),
        ("Architecture modules found", availability.get("architecture_modules_found", sum(1 for item in availability.get("variants_checked", []) if item.get("architecture_found")))),
        ("Architecture status", availability.get("architecture_status") or "missing"),
        ("Weights found", availability.get("weights_found")),
        ("Weights status", availability.get("weights_status") or "missing"),
        ("Weight path", availability.get("weights_path") or "None"),
        ("Weight type", availability.get("weight_type") or "missing"),
        ("Selected variant", availability.get("selected_variant") or "None"),
        ("Inference implementation status", availability.get("inference_implementation_status") or "not_ready"),
        ("Ready for inference", availability.get("ready_for_inference")),
        ("Missing requirements", ", ".join(result.get("missing_requirements", [])) or "None"),
        ("Exact next action", result.get("exact_next_action") or result.get("recommended_next_step")),
    ]
    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(title="TrackNet Integration Check")
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")
        for field, value in rows:
            table.add_row(str(field), str(value))
        Console().print(table)
    except ImportError:
        print("TrackNet Integration Check")
        for field, value in rows:
            print(f"{field}: {value}")


def main() -> int:
    args = parse_args()
    result = describe_missing_requirements(PROJECT_ROOT, weights_path=resolve(args.weights))
    report_path = PROJECT_ROOT / "outputs" / "reports" / "tracknet_integration_check_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "stage": "tracknet_integration_check",
                **result,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print_summary(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
