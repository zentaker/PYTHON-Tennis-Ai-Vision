"""TrackNet-style adapter and availability contract."""

from __future__ import annotations

import importlib.util
import importlib
import json
from pathlib import Path
from typing import Any


MODEL_NAME = "tracknet_candidate"
WEIGHT_SEARCH_PATHS = (
    "models/tracknet/weights/tracknet.pt",
    "models/tracknet/weights/tracknet.pth",
    "models/tracknet/weights/tracknetv2.pt",
    "models/tracknet/weights/tracknetv2.pth",
    "models/tracknet/weights/tracknetv3.pt",
    "models/tracknet/weights/tracknetv3.pth",
    "models/tracknet/weights",
    "models/tracknet/checkpoints",
    "models/tracknet",
)
COMMON_MODEL_DIRS = ("models/tracknet", "models", "weights", "pretrained", "external_models", "src/tennis_vision/models")
WEIGHT_SUFFIXES = (".pt", ".pth", ".ckpt", ".h5", ".hdf5", ".keras", ".onnx")


def is_available(project_root: Path, weights_path: Path | None = None) -> bool:
    """Return whether a runnable local TrackNet path is available."""
    availability = check_availability(project_root, weights_path=weights_path)
    return bool(availability.get("available"))


def check_dependencies(project_root: Path | None = None) -> dict[str, Any]:
    """Check lightweight runtime dependencies and local implementation presence."""
    del project_root
    required = ("cv2", "numpy")
    optional_inference = ("torch",)
    missing_required = [name for name in required if importlib.util.find_spec(name) is None]
    missing_optional = [name for name in optional_inference if importlib.util.find_spec(name) is None]
    return {
        "dependencies_available": not missing_required,
        "missing_dependencies": missing_required,
        "missing_optional_inference_dependencies": missing_optional,
        "notes": "A local TrackNet inference implementation is still required even when base Python packages are present.",
    }


def load_tracknet_config(project_root: Path) -> dict[str, Any]:
    """Load local TrackNet config when available."""
    path = project_root / "configs" / "models" / "tracknet_config.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_tracknet_registry(project_root: Path) -> dict[str, Any]:
    """Load the local TrackNet variant registry."""
    path = project_root / "configs" / "models" / "tracknet_registry.json"
    if not path.exists():
        return {"registry_loaded": False, "variants": {}}
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["registry_loaded"] = True
    return payload


def architecture_available(module_spec: str) -> bool:
    """Return whether a concrete architecture class is importable and non-placeholder."""
    if not module_spec or ":" not in module_spec:
        return False
    module_name, class_name = module_spec.split(":", 1)
    try:
        module = importlib.import_module(module_name)
        cls = getattr(module, class_name)
    except (ImportError, AttributeError):
        return False
    return not bool(getattr(cls, "is_placeholder", False))


def weight_matches(project_root: Path, patterns: list[str]) -> list[str]:
    """Return existing weight paths matching explicit registry patterns."""
    matches: list[str] = []
    for pattern in patterns:
        path = project_root / pattern
        if path.exists() and path.is_file():
            matches.append(str(path))
    return matches


def discover_tracknet_assets(project_root: Path, explicit_path: Path | None = None) -> dict[str, Any]:
    """Discover registry variants, architecture availability, and local weights."""
    registry = load_tracknet_registry(project_root)
    variants = registry.get("variants", {})
    discovered: list[dict[str, Any]] = []
    for variant_name, entry in variants.items():
        patterns = list(entry.get("expected_weights_patterns") or entry.get("weights_patterns") or [])
        matched_weights = weight_matches(project_root, patterns)
        arch_module = str(entry.get("expected_architecture_module") or entry.get("architecture_module_expected") or "")
        arch_found = architecture_available(arch_module)
        status = "ready" if arch_found and matched_weights else "architecture_missing" if matched_weights else "weights_missing"
        if not arch_found and not matched_weights:
            status = "not_installed"
        discovered.append(
            {
                "variant": variant_name,
                "model_family": entry.get("model_family", ""),
                "architecture_module": arch_module,
                "architecture_class_expected": entry.get("architecture_class_expected", ""),
                "architecture_found": arch_found,
                "weights_found": bool(matched_weights),
                "weights": matched_weights,
                "input_frame_count": entry.get("input_frame_count", entry.get("input_frames", "")),
                "expected_input_shape": entry.get("expected_input_shape", ""),
                "expected_output_type": entry.get("expected_output_type", entry.get("output_type", "unknown")),
                "status": status,
                "notes": entry.get("notes", ""),
            }
        )
    explicit = find_weights(project_root, explicit_path=explicit_path) if explicit_path else {"weights_found": False, "weights_path": ""}
    return {
        "registry_loaded": bool(registry.get("registry_loaded")),
        "variants_checked": discovered,
        "explicit_weights": explicit,
    }


