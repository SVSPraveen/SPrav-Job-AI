import time
import subprocess
import os
try:
    from PIL import ImageGrab
except ImportError:
    os.system('.venv\\Scripts\\python.exe -m pip install Pillow')
    from PIL import ImageGrab

# Launch the app
exe_path = r"dist\SPravJobAI\SPravJobAI.exe"
print("Launching app...")
p = subprocess.Popen([exe_path])

print("Waiting 15 seconds for app to fully load and render...")
time.sleep(15)

print("Taking screenshot...")
img = ImageGrab.grab()
screenshot_path = r"C:\Users\svspr\.gemini\antigravity-ide\brain\ab800fc1-8811-4105-99a9-a7b64e4d6258\settings_github_token.png"
img.save(screenshot_path)
print(f"Screenshot saved to {screenshot_path}")

print("Killing app...")
p.terminate()
time.sleep(1)
if p.poll() is None:
    p.kill()
os.system('taskkill /F /IM msedgewebview2.exe /T >nul 2>&1')
print("Done.")
