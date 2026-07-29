import webview
import time
import subprocess
import sys
import os
import threading
from engine.utils import get_resource_path, get_data_dir, init_data_dir

try:
    # CRITICAL: Must be set before any module imports playwright
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(get_data_dir(), "playwright_browsers")
except Exception as e:
    with open(os.path.join(os.environ.get("LOCALAPPDATA", "C:\\"), "SPravJobAI", "early_crash.log"), "w") as f:
        f.write(str(e))



def _kill_orphaned_webview2(profile_dir: str):
    """Kill msedgewebview2.exe processes whose --user-data-dir matches our profile path.

    pywebview passes storage_path to WebView2 as --user-data-dir=<profile_dir>.
    Matching on that path correctly identifies only our WebView2 subprocesses,
    not any other Edge/WebView2 instances the user has open.
    """
    try:
        escaped = profile_dir.replace("\\", "\\\\")
        ps = (
            "Get-CimInstance Win32_Process -Filter \"Name='msedgewebview2.exe'\" | "
            f"Where-Object {{ $_.CommandLine -match '{escaped}' }} | "
            "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=8
        )
    except Exception as e:
        print(f"[Cleanup] WebView2 cleanup error: {e}")


def run_api():

    import uvicorn
    from api import app
    uvicorn.run(app, host="127.0.0.1", port=8000)

def run_daemon_worker():
    # Provide valid file descriptors for sys.stdin/out/err to avoid OS Error 6 inside subprocess.Popen (Playwright)
    # The parent process hooks stdout/stderr, but we must make sure python sees them as valid or patch them.
    # We'll just patch sys.stdin to os.devnull.
    import sys, os
    sys.stdin = open(os.devnull, "r")
    
    # PILOT TEST
    try:
        from engine.jd_extractor import fetch_jd_text
        print("Testing jd_extractor...")
        res = fetch_jd_text("https://example.com")
        print(f"Test scrape result: {res}")
    except Exception as e:
        print(f"Test scrape crashed: {e}")
    sys.stdout.flush()

    from engine.daemon import run_daemon
    run_daemon()

def check_and_install_playwright():
    browser_path = os.environ["PLAYWRIGHT_BROWSERS_PATH"]
    has_chromium = False
    if os.path.exists(browser_path):
        for item in os.listdir(browser_path):
            if item.startswith("chromium"):
                has_chromium = True
                break
    
    if not has_chromium:
        print("[Install] Playwright Chromium not found. Downloading in background...")
        executable = os.path.abspath(sys.executable)
        exe_dir = os.path.dirname(executable)
        cmd_prefix = [executable] if getattr(sys, 'frozen', False) else [executable, os.path.abspath(__file__)]
        subprocess.run(
            cmd_prefix + ["--install-browser"],
            creationflags=subprocess.CREATE_NO_WINDOW,
            cwd=exe_dir
        )
        print("[Install] Playwright Chromium installed.")

def start_backend():
    print("Starting backend services...")
    from engine.ollama_manager import verify_ollama
    threading.Thread(target=verify_ollama, daemon=True).start()
    threading.Thread(target=check_and_install_playwright, daemon=True).start()
    
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    # Always resolve the absolute path to the bundled .exe so that launching
    # from a shortcut with a different CWD doesn't cause sys.executable to
    # point at the venv python instead of the PyInstaller bundle.
    executable = os.path.abspath(sys.executable)
    # The exe must be invoked from its own directory so PyInstaller's bootloader
    # can find its _internal/ folder (DLLs, data files, etc.).
    exe_dir = os.path.dirname(executable)
    
    api_log = open(os.path.join(get_data_dir(), "api.log"), "w", encoding="utf-8")
    daemon_log = open(os.path.join(get_data_dir(), "daemon.log"), "w", encoding="utf-8")

    # DEBUG: log the resolved executable so we can verify sys.executable behavior
    api_log.write(f"[DEBUG] sys.executable      = {sys.executable}\n")
    api_log.write(f"[DEBUG] os.path.abspath(exe) = {executable}\n")
    api_log.write(f"[DEBUG] exe_dir              = {exe_dir}\n")
    api_log.write(f"[DEBUG] os.getcwd()          = {os.getcwd()}\n")
    api_log.write(f"[DEBUG] frozen               = {getattr(sys, 'frozen', False)}\n")
    api_log.flush()
    
    # If unfrozen, we need to invoke python with the script name
    is_frozen = getattr(sys, 'frozen', False)
    cmd_prefix = [executable] if is_frozen else [executable, os.path.abspath(__file__)]
    sub_cwd = exe_dir if is_frozen else os.path.dirname(os.path.abspath(__file__))
    
    api_proc = subprocess.Popen(
        cmd_prefix + ["--api"],
        startupinfo=startupinfo,
        creationflags=subprocess.CREATE_NO_WINDOW,
        stdin=subprocess.DEVNULL,
        stdout=api_log,
        stderr=subprocess.STDOUT,
        env=env,
        cwd=exe_dir
    )

    daemon_proc = subprocess.Popen(
        cmd_prefix + ["--daemon"],
        startupinfo=startupinfo,
        creationflags=subprocess.CREATE_NO_WINDOW,
        stdin=subprocess.DEVNULL,
        stdout=daemon_log,
        stderr=subprocess.STDOUT,
        env=env,
        cwd=exe_dir
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
    
    # Kill any orphaned WebView2 processes from previous sessions that might be
    # holding the profile directory or conflicting with a new WebView2 init.
    # Match by storage_path pattern in command line (pywebview passes it as --user-data-dir).
    _kill_orphaned_webview2(profile_dir)
    
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
        
        # Kill all WebView2 processes associated with our profile directory
        _kill_orphaned_webview2(profile_dir)
        
        app_dir = os.path.dirname(os.path.abspath(__file__))
        cleanup_node_ps1 = f"Get-CimInstance Win32_Process -Filter \"Name='node.exe'\" | Where-Object {{ $_.CommandLine -like '*{app_dir}*' }} | ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force }}"
        subprocess.run(["powershell", "-Command", cleanup_node_ps1], creationflags=subprocess.CREATE_NO_WINDOW)
        
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
    elif "--install-browser" in sys.argv:
        log_file = open(os.path.join(get_data_dir(), "install_browser.log"), "w", encoding="utf-8")
        print("Starting playwright install...", file=log_file)
        log_file.flush()
        try:
            from playwright._impl._driver import compute_driver_executable, get_driver_env
            driver, cli = compute_driver_executable()
            env = get_driver_env()
            subprocess.run(
                [driver, cli, 'install', 'chromium'],
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=log_file,
                stderr=subprocess.STDOUT
            )
            print("Playwright install finished.", file=log_file)
        except Exception as e:
            print(f"Exception during playwright install: {e}", file=log_file)
        finally:
            log_file.close()
        sys.exit(0)
    else:
        main()
