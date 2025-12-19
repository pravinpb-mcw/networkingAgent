@echo off
REM Check Agent Status
cd /d "%~dp0"
"..\.wenv\Scripts\python.exe" scripts/check_agents.py
pause
