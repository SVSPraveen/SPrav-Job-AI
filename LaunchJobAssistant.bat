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

echo Launching FastAPI Backend Engine...
start "AutoJob API Backend" cmd /c ".venv\Scripts\activate && uvicorn api:app --host 127.0.0.1 --port 8000"

echo Launching SPrav Daemon...
start "SPrav Daemon" cmd /c ".venv\Scripts\activate && python -m engine.daemon"

echo Launching Vite React Frontend...
start "AutoJob UI" cmd /c "cd frontend && npm run dev -- --open"

echo Launching Terminal Dashboard (TUI)...
start "AutoJob Terminal Dashboard" cmd /c ".venv\Scripts\activate && python tui.py"

echo.
echo ==================================================
echo [WARNING] Check knowledge_base/me.json! 
echo If it still contains "Jane Doe", your generated 
echo resumes will be fake! Update it via the UI ASAP.
echo ==================================================
echo.
echo Both servers and the daemon are booting up. 
echo Your browser should open automatically to the new Dashboard!
echo.
echo Keep this window open. Press any key to exit all servers.
pause >nul

taskkill /FI "WindowTitle eq AutoJob API Backend*" /T /F
taskkill /FI "WindowTitle eq SPrav Daemon*" /T /F
taskkill /FI "WindowTitle eq AutoJob UI*" /T /F
taskkill /FI "WindowTitle eq AutoJob Terminal Dashboard*" /T /F
