"""Update the Tennis AI Vision Markdown lab notebook."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from tennis_vision.lab_notebook import update_lab_notebook  # noqa: E402


def main() -> int:
    try:
        written = update_lab_notebook(PROJECT_ROOT)
    except Exception as exc:
        print(f"Failed to update lab notebook: {exc}", file=sys.stderr)
        return 1

    print("Lab notebook updated:")
    for path in written:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
