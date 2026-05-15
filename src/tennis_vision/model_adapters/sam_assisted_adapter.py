"""SAM/SAM2-assisted ball tracking adapter.

SAM is treated as an experimental segmentation helper, not a tennis-specific
tracker. This adapter refuses to fabricate positions when dependencies,
weights, or point prompts are missing.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


MODEL_NAME = "sam_assisted_candidate"
WEIGHT_SUFFIXES = (".pt", ".pth", ".ckpt")
DEFAULT_SEARCH_PATHS = (
    "models/sam/weights/sam.pt",
    "models/sam/weights/sam.pth",
    "models/sam/weights/sam_vit_b.pth",
    "models/sam/weights/sam_vit_l.pth",
    "models/sam/weights/sam_vit_h.pth",
    "models/sam/weights",
    "models/sam2/weights/sam2.pt",
    "models/sam2/weights/sam2.pth",
    "models/sam2/weights",
    "models/sam2/checkpoints",
)

STATUS_VALUES = (
    "dependency_missing",
    "weights_missing",
    "seed_missing",
    "inference_not_implemented",
    "ready_for_inference",
    "unsupported_backend",
    "model_load_failed",
)


def check_dependencies(project_root: Path | None = None) -> dict[str, Any]:
    """Check local SAM/SAM2 and base CV dependencies."""
    del project_root
    missing_base = [name for name in ("cv2", "numpy", "torch") if importlib.util.find_spec(name) is None]
    sam_available = importlib.util.find_spec("segment_anything") is not None
    sam2_available = importlib.util.find_spec("sam2") is not None
    return {
        "dependencies_available": not missing_base and (sam_available or sam2_available),
        "base_dependencies_available": not missing_base,
        "missing_dependencies": missing_base,
        "segment_anything_available": sam_available,
        "sam2_available": sam2_available,
        "sam_family_available": sam_available or sam2_available,
    }


def load_sam_config(project_root: Path) -> dict[str, Any]:
    """Load SAM-assisted local config."""
    path = project_root / "configs" / "models" / "sam_assisted_config.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def find_weights(project_root: Path, explicit_path: Path | None = None) -> dict[str, Any]:
    """Find local SAM/SAM2 weights without downloading anything."""
    if explicit_path:
        path = explicit_path if explicit_path.is_absolute() else project_root / explicit_path
        family = infer_model_family(str(path))
        return {
            "weights_found": path.exists() and path.is_file(),
            "weights_path": str(path) if path.exists() and path.is_file() else "",
            "sam_weights_found": path.exists() and path.is_file() and family == "sam",
            "sam2_weights_found": path.exists() and path.is_file() and family == "sam2",
            "sam_weights_path": str(path) if path.exists() and path.is_file() and family == "sam" else "",
            "sam2_weights_path": str(path) if path.exists() and path.is_file() and family == "sam2" else "",
            "searched_paths": [str(path)],
        }
    config = load_sam_config(project_root)
    search_paths = tuple(config.get("default_weights_search_paths") or DEFAULT_SEARCH_PATHS)
    searched: list[str] = []
    candidates: list[Path] = []
    sam_candidates: list[Path] = []
    sam2_candidates: list[Path] = []
    for relative in search_paths:
        root = project_root / relative
        searched.append(str(root))
        if root.is_file() and root.suffix.lower() in WEIGHT_SUFFIXES:
            candidates.append(root)
            if infer_model_family(str(root)) == "sam2":
                sam2_candidates.append(root)
            else:
                sam_candidates.append(root)
        elif root.is_dir():
            for path in root.rglob("*"):
                lower = path.name.lower()
                if ("sam" in lower or "segment" in lower) and path.suffix.lower() in WEIGHT_SUFFIXES:
                    candidates.append(path)
                    if infer_model_family(str(path)) == "sam2":
                        sam2_candidates.append(path)
                    else:
                        sam_candidates.append(path)
    return {
        "weights_found": bool(candidates),
        "weights_path": str(candidates[0]) if candidates else "",
        "sam_weights_found": bool(sam_candidates),
        "sam2_weights_found": bool(sam2_candidates),
        "sam_weights_path": str(sam_candidates[0]) if sam_candidates else "",
        "sam2_weights_path": str(sam2_candidates[0]) if sam2_candidates else "",
        "searched_paths": searched,
    }


def infer_model_family(weights_path: str) -> str:
    """Infer SAM family from weight path naming."""
    lower = weights_path.lower()
    if "sam2" in lower:
        return "sam2"
    return "sam"


def infer_sam_model_type(weights_path: str, config: dict[str, Any] | None = None) -> str:
    """Infer segment-anything registry model type."""
    lower = weights_path.lower()
    if "vit_h" in lower:
        return "vit_h"
    if "vit_l" in lower:
        return "vit_l"
    if "vit_b" in lower:
        return "vit_b"
    return str((config or {}).get("default_sam_model_type") or "vit_b")


def check_availability(project_root: Path, weights_path: Path | None = None) -> dict[str, Any]:
    """Return SAM-assisted integration readiness."""
    dependencies = check_dependencies(project_root)
    weights = find_weights(project_root, explicit_path=weights_path)
    if not dependencies["base_dependencies_available"]:
        return add_diagnostics({
            "model_name": MODEL_NAME,
            "available": False,
            "status": "dependency_missing",
            "dependencies_available": False,
            "weights_found": weights["weights_found"],
            "weights_path": weights["weights_path"],
            "architecture_available": False,
            "ready_for_inference": False,
            "seed_required": True,
            "seed_available": False,
            "reason": f"Missing required local dependencies: {', '.join(dependencies['missing_dependencies'])}.",
            **dependencies,
            "searched_weight_paths": weights["searched_paths"],
            **weight_summary(weights),
        })
    if not dependencies["sam_family_available"]:
        return add_diagnostics({
            "model_name": MODEL_NAME,
            "available": False,
            "status": "dependency_missing",
            "dependencies_available": False,
            "weights_found": weights["weights_found"],
            "weights_path": weights["weights_path"],
            "architecture_available": False,
            "ready_for_inference": False,
            "seed_required": True,
            "seed_available": False,
            "reason": "No local segment_anything or sam2 Python dependency is installed.",
            **dependencies,
            "searched_weight_paths": weights["searched_paths"],
            **weight_summary(weights),
        })
    if not weights["weights_found"]:
        return add_diagnostics({
            "model_name": MODEL_NAME,
            "available": False,
            "status": "weights_missing",
            "dependencies_available": True,
            "weights_found": False,
            "weights_path": "",
            "architecture_available": False,
            "ready_for_inference": False,
            "seed_required": True,
            "seed_available": False,
            "reason": "SAM/SAM2 dependency is available, but no local SAM/SAM2 weights were found.",
            **dependencies,
            "searched_weight_paths": weights["searched_paths"],
            **weight_summary(weights),
        })
    family = infer_model_family(weights["weights_path"])
    if family == "sam2":
        return add_diagnostics({
            "model_name": MODEL_NAME,
            "available": False,
            "status": "inference_not_implemented",
            "dependencies_available": True,
            "weights_found": True,
            "weights_path": weights["weights_path"],
            "architecture_available": dependencies["sam2_available"],
            "ready_for_inference": False,
            "seed_required": True,
            "seed_available": False,
            "reason": "SAM2 weights were found, but this repo does not yet wire a SAM2 video predictor.",
            **dependencies,
            "searched_weight_paths": weights["searched_paths"],
            **weight_summary(weights),
        })
    return add_diagnostics({
        "model_name": MODEL_NAME,
        "available": True,
        "status": "ready_for_inference",
        "dependencies_available": True,
        "weights_found": True,
        "weights_path": weights["weights_path"],
        "architecture_available": dependencies["segment_anything_available"],
        "ready_for_inference": dependencies["segment_anything_available"],
        "seed_required": True,
        "seed_available": False,
        "reason": "SAM image predictor is available. A ball seed point is still required before tracking.",
        **dependencies,
        "searched_weight_paths": weights["searched_paths"],
        **weight_summary(weights),
    })


def weight_summary(weights: dict[str, Any]) -> dict[str, Any]:
    """Return backend-specific weight status fields."""
    return {
        "sam_weights_found": bool(weights.get("sam_weights_found")),
        "sam2_weights_found": bool(weights.get("sam2_weights_found")),
        "sam_weights_path": weights.get("sam_weights_path", ""),
        "sam2_weights_path": weights.get("sam2_weights_path", ""),
    }


def add_diagnostics(payload: dict[str, Any]) -> dict[str, Any]:
    """Attach explicit SAM/SAM2 readiness diagnostics."""
    payload["selected_backend"] = selected_backend(payload)
    payload["seed_prompt_strategy_available"] = bool(payload.get("seed_required"))
    payload["status_values"] = list(STATUS_VALUES)
    payload["next_action"] = recommended_next_step(payload)
    return payload


def selected_backend(availability: dict[str, Any]) -> str:
    """Return the backend that would be used if ready."""
    if availability.get("sam2_available") and availability.get("sam2_weights_found"):
        return "sam2"
    if availability.get("segment_anything_available") and availability.get("sam_weights_found"):
        return "segment_anything"
    if availability.get("segment_anything_available"):
        return "segment_anything_waiting_for_weights"
    if availability.get("sam2_available"):
        return "sam2_waiting_for_weights"
    return "none"


def describe_missing_requirements(project_root: Path, weights_path: Path | None = None) -> dict[str, Any]:
    """Describe missing SAM/SAM2 requirements."""
    availability = check_availability(project_root, weights_path=weights_path)
    missing: list[str] = []
    if not availability.get("base_dependencies_available"):
        missing.extend(availability.get("missing_dependencies", []))
    if not availability.get("sam_family_available"):
        missing.append("segment_anything or sam2 dependency")
    if not availability.get("sam_weights_found"):
        missing.append("SAM .pt/.pth weights")
    if not availability.get("sam2_weights_found"):
        missing.append("SAM2 .pt/.pth weights")
    if availability.get("weights_found") and not availability.get("ready_for_inference"):
        missing.append("SAM/SAM2 inference wrapper")
    return {
        "status": availability.get("status"),
        "missing_requirements": missing,
        "recommended_next_step": recommended_next_step(availability),
        "next_action": availability.get("next_action") or recommended_next_step(availability),
        "availability": availability,
    }


def recommended_next_step(availability: dict[str, Any]) -> str:
    """Return a concrete next local action."""
    status = availability.get("status")
    if status == "dependency_missing":
        return "Install local segment_anything or sam2 support, then add matching local weights. TrackNet remains the preferred primary path."
    if status == "weights_missing":
        return "Place compatible SAM weights under models/sam/weights/ or SAM2 weights under models/sam2/weights/."
    if status == "seed_missing":
        return "Provide trusted ball seed prompts near manual event windows before running SAM-assisted tracking."
    if status == "inference_not_implemented":
        return "Wire the matching SAM2 video predictor or use segment_anything SAM weights for the image-prompt path."
    if status == "unsupported_backend":
        return "Use segment_anything SAM or wire a supported SAM2 backend."
    if status == "ready_for_inference":
        return "Provide a reliable ball seed point near each event or from trusted labels before running SAM-assisted tracking."
    return "Run scripts/check_sam_assisted_integration.py after adding local SAM assets."


def load_model(weights_path: Path, project_root: Path) -> dict[str, Any]:
    """Load a local SAM image predictor when segment_anything is available."""
    availability = check_availability(project_root, weights_path=weights_path)
    if availability.get("status") != "ready_for_inference":
        raise RuntimeError(f"{availability.get('status')}: {availability.get('reason')}")
    from segment_anything import SamPredictor, sam_model_registry

    config = load_sam_config(project_root)
    model_type = infer_sam_model_type(str(weights_path), config)
    if model_type not in sam_model_registry:
        raise RuntimeError(f"Unsupported SAM model_type '{model_type}'.")
    sam = sam_model_registry[model_type](checkpoint=str(weights_path))
    sam.eval()
    predictor = SamPredictor(sam)
    return {"predictor": predictor, "model_type": model_type, "family": "sam"}


def initialize_prompt(event: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Find a trusted ball seed near one manual event."""
    seeds = list(context.get("seed_rows") or [])
    if not seeds:
        return {"seed_available": False, "reason": "No trusted ball seed rows were supplied."}
    start = int(event["start_frame"]) - int(context.get("seed_tolerance", 5))
    end = int(event["end_frame"]) + int(context.get("seed_tolerance", 5))
    candidates = [row for row in seeds if start <= _int(row.get("frame_index"), -1) <= end]
    if not candidates:
        return {"seed_available": False, "reason": f"No trusted ball seed found for frames {start}-{end}."}
    target = int(event["contact_frame_estimate"])
    best = min(candidates, key=lambda row: abs(_int(row.get("frame_index"), target) - target))
    x = _float(best.get("x", best.get("ball_x", best.get("image_x"))))
    y = _float(best.get("y", best.get("ball_y", best.get("image_y"))))
    if x is None or y is None:
        return {"seed_available": False, "reason": "Nearest seed row did not include image x/y."}
    return {"seed_available": True, "frame_index": _int(best.get("frame_index"), target), "x": x, "y": y, "source": best.get("source", "trusted_seed")}


