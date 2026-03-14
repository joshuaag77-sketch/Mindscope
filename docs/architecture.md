# MindScope Architecture

MindScope is organized as a lightweight monorepo with a Python backend and a Next.js frontend.

## Backend

- FastAPI provides a small API surface for health checks, scoring, and alert state inspection.
- CSV-backed loaders provide baseline profiles, scenario centroids, and optional synthetic demo windows.
- A workbook-to-CSV script (`backend/scripts/generate_from_baseline_pack.ps1`) lets the team refresh data assets directly from the synthetic source pack.
- The scoring engine is deterministic and rules-based so the overload-risk output is explainable.
- Alert state and mock emails are persisted as JSON files in `backend/data/runtime/` using a simple local state store.
- A live ingestion service pulls ActivityWatch events from local watcher buckets, derives 10-minute features, scores windows, and updates alert persistence.

## Frontend

- Next.js App Router fetches live analytics (`/api/v1/analytics/dashboard`) and renders real trend + KPI panels with graceful fallback data.
- Shared presentation components keep API integration separate from UI cards.
- Pages are split into dashboard, setup/info, and history placeholders.

## Data Flow

1. A 10-minute activity window is sent to the scoring endpoint.
2. The backend resolves a contextual baseline row using day-of-week and hour-of-day, with fallback rows allowed for demos.
3. The scoring engine computes subscores, applies the scenario adjustment, and returns explainability details.
4. If alert tracking is enabled, the alert service updates recent score history and emits a mock email when persistence rules are met.