def select_tracknet_variant(project_root: Path, explicit_path: Path | None = None) -> dict[str, Any]:
    """Select the best available TrackNet variant from the registry."""
    assets = discover_tracknet_assets(project_root, explicit_path=explicit_path)
    variants = assets["variants_checked"]
    ready = [variant for variant in variants if variant["status"] == "ready"]
    if ready:
        return {**ready[0], "selected": True, "assets": assets}
    with_weights = [variant for variant in variants if variant["weights_found"]]
    if with_weights:
        return {**with_weights[0], "selected": True, "assets": assets}
    if explicit_path and assets["explicit_weights"].get("weights_found"):
        return {
            "variant": "custom_tracknet",
            "model_family": "custom_tracknet",
            "architecture_module": "tennis_vision.model_adapters.tracknet_architectures:TrackNetInferenceModel",
            "architecture_found": False,
            "weights_found": True,
            "weights": [assets["explicit_weights"]["weights_path"]],
            "input_frame_count": 3,
            "expected_input_shape": "temporal clip tensor, implementation-specific",
            "expected_output_type": "unknown",
            "status": "architecture_missing",
            "notes": "Explicit weights supplied, but no concrete architecture is wired.",
            "selected": True,
            "assets": assets,
        }
    return {
        "variant": "",
        "model_family": "",
        "architecture_module": "",
        "architecture_found": False,
        "weights_found": False,
        "weights": [],
        "status": "weights_missing",
        "selected": False,
        "assets": assets,
    }


def find_weights(project_root: Path, explicit_path: Path | None = None) -> dict[str, Any]:
    """Find local TrackNet weights without downloading anything."""
    config = load_tracknet_config(project_root)
    candidates: list[Path] = []
    if explicit_path:
        path = explicit_path if explicit_path.is_absolute() else project_root / explicit_path
        if path.exists() and path.is_file():
            candidates.append(path)
        return {
            "weights_found": bool(candidates),
            "weights_path": str(candidates[0]) if candidates else "",
            "searched_paths": [str(path)],
        }

    searched: list[str] = []
    search_paths = tuple(config.get("default_weights_search_paths") or WEIGHT_SEARCH_PATHS)
    for relative in search_paths:
        root = project_root / relative
        searched.append(str(root))
        if root.is_file() and root.suffix.lower() in WEIGHT_SUFFIXES:
            candidates.append(root)
        elif root.is_dir():
            for path in root.rglob("*"):
                if "tracknet" in path.name.lower() and path.suffix.lower() in WEIGHT_SUFFIXES:
                    candidates.append(path)
    return {
        "weights_found": bool(candidates),
        "weights_path": str(candidates[0]) if candidates else "",
        "searched_paths": searched,
    }


