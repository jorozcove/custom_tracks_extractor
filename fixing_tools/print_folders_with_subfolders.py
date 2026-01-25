import os

root_dir = os.path.dirname(os.path.abspath(__file__))

for dirpath, dirnames, filenames in os.walk(root_dir):
    # Skip the root directory itself
    if dirpath == root_dir:
        continue
    if dirnames:
        print(f"Folder: {dirpath} has subfolders: {', '.join(dirnames)}")
