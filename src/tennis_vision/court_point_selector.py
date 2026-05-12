"""Local helpers for manual court point selection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cv2

from tennis_vision.court_calibration import CALIBRATION_BASIS, POINT_LABELS, validate_corner_geometry


REQUIRED_POINT_NAMES = (
    "near_left_corner",
    "near_right_corner",
    "far_left_corner",
    "far_right_corner",
)


def _draw_label(image: Any, text: str, origin: tuple[int, int], color: tuple[int, int, int]) -> None:
    """Draw a readable label with a dark outline."""
    cv2.putText(image, text, origin, cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 4, cv2.LINE_AA)
    cv2.putText(image, text, origin, cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2, cv2.LINE_AA)


def generate_coordinate_grid(
    image_path: Path,
    output_path: Path,
    grid_step: int = 200,
) -> dict[str, Any]:
    """Generate a coordinate grid over a calibration reference image."""
    errors: list[str] = []
    warnings: list[str] = []

    if grid_step <= 0:
        warnings.append("Grid step must be positive; using 200 pixels.")
        grid_step = 200

    if not image_path.exists():
        return {
            "image_path": str(image_path),
            "grid_image_path": None,
            "grid_step": grid_step,
            "width": None,
            "height": None,
            "generated": False,
            "errors": [f"Reference image not found: {image_path}"],
            "warnings": warnings,
        }

    image = cv2.imread(str(image_path))
    if image is None:
        return {
            "image_path": str(image_path),
            "grid_image_path": None,
            "grid_step": grid_step,
            "width": None,
            "height": None,
            "generated": False,
            "errors": [f"OpenCV could not read reference image: {image_path}"],
            "warnings": warnings,
        }

    height, width = image.shape[:2]
    grid = image.copy()
    line_color = (0, 255, 255)
    axis_color = (0, 128, 255)
    label_color = (255, 255, 255)

    for x in range(0, width, grid_step):
        color = axis_color if x == 0 else line_color
        thickness = 3 if x == 0 else 1
        cv2.line(grid, (x, 0), (x, height - 1), color, thickness)
        _draw_label(grid, f"x={x}", (min(x + 8, width - 120), 32), label_color)

    for y in range(0, height, grid_step):
        color = axis_color if y == 0 else line_color
        thickness = 3 if y == 0 else 1
        cv2.line(grid, (0, y), (width - 1, y), color, thickness)
        _draw_label(grid, f"y={y}", (8, min(y + 28, height - 12)), label_color)

    cv2.circle(grid, (0, 0), 12, (0, 0, 255), -1)
    _draw_label(grid, "origin (0,0)", (18, 64), (255, 255, 255))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    saved = cv2.imwrite(str(output_path), grid)
    if not saved:
        errors.append(f"OpenCV failed to write grid image: {output_path}")

    return {
        "image_path": str(image_path),
        "grid_image_path": str(output_path) if saved else None,
        "grid_step": grid_step,
        "width": width,
        "height": height,
        "generated": saved,
        "errors": errors,
        "warnings": warnings,
    }


def validate_selected_points(points: dict[str, Any]) -> dict[str, Any]:
    """Validate the minimum four selected court corner points."""
    statuses: dict[str, dict[str, Any]] = {}
    usable_points: dict[str, tuple[float, float]] = {}
    valid_count = 0

    for name in REQUIRED_POINT_NAMES:
        value = points.get(name)
        status = "missing"
        x_value = None
        y_value = None
        if isinstance(value, (list, tuple)) and len(value) == 2:
            x_value, y_value = value
            if isinstance(x_value, (int, float)) and isinstance(y_value, (int, float)):
                if x_value == 0 and y_value == 0:
                    status = "placeholder"
                elif x_value >= 0 and y_value >= 0:
                    status = "valid"
                    valid_count += 1
                    usable_points[name] = (float(x_value), float(y_value))
                else:
                    status = "invalid"
            else:
                status = "invalid"
        elif isinstance(value, dict):
            x_value = value.get("x")
            y_value = value.get("y")
            if isinstance(x_value, (int, float)) and isinstance(y_value, (int, float)):
                if x_value == 0 and y_value == 0:
                    status = "placeholder"
                elif x_value >= 0 and y_value >= 0:
                    status = "valid"
                    valid_count += 1
                    usable_points[name] = (float(x_value), float(y_value))
                else:
                    status = "invalid"
            else:
                status = "invalid"

        statuses[name] = {
            "x": int(x_value) if isinstance(x_value, (int, float)) else None,
            "y": int(y_value) if isinstance(y_value, (int, float)) else None,
            "status": status,
        }

    geometry = validate_corner_geometry(usable_points)
    return {
        "points_valid": valid_count == len(REQUIRED_POINT_NAMES) and geometry["valid"],
        "valid_count": valid_count,
        "required_count": len(REQUIRED_POINT_NAMES),
        "points": statuses,
        "geometry": geometry,
        "calibration_basis": CALIBRATION_BASIS,
    }


def update_calibration_config(config_path: Path, selected_points: dict[str, list[int]]) -> dict[str, Any]:
    """Write selected court points into the calibration config."""
    errors: list[str] = []
    warnings: list[str] = []

    try:
        data = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "updated": False,
            "config_path": str(config_path),
            "errors": [f"Could not read calibration config: {exc}"],
            "warnings": warnings,
        }

    data.setdefault("points", {})
    for name, value in selected_points.items():
        data["points"][name] = [int(value[0]), int(value[1])]
    data["notes"] = "Court point coordinates were updated by the Stage 3.1 point selector."

    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        errors.append(f"Could not write calibration config: {exc}")

    return {
        "updated": not errors,
        "config_path": str(config_path),
        "errors": errors,
        "warnings": warnings,
    }


def _draw_selected_points(image: Any, selected: list[tuple[str, tuple[int, int]]]) -> Any:
    display = image.copy()
    for index, (name, (x_value, y_value)) in enumerate(selected, start=1):
        cv2.circle(display, (x_value, y_value), 14, (0, 0, 255), -1)
        cv2.circle(display, (x_value, y_value), 18, (255, 255, 255), 2)
        _draw_label(
            display,
            f"{index}. {name}: {POINT_LABELS.get(name, 'court point')} ({x_value},{y_value})",
            (x_value + 18, y_value - 18),
            (255, 255, 255),
        )
    return display


def select_court_points_interactively(
    image_path: Path,
    point_names: tuple[str, ...] = REQUIRED_POINT_NAMES,
) -> dict[str, Any]:
    """Open an OpenCV window and collect court point clicks."""
    errors: list[str] = []
    warnings: list[str] = []
    selected: list[tuple[str, tuple[int, int]]] = []

    if not image_path.exists():
        return {
            "interactive_attempted": True,
            "interactive_completed": False,
            "selected_points": {},
            "errors": [f"Reference image not found: {image_path}"],
            "warnings": warnings,
        }

    image = cv2.imread(str(image_path))
    if image is None:
        return {
            "interactive_attempted": True,
            "interactive_completed": False,
            "selected_points": {},
            "errors": [f"OpenCV could not read reference image: {image_path}"],
            "warnings": warnings,
        }

    window_name = "Stage 3.1 Court Point Selector"
    state = {"quit_without_saving": False, "saved": False}

    def on_mouse(event: int, x_value: int, y_value: int, _flags: int, _param: Any) -> None:
        if event != cv2.EVENT_LBUTTONDOWN:
            return
        if len(selected) >= len(point_names):
            warnings.append("All required points are already selected. Press s to save or u to undo.")
            return
        point_name = point_names[len(selected)]
        selected.append((point_name, (x_value, y_value)))
        print(f"Selected {point_name}: [{x_value}, {y_value}]")

    try:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 1280, 720)
        cv2.setMouseCallback(window_name, on_mouse)
        print("Calibration basis: doubles court outer boundary")
        print("Click points in this exact order:")
        for index, point_name in enumerate(point_names, start=1):
            print(f"{index}. {point_name} = {POINT_LABELS.get(point_name, 'court point')}")
        print("Keys: u=undo, s=save/finish, q=quit without saving")

        while True:
            display = _draw_selected_points(image, selected)
            if len(selected) < len(point_names):
                current = point_names[len(selected)]
                cv2.setWindowTitle(window_name, f"Click: {current} | u=undo s=save q=quit")
                _draw_label(
                    display,
                    f"Click: {current} - {POINT_LABELS.get(current, 'court point')}",
                    (24, 48),
                    (255, 255, 255),
                )
            else:
                cv2.setWindowTitle(window_name, "All points selected | s=save u=undo q=quit")
                _draw_label(display, "All required points selected. Press s to save.", (24, 48), (255, 255, 255))

            cv2.imshow(window_name, display)
            key = cv2.waitKey(30) & 0xFF
            if key == ord("u"):
                if selected:
                    removed = selected.pop()
                    print(f"Removed {removed[0]}")
            elif key == ord("s"):
                state["saved"] = len(selected) >= len(point_names)
                if not state["saved"]:
                    warnings.append("Save requested before all required points were selected.")
                break
            elif key == ord("q"):
                state["quit_without_saving"] = True
                break
    except cv2.error as exc:
        errors.append(f"OpenCV GUI is unavailable or failed: {exc}")
    except Exception as exc:  # pragma: no cover - defensive for local GUI backends.
        errors.append(f"Interactive selection failed: {exc}")
    finally:
        try:
            cv2.destroyWindow(window_name)
        except cv2.error:
            pass

    selected_points = {name: [coords[0], coords[1]] for name, coords in selected}
    return {
        "interactive_attempted": True,
        "interactive_completed": state["saved"],
        "selected_points": selected_points if state["saved"] else {},
        "errors": errors,
        "warnings": warnings,
        "quit_without_saving": state["quit_without_saving"],
    }
