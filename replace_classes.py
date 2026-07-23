import os

directory = r"C:\My Job APPLYING App\frontend\src"

def replace_in_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "glass-card" in content:
        content = content.replace("glass-card", "premium-card")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")

for root, _, files in os.walk(directory):
    for file in files:
        if file.endswith(".jsx") or file.endswith(".css"):
            replace_in_file(os.path.join(root, file))
