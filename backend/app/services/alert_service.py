"""Simple in-memory alert persistence service."""

from __future__ import annotations

from app.models.alert import AlertState
from app.scoring.engine import should_trigger_alert
from app.services.email_service import MockEmailService
from app.services.state_store import JsonStateStore


class AlertService:
    """Track recent overload scores and trigger mock alerts when persistence rules match."""

    def __init__(self, email_service: MockEmailService, history_limit: int = 12) -> None:
        self.email_service = email_service
        self.history_limit = history_limit
        self.store: JsonStateStore | None = None
        self._states: dict[str, AlertState] = {}

    @classmethod
    def from_store(
        cls,
        email_service: MockEmailService,
        store: JsonStateStore | None,
        history_limit: int = 12,
    ) -> "AlertService":
        """Build service and hydrate persisted state if available."""

        service = cls(email_service=email_service, history_limit=history_limit)
        service.store = store
        service._states = service._load_states()
        return service

    def _load_states(self) -> dict[str, AlertState]:
        """Load alert states from persistence."""

        if self.store is None:
            return {}
        raw = self.store.load(default={})
        hydrated: dict[str, AlertState] = {}
        for user_id, payload in raw.items():
            try:
                hydrated[user_id] = AlertState.model_validate(payload)
            except Exception:
                continue
        return hydrated

    def _persist(self) -> None:
        """Persist all current alert states."""

        if self.store is None:
            return
        self.store.save(
            {
                user_id: state.model_dump(mode="json")
                for user_id, state in self._states.items()
            }
        )

    def get_state(self, user_id: str) -> AlertState:
        """Return a tracked state or a fresh default one."""

        return self._states.get(user_id, AlertState(user_id=user_id))

    def evaluate_score(self, user_id: str, overload_score: float) -> AlertState:
        """Append a score, evaluate persistence rules, and send a mock alert if needed."""

        state = self.get_state(user_id).model_copy(deep=True)
        state.recent_scores.append(round(overload_score, 2))
        state.recent_scores = state.recent_scores[-self.history_limit :]
        state.consecutive_high_windows = self._count_consecutive(
            state.recent_scores,
            threshold=70.0,
        )
        state.consecutive_critical_windows = self._count_consecutive(
            state.recent_scores,
            threshold=85.0,
        )

        should_alert, rule = should_trigger_alert(state.recent_scores)
        state.should_alert = should_alert
        state.triggered_rule = rule

        if should_alert and not state.alert_active:
            message = self.email_service.send_alert(
                user_id=user_id,
                overload_score=overload_score,
                rule=rule or "unknown_rule",
            )
            state.alert_active = True
            state.last_email_at = message.sent_at
            state.last_notified_score = round(overload_score, 2)
        elif not should_alert:
            state.alert_active = False

        self._states[user_id] = state
        self._persist()
        return state

    @staticmethod
    def _count_consecutive(scores: list[float], threshold: float) -> int:
        """Count consecutive scores above a threshold from most recent backwards."""

        count = 0
        for score in reversed(scores):
            if score > threshold:
                count += 1
            else:
                break
        return count
