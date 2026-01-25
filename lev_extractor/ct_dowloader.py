import os
import json
import requests
from bs4 import BeautifulSoup
from mediafiredl import MediafireDL as MF

headers = {
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0',
    'sec-ch-ua': '"Microsoft Edge";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

def get_page_links(page_number):
    url = f'https://ctrcustomtracks.com/tracks/page/{page_number}'
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    track_info_list = []
    for h4 in soup.find_all("h4", class_="o-posts-grid-post-title"):
        track_name = h4.get_text(strip=True)
        track_meta = h4.find_next_sibling("p", class_="o-posts-grid-post-meta")
        author_name = track_meta.find("a").get_text(strip=True) if track_meta else "unknown"
        post_date = track_meta.find("time").get_text(strip=True) if track_meta else "unknown-date"
        a_tag = h4.find("a", href=True)
        if a_tag:
            track_info = {
                "track_name": track_name,
                "author": author_name,
                "date": post_date,
                "link": a_tag["href"]
            }
            print(f"Found track: {track_name} by {author_name} on {post_date}")
            track_info_list.append(track_info)

    return track_info_list

def get_all_track_info():
    all_tracks = []
    page_number = 1
    while True:
        tracks = get_page_links(page_number)
        if not tracks:
            break
        all_tracks.extend(tracks)
        page_number += 1
    return all_tracks

def get_track_download_links(track_url):
    response = requests.get(track_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    download_links = []

    # Find all anchor tags with href attributes that contain "download" and "patch"
    # NOTE: This sucks but the site structure for download links is inconsistent
    for tag in soup.find_all(href=True):
        text = tag.get_text(strip=True).lower()
        if ("download" in text and "patch" in text):
            download_links.append(tag["href"])

    return download_links

def is_mediafire_url(url):
    """Check if the URL is from Mediafire"""
    return "mediafire.com" in url.lower()

def download_regular_file(url, dest_folder="downloaded_tracks"):
    """Download non-Mediafire files"""
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
        
    local_filename = url.split("/")[-1].split("?")[0]  # Remove query params if any
    local_path = os.path.join(dest_folder, local_filename)
    try:
        with requests.get(url, headers=headers, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(local_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        print(f"Downloaded: {local_filename}")
        return (True, local_path, None)
    except Exception as e:
        return (False, None, str(e))

def sanitize_folder_name(name):
    """Remove invalid characters from folder names"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    return name.strip()

def save_track_info(track_info, folder_path):
    """Save track information as JSON file"""
    json_path = os.path.join(folder_path, "track_info.json")
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(track_info, f, indent=4, ensure_ascii=False)
        print(f"Saved track info to {json_path}")
        return None
    except Exception as e:
        return str(e)

def download_track_files(track_info, base_folder="downloaded_tracks"):
    """Download all files for a track into its own folder"""
    errors = []
    
    # Create sanitized folder name
    folder_name = sanitize_folder_name(track_info["track_name"])
    track_folder = os.path.join(base_folder, folder_name)
    
    if not os.path.exists(track_folder):
        os.makedirs(track_folder)
    
    print(f"\n{'='*60}")
    print(f"Processing: {track_info['track_name']}")
    print(f"Author: {track_info['author']} | Date: {track_info['date']}")
    print(f"Folder: {track_folder}")
    print(f"{'='*60}\n")
    
    # Save track info as JSON
    save_error = save_track_info(track_info, track_folder)
    if save_error:
        error_msg = f"Failed to save track info for '{track_info['track_name']}': {save_error}"
        errors.append(error_msg)
        print(f"✗ {error_msg}")
    
    # Get all download links for this track
    try:
        download_links = get_track_download_links(track_info["link"])
        print(f"Found {len(download_links)} download link(s)")
    except Exception as e:
        error_msg = f"Failed to get download links for '{track_info['track_name']}': {e}"
        errors.append(error_msg)
        print(f"✗ {error_msg}")
        return errors
    
    # Download all files from all links
    for idx, link in enumerate(download_links, 1):
        print(f"\nDownloading file {idx}/{len(download_links)} from: {link}")
        
        if is_mediafire_url(link):
            try:
                local_path = MF.Download(link, output=os.path.abspath(track_folder))
                file_name = os.path.basename(local_path)
                print(f"✓ Downloaded from Mediafire: {file_name}")
            except Exception as e:
                error_msg = f"Mediafire download failed for '{track_info['track_name']}' ({link}): {e}"
                errors.append(error_msg)
                print(f"✗ Failed to download Mediafire link: {e}")
        else:
            success, result, error = download_regular_file(link, track_folder)
            if success:
                print(f"✓ Downloaded successfully")
            else:
                error_msg = f"Regular download failed for '{track_info['track_name']}' ({link}): {error}"
                errors.append(error_msg)
                print(f"✗ Download failed")
    
    return errors
    
if __name__ == "__main__":
    # Get all track info
    all_tracks = get_all_track_info()
    print(f"\nTotal tracks found: {len(all_tracks)}\n")
    
    # Create base tracks folder
    base_folder = "downloaded_tracks"
    if not os.path.exists(base_folder):
        os.makedirs(base_folder)
    
    # Collect all errors
    all_errors = []
    
    # Download files for each track into its own folder
    for idx, track_info in enumerate(all_tracks, 1):
        print(f"\n[{idx}/{len(all_tracks)}] Processing track...")
        try:
            track_errors = download_track_files(track_info, base_folder)
            all_errors.extend(track_errors)
        except Exception as e:
            error_msg = f"Critical error processing track '{track_info['track_name']}': {e}"
            all_errors.append(error_msg)
            print(f"✗ {error_msg}")
            continue
    
    print(f"\n{'='*60}")
    print("All downloads completed!")
    print(f"{'='*60}")
    
    # Print all errors at the end
    if all_errors:
        print(f"\n{'='*60}")
        print(f"ERRORS SUMMARY ({len(all_errors)} total errors)")
        print(f"{'='*60}\n")
        for idx, error in enumerate(all_errors, 1):
            print(f"{idx}. {error}")
        print(f"\n{'='*60}")
    else:
        print("\n✓ No errors encountered during execution!")


        