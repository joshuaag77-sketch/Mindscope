"""Application configuration for the MindScope backend."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Simple settings container for local MVP configuration."""

    app_name: str
    api_prefix: str
    baseline_csv_path: Path
    scenario_csv_path: Path
    synthetic_windows_csv_path: Path
    mock_alert_recipient: str
    alert_state_path: Path
    email_log_path: Path
    history_path: Path
    ingestion_state_path: Path
    default_user_id: str
    activitywatch_base_url: str
    activitywatch_window_bucket_prefix: str
    activitywatch_afk_bucket_prefix: str
    ingestion_enabled: bool
    ingestion_poll_interval_seconds: int
    email_provider: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_use_tls: bool
    smtp_from_email: str


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def get_settings() -> Settings:
    """Build settings from environment variables with sensible local defaults."""

    backend_root = Path(__file__).resolve().parents[1]
    data_dir = backend_root / "data"
    runtime_dir = data_dir / "runtime"
    default_user = os.getenv("MINDSCOPE_USER_ID") or os.getenv("USERNAME") or "local-user"
    return Settings(
        app_name="MindScope API",
        api_prefix="/api/v1",
        baseline_csv_path=Path(
            os.getenv("MINDSCOPE_BASELINE_CSV", data_dir / "baseline_profile.csv")
        ),
        scenario_csv_path=Path(
            os.getenv("MINDSCOPE_SCENARIO_CSV", data_dir / "scenario_centroids.csv")
        ),
        synthetic_windows_csv_path=Path(
            os.getenv("MINDSCOPE_WINDOWS_CSV", data_dir / "synthetic_windows.csv")
        ),
        mock_alert_recipient=os.getenv(
            "MINDSCOPE_ALERT_EMAIL", "joshuaag7719@gmail.com"
        ),
        alert_state_path=Path(
            os.getenv("MINDSCOPE_ALERT_STATE_JSON", runtime_dir / "alert_state.json")
        ),
        email_log_path=Path(
            os.getenv("MINDSCOPE_EMAIL_LOG_JSON", runtime_dir / "mock_email_log.json")
        ),
        history_path=Path(
            os.getenv("MINDSCOPE_HISTORY_JSON", runtime_dir / "scored_history.json")
        ),
        ingestion_state_path=Path(
            os.getenv("MINDSCOPE_INGESTION_STATE_JSON", runtime_dir / "ingestion_state.json")
        ),
        default_user_id=default_user,
        activitywatch_base_url=os.getenv(
            "MINDSCOPE_ACTIVITYWATCH_BASE_URL",
            "http://127.0.0.1:5600/api/0",
        ),
        activitywatch_window_bucket_prefix=os.getenv(
            "MINDSCOPE_AW_WINDOW_BUCKET_PREFIX",
            "aw-watcher-window_",
        ),
        activitywatch_afk_bucket_prefix=os.getenv(
            "MINDSCOPE_AW_AFK_BUCKET_PREFIX",
            "aw-watcher-afk_",
        ),
        ingestion_enabled=_env_bool("MINDSCOPE_INGESTION_ENABLED", True),
        ingestion_poll_interval_seconds=int(
            os.getenv("MINDSCOPE_INGESTION_POLL_SECONDS", "10")
        ),
        email_provider=os.getenv("MINDSCOPE_EMAIL_PROVIDER", "mock"),
        smtp_host=os.getenv("MINDSCOPE_SMTP_HOST", ""),
        smtp_port=int(os.getenv("MINDSCOPE_SMTP_PORT", "587")),
        smtp_username=os.getenv("MINDSCOPE_SMTP_USERNAME", ""),
        smtp_password=os.getenv("MINDSCOPE_SMTP_PASSWORD", ""),
        smtp_use_tls=_env_bool("MINDSCOPE_SMTP_USE_TLS", True),
        smtp_from_email=os.getenv("MINDSCOPE_SMTP_FROM", "mindscope@localhost"),
    )
