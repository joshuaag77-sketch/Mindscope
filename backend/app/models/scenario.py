"""Scenario centroid models."""

from __future__ import annotations

from pydantic import BaseModel


class ScenarioCentroid(BaseModel):
    """Normalized scenario centroid for nearest-neighbor adjustments."""

    scenario_label: str
    features: dict[str, float]
