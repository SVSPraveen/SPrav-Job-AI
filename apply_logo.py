import shutil
from PIL import Image

src_png = r"C:\My Job APPLYING App\sprav_logo_moe.png"
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
