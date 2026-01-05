@echo off
setlocal enabledelayedexpansion
echo ================================================================================
echo    STARTING COMPLETE NETWORK OBSERVABILITY SYSTEM
echo ================================================================================
echo.

cd /d "%~dp0.."

REM Load environment variables from .env
call "%~dp0load_env.bat"

echo [1/5] Starting Phoenix Observability Server (Port 6006)...
start "Phoenix Server" cmd /k "cd /d "%~dp0.." && call "%~dp0load_env.bat" && "%PYTHON_EXE%" phoenix\server.py --auto-eval --eval-interval 10"
echo Waiting for Phoenix to become ready...
"%PYTHON_EXE%" "%~dp0check_phoenix.py"
if errorlevel 1 (
    echo.
    echo WARNING: Phoenix may not be ready, continuing anyway...
    echo.
)

echo [2/5] Waiting for Phoenix to initialize...
timeout /t 5 /nobreak >nul

echo [3/5] Starting Auto Risk Score Updater (reads mock data, updates every 10s)...
start "Risk Score Updater" cmd /k "cd /d "%~dp0.." && call "%~dp0load_env.bat" && "%PYTHON_EXE%" scripts\auto_risk_score_updater.py --continuous 10"

echo [4/5] Starting Agent 1 (Risk Calculation - Port 5001)...
start "Agent 1 - Risk Calculation" cmd /k "cd /d "%~dp0.." && call "%~dp0load_env.bat" && "%PYTHON_EXE%" agents\agent_1_risk_calculation.py --continuous 10"

echo [5/5] Starting Agent 2 (Nearest AP - Port 5002)...
start "Agent 2 - Nearest AP" cmd /k "cd /d "%~dp0.." && call "%~dp0load_env.bat" && "%PYTHON_EXE%" agents\agent_2_nearest_ap.py --continuous 10"

echo [6/6] Starting Agent 3 (Failover Orchestrator)...
start "Agent 3 - Failover Orchestrator" cmd /k "cd /d "%~dp0.." && call "%~dp0load_env.bat" && "%PYTHON_EXE%" agents\agent_3_failover_suggestion.py --continuous 10"

echo.
echo ================================================================================
echo    SYSTEM START INITATED
echo ================================================================================
echo    - Phoenix: http://localhost:6006
echo    - Risk Updater: Running (updates risk_scores.json every 10s)
echo    - Agent 1: http://localhost:5001
echo    - Agent 2: http://localhost:5002
echo.
