@echo off
REM Run All Agents Together
cd /d "%~dp0"
"..\.wenv\Scripts\python.exe" main.py
pause