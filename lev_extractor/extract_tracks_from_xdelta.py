import argparse
import os
import glob

from lev_extractor import Extractor


def print_summary(errors):
    print(f"\n{'='*60}")
    print("Xdelta folder processing finished")
    print(f"{'='*60}")

    if errors:
        print(f"\n{'='*60}")
        print(f"ERRORS SUMMARY ({len(errors)} total errors)")
        print(f"{'='*60}\n")
        for idx, error in enumerate(errors, 1):
            print(f"{idx}. {error}")
        print(f"\n{'='*60}")
    else:
        print("\n✓ No errors encountered during execution!")

def ensure_retail_extracted(extractor, retail_rom):
    if os.path.exists(extractor.retail_extract_dir):
        print("Retail ROM already extracted, skipping extraction.")
        return True

    try:
        retail_extract_path = extractor.extract_rom(
            retail_rom,
            extractor.retail_extract_dir,
            xml_name="retail_extract.xml",
        )
        extractor.extract_bigfile(retail_extract_path)
        return True
    except Exception as e:
        error_msg = f"Failed to extract retail ROM: {e}"
        extractor.errors.append(error_msg)
        print(f"✗ {error_msg}")
        return False

def resolve_path(base_path, path):
    """Resolve path to absolute path based on base_path when needed."""
    if path is None:
        return None
    if os.path.isabs(path):
        return path
    return os.path.join(base_path, path)

def run_xdeltas_folder(extractor, retail_rom, xdelta_dir, output_root):
    if not os.path.exists(xdelta_dir):
        print(f"ERROR: Source xdelta directory does not exist: {xdelta_dir}")
        return

    xdelta_files = sorted(glob.glob(os.path.join(xdelta_dir, "*.xdelta")))
    if not xdelta_files:
        print(f"ERROR: No xdelta files found in '{xdelta_dir}'")
        return

    os.makedirs(output_root, exist_ok=True)

    print(f"Using retail ROM: {os.path.basename(retail_rom)}")
    print(f"Found {len(xdelta_files)} xdelta file(s) in {xdelta_dir}")

    if not ensure_retail_extracted(extractor, retail_rom):
        print_summary(extractor.errors)
        return

    for idx, xdelta_path in enumerate(xdelta_files, 1):
        xdelta_name = os.path.splitext(os.path.basename(xdelta_path))[0]
        output_track_dir = os.path.join(output_root, extractor.sanitize_name(xdelta_name))

        print(f"\n[{idx}/{len(xdelta_files)}] Processing xdelta from directory...")
        extractor.process_xdelta_file(
            xdelta_path=xdelta_path,
            retail_rom=retail_rom,
            track_name=xdelta_name,
            output_dir=output_track_dir,
            track_info_path=None,
        )

    print_summary(extractor.errors)


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    parser = argparse.ArgumentParser(
        description="Extract track files from a folder that contains .xdelta files"
    )
    parser.add_argument(
        "--retail-rom",
        default=None,
        help="Path to retail .bin ROM (default: first .bin in script directory)",
    )
    parser.add_argument(
        "--xdelta-dir",
        default=script_dir,
        help="Folder containing .xdelta files (default: current script folder)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output folder for extracted files",
    )

    args = parser.parse_args()

    extractor = Extractor(base_dir=script_dir)

    if not args.retail_rom:
        print("No retail ROM path provided")
        return

    run_xdeltas_folder(extractor, args.retail_rom, args.xdelta_dir, args.output_dir)

if __name__ == "__main__":
    main()
