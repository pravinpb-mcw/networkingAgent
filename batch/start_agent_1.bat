@echo off
setlocal enabledelayedexpansion
echo Starting Agent 1 - Risk Calculation...
cd /d "%~dp0.."

REM Load environment variables from .env
call "%~dp0load_env.bat"

"%PYTHON_EXE%" agents\agent_1_risk_calculation.py --continuous 10
pause
