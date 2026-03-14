"""Scoring output models."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.models.alert import AlertState


class ScoringOutput(BaseModel):
    """Explainable overload-risk scoring response."""

    overload_score: float = Field(..., ge=0.0, le=100.0)
    state_band: str
    fragmentation_score: float = Field(..., ge=0.0, le=100.0)
    focus_instability_score: float = Field(..., ge=0.0, le=100.0)
    interruption_score: float = Field(..., ge=0.0, le=100.0)
    nearest_scenario: str
    top_drivers: list[str] = Field(default_factory=list)


class ScoringEnvelope(BaseModel):
    """Envelope returned by the scoring endpoint."""

    result: ScoringOutput
    alert_state: Optional[AlertState] = None
