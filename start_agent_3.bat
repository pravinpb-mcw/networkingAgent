@echo off
echo Starting Agent 3 - Failover Coordinator...
cd /d "%~dp0"
.wenv\Scripts\python.exe agents\agent_3_failover_suggestion.py --continuous 10
pause
