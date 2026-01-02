@echo off
REM Start Phoenix Observability Server with Auto-Evaluation
REM Usage: start_phoenix.bat [--auto-eval] [--eval-interval 30]

cd /d "%~dp0.."
call "../.wenv/Scripts/activate.bat"
python phoenix\server.py --auto-eval --eval-interval 10
pause
