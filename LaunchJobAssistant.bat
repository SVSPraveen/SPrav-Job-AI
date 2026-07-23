@echo off
title AI Job Assistant - NextGen UI Launcher
color 0B

echo ==================================================
echo         AUTOJOB AI: NEXT-GEN UI
echo ==================================================
echo.

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

echo Launching FastAPI Backend Engine...
start /B "" cmd /c ".venv\Scripts\activate && uvicorn api:app --host 127.0.0.1 --port 8000 > logs\api.log 2>&1"

echo Launching SPrav Daemon...
start /B "" cmd /c ".venv\Scripts\activate && python -m engine.daemon > logs\daemon.log 2>&1"

echo Launching Vite React Frontend...
start /B "" cmd /c "cd frontend && npm run dev > ..\logs\frontend.log 2>&1"

echo.
echo ==================================================
echo [WARNING] Check knowledge_base/me.json! 
echo If it still contains "Jane Doe", your generated 
echo resumes will be fake! Update it via the UI ASAP.
echo ==================================================
echo.
echo Both servers and the daemon are booting up. 
echo Launching SPrav Desktop App...
timeout /t 3 /nobreak >nul
start msedge --app="http://localhost:5173" --profile-directory="Default"
echo.
echo Keep this window open. Close it to shut down SPrav Job AI.
pause >nul

taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
