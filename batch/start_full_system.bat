@echo off
setlocal enabledelayedexpansion
title Complete System with Phoenix
echo ================================================================================
echo    STARTING COMPLETE SYSTEM (Phoenix + Risk Updater + 3 Agents)
echo ================================================================================
echo.

cd /d "%~dp0.."

REM Load environment variables from .env
call "%~dp0load_env.bat"

echo Killing existing processes...
taskkill /F /FI "WINDOWTITLE eq Phoenix Server*" 2>nul
taskkill /F /FI "WINDOWTITLE eq Risk Score Updater*" 2>nul
taskkill /F /FI "WINDOWTITLE eq Agent 1*" 2>nul
taskkill /F /FI "WINDOWTITLE eq Agent 2*" 2>nul
taskkill /F /FI "WINDOWTITLE eq Agent 3*" 2>nul
timeout /t 2 /nobreak >nul

echo.
echo [1/5] Starting Phoenix Server (Port 6006)...
start "Phoenix Server" cmd /k "cd /d "%~dp0.." && call "%~dp0load_env.bat" && "%PYTHON_EXE%" phoenix\server.py --auto-eval --eval-interval 10"
timeout /t 5 /nobreak >nul

echo [2/5] Starting Risk Score Updater...
start "Risk Score Updater" cmd /k "cd /d "%~dp0.." && call "%~dp0load_env.bat" && "%PYTHON_EXE%" scripts\auto_risk_score_updater.py --continuous 10"
timeout /t 3 /nobreak >nul

echo [3/5] Starting Agent 1 - Risk Calculation...
start "Agent 1 - Risk Calculation" cmd /k "cd /d "%~dp0.." && call "%~dp0load_env.bat" && "%PYTHON_EXE%" agents\agent_1_risk_calculation.py --continuous 10"
timeout /t 3 /nobreak >nul

echo [4/5] Starting Agent 2 - Nearest AP Analysis...
start "Agent 2 - Nearest AP" cmd /k "cd /d "%~dp0.." && call "%~dp0load_env.bat" && "%PYTHON_EXE%" agents\agent_2_nearest_ap.py --continuous 10"
timeout /t 3 /nobreak >nul

echo [5/5] Starting Agent 3 - Failover Coordinator...
start "Agent 3 - Failover" cmd /k "cd /d "%~dp0.." && call "%~dp0load_env.bat" && "%PYTHON_EXE%" agents\agent_3_failover_suggestion.py --continuous 10"

echo.
echo ================================================================================
echo    ALL SYSTEMS ONLINE!
echo ================================================================================
echo.
echo Windows opened:
echo   - Phoenix Server: http://localhost:6006
echo   - Risk Score Updater (updates every 10s)
echo   - Agent 1: Risk Calculation
echo   - Agent 2: Nearest AP Analysis  
echo   - Agent 3: Failover Coordinator
echo.
echo To simulate failures, use the dashboard or run scenario scripts.
echo.
pause
