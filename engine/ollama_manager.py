import os
import sys
import subprocess
import urllib.request
import time

REQUIRED_MODELS = [
    "qwen2.5:7b-instruct",
    "deepseek-r1:7b",
    "bespoke-minicheck",
    "hermes3:8b",
    "nomic-embed-text"
]

def get_ollama_path():
    """Returns the absolute path to ollama.exe if present, otherwise just 'ollama' for PATH resolution."""
    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            abs_path = os.path.join(local_app_data, "Programs", "Ollama", "ollama.exe")
            if os.path.exists(abs_path):
                return abs_path
    return "ollama"

def is_ollama_installed() -> bool:
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        result = subprocess.run(
            [get_ollama_path(), "--version"], 
            capture_output=True, 
            text=True, 
            startupinfo=startupinfo,
            stdin=subprocess.DEVNULL
        )
        return "ollama version" in result.stdout.lower()
    except Exception:
        return False

def install_ollama_windows():
    print("[Ollama Manager] Ollama is not installed. Downloading OllamaSetup.exe...")
    installer_path = os.path.join(os.environ.get("TEMP", "C:\\Temp"), "OllamaSetup.exe")
    try:
        urllib.request.urlretrieve("https://ollama.com/download/OllamaSetup.exe", installer_path)
        print("[Ollama Manager] Download complete. Launching installer...")
        # Run installer and wait for it to finish
        subprocess.run([installer_path], check=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[Ollama Manager] Installation completed.")
        
        # Give the background service a moment to start
        time.sleep(5)
    except Exception as e:
        print(f"[Ollama Manager] Failed to install Ollama automatically: {e}")
        print("Please install it manually from https://ollama.com")

def ensure_ollama_running():
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    print("[Ollama Manager] Checking if Ollama server is awake...")
    try:
        result = subprocess.run(
            [get_ollama_path(), "list"], 
            capture_output=True, 
            text=True, 
            startupinfo=startupinfo,
            stdin=subprocess.DEVNULL
        )
        if "could not connect" in result.stderr.lower() or "error" in result.stderr.lower():
            print("[Ollama Manager] Ollama is asleep. Waking it up in the background...")
            subprocess.Popen(
                [get_ollama_path(), "serve"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            time.sleep(3) # Give it time to boot
    except Exception as e:
        print(f"[Ollama Manager] Error checking Ollama server state: {e}")
def check_and_pull_models():
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    for model in REQUIRED_MODELS:
        print(f"[Ollama Manager] Checking model: {model}...")
        try:
            # Check if model exists
            result = subprocess.run(
                [get_ollama_path(), "list"], 
                capture_output=True, 
                text=True, 
                startupinfo=startupinfo,
                stdin=subprocess.DEVNULL
            )
            if model not in result.stdout:
                print(f"[Ollama Manager] Pulling {model}... This may take a while depending on your internet speed.")
                
                if sys.platform == "win32":
                    # Use 'start' to spawn a completely detached console window with a title and an explanation
                    # This avoids all handle inheritance issues and ensures the progress bar renders correctly.
                    cmd_str = f'start "SPrav AI Downloader" cmd /c "echo [SPrav AI Engine] && echo Downloading required model: {model}... && echo This may take a few minutes depending on your internet connection. && echo. && "{get_ollama_path()}" pull {model}"'
                    subprocess.run(cmd_str, shell=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    subprocess.run([get_ollama_path(), "pull", model], stdin=subprocess.DEVNULL)
            else:
                print(f"[Ollama Manager] Model {model} is already installed.")
        except Exception as e:
            print(f"[Ollama Manager] Failed to pull model {model}: {e}")

def verify_ollama():
    if not is_ollama_installed():
        if sys.platform == "win32":
            install_ollama_windows()
        else:
            print("[Ollama Manager] Please install Ollama from https://ollama.com")
            
    # Check models after ensuring installation
    if is_ollama_installed():
        ensure_ollama_running()
        check_and_pull_models()
