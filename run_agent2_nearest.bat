@echo off
REM Run Nearest AP Agent (Agent 2)
cd /d "%~dp0"
"..\.wenv\Scripts\python.exe" main.py --agent nearest
pause