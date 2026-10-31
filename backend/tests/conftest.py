"""Keep API tests authenticated, offline and isolated from personal runtime data."""
import pytest


@pytest.fixture(autouse=True)
def isolated_configuration(monkeypatch, tmp_path):
    monkeypatch.setenv("MINDSCOPE_API_TOKEN", "test-token-" + "x" * 40)
    monkeypatch.setenv("MINDSCOPE_USER_ID", "test-user")
    monkeypatch.setenv("MINDSCOPE_EMAIL_PROVIDER", "mock")
    monkeypatch.setenv("MINDSCOPE_INGESTION_ENABLED", "false")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    for name in ("ALERT_STATE", "EMAIL_LOG", "HISTORY", "INGESTION_STATE"):
        monkeypatch.setenv(f"MINDSCOPE_{name}_JSON", str(tmp_path / f"{name}.json"))
    from app.main import app
    app.middleware_stack = None
