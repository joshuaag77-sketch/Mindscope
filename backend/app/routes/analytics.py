"""Live analytics and ingestion endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.post("/ingest/run-once")
def ingest_run_once(
    request: Request,
    user_id: str | None = Query(default=None),
) -> dict:
    """Trigger one live ingestion pass immediately."""

    live_service = request.app.state.live_ingestion_service
    try:
        record = live_service.run_once(user_id=user_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"Live ingestion failed: {exc}") from exc
    if record is None:
        return {"status": "no_new_window"}
    return {"status": "ok", "record": record}


@router.get("/dashboard")
def analytics_dashboard(
    request: Request,
    user_id: str | None = Query(default=None),
    limit: int = Query(default=72, ge=1, le=720),
    ingest_if_needed: bool = Query(default=True),
) -> dict:
    """Return current + history + summary analytics for dashboard rendering."""

    live_service = request.app.state.live_ingestion_service
    if ingest_if_needed:
        try:
            live_service.run_once(user_id=user_id)
        except Exception:
            # Dashboard can still render from persisted history.
            pass

    history = live_service.get_history(user_id=user_id, limit=limit)
    current = history[-1] if history else live_service.get_current(user_id=user_id)
    if current is None:
        raise HTTPException(
            status_code=404,
            detail="No live analytics available yet. Ensure ActivityWatch is running.",
        )
    return {
        "source": "activitywatch_live",
        "current": current,
        "history": history,
        "summary": live_service.get_summary(user_id=user_id, limit=limit),
    }
