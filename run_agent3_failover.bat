@echo off
REM Agent 3: Failover Suggestion Agent Runner
REM Analyzes risk scores and nearest APs to generate failover suggestions

echo ============================================================
echo   AGENT 3: FAILOVER SUGGESTION AGENT
echo ============================================================
echo.

REM Activate virtual environment
cd /d "e:\network of obserbility\networkingAgent"
call .wenv\Scripts\activate

REM Run Agent 3
echo Running Agent 3...
python agents/agent_3_failover_suggestion.py

echo.
echo ============================================================
echo   AGENT 3 COMPLETE
echo ============================================================
pause
