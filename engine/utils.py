import sys
import os
import shutil

def get_resource_path(relative_path):
    # Get absolute path to resource, works for dev and for PyInstaller
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def get_node_path():
    # Resolves the path to the bundled node.exe in a PyInstaller build.
    try:
        if hasattr(sys, '_MEIPASS'):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        # Check PyInstaller Playwright internal bundle path first
        node_exe_internal = os.path.join(base_path, "_internal", "playwright", "driver", "node.exe")
        if os.path.exists(node_exe_internal):
            return node_exe_internal
            
        node_exe = os.path.join(base_path, "nodejs", "node.exe")
        if os.path.exists(node_exe):
            return node_exe
    except Exception:
        pass
    return "node"

def get_data_dir():
    # Returns the absolute path to the mutable user data directory.
    local_app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    return os.path.join(local_app_data, "SPravJobAI")

def init_data_dir():
    # Initializes the user data directory structure on first launch.
    data_dir = get_data_dir()
    os.makedirs(data_dir, exist_ok=True)
    
    os.makedirs(os.path.join(data_dir, "knowledge_base"), exist_ok=True)
    os.makedirs(os.path.join(data_dir, "resumes"), exist_ok=True)
    os.makedirs(os.path.join(data_dir, "output"), exist_ok=True)
    os.makedirs(os.path.join(data_dir, "snapshots"), exist_ok=True)
    os.makedirs(os.path.join(data_dir, "webview_profile"), exist_ok=True)

    cwd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    migration_files = [
        "jobs.db", 
        "users.db", 
        "config.json", 
        "blacklist.txt", 
        "watchlist.json", 
        ".env",
        os.path.join("knowledge_base", "me.json"),
        os.path.join("knowledge_base", "scope.json")
    ]
    
    for rel_path in migration_files:
        src = os.path.join(cwd, rel_path)
        dst = os.path.join(data_dir, rel_path)
        if os.path.exists(src):
            if not os.path.exists(dst) or os.path.getmtime(src) > os.path.getmtime(dst):
                try:
                    shutil.copy2(src, dst)
                    print(f"[Init] Migrated/Synced {rel_path} to data directory.")
                except Exception as e:
                    pass

    cwd_resumes = os.path.join(cwd, "resumes")
    data_resumes = os.path.join(data_dir, "resumes")
    if os.path.exists(cwd_resumes) and not os.listdir(data_resumes):
        for f in os.listdir(cwd_resumes):
            try:
                shutil.copy2(os.path.join(cwd_resumes, f), os.path.join(data_resumes, f))
            except Exception:
                pass
                
    seeds = {
        "config.example.json": "config.json",
        "watchlist.example.json": "watchlist.json",
        os.path.join("knowledge_base", "me.example.json"): os.path.join("knowledge_base", "me.json"),
        os.path.join("knowledge_base", "scope.example.json"): os.path.join("knowledge_base", "scope.json")
    }
    
    for example, target in seeds.items():
        dst = os.path.join(data_dir, target)
        if not os.path.exists(dst):
            src = get_resource_path(example)
            if os.path.exists(src):
                try:
                    shutil.copy2(src, dst)
                    print(f"[Init] Seeded {target} from example template.")
                except Exception as e:
                    pass