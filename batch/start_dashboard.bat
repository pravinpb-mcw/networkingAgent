@echo off
title Network Observability Dashboard
echo ================================================================================
echo    STARTING NETWORK OBSERVABILITY DASHBOARD (v2.0)
echo ================================================================================
echo.
cd /d "%~dp0.."

echo [1/4] Clearing old agent data (keeping nearest_aps)...
echo [] > agent_data\risk_scores.json
echo [] > agent_data\failover_suggestions.json
echo [] > agent_data\analysis_history.json
echo    ✓ Data cleared (nearest_aps.json preserved)
echo.

echo [2/4] Verifying environment...
if not exist "../.wenv/Scripts/python.exe" (
    echo Error: Python environment not found in ../.wenv
    pause
    exit /b
)

echo [3/4] Checking dependencies...
"../.wenv/Scripts/python.exe" -m pip install -r dashboard/backend/requirements.txt > nul

echo [4/4] Launching Dashboard...
echo.
echo    Backend: http://localhost:8000
echo    Frontend: Integrated
echo.
echo Closing this window will stop the dashboard.
echo.

start http://localhost:8000
"../.wenv/Scripts/python.exe" -m uvicorn dashboard.backend.main:app --host 0.0.0.0 --port 8000 --reload

pause
