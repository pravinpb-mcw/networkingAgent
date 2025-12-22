@echo off
REM Start all 3 agents with A2A communication
REM Agent 1 (Risk Score) - Continuous on port 5001
REM Agent 2 (Nearest AP) - Continuous on port 5002
REM Agent 3 (Failover) - Queries Agent 1 & 2 via A2A

echo ========================================================================
echo           STARTING 3-AGENT SYSTEM WITH A2A COMMUNICATION
echo ========================================================================
echo.
echo Agent 1: Risk Score Calculation (Port 5001)
echo Agent 2: Nearest AP Finder (Port 5002)
echo Agent 3: Intelligent Failover Orchestrator (A2A Client)
echo.
echo ========================================================================
echo.

echo Starting Agent 1 (Risk Score) in new window...
start "Agent 1 - Risk Score" cmd /k "cd /d "%~dp0.." && .wenv\Scripts\activate && python agents\agent_1_risk_calculation.py --continuous 10"

timeout /t 3 /nobreak >nul

echo Starting Agent 2 (Nearest AP) in new window...
start "Agent 2 - Nearest AP" cmd /k "cd /d "%~dp0.." && .wenv\Scripts\activate && python agents\agent_2_nearest_ap.py --continuous 30"

timeout /t 3 /nobreak >nul

echo Starting Agent 3 (Failover A2A) in new window...
start "Agent 3 - Failover A2A" cmd /k "cd /d "%~dp0.." && .wenv\Scripts\activate && python agents\agent_3_failover_a2a.py --continuous 15"

echo.
echo ========================================================================
echo All agents started!
echo ========================================================================
echo.
echo Check the individual windows to see each agent running.
echo.
echo To stop: Close each window individually or press Ctrl+C in each
echo ========================================================================
pause
