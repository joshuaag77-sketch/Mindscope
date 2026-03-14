# MindScope API Contract

## `GET /health`

Returns service health and whether baseline/scenario CSV assets loaded successfully.

## `POST /api/v1/scoring?track_alert=false`

Scores a single activity window.

### Request body

```json
{
  "user_id": "demo-user",
  "timestamp_start": "2026-03-10T09:40:00Z",
  "day_of_week": 1,
  "hour_of_day": 9,
  "is_workday": true,
  "app_switch_count": 17,
  "distinct_app_count": 8,
  "focus_streak_minutes": 9,
  "afk_count": 3,
  "afk_minutes": 8,
  "work_context_entropy": 3.0,
  "work_reentry_count": 6
}
```

### Response body

```json
{
  "result": {
    "overload_score": 82.3,
    "state_band": "Sustained Overload Risk",
    "fragmentation_score": 84.0,
    "focus_instability_score": 77.5,
    "interruption_score": 63.3,
    "nearest_scenario": "overload",
    "top_drivers": [
      "App switching is 113% above baseline",
      "Focus streak is 67% below baseline",
      "Work context entropy is 58% above baseline"
    ]
  },
  "alert_state": null
}
```

If `track_alert=true`, the response includes the updated alert state.

## `GET /api/v1/scoring/synthetic-demo?limit=24&user_id=user_001`

Returns a scored trend series from synthetic windows for dashboard bootstrapping.

## `GET /api/v1/scoring/synthetic-current?user_id=user_001`

Returns a full scoring envelope for the latest synthetic window.

## `POST /api/v1/analytics/ingest/run-once`

Triggers one immediate live ingestion pass from ActivityWatch and returns the scored record.

## `GET /api/v1/analytics/dashboard?limit=72&ingest_if_needed=true`

Primary live dashboard payload.

- `source`: data source label (`activitywatch_live`)
- `current`: latest scored live record
- `history`: recent scored records
- `summary`: aggregate KPIs (`avg_score`, `max_score`, `high_risk_windows`, etc.)

## `POST /api/v1/alerts/evaluate`

Accepts a precomputed overload score and updates persistence tracking.

## `GET /api/v1/alerts/state/{user_id}`

Returns the current in-memory alert state for a user.

## `GET /api/v1/alerts/emails`

Returns mock emails captured by the fake email service for demos and debugging.

## Persistence note

Alert state and mock emails are persisted to JSON files under `backend/data/runtime/` in the current MVP.
