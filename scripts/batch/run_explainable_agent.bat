@echo off
REM Run Risk Score Agent with FULL EXPLAINABILITY
REM Every action will be explained and visible in Phoenix dashboard

echo ================================================================================
echo   RISK SCORE AGENT WITH EXPLAINABILITY
echo ================================================================================
echo.
echo This will start:
echo   1. Phoenix observability on http://localhost:6006
echo   2. Risk Score Agent with full explanations
echo   3. Hallucination detection on all outputs
echo   4. Explanation logs saved to ./explanations/
echo.
echo View real-time explanations in Phoenix dashboard!
echo ================================================================================
echo.

cd /d "%~dp0"

python agents\risk_score_agent_with_explainability.py --continuous 15

pause
