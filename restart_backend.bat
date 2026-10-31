@echo off
cd /d "%~dp0"
echo Stop the existing Mindscope backend with Ctrl+C before restarting.
python start_backend.py
