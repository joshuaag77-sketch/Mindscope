"""Scoring endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from app.models.activity import ActivityWindowInput
from app.models.scoring import ScoringEnvelope

router = APIRouter(prefix="/api/v1/scoring", tags=["scoring"])


@router.post("", response_model=ScoringEnvelope)
def score_window(
    window: ActivityWindowInput,
    request: Request,
    track_alert: bool = Query(
        default=False,
        description="If true, update alert persistence state for this user.",
    ),
) -> ScoringEnvelope:
    """Compute a contextual overload-risk score for one activity window."""

    scoring_service = request.app.state.scoring_service
    alert_service = request.app.state.alert_service
    try:
        result = scoring_service.score_window(window)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    alert_state = None
    if track_alert:
        alert_state = alert_service.evaluate_score(
            user_id=window.user_id,
            overload_score=result.overload_score,
        )

    return ScoringEnvelope(result=result, alert_state=alert_state)


@router.get("/synthetic-demo")
def synthetic_demo(
    request: Request,
    limit: int = Query(default=24, ge=1, le=240),
    user_id: str | None = Query(default=None),
) -> dict[str, object]:
    """Return a scored synthetic trend for frontend dashboard bootstrapping."""

    scoring_service = request.app.state.scoring_service
    scored = scoring_service.score_synthetic_windows(limit=limit, user_id=user_id)
    if not scored:
        return {"trend_scores": [], "windows": [], "latest": None}

    latest = scored[-1]
    return {
        "trend_scores": [window.overload_score for window in scored],
        "windows": [
            {
                "timestamp_start": window.timestamp_start,
                "scenario_label": window.scenario_label,
                "overload_score": window.overload_score,
            }
            for window in scored
        ],
        "latest": {
            "timestamp_start": latest.timestamp_start,
            "scenario_label": latest.scenario_label,
            "overload_score": latest.overload_score,
        },
    }


@router.get("/synthetic-current", response_model=ScoringEnvelope)
def synthetic_current(
    request: Request,
    user_id: str | None = Query(default=None),
    track_alert: bool = Query(default=False),
) -> ScoringEnvelope:
    """Score the latest synthetic window for quick frontend bootstrapping."""

    scoring_service = request.app.state.scoring_service
    alert_service = request.app.state.alert_service
    windows = scoring_service.synthetic_windows
    if user_id:
        windows = [window for window in windows if window.user_id == user_id]
    if not windows:
        raise HTTPException(status_code=404, detail="No synthetic windows available.")

    latest_window = windows[-1]
    result = scoring_service.score_window(latest_window)

    alert_state = None
    if track_alert:
        alert_state = alert_service.evaluate_score(
            user_id=latest_window.user_id,
            overload_score=result.overload_score,
        )
    return ScoringEnvelope(result=result, alert_state=alert_state)
