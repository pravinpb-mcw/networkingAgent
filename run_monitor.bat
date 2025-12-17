@echo off
REM Run Network Monitoring Agent with Virtual Environment
cd /d "%~dp0"
"..\.wenv\Scripts\python.exe" main.py --agent monitor
pause
