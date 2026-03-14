"""Core overload-risk scoring engine."""

from __future__ import annotations

from math import sqrt
from typing import Sequence

from app.models.activity import ActivityWindowInput
from app.models.baseline import BaselineRow
from app.models.scenario import ScenarioCentroid
from app.models.scoring import ScoringOutput

CORE_FEATURES = [
    "app_switch_count",
    "distinct_app_count",
    "focus_streak_minutes",
    "afk_count",
    "afk_minutes",
    "work_context_entropy",
    "work_reentry_count",
]
LOWER_IS_WORSE = {"focus_streak_minutes"}
SCENARIO_ADJUSTMENTS = {
    "overload": 8.0,
    "admin_fragmented": 3.0,
    "meeting_heavy": 0.0,
    "normal_work": 0.0,
    "deep_work": -10.0,
    "procrastination": -5.0,
}
FEATURE_LABELS = {
    "app_switch_count": "App switching",
    "distinct_app_count": "Distinct apps",
    "focus_streak_minutes": "Focus streak",
    "afk_count": "AFK count",
    "afk_minutes": "AFK time",
    "work_context_entropy": "Work context entropy",
    "work_reentry_count": "Work re-entry count",
}


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp a numeric value to a closed interval."""

    return max(minimum, min(value, maximum))


def capped_positive_z(
    current: float,
    mean: float,
    std: float,
    lower_is_worse: bool = False,
) -> float:
    """Return a one-sided capped z-score in the overload direction."""

    safe_std = std if std > 0 else 1.0
    raw = (mean - current) / safe_std if lower_is_worse else (current - mean) / safe_std
    return clamp(raw, 0.0, 3.0)


def compute_fragmentation_score(
    switch_z: float,
    distinct_z: float,
    entropy_z: float,
) -> float:
    """Compute fragmentation risk from app switching and context dispersion."""

    fragmentation_raw = (0.45 * switch_z) + (0.25 * distinct_z) + (0.30 * entropy_z)
    return clamp((fragmentation_raw / 3.0) * 100.0, 0.0, 100.0)


def compute_focus_instability_score(
    focus_drop_z: float,
    reentry_z: float,
) -> float:
    """Compute focus instability from shorter streaks and more re-entry events."""

    focus_raw = (0.65 * focus_drop_z) + (0.35 * reentry_z)
    return clamp((focus_raw / 3.0) * 100.0, 0.0, 100.0)


def compute_interruption_score(
    afk_count_z: float,
    afk_minutes_z: float,
) -> float:
    """Compute interruption load from AFK events and minutes."""

    interrupt_raw = (0.60 * afk_count_z) + (0.40 * afk_minutes_z)
    return clamp((interrupt_raw / 3.0) * 100.0, 0.0, 100.0)


def _signed_overload_z(
    current: float,
    mean: float,
    std: float,
    lower_is_worse: bool = False,
) -> float:
    """Return a signed z-score where positive values mean more overload-like."""

    safe_std = std if std > 0 else 1.0
    raw = (mean - current) / safe_std if lower_is_worse else (current - mean) / safe_std
    return clamp(raw, -3.0, 3.0)


def find_nearest_scenario(
    normalized_vector: dict[str, float],
    scenario_centroids: Sequence[ScenarioCentroid],
) -> str:
    """Return the label of the nearest scenario centroid."""

    if not scenario_centroids:
        return "normal_work"

    nearest_label = scenario_centroids[0].scenario_label
    nearest_distance = float("inf")
    for centroid in scenario_centroids:
        distance_squared = 0.0
        for feature in CORE_FEATURES:
            current_value = normalized_vector.get(feature, 0.0)
            centroid_value = centroid.features.get(feature, 0.0)
            distance_squared += (current_value - centroid_value) ** 2
        distance = sqrt(distance_squared)
        if distance < nearest_distance:
            nearest_distance = distance
            nearest_label = centroid.scenario_label
    return nearest_label


def _state_band(score: float) -> str:
    """Convert the final overload score into a band label."""

    if score <= 39:
        return "Normal"
    if score <= 59:
        return "Elevated"
    if score <= 74:
        return "High"
    return "Sustained Overload Risk"


def _driver_text(
    feature: str,
    current: float,
    mean: float,
    overload_z: float,
) -> str:
    """Create a readable explanation for an overload driver."""

    label = FEATURE_LABELS[feature]
    lower_is_worse = feature in LOWER_IS_WORSE
    if abs(mean) > 1e-6:
        if lower_is_worse:
            percent = abs(((mean - current) / mean) * 100.0)
            return f"{label} is {percent:.0f}% below baseline"
        percent = abs(((current - mean) / mean) * 100.0)
        return f"{label} is {percent:.0f}% above baseline"

    direction = "below expected" if lower_is_worse else "above expected"
    return f"{label} is {overload_z:.1f} standard deviations {direction}"


def should_trigger_alert(recent_scores: Sequence[float]) -> tuple[bool, str | None]:
    """Evaluate the persistence rule using a recent score history."""

    if len(recent_scores) >= 2 and all(score > 85.0 for score in recent_scores[-2:]):
        return True, "critical_2x"
    if len(recent_scores) >= 3 and all(score > 70.0 for score in recent_scores[-3:]):
        return True, "high_3x"
    return False, None


def compute_overload_score(
    window: ActivityWindowInput,
    baseline: BaselineRow,
    scenario_centroids: Sequence[ScenarioCentroid],
) -> ScoringOutput:
    """Compute the explainable overload-risk score for one activity window."""

    positive_z_scores: dict[str, float] = {}
    signed_z_scores: dict[str, float] = {}
    for feature in CORE_FEATURES:
        stats = baseline.features[feature]
        current_value = getattr(window, feature)
        lower_is_worse = feature in LOWER_IS_WORSE
        positive_z_scores[feature] = capped_positive_z(
            current=current_value,
            mean=stats.mean,
            std=stats.std,
            lower_is_worse=lower_is_worse,
        )
        signed_z_scores[feature] = _signed_overload_z(
            current=current_value,
            mean=stats.mean,
            std=stats.std,
            lower_is_worse=lower_is_worse,
        )

    fragmentation_score = compute_fragmentation_score(
        switch_z=positive_z_scores["app_switch_count"],
        distinct_z=positive_z_scores["distinct_app_count"],
        entropy_z=positive_z_scores["work_context_entropy"],
    )
    focus_instability_score = compute_focus_instability_score(
        focus_drop_z=positive_z_scores["focus_streak_minutes"],
        reentry_z=positive_z_scores["work_reentry_count"],
    )
    interruption_score = compute_interruption_score(
        afk_count_z=positive_z_scores["afk_count"],
        afk_minutes_z=positive_z_scores["afk_minutes"],
    )

    raw_score = (
        (0.45 * fragmentation_score)
        + (0.35 * focus_instability_score)
        + (0.20 * interruption_score)
    )
    nearest_scenario = find_nearest_scenario(signed_z_scores, scenario_centroids)
    adjusted_score = clamp(
        raw_score + SCENARIO_ADJUSTMENTS.get(nearest_scenario, 0.0),
        0.0,
        100.0,
    )

    ranked_features = sorted(
        CORE_FEATURES,
        key=lambda feature_name: positive_z_scores[feature_name],
        reverse=True,
    )
    top_drivers = [
        _driver_text(
            feature=feature_name,
            current=getattr(window, feature_name),
            mean=baseline.features[feature_name].mean,
            overload_z=positive_z_scores[feature_name],
        )
        for feature_name in ranked_features
        if positive_z_scores[feature_name] > 0
    ][:3]
    if not top_drivers:
        top_drivers = ["Current behavior is close to the expected baseline."]

    return ScoringOutput(
        overload_score=round(adjusted_score, 2),
        state_band=_state_band(adjusted_score),
        fragmentation_score=round(fragmentation_score, 2),
        focus_instability_score=round(focus_instability_score, 2),
        interruption_score=round(interruption_score, 2),
        nearest_scenario=nearest_scenario,
        top_drivers=top_drivers,
    )
