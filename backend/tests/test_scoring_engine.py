"""High-level tests for the overload-risk scoring engine."""

from __future__ import annotations

from datetime import datetime, timezone

from app.models.activity import ActivityWindowInput
from app.models.baseline import BaselineRow, FeatureBaselineStats
from app.models.scenario import ScenarioCentroid
from app.scoring.engine import compute_overload_score, should_trigger_alert


def build_baseline() -> BaselineRow:
    return BaselineRow(
        user_id="demo-user",
        day_of_week=1,
        hour_of_day=9,
        features={
            "app_switch_count": FeatureBaselineStats(mean=8, std=2),
            "distinct_app_count": FeatureBaselineStats(mean=4, std=1),
            "focus_streak_minutes": FeatureBaselineStats(mean=27, std=6),
            "afk_count": FeatureBaselineStats(mean=1, std=1),
            "afk_minutes": FeatureBaselineStats(mean=6, std=2),
            "work_context_entropy": FeatureBaselineStats(mean=1.8, std=0.4),
            "work_reentry_count": FeatureBaselineStats(mean=2, std=1),
        },
    )


def build_window() -> ActivityWindowInput:
    return ActivityWindowInput(
        user_id="demo-user",
        timestamp_start=datetime(2026, 3, 10, 9, 30, tzinfo=timezone.utc),
        day_of_week=1,
        hour_of_day=9,
        is_workday=True,
        app_switch_count=16,
        distinct_app_count=7,
        focus_streak_minutes=10,
        afk_count=3,
        afk_minutes=9,
        work_context_entropy=2.9,
        work_reentry_count=5,
    )


def test_compute_overload_score_returns_explainable_payload() -> None:
    result = compute_overload_score(
        window=build_window(),
        baseline=build_baseline(),
        scenario_centroids=[
            ScenarioCentroid(
                scenario_label="normal_work",
                features={feature: 0.0 for feature in build_baseline().features},
            ),
            ScenarioCentroid(
                scenario_label="overload",
                features={
                    "app_switch_count": 2.0,
                    "distinct_app_count": 1.5,
                    "focus_streak_minutes": 2.0,
                    "afk_count": 1.2,
                    "afk_minutes": 1.2,
                    "work_context_entropy": 2.2,
                    "work_reentry_count": 1.6,
                },
            ),
        ],
    )

    assert 0 <= result.overload_score <= 100
    assert result.nearest_scenario == "overload"
    assert result.state_band in {
        "Normal",
        "Elevated",
        "High",
        "Sustained Overload Risk",
    }
    assert result.top_drivers


def test_should_trigger_alert_respects_persistence_rules() -> None:
    assert should_trigger_alert([72.0, 74.0, 76.0]) == (True, "high_3x")
    assert should_trigger_alert([86.0, 90.0]) == (True, "critical_2x")
    assert should_trigger_alert([60.0, 72.0, 68.0]) == (False, None)
