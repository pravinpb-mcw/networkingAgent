@echo off
title Stop All Agents
echo ================================================================================
echo    STOPPING ALL AGENTS
echo ================================================================================
echo.

echo Terminating agent processes...
taskkill /F /FI "WINDOWTITLE eq Agent 1*" 2>nul
taskkill /F /FI "WINDOWTITLE eq Agent 2*" 2>nul
taskkill /F /FI "WINDOWTITLE eq Agent 3*" 2>nul

echo.
echo ✓ All agent processes stopped
echo.
pause
