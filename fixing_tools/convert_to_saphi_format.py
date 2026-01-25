"""
Script to convert all track folders into the 'saphi_ready' format
"""
import os
import shutil
import json

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
DST_DIR = os.path.join(SRC_DIR, 'saphi_ready')
TRACK_INFO_FILE = os.path.join(SRC_DIR, 'track_info.json')

# Load track info if available
track_info = {}
if os.path.exists(TRACK_INFO_FILE):
    with open(TRACK_INFO_FILE, 'r', encoding='utf-8') as f:
        try:
            track_info = json.load(f)
        except Exception:
            track_info = {}

def get_next_folder_number(start=10001):
    n = start
    while True:
        yield n
        n += 1

folder_number_gen = get_next_folder_number()

# Helper to get track metadata
def get_track_metadata(track_folder):
    # Try to load track_info.json from the folder, else fallback to global
    info_path = os.path.join(track_folder, 'track_info.json')
    if os.path.isfile(info_path):
        try:
            with open(info_path, 'r', encoding='utf-8') as f:
                info = json.load(f)
            # Normalize keys: support both formats
            result = {
                'creator': info.get('author', info.get('creator', 'Unknown')),
                'name': info.get('track_name', info.get('name', os.path.basename(track_folder)))
            }
            return result
        except Exception:
            pass
    name = os.path.basename(track_folder)
    creator = track_info.get(name, {}).get('creator', 'Unknown')
    display_name = track_info.get(name, {}).get('name', name)
    return {'creator': creator, 'name': display_name}

# Helper to copy and structure a single track
def process_track(src_folder, dst_folder, metadata):
    os.makedirs(dst_folder, exist_ok=True)
    files = os.listdir(src_folder)
    # Find ANY .vrm and .lev files (handles both matching folder names and subfolders)
    vrm_file = next((f for f in files if f.lower().endswith('.vrm')), None)
    lev_file = next((f for f in files if f.lower().endswith('.lev')), None)
    # Copy and rename to data.vrm/data.lev
    if vrm_file:
        shutil.copy2(os.path.join(src_folder, vrm_file), os.path.join(dst_folder, 'data.vrm'))
    if lev_file:
        shutil.copy2(os.path.join(src_folder, lev_file), os.path.join(dst_folder, 'data.lev'))
    # Write data.json with UTF-8 and ensure_ascii=False
    with open(os.path.join(dst_folder, 'data.json'), 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)
    # Write ghosts/data.json and replays/data.json with UTF-8 and ensure_ascii=False
    for sub in ['ghosts', 'replays']:
        subdir = os.path.join(dst_folder, sub)
        os.makedirs(subdir, exist_ok=True)
        with open(os.path.join(subdir, 'data.json'), 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False)

def is_track_folder(folder):
    # Must contain ANY .vrm and .lev files (handles both matching names and subfolders)
    files = os.listdir(folder)
    has_vrm = any(f.lower().endswith('.vrm') for f in files)
    has_lev = any(f.lower().endswith('.lev') for f in files)
    return has_vrm and has_lev

def main():
    if not os.path.exists(DST_DIR):
        os.makedirs(DST_DIR)
    for entry in os.listdir(SRC_DIR):
        src_path = os.path.join(SRC_DIR, entry)
        if os.path.isdir(src_path) and entry != 'saphi_ready':
            # Check for subfolders
            subfolders = [f for f in os.listdir(src_path)
                          if os.path.isdir(os.path.join(src_path, f))]
            if subfolders:
                for sub in subfolders:
                    sub_path = os.path.join(src_path, sub)
                    if is_track_folder(sub_path):
                        folder_num = next(folder_number_gen)
                        dst_path = os.path.join(DST_DIR, str(folder_num))
                        metadata = get_track_metadata(sub_path)
                        process_track(sub_path, dst_path, metadata)
            else:
                if is_track_folder(src_path):
                    folder_num = next(folder_number_gen)
                    dst_path = os.path.join(DST_DIR, str(folder_num))
                    metadata = get_track_metadata(src_path)
                    process_track(src_path, dst_path, metadata)

if __name__ == '__main__':
    main()
