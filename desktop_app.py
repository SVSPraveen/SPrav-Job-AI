import webview
import time
import subprocess
import sys
import os

def start_backend():
    print("Starting backend services...")
    # Hide window for subprocesses on Windows
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    venv_dir = os.path.join(os.path.dirname(__file__), ".venv", "Scripts")
    python_exe = os.path.join(venv_dir, "python.exe")

    # Start API using python -m uvicorn to avoid missing uvicorn.exe
    api_proc = subprocess.Popen(
        [python_exe, "-m", "uvicorn", "api:app", "--host", "127.0.0.1", "--port", "8000"],
        startupinfo=startupinfo,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    # Start Daemon
    daemon_proc = subprocess.Popen(
        [python_exe, "-m", "engine.daemon"],
        startupinfo=startupinfo,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    # Start Frontend (Vite)
    # Using shell=True for npm, but CREATE_NO_WINDOW ensures it stays completely hidden
    front_proc = subprocess.Popen(
        "cd frontend && npm run dev",
        shell=True,
        startupinfo=startupinfo,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    return api_proc, daemon_proc, front_proc

def main():
    api_proc, daemon_proc, front_proc = start_backend()
    
    # Wait for Vite dev server to boot and bind
    time.sleep(4)
    
    # Create the native desktop window using Windows Webview2
    window = webview.create_window(
        "SPrav Job AI", 
        "http://localhost:5173", 
        width=1280, 
        height=850,
        text_select=True,
        zoomable=True
    )
    
    # Start the UI loop
    webview.start(private_mode=False)
    
    # Clean up when the window is closed
    print("Shutting down AI engine...")
    try:
        api_proc.kill()
        daemon_proc.kill()
        front_proc.kill()
    except Exception:
        pass
    
    # Hard fallback to kill orphaned Node.js Vite servers
    subprocess.run(["taskkill", "/F", "/IM", "node.exe"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
    # Kill the background daemon/api python instances (our launcher runs via pythonw.exe)
    subprocess.run(["taskkill", "/F", "/IM", "python.exe"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
    
    sys.exit(0)

if __name__ == '__main__':
    main()
