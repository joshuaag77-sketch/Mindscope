"""Alerting-related models."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AlertState(BaseModel):
    """In-memory alert persistence state for a single user."""

    user_id: str
    recent_scores: list[float] = Field(default_factory=list)
    consecutive_high_windows: int = 0
    consecutive_critical_windows: int = 0
    should_alert: bool = False
    triggered_rule: Optional[str] = None
    alert_active: bool = False
    last_email_at: Optional[datetime] = None
    last_notified_score: Optional[float] = None


class AlertEvaluationRequest(BaseModel):
    """Payload for evaluating alert persistence from an overload score."""

    user_id: str
    overload_score: float = Field(..., ge=0.0, le=100.0)


class MockEmailMessage(BaseModel):
    """Simple mock email envelope for hackathon-safe alert previews."""

    recipient: str
    subject: str
    body: str
    sent_at: datetime
