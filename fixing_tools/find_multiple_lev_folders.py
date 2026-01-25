import os

root_dir = os.path.dirname(os.path.abspath(__file__))

for dirpath, dirnames, filenames in os.walk(root_dir):
    lev_files = [f for f in filenames if f.endswith('.lev')]
    if len(lev_files) > 1:
        print(f"Folder: {dirpath} has {len(lev_files)} .lev files: {', '.join(lev_files)}")
