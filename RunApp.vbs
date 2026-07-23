Set WshShell = CreateObject("WScript.Shell")
' Run the Python Native Desktop App silently (0 = hide window)
WshShell.Run ".venv\Scripts\pythonw.exe desktop_app.py", 0, False
