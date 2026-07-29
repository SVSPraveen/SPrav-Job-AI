import subprocess

try:
    p = subprocess.run(['.venv\\Scripts\\python.exe', '-v', 'desktop_app.py', '--daemon'], capture_output=True, text=True, timeout=5)
    print(p.stderr)
except subprocess.TimeoutExpired as e:
    print("TIMEOUT")
    if e.stderr:
        # Print the last 50 lines of stderr to see where it hung
        lines = e.stderr.decode('utf-8') if isinstance(e.stderr, bytes) else e.stderr
        print('\n'.join(lines.split('\n')[-50:]))
