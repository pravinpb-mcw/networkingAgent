@echo off
REM Start standalone Phoenix observability server
REM This runs Phoenix as a persistent server independent of agents

echo ================================================================================
echo Starting Phoenix Observability Server (Standalone Mode)
echo ================================================================================
echo.
echo This will start a persistent Phoenix server that:
echo   - Stays running even after agents stop
echo   - Allows you to view traces anytime
echo   - Stores data in .phoenix/ directory
echo.
echo Phoenix UI will be available at: http://localhost:6006
echo.
echo Press Ctrl+C to stop the Phoenix server
echo.

python start_phoenix_standalone.py --port 6006
