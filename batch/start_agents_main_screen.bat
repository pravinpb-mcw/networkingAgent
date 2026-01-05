@echo off
setlocal enabledelayedexpansion
REM Start agents on main screen using PowerShell
echo ================================================================================
echo    STARTING ALL AGENTS ON MAIN SCREEN
echo ================================================================================
echo.

cd /d "%~dp0.."

echo Launching agents on your current/main monitor...
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0start_agents_vscode.ps1"

echo.
echo Done! Check your main screen for agent windows.
pause
