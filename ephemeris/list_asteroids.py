import os
from pathlib import Path

def list_ephemeris_asteroids_recursively(directory_path):
    ephemeris_dir = Path(directory_path)

    if not ephemeris_dir.exists():
        print(f"Oops! The directory '{directory_path}' does not exist.")
        return

    if not ephemeris_dir.is_dir():
        print(f"Oops! '{directory_path}' is a file, not a directory.")
        return

    eph_extensions = {'.se1', '.swe', '.bsp', '.eph'}
    asteroid_files = []

    # Using rglob('*') tells Python to search this folder AND all subfolders recursively!
    for file_path in ephemeris_dir.rglob('*'):
        if file_path.is_file():
            if file_path.suffix.lower() in eph_extensions:
                # This grabs the path relative to your main folder so it's clean and readable
                relative_path = file_path.relative_to(ephemeris_dir)
                asteroid_files.append(str(relative_path))

    print(f"\n--- Deep Scanning: {directory_path} ---\n")
    
    if asteroid_files:
        print(f"✨ Found {len(asteroid_files)} ephemeris/asteroid files:")
        for ast in sorted(asteroid_files):
            print(f"  • {ast}")
    else:
        print(f"No common ephemeris files ({', '.join(eph_extensions)}) were found.")

if __name__ == "__main__":
    target_dir = r"C:\entangled_oracle\ephemeris"
    list_ephemeris_asteroids_recursively(target_dir)