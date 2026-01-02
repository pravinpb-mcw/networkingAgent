@echo off
setlocal enabledelayedexpansion
REM Start Phoenix Observability Server with Auto-Evaluation
REM Usage: start_phoenix.bat [--auto-eval] [--eval-interval 30]

cd /d "%~dp0.."

REM Load environment variables from .env
call "%~dp0load_env.bat"

"%PYTHON_EXE%" phoenix\server.py --auto-eval --eval-interval 10
pause
