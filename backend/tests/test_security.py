import pytest
from fastapi.testclient import TestClient
from app.main import app

AUTH = {"Authorization": "Bearer test-token-" + "x" * 40}


@pytest.mark.parametrize("method,path", [
    ("GET", "/health"), ("GET", "/api/v1/baseline/summary"),
    ("GET", "/api/v1/alerts/emails"), ("GET", "/api/v1/analytics/dashboard"),
    ("POST", "/api/v1/chat/prioritize"), ("POST", "/api/v1/alerts/fire-demo/test-user"),
])
def test_unauthenticated_requests_fail(method, path):
    with TestClient(app) as client:
        assert client.request(method, path).status_code == 401


@pytest.mark.parametrize("method,path,body", [
    ("GET", "/api/v1/analytics/dashboard?user_id=another-user", None),
    ("GET", "/api/v1/scoring/synthetic-demo?user_id=another-user", None),
    ("GET", "/api/v1/alerts/state/another-user", None),
    ("POST", "/api/v1/alerts/fire-demo/another-user", None),
    ("POST", "/api/v1/scoring", {"user_id": "another-user"}),
    ("POST", "/api/v1/chat/prioritize", {"user_id": "another-user", "tasks": "test"}),
])
def test_cross_user_requests_fail(method, path, body):
    with TestClient(app, headers=AUTH) as client:
        assert client.request(method, path, json=body).status_code == 403


def test_owner_chat_and_alert_flow():
    with TestClient(app, headers=AUTH) as client:
        assert client.post("/api/v1/chat/prioritize", json={"tasks": "write report"}).status_code == 200
        assert client.post("/api/v1/alerts/fire-demo/test-user").status_code == 200


def test_missing_configuration_fails_closed(monkeypatch):
    monkeypatch.delenv("MINDSCOPE_API_TOKEN")
    with TestClient(app, headers=AUTH) as client:
        assert client.get("/health").status_code == 503


def test_bad_origin_and_oversized_body():
    with TestClient(app, headers=AUTH) as client:
        assert client.get("/health", headers={"Origin": "https://evil.example"}).status_code == 403
        assert client.post("/api/v1/chat/prioritize", content=b"x" * 32769).status_code == 413
        assert client.post("/api/v1/chat/prioritize", json={"tasks": "x" * 8001}).status_code == 422
        assert client.post("/api/v1/chat/schedule", json={"tasks": [{}] * 21}).status_code == 422


def test_costly_endpoints_are_rate_limited():
    with TestClient(app, headers=AUTH) as client:
        for _ in range(10):
            assert client.post("/api/v1/chat/prioritize", json={"tasks": "test"}).status_code == 200
        assert client.post("/api/v1/chat/prioritize", json={"tasks": "test"}).status_code == 429
