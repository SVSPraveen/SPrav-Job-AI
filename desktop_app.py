import webview
import time
import subprocess
import sys
import os

# Fix pythonw.exe crashing on print() by redirecting to a file
log_file = open("desktop_app.log", "w", encoding="utf-8")
sys.stdout = log_file
sys.stderr = log_file

from engine.ollama_manager import verify_ollama

import threading

def start_backend():
    print("Starting backend services...")
    
    # Verify Ollama is installed and pull necessary models in the background
    # so it doesn't freeze the UI on first launch!
    threading.Thread(target=verify_ollama, daemon=True).start()
    
    # Hide window for subprocesses on Windows
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    venv_dir = os.path.join(os.path.dirname(__file__), ".venv", "Scripts")
    python_exe = os.path.join(venv_dir, "python.exe")

    # Start API using python -m uvicorn to avoid missing uvicorn.exe
    api_proc = subprocess.Popen(
        [python_exe, "-m", "uvicorn", "api:app", "--host", "127.0.0.1", "--port", "8000"],
        startupinfo=startupinfo,
        creationflags=subprocess.CREATE_NO_WINDOW,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Start Daemon
    daemon_proc = subprocess.Popen(
        [python_exe, "-m", "engine.daemon"],
        startupinfo=startupinfo,
        creationflags=subprocess.CREATE_NO_WINDOW,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Start Frontend (Vite) - REMOVED!
    # The application is now compiled into frontend/dist and served natively by FastAPI
    # This eliminates Node.js from production, resulting in instant booting and lower memory usage.
    
    return api_proc, daemon_proc

def main():
    api_proc, daemon_proc = start_backend()
    
    # Wait briefly for FastAPI to bind
    time.sleep(1)
    
    # Tell Windows this is a separate app, not just a generic 'python.exe' process.
    # This forces the taskbar to use the desktop shortcut's icon (or the one we pass).
    import ctypes
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('sprav.job.ai.app')
    except Exception:
        pass
    
    # Create the native desktop window using Windows Webview2
    window = webview.create_window(
        "SPrav Job AI", 
        "http://127.0.0.1:8000/", 
        text_select=True,
        zoomable=True,
        maximized=True
    )
    
    # Start the UI loop (passing the icon for the window title bar and taskbar)
    import os
    icon_path = os.path.join(os.path.dirname(__file__), 'app_icon_v2.ico')
    webview.start(private_mode=False, icon=icon_path)
    
    # Clean up when the window is closed
    print("Shutting down AI engine...")
    try:
        api_proc.kill()
        daemon_proc.kill()
    except Exception:
        pass
    
    # Hard fallback to kill orphaned Node.js Vite servers
    subprocess.run(["taskkill", "/F", "/IM", "node.exe"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
    # Kill the background daemon/api python instances (our launcher runs via pythonw.exe)
    subprocess.run(["taskkill", "/F", "/IM", "python.exe"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
    
    sys.exit(0)

if __name__ == '__main__':
    main()
