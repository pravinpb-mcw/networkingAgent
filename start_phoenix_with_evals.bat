@echo off
REM Phoenix Server with Auto-Evaluation
REM Single command to run Phoenix + automatic LLM-as-a-Judge evaluations

echo ================================================================================
echo Phoenix Server with Auto-Evaluation (All-in-One)
echo ================================================================================
echo.
echo This will start:
echo   - Phoenix observability server on port 6006
echo   - Automatic hallucination detection every 60 seconds
echo   - Persistent UI that stays running
echo.
echo Phoenix UI: http://localhost:6006
echo Evaluation results: phoenix_auto_eval_results.csv
echo.
echo Press Ctrl+C to stop
echo.

python phoenix_with_evals.py --auto-eval --eval-interval 60
