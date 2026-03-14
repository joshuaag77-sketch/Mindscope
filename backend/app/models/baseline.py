"""Baseline models."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class FeatureBaselineStats(BaseModel):
    """Mean and standard deviation for one feature in a baseline slice."""

    mean: float
    std: float = Field(..., gt=0.0)


class BaselineRow(BaseModel):
    """Contextual baseline row keyed by user and time context."""

    user_id: Optional[str] = Field(
        default=None,
        description="Optional user-specific row. Null or 'global' rows are shared.",
    )
    day_of_week: int = Field(
        ...,
        ge=-1,
        le=6,
        description="Monday=0 through Sunday=6. Use -1 for any day fallback rows.",
    )
    hour_of_day: int = Field(..., ge=0, le=23)
    features: dict[str, FeatureBaselineStats]
