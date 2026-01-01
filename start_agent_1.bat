@echo off
echo Starting Agent 1 - Risk Calculation...
cd /d "%~dp0"
.wenv\Scripts\python.exe agents\agent_1_risk_calculation.py --continuous 10
pause
