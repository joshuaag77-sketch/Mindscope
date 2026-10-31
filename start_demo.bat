@echo off
cd /d "%~dp0"
echo Mindscope uses private configuration; see SECURITY.md.
start "MindScope backend" cmd /k python start_backend.py
start "MindScope frontend" cmd /k python start_frontend.py
