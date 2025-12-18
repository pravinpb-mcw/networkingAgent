@echo off
echo Starting Phoenix with PERSISTENT storage...
echo Database will be saved in .phoenix\phoenix_traces.db
echo.

cd /d "%~dp0"
"E:\network of obserbility\.wenv\Scripts\python.exe" phoenix_persistent.py --auto-eval

pause
