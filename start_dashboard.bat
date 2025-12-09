@echo off
echo Starting Network Observability Dashboard...
set PYTHONPATH=%PYTHONPATH%;%CD%
streamlit run dashboard.py
pause
