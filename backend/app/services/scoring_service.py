"""Service wrapper around CSV-backed scoring assets."""

from __future__ import annotations

from pathlib import Path

from app.models.activity import ActivityWindowInput
from app.models.baseline import BaselineRow
from app.models.scenario import ScenarioCentroid
from app.models.scoring import ScoringOutput
from app.scoring.engine import compute_overload_score
from app.utils.csv_loader import (
    load_activity_windows,
    load_baseline_rows,
    load_scenario_centroids,
)


class ScoredSyntheticWindow:
    """Scored synthetic window container used for demo trend endpoints."""

    def __init__(
        self,
        timestamp_start: str,
        scenario_label: str | None,
        overload_score: float,
    ) -> None:
        self.timestamp_start = timestamp_start
        self.scenario_label = scenario_label
        self.overload_score = overload_score


class ScoringService:
    """Load contextual scoring assets from CSV files and score activity windows."""

    def __init__(
        self,
        baseline_csv_path: Path,
        scenario_csv_path: Path,
        synthetic_windows_csv_path: Path | None = None,
    ) -> None:
        self.baseline_csv_path = baseline_csv_path
        self.scenario_csv_path = scenario_csv_path
        self.synthetic_windows_csv_path = synthetic_windows_csv_path
        self.baseline_rows: list[BaselineRow] = []
        self.scenario_centroids: list[ScenarioCentroid] = []
        self.synthetic_windows: list[ActivityWindowInput] = []

    def refresh(self) -> None:
        """Reload baseline and scenario data from disk."""

        self.baseline_rows = load_baseline_rows(self.baseline_csv_path)
        self.scenario_centroids = load_scenario_centroids(self.scenario_csv_path)
        if self.synthetic_windows_csv_path and self.synthetic_windows_csv_path.exists():
            self.synthetic_windows = load_activity_windows(self.synthetic_windows_csv_path)
        else:
            self.synthetic_windows = []

    def score_window(self, window: ActivityWindowInput) -> ScoringOutput:
        """Resolve a baseline row and compute the overload-risk score."""

        baseline_row = self.get_baseline_for_window(window)
        return compute_overload_score(
            window=window,
            baseline=baseline_row,
            scenario_centroids=self.scenario_centroids,
        )

    def get_baseline_for_window(self, window: ActivityWindowInput) -> BaselineRow:
        """Find the best contextual baseline match with graceful fallbacks."""

        if not self.baseline_rows:
            raise ValueError("No baseline rows are loaded.")

        def matches(row: BaselineRow, *, user_id: str | None, day_of_week: int, hour: int) -> bool:
            row_user = (row.user_id or "global").lower()
            expected_user = (user_id or "global").lower()
            return (
                row_user == expected_user
                and row.day_of_week == day_of_week
                and row.hour_of_day == hour
            )

        candidates = [
            next(
                (
                    row
                    for row in self.baseline_rows
                    if matches(
                        row,
                        user_id=window.user_id,
                        day_of_week=window.day_of_week,
                        hour=window.hour_of_day,
                    )
                ),
                None,
            ),
            next(
                (
                    row
                    for row in self.baseline_rows
                    if matches(
                        row,
                        user_id=None,
                        day_of_week=window.day_of_week,
                        hour=window.hour_of_day,
                    )
                ),
                None,
            ),
            next(
                (
                    row
                    for row in self.baseline_rows
                    if matches(
                        row,
                        user_id=window.user_id,
                        day_of_week=-1,
                        hour=window.hour_of_day,
                    )
                ),
                None,
            ),
            next(
                (
                    row
                    for row in self.baseline_rows
                    if matches(
                        row,
                        user_id=None,
                        day_of_week=-1,
                        hour=window.hour_of_day,
                    )
                ),
                None,
            ),
            next(
                (
                    row
                    for row in self.baseline_rows
                    if row.hour_of_day == window.hour_of_day
                ),
                None,
            ),
        ]
        for candidate in candidates:
            if candidate is not None:
                return candidate

        # Final fallback: nearest available hour for this user/global row.
        same_user_or_global = [
            row
            for row in self.baseline_rows
            if (row.user_id or "global").lower() in {(window.user_id or "global").lower(), "global"}
        ]
        if same_user_or_global:
            return min(
                same_user_or_global,
                key=lambda row: abs(row.hour_of_day - window.hour_of_day),
            )

        raise ValueError(
            "No baseline row found for the supplied day/hour context. "
            "Add a matching row to the baseline CSV."
        )

    def score_synthetic_windows(
        self,
        limit: int = 24,
        user_id: str | None = None,
    ) -> list[ScoredSyntheticWindow]:
        """Score synthetic windows and return a lightweight trend series."""

        if not self.synthetic_windows:
            return []
        filtered = self.synthetic_windows
        if user_id:
            filtered = [window for window in filtered if window.user_id == user_id]
        if limit > 0:
            filtered = filtered[-limit:]

        scored: list[ScoredSyntheticWindow] = []
        for window in filtered:
            result = self.score_window(window)
            scored.append(
                ScoredSyntheticWindow(
                    timestamp_start=window.timestamp_start.isoformat(),
                    scenario_label=window.scenario_label,
                    overload_score=result.overload_score,
                )
            )
        return scored
