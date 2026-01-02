@echo off
setlocal enabledelayedexpansion
title Network Observability Dashboard
echo ================================================================================
echo    STARTING NETWORK OBSERVABILITY DASHBOARD (v2.0)
echo ================================================================================
echo.
cd /d "%~dp0.."

REM Load environment variables from .env
call "%~dp0load_env.bat"

echo [1/4] Clearing old agent data (keeping nearest_aps)...
echo [] > agent_data\risk_scores.json
echo [] > agent_data\failover_suggestions.json
echo [] > agent_data\analysis_history.json
echo    ✓ Data cleared (nearest_aps.json preserved)
echo.

echo [2/4] Verifying environment...
if not exist "%PYTHON_EXE%" (
    echo Error: Python environment not found at %PYTHON_EXE%
    pause
    exit /b
)

echo [3/4] Checking dependencies...
"%PYTHON_EXE%" -m pip install -r dashboard/backend/requirements.txt > nul

echo [4/4] Launching Dashboard...
echo.
echo    Backend: http://localhost:8000
echo    Frontend: Integrated
echo.
echo Closing this window will stop the dashboard.
echo.

start http://localhost:8000
"%PYTHON_EXE%" -m uvicorn dashboard.backend.main:app --host 0.0.0.0 --port 8000 --reload

pause
