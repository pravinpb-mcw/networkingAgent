@echo off
setlocal enabledelayedexpansion
echo ================================================================================
echo    TESTING .ENV CONFIGURATION
echo ================================================================================
echo.

cd /d "%~dp0.."

REM Load environment variables from .env
call "%~dp0load_env.bat"

echo Environment Variables Loaded:
echo.
echo BASE_PATH = %BASE_PATH%
echo VENV_PATH = %VENV_PATH%
echo PYTHON_EXE = %PYTHON_EXE%
echo VENV_ACTIVATE = %VENV_ACTIVATE%
echo PROJECT_ROOT = %PROJECT_ROOT%
echo.

echo Checking if Python executable exists...
if exist "%PYTHON_EXE%" (
    echo [OK] Python found at: %PYTHON_EXE%
    echo.
    echo Python Version:
    "%PYTHON_EXE%" --version
) else (
    echo [ERROR] Python not found at: %PYTHON_EXE%
)

echo.
echo ================================================================================
pause
