$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("C:\Users\svspr\OneDrive\Desktop\SPrav JOB.lnk")
$Shortcut.IconLocation = "C:\My Job APPLYING App\app_icon_v2.ico"
$Shortcut.Save()
Write-Host "Shortcut updated successfully."
