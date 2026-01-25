import os

# Set the root directory to scan
root_dir = os.path.dirname(os.path.abspath(__file__))

# Required file extensions and filenames
required_exts = ['.lev', '.vrm', '.xdelta']
required_files = ['track_info.json']

missing_folders = []


for dirpath, dirnames, filenames in os.walk(root_dir):
    # Skip the root directory itself
    if dirpath == root_dir:
        continue
    # Skip folders that have subfolders
    if dirnames:
        continue

    has_lev = any(f.endswith('.lev') for f in filenames)
    has_vrm = any(f.endswith('.vrm') for f in filenames)
    has_xdelta = any(f.endswith('.xdelta') for f in filenames)
    has_track_info = 'track_info.json' in filenames

    missing = []
    if not has_lev:
        missing.append('.lev')
    if not has_vrm:
        missing.append('.vrm')
    if not has_xdelta:
        missing.append('.xdelta')
    if not has_track_info:
        missing.append('track_info.json')

    if missing:
        missing_folders.append((dirpath, missing))

# Print results
for folder, missing in missing_folders:
    print(f"Folder: {folder} is missing: {', '.join(missing)}")