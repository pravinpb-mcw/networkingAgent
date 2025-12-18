@echo off
REM Test Ollama Evaluation Setup

echo ================================================================================
echo   OLLAMA EVALUATION TEST
echo ================================================================================
echo.
echo This will test:
echo   1. Ollama connection to 192.168.13.162:11434
echo   2. Mixtral:8x7b model availability
echo   3. LiteLLM integration
echo   4. Phoenix evaluation pipeline
echo.
echo ================================================================================
echo.

cd /d "%~dp0"

python test_ollama_eval.py

echo.
echo ================================================================================
echo.
echo If all tests passed, you can now:
echo   1. Start Phoenix:  python phoenix_persistent.py --auto-eval
echo   2. Run agent:      python agents\risk_score_agent.py --continuous
echo   3. View dashboard: http://localhost:6006
echo.
echo ================================================================================
echo.

pause
