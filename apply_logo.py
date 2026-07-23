import shutil
from PIL import Image

src_png = r"C:\Users\svspr\.gemini\antigravity-ide\brain\e4f7e4d9-c056-431d-9b68-b5b6b04951b0\sprav_logo_v3_1784834461215.png"
dst_favicon = r"C:\My Job APPLYING App\frontend\public\favicon.png"
dst_ico = r"C:\My Job APPLYING App\app_icon.ico"

# Copy for frontend
shutil.copy(src_png, dst_favicon)
print("Saved frontend favicon.png")

# Convert to multi-size ICO for Windows shortcut
img = Image.open(src_png)
# Generate multiple sizes for the ICO file for the best taskbar/desktop scaling
icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
img.save(dst_ico, format="ICO", sizes=icon_sizes)
print("Generated Windows app_icon.ico")
