"""FastAPI entrypoint for the MindScope backend."""

from __future__ import annotations

import asyncio
import contextlib
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes.analytics import router as analytics_router
from app.routes.alerts import router as alerts_router
from app.routes.baseline import router as baseline_router
from app.routes.health import router as health_router
from app.routes.scoring import router as scoring_router
from app.services.activity_feature_extractor import ActivityFeatureExtractor
from app.services.activitywatch_client import ActivityWatchClient
from app.services.alert_service import AlertService
from app.services.email_service import MockEmailService, SMTPEmailService
from app.services.live_ingestion_service import LiveIngestionService
from app.services.scoring_service import ScoringService
from app.services.state_store import JsonStateStore

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize lightweight singleton services for the MVP."""

    settings = get_settings()
    email_store = JsonStateStore(settings.email_log_path)
    alert_store = JsonStateStore(settings.alert_state_path)
    if settings.email_provider.lower() == "smtp" and settings.smtp_host:
        email_service = SMTPEmailService(
            default_recipient=settings.mock_alert_recipient,
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            smtp_username=settings.smtp_username,
            smtp_password=settings.smtp_password,
            smtp_use_tls=settings.smtp_use_tls,
            smtp_from_email=settings.smtp_from_email,
            store=email_store,
        )
    else:
        email_service = MockEmailService(
            default_recipient=settings.mock_alert_recipient,
            store=email_store,
        )
    scoring_service = ScoringService(
        baseline_csv_path=settings.baseline_csv_path,
        scenario_csv_path=settings.scenario_csv_path,
        synthetic_windows_csv_path=settings.synthetic_windows_csv_path,
    )
    scoring_service.refresh()
    app.state.settings = settings
    app.state.email_service = email_service
    app.state.scoring_service = scoring_service
    app.state.alert_service = AlertService.from_store(
        email_service=email_service,
        store=alert_store,
    )
    aw_client = ActivityWatchClient(base_url=settings.activitywatch_base_url)
    extractor = ActivityFeatureExtractor(
        client=aw_client,
        window_bucket_prefix=settings.activitywatch_window_bucket_prefix,
        afk_bucket_prefix=settings.activitywatch_afk_bucket_prefix,
    )
    app.state.live_ingestion_service = LiveIngestionService(
        extractor=extractor,
        scoring_service=scoring_service,
        alert_service=app.state.alert_service,
        history_store=JsonStateStore(settings.history_path),
        state_store=JsonStateStore(settings.ingestion_state_path),
        default_user_id=settings.default_user_id,
    )

    ingestion_task: asyncio.Task | None = None
    if settings.ingestion_enabled:
        live_service = app.state.live_ingestion_service

        async def _ingestion_loop() -> None:
            _last_err: str = ""
            _err_count: int = 0
            while True:
                try:
                    live_service.run_once()
                    if _err_count:
                        logger.info("Live ingestion recovered after %d failures.", _err_count)
                        _last_err = ""
                        _err_count = 0
                except Exception as exc:  # noqa: BLE001
                    msg = f"{type(exc).__name__}: {exc}"
                    if msg != _last_err:
                        logger.warning("Live ingestion pass failed: %s", msg, exc_info=True)
                        _last_err = msg
                        _err_count = 1
                    else:
                        _err_count += 1
                        if _err_count % 60 == 0:
                            logger.warning(
                                "Live ingestion still failing (%d times): %s", _err_count, msg
                            )
                await asyncio.sleep(max(settings.ingestion_poll_interval_seconds, 5))

        ingestion_task = asyncio.create_task(_ingestion_loop())
    yield
    if ingestion_task:
        ingestion_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await ingestion_task


app = FastAPI(
    title="MindScope API",
    description=(
        "Hackathon MVP for estimating overload risk from ActivityWatch-style "
        "desktop activity telemetry."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(baseline_router)
app.include_router(scoring_router)
app.include_router(alerts_router)
app.include_router(analytics_router)
