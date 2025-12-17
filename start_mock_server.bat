@echo off
REM Start Mock Meraki Server
cd /d "%~dp0"
echo Starting Mock Meraki Server...
start "Mock Meraki Server" "..\.wenv\Scripts\python.exe" server\mock_server.py
timeout /t 3 /nobreak >nul
echo Mock server started!
echo.
echo You can now run the agents in separate terminals:
echo   - run_agent1_risk.bat
echo   - run_agent2_nearest.bat  
echo   - run_monitor.bat
echo.
pause
