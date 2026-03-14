"""Feature extraction from ActivityWatch events into MindScope windows."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from math import log2

from app.models.activity import ActivityWindowInput
from app.services.activitywatch_client import ActivityWatchClient


def _category_for_event(app_name: str, title: str) -> str:
    app = (app_name or "").lower()
    text = f"{app} {(title or '').lower()}"
    if any(token in text for token in ["zoom", "teams", "meet", "webex", "slack huddle"]):
        return "meeting"
    if any(token in text for token in ["outlook", "gmail", "mail"]):
        return "email"
    if any(token in text for token in ["slack", "discord", "teams", "chat"]):
        return "chat"
    if any(token in text for token in ["cursor", "code", "pycharm", "idea", "vim", "sublime"]):
        return "ide"
    if any(token in text for token in ["word", "docs", "notion", "onenote", "obsidian"]):
        return "docs"
    if any(token in text for token in ["excel", "sheet", "admin", "settings", "explorer"]):
        return "admin"
    if any(token in text for token in ["chrome", "brave", "firefox", "edge", "browser"]):
        return "browser"
    return "browser"


def _minutes_from_duration(duration_seconds: float) -> float:
    return max(duration_seconds, 0.0) / 60.0


class ActivityFeatureExtractor:
    """Convert ActivityWatch window/AFK events into scoring input features."""

    def __init__(
        self,
        client: ActivityWatchClient,
        window_bucket_prefix: str,
        afk_bucket_prefix: str,
    ) -> None:
        self.client = client
        self.window_bucket_prefix = window_bucket_prefix
        self.afk_bucket_prefix = afk_bucket_prefix

    def resolve_bucket_ids(self) -> tuple[str, str]:
        """Resolve the most recently updated watcher buckets."""

        buckets = self.client.get_buckets()
        window_candidates = [
            bucket for bucket in buckets.values() if bucket["id"].startswith(self.window_bucket_prefix)
        ]
        afk_candidates = [
            bucket for bucket in buckets.values() if bucket["id"].startswith(self.afk_bucket_prefix)
        ]
        if not window_candidates or not afk_candidates:
            raise ValueError("ActivityWatch buckets not found for window/afk watchers.")
        window_bucket = max(window_candidates, key=lambda item: item.get("last_updated", ""))
        afk_bucket = max(afk_candidates, key=lambda item: item.get("last_updated", ""))
        return window_bucket["id"], afk_bucket["id"]

    def build_window(
        self,
        *,
        user_id: str,
        timestamp_start: datetime,
        timestamp_end: datetime,
    ) -> ActivityWindowInput:
        """Construct a MindScope `ActivityWindowInput` from ActivityWatch events."""

        window_bucket_id, afk_bucket_id = self.resolve_bucket_ids()
        window_events = self.client.get_events(window_bucket_id, timestamp_start, timestamp_end)
        afk_events = self.client.get_events(afk_bucket_id, timestamp_start, timestamp_end)

        app_durations: dict[str, float] = defaultdict(float)
        category_minutes: dict[str, float] = defaultdict(float)
        app_switch_count = 0
        work_reentry_count = 0
        prev_app: str | None = None
        seen_apps: set[str] = set()
        focus_streak_minutes = 0.0
        current_streak_minutes = 0.0

        for event in window_events:
            data = event.get("data", {}) or {}
            app_name = str(data.get("app", "unknown"))
            title = str(data.get("title", ""))
            duration_minutes = _minutes_from_duration(float(event.get("duration", 0.0)))
            app_durations[app_name] += duration_minutes

            category = _category_for_event(app_name, title)
            category_minutes[category] += duration_minutes

            if prev_app is not None and prev_app != app_name:
                app_switch_count += 1
                if app_name in seen_apps:
                    work_reentry_count += 1
                current_streak_minutes = duration_minutes
            else:
                current_streak_minutes += duration_minutes

            if current_streak_minutes > focus_streak_minutes:
                focus_streak_minutes = current_streak_minutes
            seen_apps.add(app_name)
            prev_app = app_name

        afk_minutes = 0.0
        afk_count = 0
        for event in afk_events:
            data = event.get("data", {}) or {}
            status = str(data.get("status", "not-afk")).lower()
            if status == "afk":
                afk_count += 1
                afk_minutes += _minutes_from_duration(float(event.get("duration", 0.0)))

        total_active_minutes = sum(app_durations.values())
        entropy = 0.0
        if total_active_minutes > 0:
            for duration in app_durations.values():
                p = duration / total_active_minutes
                if p > 0:
                    entropy += -p * log2(p)

        top_category = "browser"
        if category_minutes:
            top_category = max(category_minutes, key=category_minutes.get)

        timestamp_start = timestamp_start.astimezone(UTC)
        return ActivityWindowInput(
            user_id=user_id,
            timestamp_start=timestamp_start,
            day_of_week=timestamp_start.weekday(),
            hour_of_day=timestamp_start.hour,
            is_workday=timestamp_start.weekday() < 5,
            scenario_label=None,
            active_minutes=round(min(total_active_minutes, 10.0), 3),
            afk_minutes=round(min(afk_minutes, 10.0), 3),
            afk_count=float(afk_count),
            app_switch_count=float(app_switch_count),
            distinct_app_count=float(len(app_durations)),
            top_app_category=top_category,
            email_minutes=round(category_minutes.get("email", 0.0), 3),
            chat_minutes=round(category_minutes.get("chat", 0.0), 3),
            browser_minutes=round(category_minutes.get("browser", 0.0), 3),
            docs_minutes=round(category_minutes.get("docs", 0.0), 3),
            ide_minutes=round(category_minutes.get("ide", 0.0), 3),
            meeting_minutes=round(category_minutes.get("meeting", 0.0), 3),
            admin_minutes=round(category_minutes.get("admin", 0.0), 3),
            focus_streak_minutes=round(min(focus_streak_minutes, 10.0), 3),
            work_context_entropy=round(entropy, 6),
            work_reentry_count=float(work_reentry_count),
        )