def inspect_weight_file(weights_path: Path) -> dict[str, Any]:
    """Inspect TrackNet weight file type without assuming architecture."""
    if not weights_path.exists():
        return {
            "weight_type": "missing",
            "architecture_available": False,
            "ready_for_inference": False,
            "status": "weights_missing",
            "weights_status": "missing",
            "reason": f"Weight file does not exist: {weights_path}",
        }
    suffix = weights_path.suffix.lower()
    if suffix == ".onnx":
        return {
            "weight_type": "onnx",
            "architecture_available": False,
            "ready_for_inference": False,
            "status": "unsupported_onnx_for_current_adapter",
            "weights_status": "unsupported_onnx_for_current_adapter",
            "reason": "ONNX TrackNet weights were found, but this adapter does not include ONNX Runtime support.",
        }
    if suffix not in {".pt", ".pth", ".ckpt"}:
        return {
            "weight_type": "unknown",
            "architecture_available": False,
            "ready_for_inference": False,
            "status": "unsupported_weight_format",
            "weights_status": "unsupported_weight_format",
            "reason": f"Unsupported TrackNet weight format: {suffix}. Use .pt/.pth with PyTorch model support, or add a dedicated adapter.",
        }
    if importlib.util.find_spec("torch") is None:
        return {
            "weight_type": "unknown_torch_unavailable",
            "architecture_available": False,
            "ready_for_inference": False,
            "status": "dependency_missing",
            "weights_status": "torch_missing_for_inspection",
            "reason": "PyTorch is required to inspect .pt/.pth weights.",
        }
    try:
        import torch

        checkpoint = _torch_load_local(weights_path)
    except Exception as exc:  # pragma: no cover - depends on external weight file
        return {
            "weight_type": "unknown",
            "architecture_available": False,
            "ready_for_inference": False,
            "status": "model_load_failed",
            "weights_status": "load_failed",
            "reason": f"torch.load failed: {type(exc).__name__}: {exc}",
        }

    if hasattr(checkpoint, "forward"):
        return {
            "weight_type": "full_model",
            "architecture_available": True,
            "ready_for_inference": True,
            "status": "ready_for_inference",
            "weights_status": "potentially_ready",
            "reason": "A full PyTorch model loaded successfully and can be attempted through the generic TrackNet temporal-clip adapter.",
        }
    if isinstance(checkpoint, dict):
        keys = set(checkpoint.keys())
        if "state_dict" in keys or any(str(key).startswith(("module.", "conv", "encoder", "decoder")) for key in keys):
            return {
                "weight_type": "state_dict",
                "architecture_available": False,
                "ready_for_inference": False,
                "status": "architecture_missing",
                "weights_status": "state_dict_requires_architecture",
                "reason": "Weights appear to be a state_dict/checkpoint. A TrackNet architecture class must be wired before inference.",
            }
        return {
            "weight_type": "checkpoint_dict",
            "architecture_available": False,
            "ready_for_inference": False,
            "status": "architecture_missing",
            "weights_status": "checkpoint_dict_requires_architecture",
            "reason": "Checkpoint dictionary loaded, but no supported TrackNet architecture wrapper is available.",
        }
    return {
        "weight_type": "unknown",
        "architecture_available": False,
        "ready_for_inference": False,
        "status": "architecture_missing",
        "weights_status": "unknown_requires_adapter",
        "reason": f"Weight file loaded as {type(checkpoint).__name__}, but did not match a supported full-model, state_dict, or checkpoint pattern.",
    }


def architecture_status(variants: list[dict[str, Any]]) -> str:
    """Return a concise architecture status."""
    found = sum(1 for item in variants if item.get("architecture_found"))
    if found:
        return f"found:{found}"
    return "missing"


def inference_implementation_status(availability: dict[str, Any]) -> str:
    """Classify inference implementation readiness."""
    status = availability.get("status")
    if availability.get("ready_for_inference"):
        return "ready_for_inference"
    if status == "weights_missing":
        return "waiting_for_weights"
    if status == "architecture_missing":
        return "architecture_missing"
    if status == "unsupported_onnx_for_current_adapter":
        return "onnx_runtime_not_supported"
    if status == "model_load_failed":
        return "model_load_failed"
    if status == "dependency_missing":
        return "dependency_missing"
    return "not_ready"


def check_availability(project_root: Path, weights_path: Path | None = None) -> dict[str, Any]:
    """Check whether TrackNet code and weights appear to exist locally."""
    return _check_availability(project_root, weights_path=weights_path)


