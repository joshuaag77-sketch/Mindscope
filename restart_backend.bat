@echo off
echo Stopping any existing backend on port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul

echo Loading SMTP env vars from backend\.env.demo...
for /f "usebackq tokens=1,* delims==" %%A in (`findstr /v "^#" backend\.env.demo`) do (
    if not "%%A"=="" set %%A=%%B
)

echo Starting backend with SMTP email...
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
