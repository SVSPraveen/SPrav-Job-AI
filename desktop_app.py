import webview
import time
import subprocess
import sys
import os

# Fix pythonw.exe crashing on print() by redirecting to a file
log_file = open("desktop_app.log", "w", encoding="utf-8")
sys.stdout = log_file
sys.stderr = log_file

api_log = open("api.log", "w", encoding="utf-8")
daemon_log = open("daemon.log", "w", encoding="utf-8")

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
    
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    venv_dir = os.path.join(os.path.dirname(__file__), ".venv", "Scripts")
    python_exe = os.path.join(venv_dir, "python.exe")

    # Start API using python -m uvicorn to avoid missing uvicorn.exe
    api_proc = subprocess.Popen(
        [python_exe, "-m", "uvicorn", "api:app", "--host", "127.0.0.1", "--port", "8000"],
        startupinfo=startupinfo,
        creationflags=subprocess.CREATE_NO_WINDOW,
        stdin=subprocess.DEVNULL,
        stdout=api_log,
        stderr=subprocess.STDOUT,
        env=env
    )

    # Start Daemon
    daemon_proc = subprocess.Popen(
        [python_exe, "-m", "engine.daemon"],
        startupinfo=startupinfo,
        creationflags=subprocess.CREATE_NO_WINDOW,
        stdin=subprocess.DEVNULL,
        stdout=daemon_log,
        stderr=subprocess.STDOUT,
        env=env
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
    
    import os
    icon_path = os.path.join(os.path.dirname(__file__), 'app_icon_v2.ico')
    
    # Isolate WebView2 profile to avoid locking conflicts with other pywebview apps
    # We use a dedicated folder in LOCALAPPDATA
    profile_dir = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "SPravJobAI_WebView")
    
    # TARGETED ZOMBIE CLEANUP: Kill only webview processes that are locking OUR profile directory
    # This ensures that even if the app crashed previously, the lock is cleared before we start!
    cleanup_ps1 = f"Get-CimInstance Win32_Process -Filter \"Name='msedgewebview2.exe'\" | Where-Object {{ $_.CommandLine -match 'SPravJobAI_WebView' }} | ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force }}"
    subprocess.run(["powershell", "-Command", cleanup_ps1], creationflags=subprocess.CREATE_NO_WINDOW)
    
    try:
        # Start the UI loop (passing the icon for the window title bar and taskbar)
        webview.start(private_mode=False, icon=icon_path, storage_path=profile_dir)
    finally:
        # Clean up when the window is closed
        print("Shutting down AI engine...")
        try:
            api_proc.kill()
            daemon_proc.kill()
        except Exception:
            pass
        
        # Hard fallback to kill orphaned Node.js Vite servers
        subprocess.run(["taskkill", "/F", "/IM", "node.exe"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
        # Kill orphaned WebView2 processes for OUR app to prevent locking errors on next launch
        subprocess.run(["powershell", "-Command", cleanup_ps1], creationflags=subprocess.CREATE_NO_WINDOW)
        
        sys.exit(0)

if __name__ == '__main__':
    main()
