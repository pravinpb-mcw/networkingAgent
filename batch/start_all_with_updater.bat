@echo off
setlocal enabledelayedexpansion
title Start All Agents + Risk Updater
echo ================================================================================
echo    STARTING ALL AGENTS + RISK SCORE UPDATER
echo ================================================================================
echo.

cd /d "%~dp0.."

REM Load environment variables from .env
call "%~dp0load_env.bat"

echo [1/4] Starting Risk Score Updater...
start "Risk Score Updater" cmd /k "cd /d "%~dp0.." && call "%~dp0load_env.bat" && "%PYTHON_EXE%" scripts\auto_risk_score_updater.py --continuous 10"
timeout /t 3 /nobreak >nul

echo [2/4] Starting Agent 1 - Risk Calculation...
start "Agent 1 - Risk Calculation" cmd /k "cd /d "%~dp0.." && call "%~dp0load_env.bat" && "%PYTHON_EXE%" agents\agent_1_risk_calculation.py --continuous 10"
timeout /t 3 /nobreak >nul

echo [3/4] Starting Agent 2 - Nearest AP Analysis...
start "Agent 2 - Nearest AP" cmd /k "cd /d "%~dp0.." && call "%~dp0load_env.bat" && "%PYTHON_EXE%" agents\agent_2_nearest_ap.py --continuous 10"
timeout /t 3 /nobreak >nul

echo [4/4] Starting Agent 3 - Failover Coordinator...
start "Agent 3 - Failover" cmd /k "cd /d "%~dp0.." && call "%~dp0load_env.bat" && "%PYTHON_EXE%" agents\agent_3_failover_suggestion.py --continuous 10"

echo.
echo ================================================================================
echo    ALL COMPONENTS STARTED!
echo ================================================================================
echo.
echo Windows opened:
echo   - Risk Score Updater (reads mock data every 10s)
echo   - Agent 1: Risk Calculation
echo   - Agent 2: Nearest AP Analysis  
echo   - Agent 3: Failover Coordinator
echo.
pause
