@echo off
setlocal enabledelayedexpansion
REM Run dashboard directly in current terminal (good for demos/recording)
echo ================================================================================
echo    STARTING DASHBOARD IN CURRENT TERMINAL
echo ================================================================================
echo.

cd /d "%~dp0.."
call "%~dp0load_env.bat"

echo [1/3] Clearing old data...
echo [] > agent_data\risk_scores.json
echo [] > agent_data\failover_suggestions.json
echo [] > agent_data\analysis_history.json
echo    Done!
echo.

echo [2/3] Installing dependencies...
"%PYTHON_EXE%" -m pip install -r dashboard/backend/requirements.txt --quiet

echo [3/3] Starting Dashboard...
echo    Backend: http://localhost:8000
echo    Press CTRL+C to stop
echo.

start http://localhost:8000
"%PYTHON_EXE%" -m uvicorn dashboard.backend.main:app --host 0.0.0.0 --port 8000 --reload
