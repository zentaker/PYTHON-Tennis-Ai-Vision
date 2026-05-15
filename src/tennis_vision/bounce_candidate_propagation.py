"""Stage 8.4 bounce candidate propagation helpers."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from tennis_vision.bounce_pattern_features import extract_features_around_bounce_window


def build_manual_bounce_windows(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Read manual bounce windows from Stage 8.3."""
    if not path.exists():
        return [], [f"Manual bounce windows missing: {path}"]
    rows: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if str(row.get("event_label") or "").lower() != "bounce":
                continue
            rows.append(
                {
                    "window_id": row.get("window_id") or f"bounce_window_{len(rows) + 1:03d}",
                    "event_label": "bounce",
                    "start_frame": int(float(row.get("start_frame") or 0)),
                    "end_frame": int(float(row.get("end_frame") or 0)),
                    "center_frame": int(float(row.get("center_frame") or 0)),
                    "label_count": int(float(row.get("label_count") or 1)),
                    "confidence": row.get("confidence") or "medium",
                    "source_frames": row.get("source_frames") or "",
                    "notes": row.get("notes") or "",
                }
            )
    return rows, []


def learn_bounce_window_signature(features: list[dict[str, Any]], windows: list[dict[str, Any]]) -> dict[str, Any]:
    """Extract a local motion signature from manually labeled bounce windows."""
    local_rows: list[dict[str, Any]] = []
    for window in windows:
        local_rows.extend(extract_features_around_bounce_window(features, window, radius=1))
    if not local_rows:
        return {
            "available": False,
            "pattern_confidence": "missing",
            "mean_proxy_score": 0.0,
            "mean_speed": 0.0,
            "notes": "No bounce-window features were available.",
        }
    proxy_values = [float(row.get("height_proxy_score") or 0.0) for row in local_rows]
    speed_values = [float(row.get("local_speed") or 0.0) for row in local_rows if row.get("local_speed") is not None]
    return {
        "available": True,
        "pattern_confidence": "weak" if len(windows) == 1 else "medium",
        "mean_proxy_score": round(sum(proxy_values) / max(len(proxy_values), 1), 3),
        "mean_speed": round(sum(speed_values) / max(len(speed_values), 1), 3),
        "manual_window_count": len(windows),
        "feature_rows": len(local_rows),
        "notes": "Only one manual bounce window exists; treat proposals as active-review candidates." if len(windows) == 1 else "Multiple bounce windows are available.",
    }


def build_manual_hit_windows(labels: list[dict[str, Any]], *, hit_window_gap: int = 3, padding: int = 2) -> list[dict[str, Any]]:
    """Group manual hit labels into conservative hit exclusion windows."""
    hit_labels = sorted((row for row in labels if row.get("event_label") == "hit"), key=lambda row: int(row["frame_index"]))
    windows: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    for label in hit_labels:
        if not current:
            current = [label]
            continue
        if int(label["frame_index"]) - int(current[-1]["frame_index"]) <= hit_window_gap:
            current.append(label)
        else:
            windows.append(build_label_window(current, "hit", len(windows) + 1, padding=padding))
            current = [label]
    if current:
        windows.append(build_label_window(current, "hit", len(windows) + 1, padding=padding))
    return windows


def build_no_event_exclusion_zones(labels: list[dict[str, Any]], *, no_event_gap: int = 1) -> list[dict[str, Any]]:
    """Group explicit no_event labels into exclusion zones."""
    no_event_labels = sorted((row for row in labels if row.get("event_label") == "no_event"), key=lambda row: int(row["frame_index"]))
    zones: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    for label in no_event_labels:
        if not current:
            current = [label]
            continue
        if int(label["frame_index"]) - int(current[-1]["frame_index"]) <= no_event_gap:
            current.append(label)
        else:
            zones.append(build_label_window(current, "no_event", len(zones) + 1, padding=0))
            current = [label]
    if current:
        zones.append(build_label_window(current, "no_event", len(zones) + 1, padding=0))
    return zones


def build_label_window(labels: list[dict[str, Any]], label: str, index: int, *, padding: int = 0) -> dict[str, Any]:
    """Build one manual label window."""
    frames = [int(row["frame_index"]) for row in labels]
    return {
        "window_id": f"{label}_window_{index:03d}",
        "event_label": label,
        "start_frame": min(frames) - padding,
        "end_frame": max(frames) + padding,
        "center_frame": int(round(sum(frames) / len(frames))),
        "label_count": len(labels),
        "confidence": "high" if any(str(row.get("confidence")) == "high" for row in labels) else "medium",
        "source_frames": ",".join(str(frame) for frame in frames),
        "notes": f"Manual {label} labels grouped as an event-sequence constraint.",
    }


