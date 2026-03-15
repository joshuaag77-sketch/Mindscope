"""Live ingestion service: ActivityWatch -> features -> score -> alert -> history."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.models.scoring import ScoringOutput
from app.services.activity_feature_extractor import ActivityFeatureExtractor
from app.services.alert_service import AlertService
from app.services.scoring_service import ScoringService
from app.services.state_store import JsonStateStore


def _floor_to_10s(dt: datetime) -> datetime:
    """Floor to the nearest 10-second boundary for near-real-time demo updates."""
    return dt.replace(second=(dt.second // 10) * 10, microsecond=0)


class LiveIngestionService:
    """Orchestrates live ActivityWatch ingestion and persistent scored history."""

    def __init__(
        self,
        *,
        extractor: ActivityFeatureExtractor,
        scoring_service: ScoringService,
        alert_service: AlertService,
        history_store: JsonStateStore,
        state_store: JsonStateStore,
        default_user_id: str,
        history_limit: int = 1000,
    ) -> None:
        self.extractor = extractor
        self.scoring_service = scoring_service
        self.alert_service = alert_service
        self.history_store = history_store
        self.state_store = state_store
        self.default_user_id = default_user_id
        self.history_limit = history_limit

    def _load_history(self) -> list[dict]:
        raw = self.history_store.load(default=[])
        if isinstance(raw, list):
            return raw
        return []

    def _save_history(self, history: list[dict]) -> None:
        self.history_store.save(history[-self.history_limit :])

    def run_once(self, user_id: str | None = None, now: datetime | None = None) -> dict | None:
        """Ingest and score the latest complete 10-minute window once."""

        effective_user = user_id or self.default_user_id
        utc_now = now or datetime.now(UTC)
        # Rolling 10-minute window ending at current minute for near real-time updates.
        end = _floor_to_10s(utc_now)
        start = end - timedelta(minutes=10)

        state = self.state_store.load(default={})
        last_end = str(state.get("last_processed_end", ""))
        end_iso = end.isoformat()
        if last_end == end_iso:
            history = self._load_history()
            if history:
                return history[-1]
            return None

        window = self.extractor.build_window(
            user_id=effective_user,
            timestamp_start=start,
            timestamp_end=end,
        )
        scoring = self.scoring_service.score_window(window)
        alert_state = self.alert_service.evaluate_score(
            user_id=effective_user,
            overload_score=scoring.overload_score,
        )

        record = self._build_record(window=window, scoring=scoring, alert_state=alert_state.model_dump(mode="json"))
        history = self._load_history()
        history.append(record)
        self._save_history(history)
        self.state_store.save({"last_processed_end": end_iso})
        return record

    @staticmethod
    def _build_record(window, scoring: ScoringOutput, alert_state: dict) -> dict:
        return {
            "timestamp_start": window.timestamp_start.isoformat(),
            "user_id": window.user_id,
            "overload_score": scoring.overload_score,
            "state_band": scoring.state_band,
            "fragmentation_score": scoring.fragmentation_score,
            "focus_instability_score": scoring.focus_instability_score,
            "interruption_score": scoring.interruption_score,
            "nearest_scenario": scoring.nearest_scenario,
            "top_drivers": scoring.top_drivers,
            "app_switch_count": window.app_switch_count,
            "distinct_app_count": window.distinct_app_count,
            "focus_streak_minutes": window.focus_streak_minutes,
            "afk_count": window.afk_count,
            "afk_minutes": window.afk_minutes,
            "work_context_entropy": window.work_context_entropy,
            "work_reentry_count": window.work_reentry_count,
            "alert_state": alert_state,
            "source": "activitywatch_live",
        }

    def get_history(self, user_id: str | None = None, limit: int = 72) -> list[dict]:
        """Get recent scored history records."""

        history = self._load_history()
        if user_id:
            history = [row for row in history if row.get("user_id") == user_id]
        return history[-limit:]

    def get_current(self, user_id: str | None = None) -> dict | None:
        """Return latest scored record."""

        history = self.get_history(user_id=user_id, limit=1)
        if history:
            return history[-1]
        return None

    def get_summary(self, user_id: str | None = None, limit: int = 72) -> dict:
        """Compute lightweight dashboard KPIs from history."""

        history = self.get_history(user_id=user_id, limit=limit)
        if not history:
            return {
                "windows_tracked": 0,
                "avg_score": 0.0,
                "max_score": 0.0,
                "high_risk_windows": 0,
                "latest_band": "Normal",
            }
        scores = [float(item.get("overload_score", 0.0)) for item in history]
        high_risk = [score for score in scores if score >= 60.0]
        return {
            "windows_tracked": len(scores),
            "avg_score": round(sum(scores) / len(scores), 2),
            "max_score": round(max(scores), 2),
            "high_risk_windows": len(high_risk),
            "latest_band": str(history[-1].get("state_band", "Normal")),
        }
