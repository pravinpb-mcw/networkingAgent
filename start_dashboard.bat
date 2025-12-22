@echo off
echo ================================================================================
echo    STARTING NETWORK OBSERVABILITY DASHBOARD
echo ================================================================================
echo.
echo Dashboard Features:
echo   - Agent status monitoring
echo   - Risk score analysis
echo   - Nearest AP candidates
echo   - Failover recommendations
echo   - A2A communication logs
echo   - Phoenix integration
echo.
echo ================================================================================
echo.

cd /d %~dp0
..\.wenv\Scripts\streamlit.exe run dashboard.py --server.port 8501

pause