def track_clip(
    *,
    video_path: Path,
    event: dict[str, Any],
    search_start_frame: int,
    search_end_frame: int,
    model_context: dict[str, Any],
    prompt: dict[str, Any],
    fps: int,
) -> dict[str, Any]:
    """Run prompt-based SAM segmentation over a local event clip."""
    if not prompt.get("seed_available"):
        return {"status": "seed_missing", "tracked_frames": [], "reason": prompt.get("reason", "Seed prompt missing.")}
    if importlib.util.find_spec("cv2") is None or importlib.util.find_spec("numpy") is None:
        return {"status": "dependency_missing", "tracked_frames": [], "reason": "OpenCV and NumPy are required."}
    import cv2
    import numpy as np

    predictor = model_context["predictor"]
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        return {"status": "error", "tracked_frames": [], "reason": f"Could not open video: {video_path}"}
    capture.set(cv2.CAP_PROP_POS_FRAMES, int(max(0, search_start_frame)))
    rows: list[dict[str, Any]] = []
    current = int(max(0, search_start_frame))
    point = np.array([[float(prompt["x"]), float(prompt["y"])]], dtype=np.float32)
    labels = np.array([1], dtype=np.int32)
    while current <= int(search_end_frame):
        ok, frame = capture.read()
        if not ok:
            break
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        predictor.set_image(rgb)
        masks, scores, _logits = predictor.predict(point_coords=point, point_labels=labels, multimask_output=True)
        if len(masks) == 0:
            current += 1
            continue
        best_index = int(np.argmax(scores))
        mask = masks[best_index]
        ys, xs = np.where(mask)
        if len(xs) == 0:
            current += 1
            continue
        cx = float(xs.mean())
        cy = float(ys.mean())
        confidence = float(scores[best_index])
        rows.append(
            {
                "frame_index": current,
                "timestamp_seconds": round(current / float(fps), 4),
                "ball_x": round(cx, 3),
                "ball_y": round(cy, 3),
                "confidence": round(confidence, 4),
                "source_model": MODEL_NAME,
                "visibility_status": "visible",
                "notes": f"sam_prompt_seed_frame={prompt.get('frame_index')}; event_id={event.get('event_id')}",
            }
        )
        point = np.array([[cx, cy]], dtype=np.float32)
        current += 1
    capture.release()
    return {"status": "resolved" if rows else "unresolved", "tracked_frames": rows, "reason": "SAM-assisted prompt tracking completed." if rows else "SAM produced no masks for this event clip."}


