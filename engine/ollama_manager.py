import os
import sys
import subprocess
import urllib.request
import time

REQUIRED_MODELS = [
    "qwen2.5:7b-instruct",
    "deepseek-r1:7b",
    "magnum-v4:9b",
    "llama3.1:8b",
    "nomic-embed-text"
]

def is_ollama_installed() -> bool:
    try:
        # Hide the console window on Windows
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        result = subprocess.run(
            ["ollama", "--version"], 
            capture_output=True, 
            text=True, 
            startupinfo=startupinfo
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
        subprocess.run([installer_path], check=True)
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
        # Check if server is reachable
        result = subprocess.run(
            ["ollama", "list"], 
            capture_output=True, 
            text=True, 
            startupinfo=startupinfo
        )
        if "could not connect" in result.stderr.lower() or "error" in result.stderr.lower():
            print("[Ollama Manager] Ollama is asleep. Waking it up in the background...")
            # Start the server in the background
            subprocess.Popen(
                ["ollama", "serve"],
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
                ["ollama", "list"], 
                capture_output=True, 
                text=True, 
                startupinfo=startupinfo
            )
            if model not in result.stdout:
                print(f"[Ollama Manager] Pulling {model}... This may take a while depending on your internet speed.")
                # We use Popen so it prints to the console directly for progress (if visible)
                subprocess.run(["ollama", "pull", model])
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
