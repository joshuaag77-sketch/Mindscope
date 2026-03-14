"""CSV loading helpers for baseline, scenario, and synthetic activity data."""

from __future__ import annotations

import csv
from pathlib import Path

from app.models.activity import ActivityWindowInput
from app.models.baseline import BaselineRow, FeatureBaselineStats
from app.models.scenario import ScenarioCentroid
from app.scoring.engine import CORE_FEATURES

DAY_NAME_TO_INDEX = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
    "global": -1,
    "any": -1,
}


def _first_present(row: dict[str, str], candidates: list[str], default: str = "") -> str:
    """Return the first non-empty value found across candidate columns."""

    for column in candidates:
        value = row.get(column)
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    return default


def _parse_float(value: str, default: float = 0.0) -> float:
    """Parse a float-like CSV cell."""

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_int(value: str, default: int = 0) -> int:
    """Parse an int-like CSV cell."""

    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _parse_bool(value: str, default: bool = False) -> bool:
    """Parse common truthy string representations."""

    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _parse_day_of_week(value: str) -> int:
    """Parse day-of-week values from ints or weekday names."""

    if value is None or str(value).strip() == "":
        return -1
    normalized = str(value).strip().lower()
    if normalized in DAY_NAME_TO_INDEX:
        return DAY_NAME_TO_INDEX[normalized]
    return _parse_int(normalized, default=-1)


def load_baseline_rows(path: Path) -> list[BaselineRow]:
    """Load baseline rows with flexible mean/std column naming."""

    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    rows: list[BaselineRow] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for record in reader:
            features: dict[str, FeatureBaselineStats] = {}
            for feature in CORE_FEATURES:
                aliases = BASELINE_ALIAS_COLUMNS.get(feature, [])
                mean_candidates = [f"{feature}_mean", f"mean_{feature}", f"{feature}:mean"]
                std_candidates = [f"{feature}_std", f"std_{feature}", f"{feature}:std"]
                for alias in aliases:
                    mean_candidates.extend(
                        [f"{alias}_mean", f"mean_{alias}", f"{alias}:mean"]
                    )
                    std_candidates.extend([f"{alias}_std", f"std_{alias}", f"{alias}:std"])
                mean = _parse_float(
                    _first_present(
                        record,
                        mean_candidates,
                    )
                )
                std = _parse_float(
                    _first_present(
                        record,
                        std_candidates,
                        default="1.0",
                    ),
                    default=1.0,
                )
                features[feature] = FeatureBaselineStats(mean=mean, std=max(std, 1e-6))

            rows.append(
                BaselineRow(
                    user_id=_first_present(
                        record,
                        ["user_id", "employee_id"],
                        default="global",
                    )
                    or "global",
                    day_of_week=_parse_day_of_week(
                        _first_present(
                            record,
                            ["day_of_week", "weekday"],
                            default="global",
                        )
                    ),
                    hour_of_day=_parse_int(
                        _first_present(record, ["hour_of_day", "hour"], default="0")
                    ),
                    features=features,
                )
            )
    return rows


def load_scenario_centroids(path: Path) -> list[ScenarioCentroid]:
    """Load scenario centroids from a CSV file."""

    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    centroids: list[ScenarioCentroid] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for record in reader:
            features = {
                feature: _parse_float(
                    _first_present(
                        record,
                        [feature, f"{feature}_z", f"{feature}_normalized"],
                    )
                )
                for feature in CORE_FEATURES
            }
            centroids.append(
                ScenarioCentroid(
                    scenario_label=_first_present(
                        record,
                        ["scenario_label", "scenario", "label"],
                        default="normal_work",
                    ),
                    features=features,
                )
            )
    return centroids


def load_activity_windows(path: Path) -> list[ActivityWindowInput]:
    """Load synthetic activity windows from CSV for demos or testing."""

    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    windows: list[ActivityWindowInput] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for record in reader:
            payload = {
                "user_id": _first_present(record, ["user_id"], default="demo-user"),
                "timestamp_start": _first_present(
                    record,
                    ["timestamp_start", "window_start"],
                    default="2026-03-10T09:00:00Z",
                ),
                "day_of_week": _parse_day_of_week(
                    _first_present(record, ["day_of_week", "weekday"], default="0")
                ),
                "hour_of_day": _parse_int(
                    _first_present(record, ["hour_of_day", "hour"], default="9")
                ),
                "is_workday": _parse_bool(
                    _first_present(record, ["is_workday"], default="true"),
                    default=True,
                ),
                "scenario_label": _first_present(record, ["scenario_label"], default=""),
                "active_minutes": _parse_float(
                    _first_present(record, ["active_minutes"], default="0")
                ),
                "afk_minutes": _parse_float(
                    _first_present(record, ["afk_minutes"], default="0")
                ),
                "afk_count": _parse_float(
                    _first_present(record, ["afk_count"], default="0")
                ),
                "app_switch_count": _parse_float(
                    _first_present(record, ["app_switch_count"], default="0")
                ),
                "distinct_app_count": _parse_float(
                    _first_present(record, ["distinct_app_count"], default="0")
                ),
                "top_app_category": _first_present(record, ["top_app_category"], default=""),
                "email_minutes": _parse_float(
                    _first_present(record, ["email_minutes"], default="0")
                ),
                "chat_minutes": _parse_float(
                    _first_present(record, ["chat_minutes"], default="0")
                ),
                "browser_minutes": _parse_float(
                    _first_present(record, ["browser_minutes"], default="0")
                ),
                "docs_minutes": _parse_float(
                    _first_present(record, ["docs_minutes"], default="0")
                ),
                "ide_minutes": _parse_float(
                    _first_present(record, ["ide_minutes"], default="0")
                ),
                "meeting_minutes": _parse_float(
                    _first_present(record, ["meeting_minutes"], default="0")
                ),
                "admin_minutes": _parse_float(
                    _first_present(record, ["admin_minutes"], default="0")
                ),
                "focus_streak_minutes": _parse_float(
                    _first_present(record, ["focus_streak_minutes"], default="0")
                ),
                "work_context_entropy": _parse_float(
                    _first_present(record, ["work_context_entropy"], default="0")
                ),
                "work_reentry_count": _parse_float(
                    _first_present(record, ["work_reentry_count"], default="0")
                ),
            }
            windows.append(ActivityWindowInput(**payload))
    return windows
BASELINE_ALIAS_COLUMNS = {
    "app_switch_count": ["switch_rate"],
    "distinct_app_count": ["distinct_app"],
    "focus_streak_minutes": ["focus_streak"],
    "work_context_entropy": ["entropy"],
}
