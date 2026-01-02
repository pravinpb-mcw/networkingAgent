@echo off
title Restart All Agents
echo ================================================================================
echo    RESTARTING ALL AGENTS (Kill + Start)
echo ================================================================================
echo.

cd /d "%~dp0.."

echo [1/2] Killing existing agent processes...
taskkill /F /FI "WINDOWTITLE eq Agent 1*" 2>nul
taskkill /F /FI "WINDOWTITLE eq Agent 2*" 2>nul
taskkill /F /FI "WINDOWTITLE eq Agent 3*" 2>nul
echo    ✓ Old processes terminated
echo.
timeout /t 2 /nobreak >nul

echo [2/2] Starting agents...
echo.

REM Start Agent 1
echo Starting Agent 1 - Risk Calculation (Port 5001)...
start "Agent 1 - Risk Calculation" cmd /k "cd /d "%~dp0.." && "../.wenv/Scripts/python.exe" agents\agent_1_risk_calculation.py --continuous 10"
timeout /t 3 /nobreak >nul

REM Start Agent 2
echo Starting Agent 2 - Nearest AP Analysis (Port 5002)...
start "Agent 2 - Nearest AP" cmd /k "cd /d "%~dp0.." && "../.wenv/Scripts/python.exe" agents\agent_2_nearest_ap.py --continuous 10"
timeout /t 3 /nobreak >nul

REM Start Agent 3
echo Starting Agent 3 - Failover Coordinator...
start "Agent 3 - Failover" cmd /k "cd /d "%~dp0.." && "../.wenv/Scripts/python.exe" agents\agent_3_failover_suggestion.py --continuous 10"

echo.
echo ================================================================================
echo    ALL AGENTS RESTARTED!
echo ================================================================================
echo.
pause
