import os
from pathlib import Path
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError

# Use current working directory
root_folder = Path.cwd()
output_dir = root_folder / "output_logs"
output_dir.mkdir(exist_ok=True)

print(f"🔍 Scanning MP3s under: {root_folder}\n")

# Walk through all subfolders
for dirpath, _, filenames in os.walk(root_folder):
    mp3_files = [f for f in filenames if f.lower().endswith(".mp3")]
    if not mp3_files:
        continue

    bad_files = []
    rel_folder = Path(dirpath).relative_to(root_folder)
    if rel_folder.parts[0] == "output_logs":
        continue  # Skip logging output folder itself

    print(f"📁 Folder: {rel_folder}")

    for idx, filename in enumerate(mp3_files, start=1):
        full_path = Path(dirpath) / filename
        print(f"  [{idx}] Testing: {full_path}")
        try:
            audio = AudioSegment.from_mp3(full_path)
        except CouldntDecodeError:
            print("    ❌ Could not decode")
            bad_files.append(str(full_path))
        except Exception as e:
            print(f"    ❌ Error: {str(e)}")
            bad_files.append(f"{full_path} - Error: {str(e)}")
        else:
            print("    ✅ OK")

    if bad_files:
        # Create safe filename
        subfolder_name = rel_folder.name or "root"
        log_file = output_dir / f"{subfolder_name}.txt"
        with open(log_file, "w") as f:
            for bad_file in bad_files:
                f.write(bad_file + "\n")
        print(f"  📄 Written: {log_file}\n")
    else:
        print("  ✅ All MP3s good, no log written.\n")

print("✅ Done.")