def score_bounce_candidates(features: list[dict[str, Any]], signature: dict[str, Any], windows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Score trajectory points as inferred bounce candidates."""
    scored: list[dict[str, Any]] = []
    if not signature.get("available"):
        return scored
    for row in features:
        frame = int(row["frame_index"])
        nearest_distance = nearest_existing_bounce_distance(frame, windows)
        already_validated = frame_in_windows(frame, windows)
        if already_validated:
            continue
        score = 0.0
        reasons: list[str] = []
        if row.get("image_y_direction_change"):
            score += 0.35
            reasons.append("image y direction changed")
        if row.get("projected_y_direction_change"):
            score += 0.35
            reasons.append("projected court depth direction changed")
        proxy = float(row.get("height_proxy_score") or 0.0)
        score += min(proxy, 0.2)
        if proxy > 0:
            reasons.append(f"height proxy score {proxy:.2f}")
        if nearest_distance is not None and nearest_distance >= 20:
            score += 0.1
            reasons.append("far enough from existing manual bounce window")
        if nearest_distance is not None and nearest_distance < 8:
            score *= 0.5
            reasons.append("near existing bounce window")
        score = round(min(score, 1.0), 3)
        if score <= 0:
            continue
        scored.append(
            {
                "frame_index": frame,
                "score": score,
                "confidence_like_score": round(score, 3),
                "projected_x": row.get("projected_x"),
                "projected_y": row.get("projected_y"),
                "x": row.get("x"),
                "y": row.get("y"),
                "feature_summary": "; ".join(reasons) if reasons else "weak proxy feature match",
                "nearest_existing_bounce_distance": nearest_distance,
                "already_validated": "yes" if already_validated else "no",
                "supporting_features": json.dumps(
                    {
                        "image_y_direction_change": row.get("image_y_direction_change"),
                        "projected_y_direction_change": row.get("projected_y_direction_change"),
                        "height_proxy_score": row.get("height_proxy_score"),
                        "local_speed": row.get("local_speed"),
                        "local_acceleration_proxy": row.get("local_acceleration_proxy"),
                    },
                    sort_keys=True,
                ),
            }
        )
    return scored


def propose_bounce_candidates(
    features: list[dict[str, Any]],
    windows: list[dict[str, Any]],
    *,
    hit_windows: list[dict[str, Any]] | None = None,
    no_event_zones: list[dict[str, Any]] | None = None,
    uncertain_labels: list[dict[str, Any]] | None = None,
    min_score: float,
    candidate_window_gap: int,
    max_candidates: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Score the rest of the trajectory for likely bounce candidates."""
    signature = learn_bounce_window_signature(features, windows)
    scored = score_bounce_candidates(features, signature, windows)
    constrained, constraint_summary = apply_event_sequence_constraints(
        scored,
        bounce_windows=windows,
        hit_windows=hit_windows or [],
        no_event_zones=no_event_zones or [],
        uncertain_labels=uncertain_labels or [],
        features=features,
    )
    ranked = rank_bounce_candidates(constrained)
    filtered = [row for row in ranked if float(row["score"]) >= min_score]
    candidate_windows = merge_nearby_bounce_candidates(filtered, candidate_window_gap=candidate_window_gap)
    candidate_windows = candidate_windows[:max_candidates]
    allowed_ids = {row["candidate_id"] for row in candidate_windows}
    candidate_frames = [row for row in filtered if row.get("candidate_id") in allowed_ids]
    return candidate_windows, candidate_frames, constraint_summary


def apply_event_sequence_constraints(
    rows: list[dict[str, Any]],
    *,
    bounce_windows: list[dict[str, Any]],
    hit_windows: list[dict[str, Any]],
    no_event_zones: list[dict[str, Any]],
    uncertain_labels: list[dict[str, Any]],
    features: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Apply hit/no-event exclusions and post-hit next-bounce search rules."""
    search_context = search_next_bounce_after_hit(bounce_windows, hit_windows, features)
    summary: dict[str, Any] = {
        "post_hit_search_enabled": search_context["enabled"],
        "post_hit_search_frame": search_context.get("search_after_frame"),
        "post_hit_points_count": search_context.get("post_hit_points_count", 0),
        "insufficient_post_hit_trajectory": False,
        "candidates_excluded_by_hit_labels": 0,
        "candidates_excluded_by_no_event_labels": 0,
        "candidates_penalized_by_uncertain_labels": 0,
        "excluded_candidate_frames": [],
    }
    accepted: list[dict[str, Any]] = []
    for row in rows:
        frame = int(row["frame_index"])
        updated = {
            **row,
            "sequence_context": "post_hit_search" if search_context["enabled"] else "bounce_similarity_search",
            "nearest_manual_hit_frame": nearest_window_center(frame, hit_windows),
            "distance_from_hit": nearest_window_distance(frame, hit_windows),
            "excluded_by_hit_window": "no",
            "excluded_by_no_event": "no",
            "event_sequence_status": "candidate_considered",
            "rejection_reason": "",
        }
        if search_context["enabled"] and frame <= int(search_context["search_after_frame"]):
            hit_related = frame_in_windows(frame, hit_windows) or (nearest_window_distance(frame, hit_windows) is not None and int(nearest_window_distance(frame, hit_windows) or 99) <= 3)
            updated["excluded_by_hit_window"] = "yes" if hit_related else "no"
            updated["event_sequence_status"] = "rejected_before_next_bounce_search_window"
            updated["rejection_reason"] = "Candidate occurs inside or before the manual hit window."
            if hit_related:
                summary["candidates_excluded_by_hit_labels"] += 1
            summary["excluded_candidate_frames"].append(frame)
            continue
        if frame_in_windows(frame, hit_windows) or (nearest_window_distance(frame, hit_windows) is not None and int(nearest_window_distance(frame, hit_windows) or 99) <= 3):
            updated["excluded_by_hit_window"] = "yes"
            updated["event_sequence_status"] = "rejected_near_manual_hit"
            updated["rejection_reason"] = "Candidate is inside or too near a manual hit label."
            summary["candidates_excluded_by_hit_labels"] += 1
            summary["excluded_candidate_frames"].append(frame)
            continue
        if frame_in_windows(frame, no_event_zones):
            updated["excluded_by_no_event"] = "yes"
            updated["event_sequence_status"] = "rejected_manual_no_event"
            updated["rejection_reason"] = "Candidate frame is explicitly labeled no_event."
            summary["candidates_excluded_by_no_event_labels"] += 1
            summary["excluded_candidate_frames"].append(frame)
            continue
        if nearest_label_distance(frame, uncertain_labels) is not None and int(nearest_label_distance(frame, uncertain_labels) or 99) <= 3:
            updated["score"] = round(float(updated["score"]) * 0.75, 3)
            updated["confidence_like_score"] = updated["score"]
            updated["feature_summary"] = f"{updated['feature_summary']}; confidence reduced near uncertain manual label"
            updated["event_sequence_status"] = "penalized_near_uncertain"
            summary["candidates_penalized_by_uncertain_labels"] += 1
        if search_context["enabled"]:
            updated["event_sequence_status"] = "post_hit_candidate"
        accepted.append(updated)
    if search_context["enabled"] and not accepted and int(search_context.get("post_hit_points_count") or 0) < 5:
        summary["insufficient_post_hit_trajectory"] = True
    return accepted, summary


def search_next_bounce_after_hit(bounce_windows: list[dict[str, Any]], hit_windows: list[dict[str, Any]], features: list[dict[str, Any]]) -> dict[str, Any]:
    """Find the first manual hit after a manual bounce and define the next-bounce search window."""
    if not bounce_windows or not hit_windows:
        return {"enabled": False, "reason": "manual bounce and hit sequence unavailable", "post_hit_points_count": 0}
    latest_bounce = max(bounce_windows, key=lambda row: int(row["center_frame"]))
    hits_after_bounce = [row for row in hit_windows if int(row["center_frame"]) > int(latest_bounce["center_frame"])]
    if not hits_after_bounce:
        return {"enabled": False, "reason": "no manual hit after manual bounce", "post_hit_points_count": 0}
    first_hit = min(hits_after_bounce, key=lambda row: int(row["center_frame"]))
    search_after_frame = int(first_hit["end_frame"])
    post_hit_points = [row for row in features if int(row["frame_index"]) > search_after_frame]
    return {
        "enabled": True,
        "manual_hit_frame": int(first_hit["center_frame"]),
        "search_after_frame": search_after_frame,
        "post_hit_points_count": len(post_hit_points),
        "reason": "manual hit after bounce found; searching for next bounce after hit window",
    }


def suppress_existing_bounce_windows(rows: list[dict[str, Any]], windows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove candidate rows that overlap existing manual bounce windows."""
    return [row for row in rows if not frame_in_windows(int(row["frame_index"]), windows)]


def rank_bounce_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank candidate frames by score descending."""
    return sorted(rows, key=lambda row: (float(row.get("score") or 0.0), int(row.get("frame_index") or 0)), reverse=True)


def merge_nearby_bounce_candidates(rows: list[dict[str, Any]], *, candidate_window_gap: int) -> list[dict[str, Any]]:
    """Merge nearby candidate frames into candidate windows."""
    ordered = sorted(rows, key=lambda row: int(row["frame_index"]))
    windows: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for row in ordered:
        if not current:
            current = [row]
            continue
        if int(row["frame_index"]) - int(current[-1]["frame_index"]) <= candidate_window_gap:
            current.append(row)
        else:
            windows.append(current)
            current = [row]
    if current:
        windows.append(current)
    result: list[dict[str, Any]] = []
    for index, group in enumerate(windows, start=1):
        best = max(group, key=lambda row: float(row["score"]))
        candidate_id = f"bounce_candidate_{index:03d}"
        for row in group:
            row["candidate_id"] = candidate_id
            row["recommendation"] = "manual_review"
        result.append(
            {
                "candidate_id": candidate_id,
                "start_frame": min(int(row["frame_index"]) for row in group),
                "end_frame": max(int(row["frame_index"]) for row in group),
                "center_frame": int(best["frame_index"]),
                "score": best["score"],
                "confidence_like_score": best["confidence_like_score"],
                "reason": best["feature_summary"],
                "supporting_features": best["supporting_features"],
                "already_validated": "no",
                "sequence_context": best.get("sequence_context", ""),
                "nearest_manual_hit_frame": best.get("nearest_manual_hit_frame", ""),
                "distance_from_hit": best.get("distance_from_hit", ""),
                "excluded_by_hit_window": best.get("excluded_by_hit_window", "no"),
                "excluded_by_no_event": best.get("excluded_by_no_event", "no"),
                "event_sequence_status": best.get("event_sequence_status", ""),
                "rejection_reason": best.get("rejection_reason", ""),
                "recommendation": "review_with_stage_8_2",
            }
        )
    return rank_bounce_candidates(result)


def nearest_existing_bounce_distance(frame: int, windows: list[dict[str, Any]]) -> int | None:
    """Return distance from frame to nearest existing bounce window."""
    if not windows:
        return None
    distances = []
    for window in windows:
        start = int(window["start_frame"])
        end = int(window["end_frame"])
        center = int(window["center_frame"])
        if start <= frame <= end:
            distances.append(0)
        else:
            distances.append(min(abs(frame - start), abs(frame - end), abs(frame - center)))
    return min(distances)


def frame_in_windows(frame: int, windows: list[dict[str, Any]]) -> bool:
    """Return true if frame is inside an existing manual bounce window."""
    return any(int(window["start_frame"]) <= frame <= int(window["end_frame"]) for window in windows)


def nearest_window_center(frame: int, windows: list[dict[str, Any]]) -> int | str:
    """Return nearest manual event window center frame."""
    if not windows:
        return ""
    nearest = min(windows, key=lambda window: abs(frame - int(window["center_frame"])))
    return int(nearest["center_frame"])


def nearest_window_distance(frame: int, windows: list[dict[str, Any]]) -> int | None:
    """Return distance to nearest manual event window."""
    if not windows:
        return None
    distances = []
    for window in windows:
        start = int(window["start_frame"])
        end = int(window["end_frame"])
        if start <= frame <= end:
            distances.append(0)
        else:
            distances.append(min(abs(frame - start), abs(frame - end), abs(frame - int(window["center_frame"]))))
    return min(distances)


def nearest_label_distance(frame: int, labels: list[dict[str, Any]]) -> int | None:
    """Return distance to nearest manual label row."""
    if not labels:
        return None
    return min(abs(frame - int(label["frame_index"])) for label in labels)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> Path:
    """Write CSV rows with stable fields."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    return path
