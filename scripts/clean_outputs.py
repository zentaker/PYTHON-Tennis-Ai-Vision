"""Clean generated files inside outputs while preserving folder structure."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = PROJECT_ROOT / "outputs"
PRESERVED_FOLDERS = ("reports", "logs", "frames", "annotated")


def clean_outputs() -> list[Path]:
    """Delete generated files under outputs and preserve standard folders."""
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    removed: list[Path] = []

    for folder_name in PRESERVED_FOLDERS:
        folder = OUTPUT_ROOT / folder_name
        folder.mkdir(parents=True, exist_ok=True)
        for path in folder.rglob("*"):
            if path.is_file():
                path.unlink()
                removed.append(path)

    return removed


def print_summary(removed: list[Path]) -> None:
    """Print a cleanup summary, using rich when available."""
    try:
        from rich.console import Console

        console = Console()
        console.print("[bold]Tennis AI Vision output cleanup[/bold]")
        console.print(f"Removed files: {len(removed)}")
        console.print(f"Preserved folder structure under: {OUTPUT_ROOT}")
    except ImportError:
        print("Tennis AI Vision output cleanup")
        print(f"Removed files: {len(removed)}")
        print(f"Preserved folder structure under: {OUTPUT_ROOT}")


def main() -> int:
    try:
        removed = clean_outputs()
    except OSError as exc:
        print(f"Failed to clean outputs: {exc}", file=sys.stderr)
        return 1

    print_summary(removed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
