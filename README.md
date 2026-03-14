# MindScope

MindScope is a hackathon MVP that estimates **overload risk** from passive desktop activity telemetry. The current version is intentionally transparent and rules-based, with CSV-backed inputs and a mock alerting layer.

## Monorepo Layout

- `backend/`: FastAPI API, scoring engine, CSV loaders, and in-memory alert services
- `frontend/`: Next.js dashboard shell with mock data
- `docs/`: concise implementation docs for architecture, scoring, and API shape

## Backend Quick Start

```bash
cd mindscope/backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Live ActivityWatch Ingestion

MindScope can ingest ActivityWatch events directly from your local machine.

Default assumptions:

- ActivityWatch server: `http://127.0.0.1:5600/api/0`
- Window bucket prefix: `aw-watcher-window_`
- AFK bucket prefix: `aw-watcher-afk_`
- Ingestion loop: every 60 seconds

Useful env vars:

```powershell
$env:MINDSCOPE_INGESTION_ENABLED="true"
$env:MINDSCOPE_USER_ID="joshu"
$env:MINDSCOPE_ACTIVITYWATCH_BASE_URL="http://127.0.0.1:5600/api/0"
```

Optional SMTP email alerts:

```powershell
$env:MINDSCOPE_EMAIL_PROVIDER="smtp"
$env:MINDSCOPE_ALERT_EMAIL="you@yourdomain.com"
$env:MINDSCOPE_SMTP_HOST="smtp.yourprovider.com"
$env:MINDSCOPE_SMTP_PORT="587"
$env:MINDSCOPE_SMTP_USERNAME="smtp-user"
$env:MINDSCOPE_SMTP_PASSWORD="smtp-password"
$env:MINDSCOPE_SMTP_USE_TLS="true"
$env:MINDSCOPE_SMTP_FROM="mindscope@yourdomain.com"
```

## Use the provided synthetic baseline workbook

```powershell
cd mindscope/backend
./scripts/generate_from_baseline_pack.ps1 `
  -SourceXlsx "c:\Users\joshu\OneDrive\Desktop\Hackathon\ZooTech UofC Cursor Hackathon March 2026\mindscope_synthetic_baseline_pack.xlsx" `
  -OutputDir "data"
```

## Frontend Quick Start

```bash
cd mindscope/frontend
npm install
npm run dev
```

## MVP Scope

- Real overload-risk scoring logic
- Contextual baseline comparison by day/hour with fallback sample data
- Scenario adjustment layer with explainable output
- In-memory persistence for alert triggering
- JSON-backed persistence for alert state and mock email logs
- Mock email capture endpoint for demos
- Frontend dashboard wired to live backend with mock fallback
