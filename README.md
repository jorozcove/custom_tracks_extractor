# CTR Custom Tracks Extractor

This project provides tools to **download** and **extract custom tracks** for Crash Team Racing (CTR) from [ctrcustomtracks.com](https://ctrcustomtracks.com/). It automates the process of fetching, patching, and extracting track files from community patches, making it easy to build a collection of custom tracks.

---

## Features

- **Automated Download:** Scrapes and downloads all available custom tracks and their patches.
- **Patch Extraction:** Applies `.xdelta` patches to a retail ROM and extracts the modified track files.
- **Track Organization:** Saves each track (and its metadata) in a structured folder.
---

## Usage

### 1. Download Custom Tracks

Run the downloader to fetch all available tracks and their patches:

```
python lev_extractor/ct_dowloader.py
```

This will create a `downloaded_tracks/` folder with one subfolder per track.

---

### 2. Extract Track Files

Place your **NTSC-U CTR ROM** (`.bin` file) in the root folder.

Then run the extractor:

```
python lev_extractor/lev_extractor.py
```

Extracted `.lev`, `.vrm`, and `KART.HWL` files will be saved in the `tracks/` folder, organized by track name.

---

## Disclaimer

- The extracted track files are meant **strictly for personal use** specifically, for playing and enjoying the tracks. If you want to use these files for purposes other than playing the tracks, you must ask permission from the original track authors.

---

This project is inspired on this repo: https://github.com/kkv0n/level_extractor/
