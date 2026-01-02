@echo off
setlocal enabledelayedexpansion
echo Starting Agent 2 - Nearest AP Analysis...
cd /d "%~dp0.."

REM Load environment variables from .env
call "%~dp0load_env.bat"

"%PYTHON_EXE%" agents\agent_2_nearest_ap.py --continuous 10
pause