def resolve_event_position(video_path: Path, event: dict[str, Any], search_window: list[int], context: dict[str, Any]) -> dict[str, Any]:
    """Resolve one manual event using SAM-assisted tracking rows."""
    del video_path
    rows = list(context.get("track_rows") or [])
    candidates = [row for row in rows if int(row.get("frame_index", -1)) in set(int(frame) for frame in search_window)]
    if candidates:
        target = int(event["contact_frame_estimate"])
        best = max(candidates, key=lambda row: (float(row.get("confidence") or 0.0), -abs(int(row["frame_index"]) - target)))
        return {
            "model_name": MODEL_NAME,
            "event_id": event["event_id"],
            "event_type": event["event_type"],
            "shot_type": event.get("shot_type", ""),
            "manual_frame": target,
            "search_start_frame": min(search_window) if search_window else "",
            "search_end_frame": max(search_window) if search_window else "",
            "resolved_frame": best.get("frame_index", ""),
            "image_x": best.get("ball_x", ""),
            "image_y": best.get("ball_y", ""),
            "raw_score": best.get("confidence", ""),
            "confidence": best.get("confidence", ""),
            "position_status": "resolved",
            "debug_reason": "Resolved from SAM-assisted mask centroid.",
        }
    status = context.get("status") or "model_unavailable"
    return {
        "model_name": MODEL_NAME,
        "event_id": event["event_id"],
        "event_type": event["event_type"],
        "shot_type": event.get("shot_type", ""),
        "manual_frame": event["contact_frame_estimate"],
        "search_start_frame": min(search_window) if search_window else "",
        "search_end_frame": max(search_window) if search_window else "",
        "resolved_frame": "",
        "image_x": "",
        "image_y": "",
        "raw_score": "",
        "confidence": "low",
        "position_status": status,
        "debug_reason": context.get("reason") or "SAM-assisted adapter unavailable.",
    }


def _float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default
