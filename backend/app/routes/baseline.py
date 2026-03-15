"""Baseline profile analytics endpoint."""

from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/v1/baseline", tags=["baseline"])

METRIC_META = {
    "app_switch_count": {
        "label": "App Switches",
        "unit": "/ 10 min",
        "overload_direction": "high",
        "description": "Switching between applications frequently signals fragmented attention.",
    },
    "distinct_app_count": {
        "label": "Distinct Apps Open",
        "unit": "apps",
        "overload_direction": "high",
        "description": "More apps open in parallel correlates with multitasking overload.",
    },
    "focus_streak_minutes": {
        "label": "Focus Streak",
        "unit": "min",
        "overload_direction": "low",
        "description": "Longer unbroken focus streaks indicate healthy deep-work capacity.",
    },
    "afk_count": {
        "label": "AFK Events",
        "unit": "events",
        "overload_direction": "high",
        "description": "Frequent away-from-keyboard breaks suggest interruption overload.",
    },
    "afk_minutes": {
        "label": "AFK Time",
        "unit": "min",
        "overload_direction": "high",
        "description": "Time spent away from the keyboard in each 10-minute window.",
    },
    "work_context_entropy": {
        "label": "Context Entropy",
        "unit": "bits",
        "overload_direction": "high",
        "description": "High entropy means attention is spread thinly across many contexts.",
    },
    "work_reentry_count": {
        "label": "Work Re-entries",
        "unit": "/ 10 min",
        "overload_direction": "high",
        "description": "Returning to a task after switching away — a fragmentation signal.",
    },
}


@router.get("/summary")
def baseline_summary(request: Request) -> dict:
    """Return aggregated baseline stats and hourly profile for dashboard rendering."""

    scoring_service = request.app.state.scoring_service
    rows = scoring_service.baseline_rows

    if not rows:
        return {"row_count": 0, "metrics": [], "hourly": []}

    # Aggregate overall means across all rows
    feature_totals: dict[str, list[float]] = defaultdict(list)
    std_totals: dict[str, list[float]] = defaultdict(list)
    hourly_buckets: dict[int, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    for row in rows:
        for feature, stats in row.features.items():
            feature_totals[feature].append(stats.mean)
            std_totals[feature].append(stats.std)
            hourly_buckets[row.hour_of_day][feature].append(stats.mean)

    metrics = []
    for feature, meta in METRIC_META.items():
        if feature not in feature_totals:
            continue
        means = feature_totals[feature]
        stds = std_totals[feature]
        metrics.append(
            {
                "key": feature,
                "label": meta["label"],
                "unit": meta["unit"],
                "overload_direction": meta["overload_direction"],
                "description": meta["description"],
                "mean": round(sum(means) / len(means), 3),
                "std": round(sum(stds) / len(stds), 3),
            }
        )

    # Hourly profile sorted by hour
    hourly = []
    for hour in sorted(hourly_buckets.keys()):
        bucket = hourly_buckets[hour]
        entry: dict = {"hour": hour}
        for feature in METRIC_META:
            if feature in bucket:
                vals = bucket[feature]
                entry[feature] = round(sum(vals) / len(vals), 3)
        hourly.append(entry)

    return {
        "row_count": len(rows),
        "metrics": metrics,
        "hourly": hourly,
    }