def _check_availability(project_root: Path, weights_path: Path | None = None) -> dict[str, Any]:
    dependencies = check_dependencies(project_root)
    selected_variant = select_tracknet_variant(project_root, explicit_path=weights_path)
    assets = selected_variant.get("assets", {})
    weights = find_weights(project_root, explicit_path=weights_path)
    weight_inspection = inspect_weight_file(Path(weights["weights_path"])) if weights.get("weights_path") else {
        "weight_type": "missing",
        "architecture_available": False,
        "ready_for_inference": False,
        "status": "weights_missing",
        "weights_status": "missing",
        "reason": "No TrackNet weight file was found.",
    }
    found_code: list[str] = []
    for relative in COMMON_MODEL_DIRS:
        root = project_root / relative
        if not root.exists():
            continue
        for path in root.rglob("*"):
            lower = path.name.lower()
            if "tracknet" in lower and path.is_file():
                found_code.append(str(path))

    if not dependencies["dependencies_available"]:
        payload = {
            "model_name": MODEL_NAME,
            "available": False,
            "status": "dependency_missing",
            "dependencies_available": False,
            "weights_found": weights["weights_found"],
            "weights_path": weights["weights_path"],
            "weight_type": weight_inspection["weight_type"],
            "architecture_available": weight_inspection["architecture_available"],
            "ready_for_inference": False,
            "reason": f"Missing required local dependencies: {', '.join(dependencies['missing_dependencies'])}.",
            "missing_dependencies": dependencies["missing_dependencies"],
            "found_code": found_code,
            "searched_weight_paths": weights["searched_paths"],
            "registry_loaded": bool(assets.get("registry_loaded")),
            "variants_checked": assets.get("variants_checked", []),
            "selected_variant": selected_variant.get("variant", ""),
            "weights_status": weight_inspection.get("weights_status", weight_inspection.get("status", "")),
        }
        return add_diagnostics(payload)

    if not weights["weights_found"]:
        payload = {
            "model_name": MODEL_NAME,
            "available": False,
            "status": "weights_missing",
            "dependencies_available": True,
            "weights_found": False,
            "weights_path": "",
            "weight_type": "missing",
            "architecture_available": False,
            "ready_for_inference": False,
            "reason": "No local TrackNet/TrackNetV2/TrackNetV3/TrackNetV4 weights found. Place weights under models/tracknet/weights/ or pass --tracknet-weights.",
            "missing_dependencies": [],
            "found_code": found_code,
            "searched_weight_paths": weights["searched_paths"],
            "registry_loaded": bool(assets.get("registry_loaded")),
            "variants_checked": assets.get("variants_checked", []),
            "selected_variant": "",
            "weights_status": "missing",
        }
        return add_diagnostics(payload)

    if weight_inspection["status"] == "ready_for_inference":
        payload = {
            "model_name": MODEL_NAME,
            "available": True,
            "status": "ready_for_inference",
            "dependencies_available": True,
            "weights_found": True,
            "weights_path": weights["weights_path"],
            "weight_type": weight_inspection["weight_type"],
            "architecture_available": True,
            "ready_for_inference": True,
            "reason": weight_inspection["reason"],
            "missing_dependencies": [],
            "found_code": found_code,
            "searched_weight_paths": weights["searched_paths"],
            "registry_loaded": bool(assets.get("registry_loaded")),
            "variants_checked": assets.get("variants_checked", []),
            "selected_variant": selected_variant.get("variant", "custom_tracknet"),
            "input_frame_count": selected_variant.get("input_frame_count", 3) or 3,
            "weights_status": weight_inspection.get("weights_status", "potentially_ready"),
        }
        return add_diagnostics(payload)

    if weight_inspection["status"] in {"unsupported_weight_format", "unsupported_onnx_for_current_adapter", "model_load_failed", "architecture_missing", "inference_not_implemented"}:
        payload = {
            "model_name": MODEL_NAME,
            "available": False,
            "status": weight_inspection["status"],
            "dependencies_available": True,
            "weights_found": True,
            "weights_path": weights["weights_path"],
            "weight_type": weight_inspection["weight_type"],
            "architecture_available": weight_inspection["architecture_available"],
            "ready_for_inference": False,
            "reason": weight_inspection["reason"],
            "missing_dependencies": [],
            "found_code": found_code,
            "searched_weight_paths": weights["searched_paths"],
            "registry_loaded": bool(assets.get("registry_loaded")),
            "variants_checked": assets.get("variants_checked", []),
            "selected_variant": selected_variant.get("variant", ""),
            "weights_status": weight_inspection.get("weights_status", weight_inspection.get("status", "")),
        }
        return add_diagnostics(payload)

    payload = {
        "model_name": MODEL_NAME,
        "available": False,
        "status": "model_unavailable",
        "dependencies_available": True,
        "weights_found": True,
        "weights_path": weights["weights_path"],
        "weight_type": weight_inspection["weight_type"],
        "architecture_available": weight_inspection["architecture_available"],
        "ready_for_inference": False,
        "reason": "TrackNet-like code and weights were found, but generic inference is not safely wired. Add an implementation-specific infer_clip adapter before running replay generation.",
        "found_code": found_code,
        "searched_weight_paths": weights["searched_paths"],
        "registry_loaded": bool(assets.get("registry_loaded")),
        "variants_checked": assets.get("variants_checked", []),
        "selected_variant": selected_variant.get("variant", ""),
        "weights_status": weight_inspection.get("weights_status", weight_inspection.get("status", "")),
    }
    return add_diagnostics(payload)


