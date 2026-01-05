@echo off
setlocal enabledelayedexpansion
REM Helper script to load environment variables from .env file

set "ENV_FILE=%~dp0..\.env"

if not exist "%ENV_FILE%" (
    echo Error: .env file not found at %ENV_FILE%
    exit /b 1
)

REM First pass - read BASE_PATH
for /f "usebackq tokens=1,* delims==" %%a in ("%ENV_FILE%") do (
    if "%%a"=="BASE_PATH" (
        set "BASE_PATH=%%b"
        REM Remove quotes and trim spaces
        set "BASE_PATH=!BASE_PATH:"=!"
        for /f "tokens=* delims= " %%x in ("!BASE_PATH!") do set "BASE_PATH=%%x"
    )
)

REM Calculate derived paths with proper quoting
set "VENV_PATH=!BASE_PATH!\.wenv"
set "PYTHON_EXE=!VENV_PATH!\Scripts\python.exe"
set "PROJECT_ROOT=!BASE_PATH!\networkingAgent"

REM Export to parent shell with quotes preserved
endlocal & (
    set "BASE_PATH=%BASE_PATH%"
    set "VENV_PATH=%VENV_PATH%"
    set "PYTHON_EXE=%PYTHON_EXE%"
    set "PROJECT_ROOT=%PROJECT_ROOT%"
)

exit /b 0
