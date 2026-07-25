import webview
import time
import subprocess
import sys
import os
import threading
from engine.utils import get_resource_path, get_data_dir, init_data_dir

def run_api():
    import uvicorn
    from api import app
    uvicorn.run(app, host="127.0.0.1", port=8000)

def run_daemon_worker():
    from engine.daemon import run_daemon
    run_daemon()

def start_backend():
    print("Starting backend services...")
    from engine.ollama_manager import verify_ollama
    threading.Thread(target=verify_ollama, daemon=True).start()
    
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    # In PyInstaller, sys.executable is the .exe itself!
    executable = sys.executable
    
    api_log = open(os.path.join(get_data_dir(), "api.log"), "w", encoding="utf-8")
    daemon_log = open(os.path.join(get_data_dir(), "daemon.log"), "w", encoding="utf-8")
    
    api_proc = subprocess.Popen(
        [executable, "--api"],
        startupinfo=startupinfo,
        creationflags=subprocess.CREATE_NO_WINDOW,
        stdin=subprocess.DEVNULL,
        stdout=api_log,
        stderr=subprocess.STDOUT,
        env=env
    )

    daemon_proc = subprocess.Popen(
        [executable, "--daemon"],
        startupinfo=startupinfo,
        creationflags=subprocess.CREATE_NO_WINDOW,
        stdin=subprocess.DEVNULL,
        stdout=daemon_log,
        stderr=subprocess.STDOUT,
        env=env
    )
    
    return api_proc, daemon_proc, api_log, daemon_log

def main():
    log_file = open(os.path.join(get_data_dir(), "desktop_app.log"), "w", encoding="utf-8")
    sys.stdout = log_file
    sys.stderr = log_file
    
    api_proc, daemon_proc, api_log, daemon_log = start_backend()
    
    time.sleep(1)
    
    import ctypes
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('sprav.job.ai.app')
    except Exception:
        pass
    
    window = webview.create_window(
        "SPrav Job AI", 
        "http://127.0.0.1:8000/", 
        text_select=True,
        zoomable=True,
        maximized=True
    )
    
    icon_path = get_resource_path('app_icon_v2.ico')
    profile_dir = os.path.join(get_data_dir(), "webview_profile")
    
    cleanup_ps1 = f"Get-CimInstance Win32_Process -Filter \"Name='msedgewebview2.exe'\" | Where-Object {{ $_.CommandLine -match 'SPravJobAI_WebView' }} | ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force }}"
    subprocess.run(["powershell", "-Command", cleanup_ps1], creationflags=subprocess.CREATE_NO_WINDOW)
    
    try:
        webview.start(private_mode=False, icon=icon_path, storage_path=profile_dir)
    finally:
        print("Shutting down AI engine...")
        try:
            api_proc.kill()
            daemon_proc.kill()
            api_log.close()
            daemon_log.close()
        except Exception:
            pass
        
        app_dir = os.path.dirname(os.path.abspath(__file__))
        cleanup_node_ps1 = f"Get-CimInstance Win32_Process -Filter \"Name='node.exe'\" | Where-Object {{ $_.CommandLine -like '*{app_dir}*' }} | ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force }}"
        subprocess.run(["powershell", "-Command", cleanup_node_ps1], creationflags=subprocess.CREATE_NO_WINDOW)
        
        subprocess.run(["powershell", "-Command", cleanup_ps1], creationflags=subprocess.CREATE_NO_WINDOW)
        
        sys.exit(0)

if __name__ == '__main__':
    # Add multiprocessing freeze_support just in case
    import multiprocessing
    multiprocessing.freeze_support()
    
    init_data_dir()
    
    if "--api" in sys.argv:
        run_api()
    elif "--daemon" in sys.argv:
        run_daemon_worker()
    elif "--cli" in sys.argv:
        import main
        sys.argv.remove("--cli")
        main.main()
    else:
        main()
