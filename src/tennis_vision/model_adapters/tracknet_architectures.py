"""TrackNet architecture integration interface.

This file intentionally does not implement a guessed TrackNet architecture.
Concrete TrackNet/TrackNetV2/TrackNetV3/TrackNetV4 classes should be added here
or imported here once a compatible local implementation and weights are chosen.
"""

from __future__ import annotations

from typing import Any


class TrackNetArchitectureUnavailable(Exception):
    """Raised when a concrete TrackNet architecture is not available."""


class TrackNetInferenceModel:
    """Base interface for concrete TrackNet inference wrappers."""

    is_placeholder = True

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise TrackNetArchitectureUnavailable(
            "No concrete TrackNet architecture is installed. Add a TrackNetInferenceModel "
            "subclass or variant-specific class that matches the local weights."
        )

    def preprocess_clip(self, frames: list[Any]) -> Any:
        """Convert raw frames into the model's temporal input tensor."""
        raise TrackNetArchitectureUnavailable("TrackNet clip preprocessing is not implemented.")

    def forward(self, model_input: Any) -> Any:
        """Run model inference."""
        raise TrackNetArchitectureUnavailable("TrackNet forward pass is not implemented.")

    def decode_output(self, output: Any) -> list[dict[str, Any]]:
        """Decode heatmaps or coordinates into per-frame ball positions."""
        raise TrackNetArchitectureUnavailable("TrackNet output decoding is not implemented.")
