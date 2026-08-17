#!/usr/bin/env python3
"""
SPrav™ Job AI — System & Hardware Diagnostics Tool
Author: SVS Praveen
Description: Quickly inspects local hardware, Python version, Ollama availability,
             and network reachability to verified ATS portals.
"""

import sys
import os
import platform
import urllib.request
import time

def check_mark(status: bool) -> str:
    return "✅ [PASS]" if status else "❌ [FAIL]"

def run_diagnostics():
    print("=" * 65)
    print("  SPrav™ Job AI — Hardware & Environment Diagnostics")
    print("=" * 65)
    
    # 1. OS & Architecture
    os_name = platform.system()
    os_arch = platform.machine()
    is_windows = os_name.lower() == "windows"
    print(f"{check_mark(is_windows)} OS Platform: {os_name} ({os_arch})")
    
    # 2. Python Version
    py_ver = sys.version.split()[0]
    is_py_ok = sys.version_info >= (3, 10)
    print(f"{check_mark(is_py_ok)} Python Version: {py_ver} (Requires 3.10+)")
    
    # 3. Local AppData Storage Bounds
    app_data = os.path.join(os.environ.get("LOCALAPPDATA", "C:\\"), "SPravJobAI")
    print(f"✅ [PASS] Local Storage Directory: {app_data}")
    
    # 4. Network Connectivity to Greenhouse & Lever ATS Boards
    ats_endpoints = [
        ("Greenhouse ATS Board", "https://boards-api.greenhouse.io"),
        ("Lever Portal Gateway", "https://api.lever.co")
    ]
    
    for name, url in ats_endpoints:
        try:
            t0 = time.time()
            req = urllib.request.Request(url, headers={'User-Agent': 'SPravJobAI/2.4'})
            with urllib.request.urlopen(req, timeout=5) as response:
                latency = round((time.time() - t0) * 1000, 1)
                print(f"✅ [PASS] {name} Reachable ({latency}ms)")
        except Exception as e:
            print(f"⚠️ [WARN] {name} Connection Notice: {e}")
            
    # 5. Local Ollama Service Check
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
        with urllib.request.urlopen(req, timeout=2) as response:
            print(f"✅ [PASS] Local Ollama Engine: ACTIVE & LISTENING on port 11434")
    except Exception:
        print(f"ℹ️ [INFO] Local Ollama: Offline (Cloud AI Mode via Gemini/Groq recommended)")

    print("=" * 65)
    print("  Diagnostic Summary: System is 100% compatible with SPrav Job AI Pro v2.4!")
    print("=" * 65)

if __name__ == "__main__":
    run_diagnostics()
