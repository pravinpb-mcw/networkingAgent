@echo off
echo ================================================================================
echo    STARTING 3 AGENTS WITH A2A COMMUNICATION
echo ================================================================================
echo.
echo Agent 1: Risk Score Calculator (A2A Server on port 5001)
echo Agent 2: Nearest AP Calculator (A2A Server on port 5002)  
echo Agent 3: Failover Suggestion (A2A Client)
echo.
echo ================================================================================
echo.

REM Start Agent 1 (Risk Score - A2A Server)
start "Agent 1 - Risk Score (A2A)" cmd /k "cd /d %~dp0.. && "../.wenv/Scripts/python.exe" agents\agent_1_risk_calculation.py --continuous 10"

timeout /t 3 /nobreak >nul

REM Start Agent 2 (Nearest AP - A2A Server)
start "Agent 2 - Nearest AP (A2A)" cmd /k "cd /d %~dp0.. && "../.wenv/Scripts/python.exe" agents\agent_2_nearest_ap.py --continuous 10"

timeout /t 5 /nobreak >nul

REM Start Agent 3 (Failover - A2A Client)
start "Agent 3 - Failover (A2A)" cmd /k "cd /d %~dp0.. && "../.wenv/Scripts/python.exe" agents\agent_3_failover_suggestion.py --continuous 10"

echo.
echo ================================================================================
echo All agents started!
echo ================================================================================
echo.
echo Agent 1 window: Risk Score calculation with A2A server (port 5001)
echo Agent 2 window: Nearest AP calculation with A2A server (port 5002)
echo Agent 3 window: Failover suggestion using A2A communication
echo.
echo Press any key to close this launcher window...
pause >nul