def add_diagnostics(payload: dict[str, Any]) -> dict[str, Any]:
    """Attach explicit TrackNet readiness diagnostic fields."""
    variants = list(payload.get("variants_checked") or [])
    payload["architecture_modules_found"] = sum(1 for item in variants if item.get("architecture_found"))
    payload["architecture_status"] = architecture_status(variants)
    payload["weights_status"] = payload.get("weights_status") or ("found" if payload.get("weights_found") else "missing")
    payload["inference_implementation_status"] = inference_implementation_status(payload)
    payload["exact_next_action"] = exact_next_action(payload)
    return payload


def describe_missing_requirements(project_root: Path, weights_path: Path | None = None) -> dict[str, Any]:
    """Describe missing requirements and next step for TrackNet integration."""
    availability = check_availability(project_root, weights_path=weights_path)
    missing: list[str] = []
    if not availability.get("dependencies_available"):
        missing.extend(availability.get("missing_dependencies", []))
    if int(availability.get("architecture_modules_found") or 0) == 0:
        missing.append("TrackNet architecture class / inference wrapper")
    if not availability.get("weights_found"):
        missing.append("TrackNet .pt/.pth weights")
    if availability.get("weights_found") and not availability.get("architecture_available") and "TrackNet architecture class / inference wrapper" not in missing:
        missing.append("TrackNet architecture class / inference wrapper")
    if availability.get("weights_found") and availability.get("architecture_available") and not availability.get("ready_for_inference"):
        missing.append("infer_clip implementation")
    return {
        "status": availability.get("status"),
        "missing_requirements": missing,
        "recommended_next_step": _recommended_next_step(availability),
        "exact_next_action": availability.get("exact_next_action") or exact_next_action(availability),
        "availability": availability,
    }


def _recommended_next_step(availability: dict[str, Any]) -> str:
    status = availability.get("status")
    if status == "weights_missing":
        return "Place a compatible TrackNet .pt or .pth file in models/tracknet/weights/ or pass --tracknet-weights."
    if status == "dependency_missing":
        return f"Install missing dependencies: {', '.join(availability.get('missing_dependencies', []))}."
    if status == "architecture_missing":
        return "Wire the TrackNet architecture class that matches the state_dict/checkpoint."
    if status == "inference_not_implemented":
        return "Implement load_model/infer_clip for the local TrackNet architecture."
    if status == "unsupported_weight_format":
        return "Use a .pt or .pth TrackNet weight file."
    if status == "unsupported_onnx_for_current_adapter":
        return "Add ONNX Runtime support or provide PyTorch .pt/.pth TrackNet weights."
    return "Run scripts/check_tracknet_integration.py after adding local TrackNet assets."


