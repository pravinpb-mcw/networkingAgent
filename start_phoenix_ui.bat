@echo off
REM Launch Phoenix UI standalone for viewing traces
REM Use this if you want to start Phoenix UI separately from the agent

echo ================================
echo Starting Phoenix UI
echo ================================
echo.
echo Phoenix will be available at: http://localhost:6006
echo.
echo Press Ctrl+C to stop
echo.

python -c "import phoenix as px; session = px.launch_app(port=6006); print('Phoenix UI running at http://localhost:6006'); import time; [time.sleep(1) for _ in iter(int, 1)]"
