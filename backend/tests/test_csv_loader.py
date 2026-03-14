"""CSV loader compatibility tests."""

from __future__ import annotations

from pathlib import Path

from app.utils.csv_loader import load_baseline_rows, load_scenario_centroids


def test_baseline_loader_supports_alias_columns(tmp_path: Path) -> None:
    csv_path = tmp_path / "baseline.csv"
    csv_path.write_text(
        "\n".join(
            [
                "user_id,day_of_week,hour_of_day,switch_rate_mean,switch_rate_std,distinct_app_mean,distinct_app_std,focus_streak_mean,focus_streak_std,afk_count_mean,afk_count_std,afk_minutes_mean,afk_minutes_std,entropy_mean,entropy_std,work_reentry_count_mean,work_reentry_count_std",
                "global,1,9,8,2,4,1,27,6,1,1,6,2,1.8,0.4,2,1",
            ]
        ),
        encoding="utf-8",
    )

    rows = load_baseline_rows(csv_path)
    assert len(rows) == 1
    assert rows[0].features["app_switch_count"].mean == 8
    assert rows[0].features["work_context_entropy"].mean == 1.8


def test_scenario_loader_supports_normalized_suffix(tmp_path: Path) -> None:
    csv_path = tmp_path / "scenarios.csv"
    csv_path.write_text(
        "\n".join(
            [
                "scenario_label,app_switch_count_z,distinct_app_count_z,focus_streak_minutes_z,afk_count_z,afk_minutes_z,work_context_entropy_z,work_reentry_count_z",
                "normal_work,0,0,0,0,0,0,0",
            ]
        ),
        encoding="utf-8",
    )

    rows = load_scenario_centroids(csv_path)
    assert len(rows) == 1
    assert rows[0].scenario_label == "normal_work"
    assert rows[0].features["app_switch_count"] == 0.0
