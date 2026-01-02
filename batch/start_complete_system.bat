@echo off
setlocal enabledelayedexpansion
title Complete Network Observability System
echo ================================================================================
echo    STARTING COMPLETE SYSTEM: AGENTS + DASHBOARD
echo ================================================================================
echo.
echo Starting sequence:
echo   1. Agent 1 - Risk Calculation
echo   2. Agent 2 - Nearest AP Analysis
echo   3. Agent 3 - Failover Coordinator
echo   4. Dashboard (after agents are running)
echo.
echo ================================================================================
echo.

cd /d "%~dp0.."

REM Load environment variables from .env
call "%~dp0load_env.bat"

echo [0/4] Clearing old agent data for fresh start...
echo [] > agent_data\risk_scores.json
echo [] > agent_data\nearest_aps.json
echo [] > agent_data\failover_suggestions.json
echo [] > agent_data\analysis_history.json
echo    ✓ Data files cleared
echo.
timeout /t 2 /nobreak >nul

REM Start Agent 1
echo [1/4] Starting Agent 1 - Risk Calculation (Port 5001)...
start "Agent 1 - Risk Calculation" cmd /k "cd /d "%~dp0.." && call "%~dp0load_env.bat" && "%PYTHON_EXE%" agents\agent_1_risk_calculation.py --continuous 10"

timeout /t 5 /nobreak >nul

REM Start Agent 2
echo [2/4] Starting Agent 2 - Nearest AP Analysis (Port 5002)...
start "Agent 2 - Nearest AP" cmd /k "cd /d "%~dp0.." && call "%~dp0load_env.bat" && "%PYTHON_EXE%" agents\agent_2_nearest_ap.py --continuous 10"

timeout /t 5 /nobreak >nul

REM Start Agent 3
echo [3/4] Starting Agent 3 - Failover Coordinator...
start "Agent 3 - Failover" cmd /k "cd /d "%~dp0.." && call "%~dp0load_env.bat" && "%PYTHON_EXE%" agents\agent_3_failover_suggestion.py --continuous 10"

echo.
echo [4/4] Waiting for agents to initialize and generate data...
timeout /t 8 /nobreak >nul

REM Start Dashboard
echo.
echo Starting Dashboard...
start "Network Dashboard" cmd /k "cd /d "%~dp0" && start_dashboard.bat"

echo.
echo ================================================================================
echo    ALL SYSTEMS STARTED!
echo ================================================================================
echo.
echo Windows opened:
echo   - Agent 1: Risk Calculation
echo   - Agent 2: Nearest AP Analysis  
echo   - Agent 3: Failover Coordinator
echo   - Dashboard: http://localhost:8000
echo.
echo Data will appear in dashboard as agents generate it.
echo.
pause