def exact_next_action(availability: dict[str, Any]) -> str:
    """Return the unambiguous next artifact/action for the current state."""
    if not availability.get("dependencies_available"):
        return f"Install missing local dependencies: {', '.join(availability.get('missing_dependencies', []))}."
    if not availability.get("weights_found"):
        return "Add TrackNet architecture code and matching pretrained .pt/.pth weights under models/tracknet/weights/."
    status = availability.get("status")
    if status == "architecture_missing":
        return "Wire the TrackNet architecture class that matches this state_dict/checkpoint, then rerun the check."
    if status == "unsupported_onnx_for_current_adapter":
        return "Provide PyTorch .pt/.pth weights or implement ONNX Runtime inference support."
    if status == "model_load_failed":
        return "Verify the weight file is a compatible local TrackNet checkpoint and can be loaded by PyTorch."
    if availability.get("ready_for_inference"):
        return "Run python scripts/run_tracknet_replay_pipeline.py."
    return "Implement or adjust TrackNet load_model/infer_clip/decode_heatmap for the selected architecture."


def load_model(weights_path: Path, context: dict[str, Any] | None = None) -> Any:
    """Load a TrackNet-style model from a full PyTorch model file.

    State-dict checkpoints still require a matching architecture wrapper. This
    loader deliberately refuses to guess architectures because that would make
    false inference look real.
    """
    del context
    inspection = inspect_weight_file(weights_path)
    if inspection.get("status") != "ready_for_inference":
        raise RuntimeError(f"{inspection.get('status')}: {inspection.get('reason')}")

    model = _torch_load_local(weights_path)
    if not hasattr(model, "forward"):
        raise RuntimeError("Loaded object is not a callable PyTorch model.")
    model.eval()
    return model


def _torch_load_local(weights_path: Path) -> Any:
    """Load a local PyTorch checkpoint, allowing full model files when supported."""
    import torch

    try:
        return torch.load(str(weights_path), map_location="cpu", weights_only=False)
    except TypeError:  # pragma: no cover - older PyTorch
        return torch.load(str(weights_path), map_location="cpu")


def preprocess_clip(
    frames: list[Any],
    *,
    input_size: tuple[int, int] = (288, 512),
) -> dict[str, Any]:
    """Build common temporal TrackNet tensors from OpenCV BGR frames."""
    if not frames:
        raise ValueError("TrackNet inference requires at least one frame.")
    if importlib.util.find_spec("cv2") is None or importlib.util.find_spec("numpy") is None:
        raise RuntimeError("OpenCV and NumPy are required for TrackNet preprocessing.")
    if importlib.util.find_spec("torch") is None:
        raise RuntimeError("PyTorch is required for TrackNet inference.")
    import cv2
    import numpy as np
    import torch

    height, width = input_size
    original_height, original_width = frames[0].shape[:2]
    processed: list[np.ndarray] = []
    for frame in frames:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (width, height), interpolation=cv2.INTER_AREA)
        processed.append(resized.astype("float32") / 255.0)
    array = np.stack(processed, axis=0)
    sequence = torch.from_numpy(array).permute(0, 3, 1, 2).unsqueeze(0).contiguous()
    channel_stack = sequence.reshape(1, len(frames) * 3, height, width).contiguous()
    return {
        "sequence": sequence,
        "channel_stack": channel_stack,
        "input_size": input_size,
        "original_size": (original_height, original_width),
    }


