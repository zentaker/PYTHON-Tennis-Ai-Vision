"""Multi-dimensional friction helpers for product and model validation."""

from __future__ import annotations

from typing import Any

from tennis_vision.friction import friction_band


def build_friction_breakdown(
    *,
    execution_score: int,
    execution_reason: str,
    semantic_model_score: int,
    semantic_model_reason: str,
    human_loop_score: int,
    human_loop_reason: str,
    product_validation_status: str,
    product_validation_reason: str,
    downstream_correction_score: int,
    downstream_correction_reason: str,
) -> dict[str, Any]:
    """Build a multi-dimensional friction breakdown for stage reports."""
    return {
        "execution": friction_dimension(execution_score, execution_reason),
        "semantic_model": friction_dimension(semantic_model_score, semantic_model_reason),
        "human_loop": friction_dimension(human_loop_score, human_loop_reason),
        "product_validation": {
            "status": classify_product_validation_status(product_validation_status),
            "reason": product_validation_reason,
        },
        "downstream_correction": friction_dimension(downstream_correction_score, downstream_correction_reason),
    }


def summarize_friction_breakdown(breakdown: dict[str, Any]) -> str:
    """Summarize a multi-dimensional friction breakdown in one readable sentence."""
    execution = breakdown.get("execution", {})
    semantic = breakdown.get("semantic_model", {})
    human = breakdown.get("human_loop", {})
    product = breakdown.get("product_validation", {})
    downstream = breakdown.get("downstream_correction", {})
    return (
        f"execution={execution.get('band', 'unknown')}; "
        f"semantic_model={semantic.get('band', 'unknown')}; "
        f"human_loop={human.get('band', 'unknown')}; "
        f"product_validation={product.get('status', 'unknown')}; "
        f"downstream_correction={downstream.get('band', 'unknown')}"
    )


def classify_product_validation_status(status: str) -> str:
    """Normalize product validation status text."""
    normalized = str(status or "").strip().lower()
    allowed = {
        "not_required",
        "pending_review",
        "passed",
        "passed_with_warnings",
        "failed",
        "failed_previous_candidate",
        "blocked",
    }
    return normalized if normalized in allowed else "pending_review"


def classify_human_loop_level(*, manual_labels_required: bool, manual_review_required: bool, new_manual_stage_required: bool = False) -> dict[str, Any]:
    """Classify human-loop friction from manual intervention requirements."""
    score = 0
    reasons: list[str] = []
    if manual_labels_required:
        score += 25
        reasons.append("manual labels required")
    if manual_review_required:
        score += 25
        reasons.append("manual review required")
    if new_manual_stage_required:
        score += 20
        reasons.append("new manual or validation stage required")
    if not reasons:
        reasons.append("no manual review required")
    return friction_dimension(score, "; ".join(reasons))


def friction_dimension(score: int, reason: str) -> dict[str, Any]:
    """Return one normalized friction dimension."""
    safe_score = max(0, min(int(score), 100))
    return {
        "score": safe_score,
        "band": friction_band(safe_score),
        "reason": reason,
    }
