@echo off
REM Helper script to load environment variables from .env file

set "ENV_FILE=%~dp0..\.env"

if not exist "%ENV_FILE%" (
    echo Error: .env file not found at %ENV_FILE%
    exit /b 1
)

REM Read .env file and set variables
for /f "usebackq tokens=1,* delims==" %%a in ("%ENV_FILE%") do (
    set "line=%%a"
    REM Skip comments and empty lines
    if not "!line:~0,1!"=="#" if not "%%a"=="" (
        set "key=%%a"
        set "value=%%b"
        
        REM Remove quotes if present
        set "value=!value:"=!"
        
        REM Expand variables in value (replace ${VAR} with actual value)
        call :ExpandVariables "!value!" expandedValue
        
        REM Set the environment variable
        set "%%a=!expandedValue!"
    )
)

exit /b 0

:ExpandVariables
setlocal enabledelayedexpansion
set "result=%~1"

REM Replace ${BASE_PATH} with actual BASE_PATH value
set "result=!result:${BASE_PATH}=%BASE_PATH%!"
set "result=!result:${VENV_PATH}=%VENV_PATH%!"
set "result=!result:${PROJECT_ROOT}=%PROJECT_ROOT%!"

endlocal & set "%~2=%result%"
exit /b 0
