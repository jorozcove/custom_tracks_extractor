import os
import re
print("Starting to fix invalid names...")

# Define the root directory
root_dir = os.path.dirname(os.path.abspath(__file__))

# Define invalid characters and their replacements
replacements = {
    '’': "'",
    '“': '"',
    '”': '"',
    '–': '-',
    '—': '-',
    '…': '...',
    '‘': "'",
    # Add more replacements as needed
}

# Windows forbidden characters for file/folder names
forbidden = r'[<>:"/\\|?*]'

# Function to clean a name
def clean_name(name):
    for bad, good in replacements.items():
        name = name.replace(bad, good)
    name = re.sub(forbidden, '', name)
    return name

for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
    # Fix track_name in track_info.json if present
    if 'track_info.json' in filenames:
        json_path = os.path.join(dirpath, 'track_info.json')
        try:
            import json
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if 'track_name' in data:
                cleaned = clean_name(data['track_name'])
                if cleaned != data['track_name']:
                    data['track_name'] = cleaned
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
                    print(f"Fixed track_name in: {json_path}")
        except Exception as e:
            print(f"Error fixing track_name in {json_path}: {e}")
    # Rename files
    for filename in filenames:
        new_filename = clean_name(filename)
        if new_filename != filename:
            src = os.path.join(dirpath, filename)
            dst = os.path.join(dirpath, new_filename)
            print(f"Renaming file: {src} -> {dst}")
            os.rename(src, dst)
    # Rename directories
    for dirname in dirnames:
        new_dirname = clean_name(dirname)
        if new_dirname != dirname:
            src = os.path.join(dirpath, dirname)
            dst = os.path.join(dirpath, new_dirname)
            print(f"Renaming folder: {src} -> {dst}")
            os.rename(src, dst)
