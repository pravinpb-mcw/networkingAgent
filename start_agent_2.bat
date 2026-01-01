@echo off
echo Starting Agent 2 - Nearest AP Analysis...
cd /d "%~dp0"
.wenv\Scripts\python.exe agents\agent_2_nearest_ap.py --continuous 10
pause
