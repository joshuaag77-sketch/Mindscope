"""API-level smoke tests for MindScope endpoints."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.models.activity import ActivityWindowInput


def test_health_endpoint_returns_loaded_counts() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ok"
        assert payload["baseline_rows_loaded"] > 0
        assert payload["scenario_centroids_loaded"] > 0


def test_scoring_and_alert_flow() -> None:
    with TestClient(app) as client:
        body = ActivityWindowInput(
            user_id="test-user",
            timestamp_start=datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc),
            day_of_week=1,
            hour_of_day=9,
            app_switch_count=18,
            distinct_app_count=8,
            focus_streak_minutes=8,
            afk_count=3,
            afk_minutes=8,
            work_context_entropy=2.9,
            work_reentry_count=6,
        ).model_dump(mode="json")

        response = client.post("/api/v1/scoring?track_alert=true", json=body)
        assert response.status_code == 200
        payload = response.json()
        assert "result" in payload
        assert payload["result"]["overload_score"] >= 0
        assert payload["alert_state"]["user_id"] == "test-user"


def test_synthetic_demo_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/scoring/synthetic-demo?limit=5")
        assert response.status_code == 200
        payload = response.json()
        assert "trend_scores" in payload
        assert len(payload["trend_scores"]) <= 5
