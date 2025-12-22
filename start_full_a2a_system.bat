@echo off
REM Simple 3-Agent A2A System Startup Script
REM ==========================================
REM
REM This script starts the A2A servers and client:
REM
REM 1. Agent 1 A2A Server - Serves risk scores on port 5001
REM 2. Agent 2 A2A Server - Serves nearest AP data on port 5002
REM 3. Agent 3 (Failover A2A) - Queries agents and suggests failovers

echo ========================================================================
echo     SIMPLE 3-AGENT A2A SYSTEM
echo ========================================================================
echo.
echo This will start 3 windows:
echo   1. Agent 1 A2A Server (port 5001) - Risk Scores
echo   2. Agent 2 A2A Server (port 5002) - Nearest APs
echo   3. Agent 3 A2A Client - Failover Suggestions
echo.
echo ========================================================================
echo.

cd /d "%~dp0"

REM Step 1: Start Agent 1 A2A Server
echo [1/3] Starting Agent 1 A2A Server (port 5001)...
start "Agent 1 - A2A Server" cmd /k "cd /d "%~dp0" && "..\.wenv\Scripts\python.exe" agents\agent_1_a2a_simple.py"

timeout /t 3 /nobreak >nul

REM Step 2: Start Agent 2 A2A Server
echo [2/3] Starting Agent 2 A2A Server (port 5002)...
start "Agent 2 - A2A Server" cmd /k "cd /d "%~dp0" && "..\.wenv\Scripts\python.exe" agents\agent_2_a2a_simple.py"

timeout /t 3 /nobreak >nul

REM Step 3: Start Agent 3 Failover Client
echo [3/3] Starting Agent 3 - Failover A2A Client...
start "Agent 3 - Failover Client" cmd /k "cd /d "%~dp0" && "..\.wenv\Scripts\python.exe" agents\agent_3_a2a_simple.py"

echo.
echo ========================================================================
echo                    ALL AGENTS STARTED!
echo ========================================================================
echo.
echo You should now see 3 command windows:
echo.
echo   Window 1: Agent 1 A2A server on port 5001 (risk scores)
echo   Window 2: Agent 2 A2A server on port 5002 (nearest APs)
echo   Window 3: Agent 3 querying agents and generating failover suggestions
echo.
echo ========================================================================
echo.
echo To stop: Close each window individually or press Ctrl+C in each
echo.
echo ========================================================================
pause
