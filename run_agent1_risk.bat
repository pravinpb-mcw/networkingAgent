@echo off
REM Run Risk Score Agent (Agent 1)
cd /d "%~dp0"
"..\.wenv\Scripts\python.exe" main.py --agent risk
pause