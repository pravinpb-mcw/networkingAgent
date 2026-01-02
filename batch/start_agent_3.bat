@echo off
setlocal enabledelayedexpansion
echo Starting Agent 3 - Failover Coordinator...
cd /d "%~dp0.."

REM Load environment variables from .env
call "%~dp0load_env.bat"

"%PYTHON_EXE%" agents\agent_3_failover_suggestion.py --continuous 10
pause
