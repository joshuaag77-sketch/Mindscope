"""Activity window models."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ActivityWindowInput(BaseModel):
    """One 10-minute ActivityWatch-style derived telemetry window."""

    user_id: str = Field(..., description="Stable identifier for the user.")
    timestamp_start: datetime = Field(..., description="Window start timestamp.")
    day_of_week: int = Field(..., ge=0, le=6, description="Monday=0 through Sunday=6.")
    hour_of_day: int = Field(..., ge=0, le=23)
    is_workday: bool = True
    scenario_label: Optional[str] = Field(
        default=None,
        description="Optional synthetic label used for demos or offline evaluation.",
    )
    active_minutes: float = Field(default=0.0, ge=0.0)
    afk_minutes: float = Field(default=0.0, ge=0.0)
    afk_count: float = Field(default=0.0, ge=0.0)
    app_switch_count: float = Field(default=0.0, ge=0.0)
    distinct_app_count: float = Field(default=0.0, ge=0.0)
    top_app_category: Optional[str] = None
    email_minutes: float = Field(default=0.0, ge=0.0)
    chat_minutes: float = Field(default=0.0, ge=0.0)
    browser_minutes: float = Field(default=0.0, ge=0.0)
    docs_minutes: float = Field(default=0.0, ge=0.0)
    ide_minutes: float = Field(default=0.0, ge=0.0)
    meeting_minutes: float = Field(default=0.0, ge=0.0)
    admin_minutes: float = Field(default=0.0, ge=0.0)
    focus_streak_minutes: float = Field(default=0.0, ge=0.0)
    work_context_entropy: float = Field(default=0.0, ge=0.0)
    work_reentry_count: float = Field(default=0.0, ge=0.0)
