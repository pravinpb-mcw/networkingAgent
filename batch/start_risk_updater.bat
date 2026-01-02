@echo off
setlocal enabledelayedexpansion
echo ================================================================================
echo    AUTO RISK SCORE UPDATER
echo ================================================================================
echo    Reading: mock_data/comprehensive_api_data.json
echo    Writing: agent_data/risk_scores.json
echo    Interval: 10 seconds
echo ================================================================================
echo.

cd /d "%~dp0.."

REM Load environment variables from .env
call "%~dp0load_env.bat"

"%PYTHON_EXE%" scripts\auto_risk_score_updater.py --continuous 10
