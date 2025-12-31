@echo off
echo ================================================================================
echo    STARTING COMPLETE NETWORK OBSERVABILITY SYSTEM
echo ================================================================================
echo.

cd /d "%~dp0"

echo [1/4] Starting Phoenix Observability Server (Port 6006)...
start "Phoenix Server" cmd /k "..\.wenv\Scripts\activate && python phoenix\server.py --auto-eval --eval-interval 10"

echo [2/4] Waiting for Phoenix to initialize...
timeout /t 5 /nobreak >nul

echo [3/4] Starting Agent 1 (Risk Calculation - Port 5001)...
start "Agent 1 - Risk Calculation" cmd /k "..\.wenv\Scripts\activate && python agents\agent_1_risk_calculation.py --continuous 10"

echo [4/4] Starting Agent 2 (Nearest AP - Port 5002)...
start "Agent 2 - Nearest AP" cmd /k "..\.wenv\Scripts\activate && python agents\agent_2_nearest_ap.py --continuous 10"

echo [5/5] Starting Agent 3 (Failover Orchestrator)...
start "Agent 3 - Failover Orchestrator" cmd /k "..\.wenv\Scripts\activate && python agents\agent_3_failover_suggestion.py --continuous 10"

echo.
echo ================================================================================
echo    SYSTEM START INITATED
echo ================================================================================
echo    - Phoenix: http://localhost:6006
echo    - Agent 1: http://localhost:5001
echo    - Agent 2: http://localhost:5002
echo.
