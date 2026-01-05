@echo off
setlocal enabledelayedexpansion
title Network Observability React Dashboard
echo ================================================================================
echo    STARTING REACT DASHBOARD (v3.0)
echo ================================================================================
echo.
cd /d "%~dp0.."

REM Load environment variables from .env
call "%~dp0load_env.bat"

echo [1/5] Clearing old agent data (keeping nearest_aps)...
echo [] > agent_data\risk_scores.json
echo [] > agent_data\failover_suggestions.json
echo [] > agent_data\analysis_history.json
echo    ✓ Data cleared
echo.

echo [2/5] Verifying Python environment...
if not exist "%PYTHON_EXE%" (
    echo Error: Python environment not found at %PYTHON_EXE%
    pause
    exit /b
)

echo [3/5] Checking Backend Dependencies...
"%PYTHON_EXE%" -m pip install -r dashboard/backend/requirements.txt > nul

echo [4/5] Starting Backend Server (Port 8000)...
start "Backend API" "%PYTHON_EXE%" -m uvicorn dashboard.backend.main:app --host 0.0.0.0 --port 8000 --reload

echo [5/5] Starting React Frontend...
cd react_dashboard
if not exist "node_modules" (
    echo    Installing Node dependencies (this may take a minute)...
    call npm install
)

echo.
echo    Backend: http://localhost:8000
echo    Frontend: http://localhost:5173
echo.
echo    Starting Vite server...
call npm run dev

pause
