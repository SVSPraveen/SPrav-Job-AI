@echo off
cd /d "%~dp0"
title AI Job Assistant - NextGen UI Launcher
color 0B

echo ==================================================
echo         AUTOJOB AI: NEXT-GEN UI
echo ==================================================
echo.

taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM msedgewebview2.exe >nul 2>&1

if not exist ".venv" (
    echo [ERROR] Virtual environment not found!
    echo Please run the following commands first:
    echo   python -m venv .venv
    echo   .venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

if not exist "config.json" (
    echo [NOTE] config.json not found - it will be auto-created on first API startup.
)

if not exist "logs" mkdir logs

echo Booting SPrav Desktop App Environment...
echo (This will automatically launch the backend, frontend, and auto-install Ollama if needed)
echo.
.venv\Scripts\python.exe desktop_app.py

echo.
echo Closing SPrav Job AI...
taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM msedgewebview2.exe >nul 2>&1
