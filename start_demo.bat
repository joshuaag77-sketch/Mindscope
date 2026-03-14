@echo off
echo =========================================
echo  MindScope Demo Startup
echo =========================================

REM ── Load .env.demo into environment ──────────────────────────────────────────
if exist backend\.env.demo (
    for /f "usebackq tokens=1,* delims==" %%A in (`findstr /v "^#" backend\.env.demo`) do (
        if not "%%A"=="" set %%A=%%B
    )
    echo [OK] Loaded backend\.env.demo
) else (
    echo [WARN] No .env.demo found, using defaults (mock email)
)

REM ── Clear runtime state for a fresh demo ─────────────────────────────────────
if exist backend\data\runtime (
    del /q backend\data\runtime\*.json 2>nul
    echo [OK] Cleared runtime state (fresh demo)
)

REM ── Start FastAPI backend ─────────────────────────────────────────────────────
echo.
echo [1/2] Starting backend on http://127.0.0.1:8000 ...
start "MindScope Backend" cmd /k "cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 3 /nobreak >nul

REM ── Start Next.js frontend ────────────────────────────────────────────────────
echo [2/2] Starting frontend on http://localhost:3000 ...
start "MindScope Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo =========================================
echo  Both services are starting up.
echo  Open: http://localhost:3000
echo =========================================
echo.
echo  DEMO TIPS:
echo  - Switch between apps rapidly to raise fragmentation score
echo  - Alt+Tab repeatedly (10+ times in a minute) to spike the score
echo  - Open many apps at once to increase distinct_app_count
echo  - Email alert fires after 2 windows above 85 OR 3 windows above 70
echo  - To reset between demos: DELETE backend\data\runtime\*.json
echo    OR call POST http://127.0.0.1:8000/api/v1/alerts/reset/joshu
echo =========================================
pause
