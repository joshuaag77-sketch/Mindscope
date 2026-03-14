"""Health and metadata endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(request: Request) -> dict[str, object]:
    """Report API availability and whether CSV-backed assets are loaded."""

    scoring_service = request.app.state.scoring_service
    return {
        "status": "ok",
        "service": request.app.state.settings.app_name,
        "baseline_rows_loaded": len(scoring_service.baseline_rows),
        "scenario_centroids_loaded": len(scoring_service.scenario_centroids),
        "synthetic_windows_loaded": len(scoring_service.synthetic_windows),
        "live_ingestion_enabled": bool(request.app.state.settings.ingestion_enabled),
        "activitywatch_base_url": request.app.state.settings.activitywatch_base_url,
        "email_provider": request.app.state.settings.email_provider,
        "alert_recipient": request.app.state.settings.mock_alert_recipient,
    }
