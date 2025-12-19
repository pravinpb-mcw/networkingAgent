@echo off
REM Run Agent 2: Nearest AP Calculation Agent
REM Calculates nearest APs for all access points in the network

echo ============================================================
echo Agent 2: Nearest AP Calculation Agent
echo ============================================================
echo.
echo PURPOSE:
echo - Find nearest APs for each access point
echo - Use distance and topology analysis
echo - Store results in nearest_aps.json
echo.
echo ARCHITECTURE:
echo - Agent orchestrates ONLY
echo - Script does ALL distance/ranking calculations
echo - LLM passes parameters to MCP tool
echo.
echo ============================================================
echo.

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo Virtual environment activated
) else if exist .wenv\Scripts\activate.bat (
    call .wenv\Scripts\activate.bat
    echo Virtual environment activated
) else (
    echo No virtual environment found, using system Python
)

REM Run Agent 2
echo Running Agent 2...
echo.
python agents\agent_2_nearest_ap.py

echo.
echo ============================================================
echo Agent 2 execution completed!
echo Check agent_data\nearest_aps.json for results
echo ============================================================
pause