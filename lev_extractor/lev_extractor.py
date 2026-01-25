import os
import sys
import subprocess
import shutil
import time
import glob
import json
import filecmp
from pathlib import Path

class Extractor:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.deps_dir = os.path.join(self.base_dir, "Dependencies")
        self.retail_extract_dir = os.path.join(self.base_dir, "retail_extract")
        self.tracks_dir = os.path.join(self.base_dir, "tracks")
        self.downloaded_tracks_dir = os.path.join(self.base_dir, "downloaded_tracks")
        
        # Error collection
        self.errors = []
        
        # Create necessary directories if they don't exist
        for directory in [self.tracks_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
        
        # Path to dependencies
        self.xdelta3_path = os.path.join(self.deps_dir, "xdelta3.exe")
        self.dumpsxiso_path = os.path.join(self.deps_dir, "dumpsxiso.exe")
        self.bigtool_path = os.path.join(self.deps_dir, "bigtool.exe")

    def extract_rom(self, rom_path, output_dir, xml_name=None):
        """Extract a ROM file to a directory"""
        print(f"Extracting {os.path.basename(rom_path)} to {output_dir}...")
        
        if xml_name is None:
            xml_name = f"{output_dir}.xml"
            
        # Extract the rom
        subprocess.run([
            self.dumpsxiso_path,
            rom_path,
            "-x", output_dir,
            "-s", xml_name
        ], cwd=self.base_dir, check=True)
        
        print(f"ROM extracted to {output_dir}")
        return os.path.join(self.base_dir, output_dir)

    def extract_bigfile(self, extract_dir):
        """Extract bigfile.big from an extracted ROM directory"""
        print(f"Extracting bigfile.big from {extract_dir}...")
        
        big_path = os.path.join(extract_dir, "bigfile.big")
        if not os.path.exists(big_path):
            print(f"Error: Could not find bigfile.big at {big_path}")
            return False
            
        subprocess.run([
            self.bigtool_path,
            big_path
        ], cwd=self.base_dir, check=True)
        
        print("Bigfile extracted successfully")
        return True

    def find_modified_files(self, retail_dir, modded_dir):
        """Compare directory structures and find modified files"""
        print("Comparing retail and modded ROM files to find modified tracks...")
        
        tracks_dir_retail = os.path.join(retail_dir, "bigfile", "levels", "tracks")
        tracks_dir_modded = os.path.join(modded_dir, "bigfile", "levels", "tracks")
        
        modified_levs = []
        modified_vrms = []
        modified_hwls = []
        
        # First check regular track directories
        if os.path.exists(tracks_dir_modded):
            # Walk through the modded tracks directory
            for root, dirs, files in os.walk(tracks_dir_modded):
                relative_path = os.path.relpath(root, tracks_dir_modded)
                retail_equivalent = os.path.join(tracks_dir_retail, relative_path)
                
                # Check for new directories
                if not os.path.exists(retail_equivalent):
                    print(f"Found new directory: {relative_path}")
                    for file in files:
                        if file.endswith(".lev"):
                            modified_levs.append(os.path.join(root, file))
                        if file.endswith(".vrm"):
                            modified_vrms.append(os.path.join(root, file))
                    continue
                    
                # Check for modified files
                for file in files:
                    modded_file = os.path.join(root, file)
                    retail_file = os.path.join(retail_equivalent, file)
                    
                    if not os.path.exists(retail_file) or not filecmp.cmp(modded_file, retail_file, shallow=False):
                        print(f"Found modified file: {os.path.join(relative_path, file)}")
                        if file.endswith(".lev"):
                            modified_levs.append(modded_file)
                        if file.endswith(".vrm"):
                            modified_vrms.append(modded_file)
        
        # Check for KART.HWL differences
        kart_hwl_modded = os.path.join(modded_dir, "SOUNDS", "KART.HWL")
        kart_hwl_retail = os.path.join(retail_dir, "SOUNDS", "KART.HWL")
        
        if os.path.exists(kart_hwl_modded) and os.path.exists(kart_hwl_retail):
            if not filecmp.cmp(kart_hwl_modded, kart_hwl_retail, shallow=False):
                modified_hwls.append(kart_hwl_modded)
                print(f"Found modified KART.HWL file")
        
        # Check PS1_TrackRom mod pattern if necessary
        if not modified_levs and not modified_vrms:
            print("Checking for PS1_TrackRom mod pattern...")
            level = os.path.join(modded_dir, "bigfile", "overlays", "221_EndRaceMenu_CrystalChallenge.bin")
            vrm = os.path.join(modded_dir, "bigfile", "overlays", "222_EndRaceMenu_ArcadeAdventure.bin")
            
            retail_level = os.path.join(retail_dir, "bigfile", "overlays", "221_EndRaceMenu_CrystalChallenge.bin")
            retail_vrm = os.path.join(retail_dir, "bigfile", "overlays", "222_EndRaceMenu_ArcadeAdventure.bin")
            
            if os.path.exists(level) and os.path.exists(retail_level) and not filecmp.cmp(level, retail_level, shallow=False):
                modified_levs.append(level)
                print(f"Found modified level file: {os.path.relpath(level, modded_dir)}")
            
            if os.path.exists(vrm) and os.path.exists(retail_vrm) and not filecmp.cmp(vrm, retail_vrm, shallow=False):
                modified_vrms.append(vrm)
                print(f"Found modified vrm file: {os.path.relpath(vrm, modded_dir)}")
        
        print(f"Found {len(modified_levs)} modified .lev files, {len(modified_vrms)} modified .vrm files, and {len(modified_hwls)} modified KART.HWL files")
        return modified_levs, modified_vrms, modified_hwls

    def patch_rom(self, lev_xdelta, retail_rom):
        """Apply xdelta patch to create a patched ROM"""
        print("Patching ROM...")
        
        output_bin = f"{os.path.splitext(os.path.basename(lev_xdelta))[0]}.bin"
        
        subprocess.run([
            self.xdelta3_path, 
            "-d", "-f", "-s", 
            retail_rom, 
            lev_xdelta, 
            output_bin
        ], cwd=self.base_dir, check=True)
        
        print("ROM patched successfully")
        
        return os.path.join(self.base_dir, output_bin)

    def copy_track_files(self, lev_paths, vrm_paths, hwl_paths, track_name, output_dir, xdelta_path, track_info_path):
        """Copy identified track files to output location"""
        print(f"Copying track files to {output_dir}...")
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        if not lev_paths and not vrm_paths:
            print("Warning: Could not identify any .lev or .vrm files!")
            print("Files might not be extracted correctly.")
        
        # Sanitize track name for file naming
        sanitized_name = self.sanitize_name(track_name)
        
        # Copy .lev files if found
        for i, lev_path in enumerate(lev_paths):
            if os.path.exists(lev_path):
                # If multiple files found, add _track_N suffix
                if len(lev_paths) > 1:
                    target_name = f"{sanitized_name}_track_{i+1}.lev"
                else:
                    target_name = f"{sanitized_name}.lev"
                    
                shutil.copy(lev_path, os.path.join(output_dir, target_name))
                print(f"{target_name} extracted successfully")
                
        # Copy .vrm files if found
        for i, vrm_path in enumerate(vrm_paths):
            if os.path.exists(vrm_path):
                # If multiple files found, add _track_N suffix
                if len(vrm_paths) > 1:
                    target_name = f"{sanitized_name}_track_{i+1}.vrm"
                else:
                    target_name = f"{sanitized_name}.vrm"
                    
                shutil.copy(vrm_path, os.path.join(output_dir, target_name))
                print(f"{target_name} extracted successfully")
        
        # Copy KART.HWL files if found
        for hwl_path in hwl_paths:
            if os.path.exists(hwl_path):
                shutil.copy(hwl_path, os.path.join(output_dir, "KART.HWL"))
                print("KART.HWL extracted successfully")
        
        # Copy .xdelta file
        shutil.copy(xdelta_path, os.path.join(output_dir, os.path.basename(xdelta_path)))
        print(f"{os.path.basename(xdelta_path)} copied successfully")
        
        # Copy track_info.json
        if os.path.exists(track_info_path):
            shutil.copy(track_info_path, os.path.join(output_dir, "track_info.json"))
            print("track_info.json copied successfully")
            
        return output_dir
    
    def sanitize_name(self, name):
        """Remove invalid characters from names"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name.strip()

    def cleanup_temp_files(self, levelname, patched_rom):
        """Delete temporary files and directories"""
        print("Cleaning up temporary files...")
        
        # Allow files to be fully written
        time.sleep(2)
        
        # Delete extracted directory
        extracted_dir = os.path.join(self.base_dir, levelname)
        if os.path.isdir(extracted_dir):
            shutil.rmtree(extracted_dir)
        
        # Delete temporary files
        temp_files = [
            os.path.join(self.base_dir, f"{levelname}.xml"),  # XML file
            patched_rom,  # Patched ROM file
            os.path.join(self.base_dir, "bigfile")  # Extracted bigfile directory
        ]
        
        for file_path in temp_files:
            if os.path.exists(file_path):
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
                print(f"Removed: {os.path.basename(file_path)}")
        
        print("Cleanup finished")
    
    def load_track_info(self, track_folder):
        """Load track_info.json from a track folder"""
        track_info_path = os.path.join(track_folder, "track_info.json")
        if os.path.exists(track_info_path):
            try:
                with open(track_info_path, 'r', encoding='utf-8') as f:
                    return json.load(f), track_info_path
            except Exception as e:
                self.errors.append(f"Failed to load track_info.json from '{track_folder}': {e}")
                return None, track_info_path
        return None, track_info_path
    
    def process_xdelta_file(self, xdelta_path, retail_rom, track_name, output_dir, track_info_path):
        """Process a single xdelta file"""
        levelname = os.path.splitext(os.path.basename(xdelta_path))[0]
        
        print(f"\n{'-'*40}\nProcessing xdelta: {levelname}\n{'-'*40}")
        
        try:
            # Patch the ROM
            patched_rom = self.patch_rom(xdelta_path, retail_rom)
            
            # Extract the modded ROM
            modded_extract_path = self.extract_rom(patched_rom, levelname)
            self.extract_bigfile(modded_extract_path)
            
            # Find and process modified files
            modified_levs, modified_vrms, modified_hwls = self.find_modified_files(self.retail_extract_dir, modded_extract_path)
            self.copy_track_files(modified_levs, modified_vrms, modified_hwls, track_name, output_dir, xdelta_path, track_info_path)
            
            # Clean up temporary files
            self.cleanup_temp_files(levelname, patched_rom)
            
            return True
        except Exception as e:
            error_msg = f"Error processing xdelta '{xdelta_path}': {e}"
            self.errors.append(error_msg)
            print(f"✗ {error_msg}")
            # Try cleanup even on error
            try:
                self.cleanup_temp_files(levelname, os.path.join(self.base_dir, f"{levelname}.bin"))
            except:
                pass
            return False
    
    def process_track_folder(self, track_folder, retail_rom):
        """Process all xdelta files in a downloaded track folder"""
        folder_name = os.path.basename(track_folder)
        
        print(f"\n{'='*60}")
        print(f"Processing track folder: {folder_name}")
        print(f"{'='*60}")
        
        # Load track info
        track_info, track_info_path = self.load_track_info(track_folder)
        
        if track_info:
            track_name = track_info.get("track_name", folder_name)
            print(f"Track Name: {track_name}")
            print(f"Author: {track_info.get('author', 'Unknown')}")
            print(f"Date: {track_info.get('date', 'Unknown')}")
        else:
            track_name = folder_name
            print(f"Warning: No track_info.json found, using folder name: {track_name}")
        
        # Find all xdelta files in this track folder
        xdelta_files = glob.glob(os.path.join(track_folder, "*.xdelta"))
        
        if not xdelta_files:
            error_msg = f"No xdelta files found in '{track_folder}'"
            self.errors.append(error_msg)
            print(f"✗ {error_msg}")
            return
        
        print(f"Found {len(xdelta_files)} xdelta file(s)")
        
        # Sanitize track name for folder
        sanitized_track_name = self.sanitize_name(track_name)
        track_output_dir = os.path.join(self.tracks_dir, sanitized_track_name)
        
        if not os.path.exists(track_output_dir):
            os.makedirs(track_output_dir)
        
        # Process xdelta files
        if len(xdelta_files) == 1:
            # Single xdelta - no subfolder needed
            self.process_xdelta_file(xdelta_files[0], retail_rom, track_name, track_output_dir, track_info_path)
        else:
            # Multiple xdeltas - create numbered subfolders
            for idx, xdelta_path in enumerate(xdelta_files, 1):
                subfolder = os.path.join(track_output_dir, str(idx))
                print(f"\nProcessing xdelta {idx}/{len(xdelta_files)}...")
                self.process_xdelta_file(xdelta_path, retail_rom, track_name, subfolder, track_info_path)

    def run(self):
        """Main execution flow"""
        # Find retail ROM
        ctr_bins = glob.glob(os.path.join(self.base_dir, "*.bin"))
        
        if not ctr_bins:
            print("ERROR: Can't find any .bin files in the base folder!")
            print("ERROR: Make sure to paste the retail ROM in this folder")
            return
        
        # Check if downloaded_tracks folder exists
        if not os.path.exists(self.downloaded_tracks_dir):
            print(f"ERROR: Can't find the '{self.downloaded_tracks_dir}' folder!")
            print("ERROR: Run ct_downloader.py first to download tracks")
            return
        
        # Find all track folders in downloaded_tracks
        track_folders = [
            os.path.join(self.downloaded_tracks_dir, d) 
            for d in os.listdir(self.downloaded_tracks_dir) 
            if os.path.isdir(os.path.join(self.downloaded_tracks_dir, d))
        ]
        
        if not track_folders:
            print(f"ERROR: No track folders found in '{self.downloaded_tracks_dir}'!")
            return
        
        # Use the first retail ROM found
        retail_rom = ctr_bins[0]
        print(f"Using retail ROM: {os.path.basename(retail_rom)}")
        print(f"Found {len(track_folders)} track folder(s) to process")
        
        # Extract retail ROM if not already extracted
        if not os.path.exists(self.retail_extract_dir):
            try:
                retail_extract_path = self.extract_rom(retail_rom, "retail_extract")
                self.extract_bigfile(retail_extract_path)
            except Exception as e:
                error_msg = f"Failed to extract retail ROM: {e}"
                self.errors.append(error_msg)
                print(f"✗ {error_msg}")
                return
        else:
            print("Retail ROM already extracted, skipping extraction.")
        
        # Process each track folder
        for i, track_folder in enumerate(track_folders, 1):
            print(f"\n[{i}/{len(track_folders)}] Processing track folder...")
            try:
                self.process_track_folder(track_folder, retail_rom)
            except Exception as e:
                error_msg = f"Critical error processing folder '{os.path.basename(track_folder)}': {e}"
                self.errors.append(error_msg)
                print(f"✗ {error_msg}")
                continue
        
        print(f"\n{'='*60}")
        print("All track folders processed!")
        print(f"{'='*60}")
        
        # Print all errors at the end
        if self.errors:
            print(f"\n{'='*60}")
            print(f"ERRORS SUMMARY ({len(self.errors)} total errors)")
            print(f"{'='*60}\n")
            for idx, error in enumerate(self.errors, 1):
                print(f"{idx}. {error}")
            print(f"\n{'='*60}")
        else:
            print("\n✓ No errors encountered during execution!")


if __name__ == "__main__":
    extractor = Extractor()
    extractor.run()