def infer_clip(model: Any, frames: list[Any], context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Infer TrackNet heatmaps/coordinates for a short clip."""
    context = context or {}
    frame_indices = list(context.get("frame_indices") or [])
    input_size = tuple(context.get("input_size") or (288, 512))
    preprocessed = preprocess_clip(frames, input_size=input_size)  # type: ignore[arg-type]
    import torch

    errors: list[str] = []
    with torch.no_grad():
        for input_name in ("channel_stack", "sequence"):
            try:
                output = model(preprocessed[input_name])
                return decode_heatmap(
                    output,
                    frame_indices=frame_indices,
                    original_size=preprocessed["original_size"],
                    input_size=preprocessed["input_size"],
                )
            except Exception as exc:  # pragma: no cover - depends on external model
                errors.append(f"{input_name}: {type(exc).__name__}: {exc}")
    raise RuntimeError("TrackNet inference failed for supported tensor layouts: " + " | ".join(errors))


def decode_heatmap(
    output: Any,
    *,
    frame_indices: list[int] | None = None,
    original_size: tuple[int, int] | None = None,
    input_size: tuple[int, int] | None = None,
) -> list[dict[str, Any]]:
    """Decode common TrackNet heatmap or coordinate outputs into coordinates."""
    if importlib.util.find_spec("numpy") is None:
        raise RuntimeError("NumPy is required for TrackNet output decoding.")
    import numpy as np

    if isinstance(output, (tuple, list)):
        output = output[0]
    if hasattr(output, "detach"):
        output = output.detach().cpu().numpy()
    array = np.asarray(output)
    frame_indices = frame_indices or []
    original_height, original_width = original_size or (1, 1)
    input_height, input_width = input_size or (original_height, original_width)

    coordinate_rows = _decode_coordinate_array(array, frame_indices, original_width, original_height)
    if coordinate_rows:
        return coordinate_rows

    heatmaps = _normalize_heatmap_array(array)
    rows: list[dict[str, Any]] = []
    for index, heatmap in enumerate(heatmaps):
        flat_index = int(np.nanargmax(heatmap))
        y, x = np.unravel_index(flat_index, heatmap.shape)
        confidence = float(np.nanmax(heatmap))
        if frame_indices and len(frame_indices) == len(heatmaps):
            frame_index = frame_indices[index]
        elif frame_indices:
            frame_index = frame_indices[len(frame_indices) // 2]
        else:
            frame_index = index
        rows.append(
            {
                "frame_index": int(frame_index),
                "ball_x": round(float(x) * float(original_width) / float(input_width), 3),
                "ball_y": round(float(y) * float(original_height) / float(input_height), 3),
                "confidence": round(confidence, 4),
                "source_model": MODEL_NAME,
                "visibility_status": "visible" if confidence > 0 else "unknown",
                "notes": "decoded_from_tracknet_heatmap",
            }
        )
    return rows


def _decode_coordinate_array(
    array: Any,
    frame_indices: list[int],
    original_width: int,
    original_height: int,
) -> list[dict[str, Any]]:
    """Decode coordinate-like tensors when a model returns x/y directly."""
    import numpy as np

    arr = np.asarray(array)
    if arr.ndim == 0 or arr.shape[-1] < 2:
        return []
    if arr.ndim >= 3 and arr.shape[-2] > 8:
        return []
    coords = arr.reshape(-1, arr.shape[-1])
    if coords.shape[0] > max(1, len(frame_indices), 8):
        return []
    rows: list[dict[str, Any]] = []
    for index, coord in enumerate(coords):
        x = float(coord[0])
        y = float(coord[1])
        if 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0:
            x *= float(original_width)
            y *= float(original_height)
        confidence = float(coord[2]) if len(coord) > 2 else 1.0
        frame_index = frame_indices[index] if index < len(frame_indices) else frame_indices[len(frame_indices) // 2] if frame_indices else index
        rows.append(
            {
                "frame_index": int(frame_index),
                "ball_x": round(x, 3),
                "ball_y": round(y, 3),
                "confidence": round(confidence, 4),
                "source_model": MODEL_NAME,
                "visibility_status": "visible",
                "notes": "decoded_from_tracknet_coordinate_output",
            }
        )
    return rows


def _normalize_heatmap_array(array: Any) -> list[Any]:
    """Return a list of 2D heatmaps from common tensor shapes."""
    import numpy as np

    arr = np.asarray(array)
    arr = np.squeeze(arr)
    if arr.ndim == 2:
        return [arr]
    if arr.ndim == 3:
        return [arr[index] for index in range(arr.shape[0])]
    if arr.ndim == 4:
        # Common shape after squeeze may still be T, C, H, W.
        if arr.shape[1] == 1:
            return [arr[index, 0] for index in range(arr.shape[0])]
        return [arr[index].max(axis=0) for index in range(arr.shape[0])]
    raise RuntimeError(f"Unsupported TrackNet output shape: {arr.shape}")


def track_video_segment(
    *,
    video_path: Path,
    start_frame: int,
    end_frame: int,
    weights_path: Path | None,
    project_root: Path,
    fps: int = 60,
) -> dict[str, Any]:
    """Track a video segment using TrackNet when a local implementation exists."""
    availability = _check_availability(project_root, weights_path=weights_path)
    if not availability.get("available"):
        return {
            "status": availability["status"],
            "tracked_frames": [],
            "reason": availability["reason"],
            "availability": availability,
        }
    if importlib.util.find_spec("cv2") is None:
        return {
            "status": "dependency_missing",
            "tracked_frames": [],
            "reason": "OpenCV is required for TrackNet video segment inference.",
            "availability": availability,
        }
    try:
        import cv2

        model = load_model(Path(availability["weights_path"]), context=availability)
        clip_size = int(availability.get("input_frame_count") or 3)
        clip_size = max(1, clip_size)
        capture = cv2.VideoCapture(str(video_path))
        if not capture.isOpened():
            return {
                "status": "error",
                "tracked_frames": [],
                "reason": f"Could not open video: {video_path}",
                "availability": availability,
            }
        capture.set(cv2.CAP_PROP_POS_FRAMES, int(max(0, start_frame)))
        frames: list[Any] = []
        frame_indices: list[int] = []
        tracked_by_frame: dict[int, dict[str, Any]] = {}
        current = int(max(0, start_frame))
        while current <= int(end_frame):
            ok, frame = capture.read()
            if not ok:
                break
            frames.append(frame)
            frame_indices.append(current)
            if len(frames) == clip_size:
                for row in infer_clip(model, frames, context={"frame_indices": frame_indices}):
                    tracked_by_frame[int(row["frame_index"])] = row
                frames = frames[1:]
                frame_indices = frame_indices[1:]
            current += 1
        if frames:
            for row in infer_clip(model, frames, context={"frame_indices": frame_indices}):
                tracked_by_frame[int(row["frame_index"])] = row
        capture.release()
        rows = [tracked_by_frame[key] for key in sorted(tracked_by_frame)]
        for row in rows:
            row.setdefault("timestamp_seconds", round(int(row["frame_index"]) / float(fps), 4))
        return {
            "status": "resolved",
            "tracked_frames": rows,
            "reason": f"TrackNet inference completed for frames {start_frame}-{end_frame}.",
            "availability": availability,
        }
    except NotImplementedError as exc:
        return {
            "status": "inference_not_implemented",
            "tracked_frames": [],
            "reason": str(exc),
            "availability": availability,
        }
    except Exception as exc:  # pragma: no cover - depends on external model
        return {
            "status": "model_load_failed",
            "tracked_frames": [],
            "reason": f"TrackNet inference failed: {type(exc).__name__}: {exc}",
            "availability": availability,
        }


def prepare_context(**kwargs: Any) -> dict[str, Any]:
    """Return an unavailable context; no fake inference is performed."""
    project_root = Path(kwargs["project_root"])
    return check_availability(project_root)


def resolve_event_position(
    video_path: Path,
    event: dict[str, Any],
    search_window: list[int],
    context: dict[str, Any],
) -> dict[str, Any]:
    """Resolve one event from precomputed TrackNet rows when supplied."""
    del video_path
    track_rows = list(context.get("track_rows") or context.get("tracked_frames") or [])
    if track_rows:
        candidates = [
            row
            for row in track_rows
            if row.get("frame_index") not in (None, "") and int(row["frame_index"]) in set(int(frame) for frame in search_window)
        ]
        if candidates:
            manual_frame = int(event["contact_frame_estimate"])
            best = max(candidates, key=lambda row: (float(row.get("confidence") or 0.0), -abs(int(row["frame_index"]) - manual_frame)))
            return {
                "model_name": MODEL_NAME,
                "event_id": event["event_id"],
                "event_type": event["event_type"],
                "shot_type": event.get("shot_type", ""),
                "manual_frame": manual_frame,
                "search_start_frame": min(search_window) if search_window else "",
                "search_end_frame": max(search_window) if search_window else "",
                "resolved_frame": best.get("frame_index", ""),
                "image_x": best.get("ball_x", ""),
                "image_y": best.get("ball_y", ""),
                "raw_score": best.get("confidence", ""),
                "confidence": best.get("confidence", ""),
                "position_status": "resolved",
                "debug_reason": "Resolved from TrackNet temporal trajectory.",
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
        "debug_reason": context.get("reason") or "TrackNet adapter unavailable.",
    }
