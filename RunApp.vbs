Set WshShell = CreateObject("WScript.Shell")
' Run the Python Native Desktop App (pythonw hides the console, 1 allows the GUI to show)
WshShell.Run ".venv\Scripts\pythonw.exe desktop_app.py", 1, False
