"""Alert endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.models.alert import AlertEvaluationRequest, AlertState, MockEmailMessage

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.post("/evaluate", response_model=AlertState)
def evaluate_alert(request_body: AlertEvaluationRequest, request: Request) -> AlertState:
    """Evaluate one overload score against alert persistence rules."""

    alert_service = request.app.state.alert_service
    return alert_service.evaluate_score(
        user_id=request_body.user_id,
        overload_score=request_body.overload_score,
    )


@router.get("/state/{user_id}", response_model=AlertState)
def get_alert_state(user_id: str, request: Request) -> AlertState:
    """Return the current alert persistence state for a user."""

    alert_service = request.app.state.alert_service
    return alert_service.get_state(user_id)


@router.get("/emails", response_model=list[MockEmailMessage])
def list_mock_emails(request: Request) -> list[MockEmailMessage]:
    """Inspect mock email messages sent by the MVP."""

    email_service = request.app.state.email_service
    return email_service.list_messages()


@router.post("/test-trigger/{user_id}", response_model=AlertState)
def test_trigger_alert(user_id: str, request: Request) -> AlertState:
    """Force-trigger alert rules for end-to-end email path verification."""

    alert_service = request.app.state.alert_service
    # Two critical windows guarantees trigger via 85x2 rule.
    alert_service.evaluate_score(user_id=user_id, overload_score=86.0)
    state = alert_service.evaluate_score(user_id=user_id, overload_score=88.0)
    return state


@router.post("/reset/{user_id}")
def reset_alert_state(user_id: str, request: Request) -> dict:
    """Reset alert state for a user — use between demo runs."""

    alert_service = request.app.state.alert_service
    from app.models.alert import AlertState as _AlertState
    alert_service._states[user_id] = _AlertState(user_id=user_id)
    alert_service._persist()
    return {"status": "reset", "user_id": user_id}


@router.post("/fire-demo/{user_id}", response_model=AlertState)
def fire_demo_alert(user_id: str, request: Request) -> AlertState:
    """Reset state then immediately fire a real alert email — one-click demo trigger."""

    alert_service = request.app.state.alert_service
    from app.models.alert import AlertState as _AlertState

    # Hard-reset first so the email always fires even if alert_active is already True
    alert_service._states[user_id] = _AlertState(user_id=user_id)
    alert_service._persist()

    # Two consecutive critical-range scores guarantees the persistence rule fires
    alert_service.evaluate_score(user_id=user_id, overload_score=87.0)
    state = alert_service.evaluate_score(user_id=user_id, overload_score=91.0)
    return state
